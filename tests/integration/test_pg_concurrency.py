"""Booking concurrency on REAL PostgreSQL (not SQLite). 20 threads, each its own connection/transaction, released together.
Runs against PG_TEST_URL if set, else an embedded server via `pgserver` if installed, else SKIPPED (status: READY / NOT EXECUTED)."""
from __future__ import annotations
import datetime as dt
import os
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("APP_ENV", "test")
os.environ["LAB_NOW"] = "2026-10-01T11:00:00"
from backend.db import Base
from backend import models as M, schemas as S, service

N = 20


def _pg_url():
    if os.environ.get("PG_TEST_URL"):
        return os.environ["PG_TEST_URL"], None
    try:
        import pgserver
    except ImportError:
        pytest.skip("No PostgreSQL available (set PG_TEST_URL or pip install pgserver): READY / NOT EXECUTED")
    srv = pgserver.get_server(tempfile.mkdtemp(), cleanup_mode="stop")
    uri = srv.get_uri()                                  # postgresql://postgres:@/postgres?host=/tmp/...
    return uri.replace("postgresql://", "postgresql+psycopg://", 1), srv


@pytest.fixture(scope="module")
def pg():
    url, srv = _pg_url()
    eng = create_engine(url, pool_size=N + 5, max_overflow=5, future=True)
    Base.metadata.drop_all(eng); Base.metadata.create_all(eng)
    Session = sessionmaker(bind=eng, expire_on_commit=False, future=True)
    s = Session()
    s.add(M.Tenant(id="t1", name="T1", locality="x")); s.flush()
    s.add(M.Advisor(id="a1", tenant_id="t1", name="Srinivas Reddy", name_te="శ్రీనివాస్ రెడ్డి"))
    s.add(M.Service(id="svc_oil", tenant_id="t1", code="oil_change", name_en="Oil change", name_te="ఆయిల్ చేంజ్",
                    aliases=[], price_inr=1899, price_note="", duration_min=45)); s.flush()
    for sid in ("LAST1", "LAST2"):
        s.add(M.Slot(id=sid, tenant_id="t1", advisor_id="a1", date=dt.date(2026, 10, 2), start=dt.time(10), capacity=1, booked=0))
    s.commit(); s.close()
    version = eng.connect().exec_driver_sql("select version()").scalar()
    yield Session, version
    eng.dispose()


def _hammer(Session, slot_id: str, interaction_ids: list[str]):
    barrier = threading.Barrier(len(interaction_ids))

    def one(iid):
        db = Session()
        try:
            req = S.CreateBookingRequest(slot_id=slot_id, service="oil change", customer_phone="9848012345",
                                         vehicle_reg="TS09EA4521", caller_confirmed=True, interaction_id=iid)
            barrier.wait()                                   # release all transactions at the same instant
            return service.create_booking(db, "t1", "rid-" + iid, req)
        finally:
            db.close()
    with ThreadPoolExecutor(max_workers=len(interaction_ids)) as ex:
        return list(ex.map(one, interaction_ids))


def test_seed_runs_on_postgres(pg, monkeypatch):
    """SQLite does not enforce foreign keys by default; the seed must still be valid on PostgreSQL."""
    Session, _ = pg
    import backend.seed as seed_mod
    monkeypatch.setattr(seed_mod, "SessionLocal", Session)
    monkeypatch.setattr(seed_mod.Base.metadata, "create_all", lambda *a, **k: None)
    seed_mod.seed(days=3)
    s = Session()
    assert s.scalar(select(func.count()).select_from(M.Vehicle).where(M.Vehicle.tenant_id == seed_mod.TENANT)) >= 10
    s.close()


def test_20_different_callers_one_seat(pg):
    Session, version = pg
    out = _hammer(Session, "LAST1", [f"call-{i}" for i in range(N)])
    statuses = [r.status for r in out]
    s = Session()
    booked = s.get(M.Slot, "LAST1").booked
    n_bookings = s.scalar(select(func.count()).select_from(M.Booking).where(M.Booking.slot_id == "LAST1"))
    s.close()
    print(f"\n[{version.split(',')[0]}] different callers: {statuses.count('confirmed')} confirmed, "
          f"{statuses.count('unavailable')} unavailable, bookings={n_bookings}, slot.booked={booked}")
    assert statuses.count("confirmed") == 1 and statuses.count("unavailable") == N - 1
    assert n_bookings == 1 and booked == 1
    refs = {r.booking_ref for r in out if r.status == "confirmed"}
    assert len(refs) == 1


def test_20_retries_same_request_one_booking(pg):
    Session, version = pg
    out = _hammer(Session, "LAST2", ["same-call"] * N)
    statuses = [r.status for r in out]
    refs = {r.booking_ref for r in out if r.status == "confirmed"}
    s = Session()
    booked = s.get(M.Slot, "LAST2").booked
    n_bookings = s.scalar(select(func.count()).select_from(M.Booking).where(M.Booking.slot_id == "LAST2"))
    s.close()
    print(f"\n[{version.split(',')[0]}] same request x{N}: statuses={sorted(set(statuses))}, refs={len(refs)}, "
          f"bookings={n_bookings}, slot.booked={booked}")
    assert n_bookings == 1 and booked == 1 and len(refs) == 1
    assert statuses.count("confirmed") == N, f"retries must all resolve to the same booking, got {statuses}"
