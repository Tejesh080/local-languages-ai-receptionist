from __future__ import annotations
import datetime as dt
from sqlalchemy import (String, Integer, ForeignKey, Date, Time, DateTime, Boolean, Text, JSON, UniqueConstraint, Float)
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata")
    locality: Mapped[str] = mapped_column(String(200))


class AgentCredential(Base):
    """Maps a per-agent bearer secret (stored as SHA-256) to exactly one tenant. The model never chooses tenancy."""
    __tablename__ = "agent_credentials"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    label: Mapped[str] = mapped_column(String(100))
    purpose: Mapped[str] = mapped_column(String(20), default="tools")   # "tools" | "webhook": never interchangeable
    secret_sha256: Mapped[str] = mapped_column(String(64), unique=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Advisor(Base):
    __tablename__ = "advisors"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    name: Mapped[str] = mapped_column(String(100))
    name_te: Mapped[str] = mapped_column(String(100))


class Service(Base):
    __tablename__ = "services"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    code: Mapped[str] = mapped_column(String(40))
    name_en: Mapped[str] = mapped_column(String(100))
    name_te: Mapped[str] = mapped_column(String(100))
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    price_inr: Mapped[int] = mapped_column(Integer)
    price_note: Mapped[str] = mapped_column(String(200), default="")
    duration_min: Mapped[int] = mapped_column(Integer)


class BusinessHours(Base):
    __tablename__ = "business_hours"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    weekday: Mapped[int] = mapped_column(Integer)  # 0=Mon
    opens: Mapped[dt.time | None] = mapped_column(Time, nullable=True)
    closes: Mapped[dt.time | None] = mapped_column(Time, nullable=True)


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(10))
    __table_args__ = (UniqueConstraint("tenant_id", "phone"),)


class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    reg: Mapped[str] = mapped_column(String(16))
    make_model: Mapped[str] = mapped_column(String(100))
    __table_args__ = (UniqueConstraint("tenant_id", "reg"),)


class Slot(Base):
    __tablename__ = "slots"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    advisor_id: Mapped[str] = mapped_column(ForeignKey("advisors.id"))
    date: Mapped[dt.date] = mapped_column(Date)
    start: Mapped[dt.time] = mapped_column(Time)
    capacity: Mapped[int] = mapped_column(Integer, default=1)
    booked: Mapped[int] = mapped_column(Integer, default=0)


class Booking(Base):
    __tablename__ = "bookings"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    slot_id: Mapped[str] = mapped_column(ForeignKey("slots.id"))
    service_id: Mapped[str] = mapped_column(ForeignKey("services.id"))
    customer_phone: Mapped[str] = mapped_column(String(10))
    customer_name: Mapped[str] = mapped_column(String(100), default="")
    vehicle_reg: Mapped[str] = mapped_column(String(16))
    interaction_id: Mapped[str] = mapped_column(String(120), default="")
    idempotency_key: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(20), default="confirmed")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)
    __table_args__ = (UniqueConstraint("tenant_id", "idempotency_key"),)


class Callback(Base):
    __tablename__ = "callbacks"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"))
    phone: Mapped[str] = mapped_column(String(10))
    reason: Mapped[str] = mapped_column(Text)
    preferred_time: Mapped[str] = mapped_column(String(100), default="")
    interaction_id: Mapped[str] = mapped_column(String(120), default="")
    idempotency_key: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)
    __table_args__ = (UniqueConstraint("tenant_id", "idempotency_key"),)


class ToolCallLog(Base):
    __tablename__ = "tool_call_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(String(40), index=True)
    tenant_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    tool: Mapped[str] = mapped_column(String(60))
    interaction_id: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[str] = mapped_column(String(30))
    latency_ms: Mapped[float] = mapped_column(Float)
    request_json: Mapped[dict] = mapped_column(JSON)
    response_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)


class RequestCapture(Base):
    """Raw inbound request metadata for the Sarvam tool-metadata experiment. Secrets are redacted before storage."""
    __tablename__ = "request_captures"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[str] = mapped_column(String(40))
    path: Mapped[str] = mapped_column(String(200))
    method: Mapped[str] = mapped_column(String(10))
    source_ip: Mapped[str] = mapped_column(String(64))
    headers: Mapped[dict] = mapped_column(JSON)
    query: Mapped[dict] = mapped_column(JSON)
    body: Mapped[dict | str] = mapped_column(JSON)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_now)


class CallRecord(Base):
    """Post-call webhook from Sarvam Voice Agents (feeds the cost ledger)."""
    __tablename__ = "call_records"
    interaction_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    tenant_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    app_id: Mapped[str] = mapped_column(String(120), default="")
    app_version: Mapped[int] = mapped_column(Integer, default=0)
    deployment_id: Mapped[str] = mapped_column(String(120), default="")
    agent_phone_number: Mapped[str] = mapped_column(String(20), default="")
    caller_hash: Mapped[str] = mapped_column(String(64), default="")
    duration_s: Mapped[float] = mapped_column(Float, default=0.0)
    start_datetime: Mapped[str] = mapped_column(String(40), default="")
    end_datetime: Mapped[str] = mapped_column(String(40), default="")
    transcript: Mapped[list] = mapped_column(JSON, default=list)
    final_variables: Mapped[dict] = mapped_column(JSON, default=dict)
    raw: Mapped[dict] = mapped_column(JSON, default=dict)
