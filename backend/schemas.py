"""Typed tool contracts.

Unknown fields are ignored (and captured for the metadata experiment), but tenancy keys are rejected
explicitly in app.py: the model can never choose the tenant."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class ToolRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    interaction_id: str = Field("", max_length=120, description="Sarvam Interaction ID (call-context variable)")
    caller_number: str = Field("", max_length=20, description="Sarvam User Identifier (caller phone)")


class Envelope(BaseModel):
    request_id: str
    status: Literal["ok", "needs_clarification", "not_found", "unavailable", "failed", "confirmed", "rejected"]
    message_for_agent: str = ""


class BusinessHoursRequest(ToolRequest):
    pass


class DayHours(BaseModel):
    weekday: str
    opens: str | None
    closes: str | None


class BusinessHoursResponse(Envelope):
    business_name: str = ""
    today: str = ""
    today_weekday: str = ""
    is_open_now: bool = False
    hours: list[DayHours] = []


class ServiceInfoRequest(ToolRequest):
    service: str = Field("", max_length=100, description="Service as the caller said it, any language")


class ServiceOut(BaseModel):
    code: str
    name_en: str
    name_te: str
    price_inr: int
    price_note: str
    duration_min: int


class ServiceInfoResponse(Envelope):
    services: list[ServiceOut] = []


class LookupCustomerRequest(ToolRequest):
    phone: str = Field("", max_length=40, description="Number the caller stated; empty means the calling number")


class VehicleOut(BaseModel):
    reg_masked: str
    make_model: str | None = None


class LookupCustomerResponse(Envelope):
    """Caller IDENTIFICATION only (docs/decisions/0004-caller-identity.md). Never authentication."""
    found: bool = False
    caller_id_match: bool = False          # looked-up number equals the platform-reported caller number
    identity_assurance: Literal["none", "unverified_caller_id"] = "none"
    authenticated: Literal[False] = False  # constant: this API cannot authenticate a caller
    vehicles: list[VehicleOut] = []        # masked, and only when caller_id_match
    phone_readback: str | None = None


class CheckAvailabilityRequest(ToolRequest):
    date_expression: str = Field(..., max_length=80, description="As spoken: 'రేపు', 'Saturday', '2026-10-03'")
    time_expression: str = Field("", max_length=80, description="Optional: 'సాయంత్రం 5', 'morning', '10:30'")
    service: str = Field("", max_length=100)
    advisor: str = Field("", max_length=100)


class SlotOut(BaseModel):
    slot_id: str
    date: str
    weekday: str
    time: str
    advisor: str


class CheckAvailabilityResponse(Envelope):
    resolved_date: str | None = None
    resolved_weekday: str | None = None
    date_note: str = ""
    slots: list[SlotOut] = []
    service_code: str | None = None
    candidates: list[str] = []


class CreateBookingRequest(ToolRequest):
    slot_id: str = Field(..., max_length=40)
    service: str = Field(..., max_length=100)
    customer_phone: str = Field(..., max_length=40)
    customer_name: str = Field("", max_length=100)
    vehicle_reg: str = Field(..., max_length=60)
    caller_confirmed: bool = Field(..., description="True only after reading back all details and caller said yes")


class CreateBookingResponse(Envelope):
    booking_ref: str | None = None
    date: str | None = None
    weekday: str | None = None
    time: str | None = None
    advisor: str | None = None
    service: str | None = None
    price_inr: int | None = None
    vehicle_reg_readback: str | None = None


class RequestCallbackRequest(ToolRequest):
    phone: str = Field("", max_length=40)
    reason: str = Field(..., max_length=500)
    preferred_time: str = Field("", max_length=100)


class RequestCallbackResponse(Envelope):
    callback_ref: str | None = None
    phone_readback: str | None = None
