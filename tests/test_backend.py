import os, datetime as dt
os.environ["DATABASE_URL"] = "sqlite:///./test_lab.db"
os.environ["LAB_NOW"] = "2026-10-01T11:00:00"   # Thursday, IST
if os.path.exists("test_lab.db"):
    os.remove("test_lab.db")
import pytest
from fastapi.testclient import TestClient
from backend.seed import seed, add_credential, TENANT
from backend.db import SessionLocal
from backend.models import Tenant, Slot, RequestCapture, Booking

seed()
SECRET = add_credential(TENANT, "test")
db = SessionLocal(); db.merge(Tenant(id="other-tenant", name="Other", locality="Vijayawada")); db.commit(); db.close()
OTHER = add_credential("other-tenant", "other")
from backend.app import app
client = TestClient(app)
H = {"Authorization": f"Bearer {SECRET}"}
CALLER = "9000000101"


def post(tool, body, headers=H):
    return client.post(f"/tools/{tool}", json=body, headers=headers)


def test_auth_required():
    assert post("get_business_hours", {}, headers={}).status_code == 401
    assert post("get_business_hours", {}, headers={"Authorization": "Bearer nope"}).status_code == 401


def test_model_cannot_choose_tenant():
    r = post("lookup_customer", {"tenant_id": "other-tenant", "caller_number": CALLER})
    assert r.status_code == 400 and r.json()["status"] == "rejected"


def test_business_hours():
    r = post("get_business_hours", {}).json()
    assert r["status"] == "ok" and r["today_weekday"] == "Thursday" and r["is_open_now"] is True
    assert r["hours"][6]["opens"] is None


def test_service_info_price_from_db():
    r = post("get_service_info", {"service": "బ్రేక్ చెక్"}).json()
    assert r["status"] == "ok" and r["services"][0]["price_inr"] == 499


def test_lookup_privacy():
    own = post("lookup_customer", {"caller_number": CALLER}).json()
    assert own["name"] == "Venkat Reddy" and own["vehicles"][0]["reg_full"] == "TS09EA4521"
    other = post("lookup_customer", {"caller_number": CALLER, "phone": "9000000102"}).json()
    assert other["found"] and other["name"] is None and other["vehicles"][0]["reg_full"] is None


def test_availability_and_ambiguity():
    r = post("check_availability", {"date_expression": "రేపు", "time_expression": "సాయంత్రం 4"}).json()
    assert r["status"] == "ok" and r["resolved_weekday"] == "Friday" and r["slots"]
    assert all(s["time"] in ("15:00", "16:00", "17:00") for s in r["slots"])
    amb = post("check_availability", {"date_expression": "next Saturday"}).json()
    assert amb["status"] == "needs_clarification"
    sun = post("check_availability", {"date_expression": "Sunday"}).json()
    assert sun["status"] == "unavailable"
    adv = post("check_availability", {"date_expression": "రేపు", "advisor": "Srinivas garu"}).json()
    assert adv["status"] == "needs_clarification" and set(adv["candidates"]) == {"Srinivas Reddy", "Srinivas Rao"}


def _slot():
    r = post("check_availability", {"date_expression": "రేపు", "time_expression": "10:00"}).json()
    return r["slots"][0]["slot_id"]


def test_booking_requires_confirmation_and_is_idempotent():
    slot = _slot()
    body = {"slot_id": slot, "service": "oil change", "customer_phone": "98480 12345",
            "vehicle_reg": "TS 09 EA 4521", "caller_confirmed": False, "interaction_id": "call-1"}
    assert post("create_booking", body).json()["status"] == "rejected"
    body["caller_confirmed"] = True
    a = post("create_booking", body).json()
    b = post("create_booking", body).json()
    assert a["status"] == "confirmed" and a["booking_ref"] == b["booking_ref"]
    s = SessionLocal(); assert s.get(Slot, slot).booked == 1
    s.close()
    body["interaction_id"] = "call-2"
    assert post("create_booking", body).json()["status"] == "unavailable"


def test_booking_rejects_invalid_entities():
    slot = _slot()
    base = {"slot_id": slot, "service": "oil change", "customer_phone": "12345", "vehicle_reg": "TS09EA4521",
            "caller_confirmed": True, "interaction_id": "call-3"}
    assert post("create_booking", base).json()["status"] == "needs_clarification"
    base |= {"customer_phone": "9848012345", "vehicle_reg": "TS 09 EA"}
    assert post("create_booking", base).json()["status"] == "needs_clarification"


def test_cross_tenant_slot_rejected():
    slot = _slot()
    r = post("create_booking", {"slot_id": slot, "service": "oil change", "customer_phone": "9848012345",
                                "vehicle_reg": "TS09EA4521", "caller_confirmed": True, "interaction_id": "x"},
             headers={"Authorization": f"Bearer {OTHER}"}).json()
    assert r["status"] in ("not_found", "needs_clarification")


def test_callback_and_capture_redaction():
    r = post("request_callback", {"reason": "price for clutch plate", "caller_number": CALLER, "interaction_id": "c9"}).json()
    assert r["status"] == "confirmed" and r["phone_readback"] == "90000 00101"
    s = SessionLocal()
    cap = s.query(RequestCapture).order_by(RequestCapture.id.desc()).first()
    s.close()
    assert SECRET not in str(cap.headers) and "REDACTED" in cap.headers["authorization"]
