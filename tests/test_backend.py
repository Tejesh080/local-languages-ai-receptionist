import os, datetime as dt
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test_lab.db"
os.environ["PHONE_HASH_SALT"] = "unit-test-salt-not-secret"
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


def test_lookup_is_identification_not_authentication():
    own = post("lookup_customer", {"caller_number": CALLER}).json()
    assert own["caller_id_match"] is True and own["identity_assurance"] == "unverified_caller_id"
    assert own["authenticated"] is False and "name" not in own
    assert own["vehicles"][0]["reg_masked"] == "****4521" and "TS09EA4521" not in str(own)
    other = post("lookup_customer", {"caller_number": CALLER, "phone": "9000000102"}).json()
    assert other["found"] and other["caller_id_match"] is False and other["vehicles"] == []
    assert other["identity_assurance"] == "none" and other["authenticated"] is False


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


PII = {"customer_phone": "9848077777", "customer_name": "Bhavani Shankar", "vehicle_reg": "TS 11 ZZ 9876",
       "caller_number": "+919812300000", "reason": "my daughter Keerthi needs the car on Friday", "preferred_time": "after 6 at Madhapur office"}


def test_default_capture_and_logs_contain_no_pii():
    from backend.models import ToolCallLog
    slot = _slot()
    post("create_booking", {"slot_id": slot, "service": "oil change", "caller_confirmed": True, "interaction_id": "pii-1", **{k: v for k, v in PII.items() if k in ("customer_phone", "customer_name", "vehicle_reg", "caller_number")}})
    post("request_callback", {"interaction_id": "pii-2", "phone": PII["customer_phone"], "reason": PII["reason"], "preferred_time": PII["preferred_time"], "caller_number": PII["caller_number"]})
    post("lookup_customer", {"caller_number": PII["caller_number"], "phone": PII["customer_phone"], "interaction_id": "pii-3"})
    s = SessionLocal()
    dump = str([(c.body, c.headers, c.query) for c in s.query(RequestCapture).all()]) + str(
        [(t.request_json, t.response_json) for t in s.query(ToolCallLog).all()])
    s.close()
    needles = ["9848077777", "98480 77777", "Bhavani", "TS11ZZ9876", "TS 11 ZZ 9876", "9812300000", "Keerthi", "Madhapur", "T S 1 1 Z Z"]
    leaked = [n for n in needles if n in dump]
    assert not leaked, f"PII leaked into persisted capture/logs: {leaked}"
    assert "'present': True" in dump and "sha256" in dump           # correlation still possible via salted hashes


def test_credential_purposes_are_not_interchangeable():
    wh = add_credential(TENANT, "wh-test", "webhook")
    assert post("get_business_hours", {}, headers={"Authorization": f"Bearer {wh}"}).status_code == 401
    r = client.post("/webhooks/sarvam/call-complete", json={"interaction_id": "w0", "metadata": {"tvl_webhook_token": SECRET}})
    assert r.status_code == 401


def test_webhook_auth_and_privacy():
    wh = add_credential(TENANT, "wh-test2", "webhook")
    body = {"app_id": "A1", "app_version": 3, "deployment_id": "D1", "interaction_id": "20261001/abc",
            "user_phone_number": "+919812300000", "agent_phone_number": "+918000000000", "duration": 51.5,
            "interaction_transcript": [{"role": "user", "en_text": "my name is Bhavani"}],
            "final_agent_variables": {"customer_name": "Bhavani"}, "metadata": {"tvl_webhook_token": wh}}
    assert client.post("/webhooks/sarvam/call-complete", json={**body, "metadata": {}}).status_code == 401
    assert client.post("/webhooks/sarvam/call-complete", json={**body, "metadata": {"tvl_webhook_token": "nope"}}).status_code == 401
    assert client.post("/webhooks/sarvam/call-complete", json=body).status_code == 200
    assert client.post("/webhooks/sarvam/call-complete", json=body).status_code == 200      # retry is idempotent
    from backend.models import CallRecord
    s = SessionLocal(); rec = s.get(CallRecord, "20261001/abc"); s.close()
    assert rec.duration_s == 51.5 and rec.transcript == [] and "Bhavani" not in str(rec.final_variables) + str(rec.raw)
    assert "9812300000" not in str(rec.raw) + rec.caller_hash
    other_wh = add_credential("other-tenant", "wh-other", "webhook")
    r = client.post("/webhooks/sarvam/call-complete", json={**body, "metadata": {"tvl_webhook_token": other_wh}})
    assert r.status_code == 409                                                          # cannot overwrite another tenant's call
