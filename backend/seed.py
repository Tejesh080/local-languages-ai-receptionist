"""Seed the fictional benchmark tenant. All names, phones and vehicles are fictional."""
from __future__ import annotations
import datetime as dt
import sys
from sqlalchemy import delete
from .db import Base, SessionLocal, engine
from .models import (Tenant, Advisor, Service, BusinessHours, Customer, Vehicle, Slot, AgentCredential, Booking, Callback)
from .service import now_ist
from .tenancy import sha256, new_secret

TENANT = "kaveri-auto-care"

ADVISORS = [("adv1", "Srinivas Reddy", "శ్రీనివాస్ రెడ్డి"), ("adv2", "Srinivas Rao", "శ్రీనివాస్ రావు"),
            ("adv3", "Lakshmi Naidu", "లక్ష్మి నాయుడు")]
SERVICES = [
    ("general_service", "General service", "జనరల్ సర్వీస్", ["full service", "periodic service", "car service", "servicing", "సర్వీసింగ్", "సర్వీస్"], 3499, "starting price; parts extra", 180),
    ("oil_change", "Oil change", "ఆయిల్ చేంజ్", ["engine oil change", "oil marchali", "ఆయిల్ మార్చాలి", "ఇంజన్ ఆయిల్"], 1899, "includes oil filter", 45),
    ("brake_inspection", "Brake inspection", "బ్రేక్ ఇన్స్పెక్షన్", ["brake check", "brakes", "బ్రేక్ చెక్", "బ్రేకులు"], 499, "inspection only; repairs quoted after", 30),
    ("ac_repair", "AC repair", "ఏసీ రిపేర్", ["ac service", "ac not cooling", "ఏసీ సర్వీస్", "ఏసీ కూలింగ్"], 1200, "diagnosis and gas top-up, starting price", 90),
    ("battery_replacement", "Battery replacement", "బ్యాటరీ మార్పు", ["battery change", "new battery", "బ్యాటరీ చేంజ్", "బ్యాటరీ"], 4500, "starting price; depends on battery model", 30),
    ("wheel_alignment", "Wheel alignment", "వీల్ అలైన్మెంట్", ["alignment", "wheel balancing", "అలైన్మెంట్"], 699, "alignment only; balancing extra", 45),
]
CUSTOMERS = [  # (id, name, phone, [(reg, model)])  fictional 90000xxxxx numbers
    ("c01", "Venkat Reddy", "9000000101", [("TS09EA4521", "Maruti Swift")]),
    ("c02", "Venkat Rao", "9000000102", [("TS09EA4527", "Hyundai i20")]),
    ("c03", "Ravi Naidu", "9000000103", [("AP39BK7788", "Honda City")]),
    ("c04", "Priya Sharma", "9000000104", [("TG08C1234", "Tata Nexon")]),
    ("c05", "Suresh Babu", "9000000105", [("TS07FJ3301", "Maruti Baleno"), ("TS07FJ3310", "Honda Activa")]),
    ("c06", "Anjali Chowdary", "9000000106", [("AP16DD9090", "Toyota Innova")]),
    ("c07", "Mahesh Goud", "9000000107", [("TG10AB0042", "Mahindra XUV300")]),
    ("c08", "Kiran Kumar", "9000000108", [("TS13EZ5566", "Kia Sonet")]),
    ("c09", "Sai Teja", "9000000109", [("22BH1234AB", "Hyundai Creta")]),
    ("c10", "Harika Yadav", "9000000110", [("TS08GH7070", "Renault Kwid")]),
]


def seed(days: int = 21) -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    for m in (Booking, Callback, Slot, Vehicle, Customer, BusinessHours, Service, Advisor):
        db.execute(delete(m).where(m.tenant_id == TENANT))
    db.merge(Tenant(id=TENANT, name="Kaveri Auto Care (fictional)", locality="Kukatpally, Hyderabad"))
    db.flush()                     # PostgreSQL enforces FKs (SQLite does not by default): parents first
    for aid, n, nte in ADVISORS:
        db.add(Advisor(id=aid, tenant_id=TENANT, name=n, name_te=nte))
    for code, en, te, aliases, price, note, mins in SERVICES:
        db.add(Service(id="svc_" + code, tenant_id=TENANT, code=code, name_en=en, name_te=te, aliases=aliases,
                       price_inr=price, price_note=note, duration_min=mins))
    for d in range(7):
        db.add(BusinessHours(tenant_id=TENANT, weekday=d, opens=None if d == 6 else dt.time(9),
                             closes=None if d == 6 else dt.time(19)))
    db.flush()
    for cid, n, ph, vehicles in CUSTOMERS:
        db.add(Customer(id=cid, tenant_id=TENANT, name=n, phone=ph))
        db.flush()
        for i, (reg, model) in enumerate(vehicles):
            db.add(Vehicle(id=f"{cid}v{i}", tenant_id=TENANT, customer_id=cid, reg=reg, make_model=model))
    db.flush()
    start = now_ist().date()
    for k in range(days):
        day = start + dt.timedelta(days=k)
        if day.weekday() == 6:
            continue
        for h in range(9, 18):
            for aid, *_ in ADVISORS:
                db.add(Slot(id=f"S{day:%m%d}{h:02d}{aid[-1]}", tenant_id=TENANT, advisor_id=aid, date=day, start=dt.time(h)))
    db.commit()
    db.close()


def add_credential(tenant: str, label: str, purpose: str = "tools") -> str:
    if purpose not in ("tools", "webhook"):
        raise ValueError("purpose must be tools or webhook")
    Base.metadata.create_all(engine)
    secret = new_secret()
    db = SessionLocal()
    db.add(AgentCredential(tenant_id=tenant, label=label, purpose=purpose, secret_sha256=sha256(secret)))
    db.commit()
    db.close()
    return secret


if __name__ == "__main__":
    seed()
    if len(sys.argv) > 1 and sys.argv[1] == "--with-credentials":
        # Printed once to the terminal (stdout), never to application logs. Only SHA-256 hashes are stored.
        print("TOOLS_BEARER_SECRET=" + add_credential(TENANT, "sarvam-agent-smoke", "tools"))
        print("WEBHOOK_METADATA_TOKEN=" + add_credential(TENANT, "sarvam-webhook", "webhook"))
        print("Store these now in your password manager; they cannot be shown again.")
    print("seeded", TENANT)
