"""Redaction for anything we persist about requests/responses. Default output contains structure, not personal values."""
from __future__ import annotations
import hashlib
from typing import Any

# Business vocabulary and platform identifiers: safe to keep (truncated).
SAFE_KEYS = {"interaction_id", "caller_confirmed", "slot_id", "date_expression", "time_expression", "service", "advisor",
             "status", "request_id", "message_for_agent", "resolved_date", "resolved_weekday", "date_note", "found",
             "caller_id_match", "identity_assurance", "authenticated", "booking_ref", "callback_ref", "date", "weekday",
             "time", "price_inr", "service_code", "reg_masked", "make_model", "app_id", "app_version", "deployment_id",
             "duration", "start_datetime", "end_datetime", "code", "name_en", "name_te", "price_note", "duration_min",
             "is_open_now", "today", "today_weekday", "business_name", "opens", "closes", "candidates", "errors"}
# Identifiers we need to correlate but must not store in plaintext.
HASH_KEYS = {"caller_number", "customer_phone", "phone", "user_phone_number", "agent_phone_number", "phone_readback"}
MASK_KEYS = {"vehicle_reg", "vehicle_reg_readback", "reg_full"}
# Free text / names: never stored, only length.
REDACT_KEYS = {"customer_name", "name", "reason", "preferred_time", "interaction_transcript", "transcript",
               "final_agent_variables", "output_agent_variables", "en_text", "indic_text"}


def salted_hash(value: str, salt: str) -> str:
    return hashlib.sha256((salt + "|" + value).encode()).hexdigest()[:16]


def redact(obj: Any, salt: str, key: str | None = None) -> Any:
    if isinstance(obj, dict):
        return {k: redact(v, salt, k) for k, v in obj.items()}
    if isinstance(obj, list):
        if key in REDACT_KEYS:
            return {"redacted": True, "items": len(obj)}
        return [redact(v, salt, key) for v in obj[:50]]
    if key is None:
        return {"type": type(obj).__name__}
    if key in SAFE_KEYS and (obj is None or isinstance(obj, (bool, int, float, str))):
        return obj[:120] if isinstance(obj, str) else obj
    if key in HASH_KEYS:
        s = "" if obj is None else str(obj)
        return {"present": bool(s), "sha256": salted_hash(s, salt) if s else None, "len": len(s)}
    if key in MASK_KEYS:
        s = "" if obj is None else str(obj).replace(" ", "")
        return {"present": bool(s), "masked": ("*" * max(0, len(s) - 2) + s[-2:]) if s else None,
                "sha256": salted_hash(s, salt) if s else None}
    if key in REDACT_KEYS:
        return {"redacted": True, "len": len(str(obj)) if obj is not None else 0}
    # Unknown field: keep the key (the metadata experiment needs field names) but never the value.
    return {"unknown_field": True, "type": type(obj).__name__, "len": len(str(obj)) if obj is not None else 0}
