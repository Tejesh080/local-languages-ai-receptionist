"""Deterministic business logic. The LLM phrases; this module decides facts."""
from __future__ import annotations
import datetime as dt
import hashlib
import os
import uuid
from zoneinfo import ZoneInfo
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from entities.normalize import normalize_phone, normalize_vehicle_reg, format_phone_readback, format_vehicle_reg_readback
from entities.dates import parse_date, parse_time
from entities.resolver import Candidate, resolve_name
from . import schemas as S
from .models import Tenant, BusinessHours, Service, Customer, Vehicle, Slot, Booking, Callback, Advisor

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
IST = ZoneInfo("Asia/Kolkata")


def now_ist() -> dt.datetime:
    override = os.environ.get("LAB_NOW")
    return dt.datetime.fromisoformat(override).replace(tzinfo=IST) if override else dt.datetime.now(IST)


def _key(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def _services(db: Session, tenant_id: str) -> list[Service]:
    return list(db.scalars(select(Service).where(Service.tenant_id == tenant_id)))


def _resolve_service(db: Session, tenant_id: str, text: str):
    svcs = _services(db, tenant_id)
    cands = [Candidate(s.id, s.name_en, [s.name_te, s.code.replace("_", " "), *s.aliases]) for s in svcs]
    res = resolve_name(text, cands, confirm_threshold=0.78)
    by_id = {s.id: s for s in svcs}
    return res, by_id


def business_hours(db: Session, tenant_id: str, rid: str, req: S.BusinessHoursRequest | None = None) -> S.BusinessHoursResponse:
    t = db.get(Tenant, tenant_id)
    rows = {r.weekday: r for r in db.scalars(select(BusinessHours).where(BusinessHours.tenant_id == tenant_id))}
    now = now_ist()
    today = rows.get(now.weekday())
    open_now = bool(today and today.opens and today.opens <= now.time() < today.closes)
    hours = [S.DayHours(weekday=WEEKDAY_NAMES[d], opens=rows[d].opens.strftime("%H:%M") if d in rows and rows[d].opens else None,
                        closes=rows[d].closes.strftime("%H:%M") if d in rows and rows[d].closes else None) for d in range(7)]
    return S.BusinessHoursResponse(request_id=rid, status="ok", business_name=t.name, today=now.date().isoformat(),
                                   today_weekday=WEEKDAY_NAMES[now.weekday()], is_open_now=open_now, hours=hours)


def service_info(db: Session, tenant_id: str, rid: str, req: S.ServiceInfoRequest) -> S.ServiceInfoResponse:
    def out(s: Service) -> S.ServiceOut:
        return S.ServiceOut(code=s.code, name_en=s.name_en, name_te=s.name_te, price_inr=s.price_inr,
                            price_note=s.price_note, duration_min=s.duration_min)
    if not req.service.strip():
        return S.ServiceInfoResponse(request_id=rid, status="ok", services=[out(s) for s in _services(db, tenant_id)])
    res, by_id = _resolve_service(db, tenant_id, req.service)
    if res.decision in ("auto", "confirm"):
        return S.ServiceInfoResponse(request_id=rid, status="ok", services=[out(by_id[res.best.id])])
    if res.decision == "clarify":
        return S.ServiceInfoResponse(request_id=rid, status="needs_clarification",
                                     message_for_agent="Ask which of these services the caller means.",
                                     services=[out(by_id[s.candidate.id]) for s in res.top])
    return S.ServiceInfoResponse(request_id=rid, status="not_found", services=[out(s) for s in _services(db, tenant_id)],
                                 message_for_agent="Service not offered or not understood. List offered services; do not invent prices.")


def lookup_customer(db: Session, tenant_id: str, rid: str, req: S.LookupCustomerRequest) -> S.LookupCustomerResponse:
    caller = normalize_phone(req.caller_number) if req.caller_number else None
    phone = normalize_phone(req.phone) if req.phone.strip() else caller
    if not phone:
        return S.LookupCustomerResponse(request_id=rid, status="needs_clarification",
                                        message_for_agent="Ask for a 10-digit mobile number.")
    cust = db.scalar(select(Customer).where(Customer.tenant_id == tenant_id, Customer.phone == phone))
    readback = format_phone_readback(phone)
    if not cust:
        return S.LookupCustomerResponse(request_id=rid, status="not_found", found=False, phone_readback=readback,
                                        is_calling_number=phone == caller)
    vehicles = list(db.scalars(select(Vehicle).where(Vehicle.customer_id == cust.id)))
    if phone == caller:
        return S.LookupCustomerResponse(request_id=rid, status="ok", found=True, is_calling_number=True, name=cust.name,
                                        phone_readback=readback,
                                        vehicles=[S.VehicleOut(reg_masked="****" + v.reg[-4:], reg_full=v.reg, make_model=v.make_model) for v in vehicles])
    # Privacy: a different number than the caller's own -> no name, masked vehicles only.
    return S.LookupCustomerResponse(
        request_id=rid, status="ok", found=True, is_calling_number=False, name=None, phone_readback=readback,
        vehicles=[S.VehicleOut(reg_masked="****" + v.reg[-4:]) for v in vehicles],
        message_for_agent="Number is on file but is not the calling number. Do not reveal name or history; ask the caller to state the full vehicle number.")


def check_availability(db: Session, tenant_id: str, rid: str, req: S.CheckAvailabilityRequest) -> S.CheckAvailabilityResponse:
    now = now_ist()
    d = parse_date(req.date_expression, now.date())
    if d.date is None:
        return S.CheckAvailabilityResponse(request_id=rid, status="needs_clarification",
                                           message_for_agent="Ask which day the caller wants.")
    if d.date < now.date():
        return S.CheckAvailabilityResponse(request_id=rid, status="rejected", message_for_agent="That date is in the past.")
    hours = db.scalar(select(BusinessHours).where(BusinessHours.tenant_id == tenant_id, BusinessHours.weekday == d.date.weekday()))
    base_resp = dict(request_id=rid, resolved_date=d.date.isoformat(), resolved_weekday=WEEKDAY_NAMES[d.date.weekday()],
                     date_note=d.note)
    if d.status == "ambiguous":
        return S.CheckAvailabilityResponse(status="needs_clarification", **base_resp,
                                           message_for_agent=f"Ambiguous day. Confirm with the caller: {d.date.isoformat()} or {d.note}.")
    if not hours or not hours.opens:
        return S.CheckAvailabilityResponse(status="unavailable", **base_resp, message_for_agent="Closed on that day.")
    service_code = None
    if req.service.strip():
        res, by_id = _resolve_service(db, tenant_id, req.service)
        if res.decision == "clarify":
            return S.CheckAvailabilityResponse(status="needs_clarification", **base_resp,
                                               candidates=[by_id[s.candidate.id].name_en for s in res.top],
                                               message_for_agent="Ask which service.")
        if res.best and res.decision != "no_match":
            service_code = by_id[res.best.id].code
    advisor_id = None
    if req.advisor.strip():
        advisors = list(db.scalars(select(Advisor).where(Advisor.tenant_id == tenant_id)))
        ares = resolve_name(req.advisor, [Candidate(a.id, a.name, [a.name_te]) for a in advisors])
        if ares.decision == "clarify":
            names = {a.id: a.name for a in advisors}
            return S.CheckAvailabilityResponse(status="needs_clarification", **base_resp,
                                               candidates=[names[s.candidate.id] for s in ares.top],
                                               message_for_agent="Ask which advisor the caller means.")
        if ares.decision in ("auto", "confirm"):
            advisor_id = ares.best.id
    q = select(Slot, Advisor).join(Advisor, Advisor.id == Slot.advisor_id).where(
        Slot.tenant_id == tenant_id, Slot.date == d.date, Slot.booked < Slot.capacity).order_by(Slot.start)
    if advisor_id:
        q = q.where(Slot.advisor_id == advisor_id)
    rows = [(s, a) for s, a in db.execute(q) if not (d.date == now.date() and s.start <= now.time())]
    t = parse_time(req.time_expression) if req.time_expression.strip() else None
    note = ""
    if t and t.time:
        target = t.time.hour * 60 + t.time.minute
        near = [(s, a) for s, a in rows if abs(s.start.hour * 60 + s.start.minute - target) <= 60]
        if near:
            rows = near
        else:
            note = "Requested time not available; offering other times that day."
    elif t and t.daypart:
        part = [(s, a) for s, a in rows if (s.start.hour >= 12) == (t.daypart == "pm")]
        rows = part or rows
    slots = [S.SlotOut(slot_id=s.id, date=s.date.isoformat(), weekday=WEEKDAY_NAMES[s.date.weekday()],
                       time=s.start.strftime("%H:%M"), advisor=a.name) for s, a in rows[:4]]
    if not slots:
        return S.CheckAvailabilityResponse(status="unavailable", **base_resp, service_code=service_code,
                                           message_for_agent="No free slots that day. Offer another day or a callback.")
    return S.CheckAvailabilityResponse(status="ok", **base_resp, slots=slots, service_code=service_code,
                                       message_for_agent=note or "Offer at most two options. Read back weekday and date.")


def create_booking(db: Session, tenant_id: str, rid: str, req: S.CreateBookingRequest) -> S.CreateBookingResponse:
    if not req.caller_confirmed:
        return S.CreateBookingResponse(request_id=rid, status="rejected",
                                       message_for_agent="Read back service, day, date, time, vehicle and phone, get an explicit yes, then call again with caller_confirmed=true.")
    phone = normalize_phone(req.customer_phone)
    reg = normalize_vehicle_reg(req.vehicle_reg)
    if not phone:
        return S.CreateBookingResponse(request_id=rid, status="needs_clarification", message_for_agent="Phone number invalid; ask again.")
    if not reg:
        return S.CreateBookingResponse(request_id=rid, status="needs_clarification",
                                       message_for_agent="Vehicle number invalid; ask the caller to say it slowly, character by character.")
    res, by_id = _resolve_service(db, tenant_id, req.service)
    if res.decision not in ("auto", "confirm"):
        return S.CreateBookingResponse(request_id=rid, status="needs_clarification", message_for_agent="Service unclear; ask which service.")
    svc = by_id[res.best.id]
    slot = db.get(Slot, req.slot_id)
    if not slot or slot.tenant_id != tenant_id:
        return S.CreateBookingResponse(request_id=rid, status="not_found", message_for_agent="Slot not found. Check availability again.")
    now = now_ist()
    if dt.datetime.combine(slot.date, slot.start, IST) <= now:
        return S.CreateBookingResponse(request_id=rid, status="rejected", message_for_agent="Slot is in the past.")
    key = _key(tenant_id, req.interaction_id or rid, slot.id, reg, svc.code)
    existing = db.scalar(select(Booking).where(Booking.tenant_id == tenant_id, Booking.idempotency_key == key))
    if existing is None:
        claimed = db.execute(update(Slot).where(Slot.id == slot.id, Slot.booked < Slot.capacity)
                             .values(booked=Slot.booked + 1)).rowcount
        if claimed != 1:
            db.rollback()
            return S.CreateBookingResponse(request_id=rid, status="unavailable",
                                           message_for_agent="Slot just got taken. Check availability again; do not say booked.")
        db.add(Booking(id="BK" + uuid.uuid4().hex[:6].upper(), tenant_id=tenant_id, slot_id=slot.id, service_id=svc.id,
                       customer_phone=phone, customer_name=req.customer_name, vehicle_reg=reg,
                       interaction_id=req.interaction_id, idempotency_key=key))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
    # Read back from the database: only a persisted row counts as confirmed.
    b = db.scalar(select(Booking).where(Booking.tenant_id == tenant_id, Booking.idempotency_key == key))
    if b is None:
        return S.CreateBookingResponse(request_id=rid, status="failed", message_for_agent="Could not confirm. Do not say booked; offer a callback.")
    adv = db.get(Advisor, slot.advisor_id)
    return S.CreateBookingResponse(request_id=rid, status="confirmed", booking_ref=b.id, date=slot.date.isoformat(),
                                   weekday=WEEKDAY_NAMES[slot.date.weekday()], time=slot.start.strftime("%H:%M"),
                                   advisor=adv.name, service=svc.name_en, price_inr=svc.price_inr,
                                   vehicle_reg_readback=format_vehicle_reg_readback(reg),
                                   message_for_agent="Booking is saved. Tell the caller the booking reference.")


def request_callback(db: Session, tenant_id: str, rid: str, req: S.RequestCallbackRequest) -> S.RequestCallbackResponse:
    phone = normalize_phone(req.phone) if req.phone.strip() else normalize_phone(req.caller_number)
    if not phone:
        return S.RequestCallbackResponse(request_id=rid, status="needs_clarification", message_for_agent="Ask for a 10-digit mobile number.")
    key = _key(tenant_id, req.interaction_id or rid, phone, req.reason[:60])
    cb = db.scalar(select(Callback).where(Callback.tenant_id == tenant_id, Callback.idempotency_key == key))
    if cb is None:
        cb = Callback(id="CB" + uuid.uuid4().hex[:6].upper(), tenant_id=tenant_id, phone=phone, reason=req.reason,
                      preferred_time=req.preferred_time, interaction_id=req.interaction_id, idempotency_key=key)
        db.add(cb)
        db.commit()
    return S.RequestCallbackResponse(request_id=rid, status="confirmed", callback_ref=cb.id, phone_readback=format_phone_readback(phone))
