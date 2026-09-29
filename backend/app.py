"""Tool API for System A (Sarvam Voice Agents HTTP tools) and later System B. Same backend for both."""
from __future__ import annotations
import asyncio
import json
import logging
import time
import uuid
from typing import Callable
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool
from . import schemas as S, service
from .config import load
from .db import Base, SessionLocal, engine
from .models import ToolCallLog, RequestCapture, CallRecord
from .privacy import redact, salted_hash
from .tenancy import resolve_tenant, redact_headers, source_ip, FORBIDDEN_BODY_KEYS, match_credential

SETTINGS = load()                      # raises ConfigError at startup on insecure configuration
logging.basicConfig(level="INFO", format="%(message)s")
log = logging.getLogger("tvl")

Base.metadata.create_all(engine)
app = FastAPI(title="telugu-voice-lab tools", version="0.2.0")

TOOLS: dict[str, tuple[type[S.ToolRequest], Callable]] = {
    "get_business_hours": (S.BusinessHoursRequest, service.business_hours),
    "get_service_info": (S.ServiceInfoRequest, service.service_info),
    "lookup_customer": (S.LookupCustomerRequest, service.lookup_customer),
    "check_availability": (S.CheckAvailabilityRequest, service.check_availability),
    "create_booking": (S.CreateBookingRequest, service.create_booking),
    "request_callback": (S.RequestCallbackRequest, service.request_callback),
}


def _capture(db, rid: str, request: Request, raw: bytes) -> None:
    """Metadata experiment capture. Default: field names, header names, source IP; personal values hashed/redacted."""
    try:
        body = json.loads(raw) if raw else {}
    except ValueError:
        body = {"unparseable_body": True, "len": len(raw)}
    if SETTINGS.capture_mode != "full_body_pii_debug":
        body = redact(body, SETTINGS.phone_hash_salt)
    db.add(RequestCapture(request_id=rid, path=request.url.path, method=request.method,
                          source_ip=source_ip(request, SETTINGS.trust_proxy),
                          headers=redact_headers(dict(request.headers)), query=dict(request.query_params), body=body))
    db.commit()


@app.get("/healthz")
def healthz():
    return {"ok": True, "env": SETTINGS.app_env}


@app.post("/tools/{tool}")
async def call_tool(tool: str, request: Request):
    rid = "req_" + uuid.uuid4().hex[:12]
    t0 = time.perf_counter()
    raw = await request.body()
    db = SessionLocal()
    try:
        _capture(db, rid, request, raw)
        if tool not in TOOLS:
            raise HTTPException(status_code=404, detail="unknown tool")
        try:
            tenant_id, _ = resolve_tenant(request, db, SETTINGS.allowed_source_ips, SETTINGS.trust_proxy)
        except HTTPException:
            log.info(json.dumps({"event": "auth_failed", "request_id": rid, "tool": tool}))
            raise
        try:
            payload = json.loads(raw) if raw else {}
        except ValueError:
            payload = None
        if not isinstance(payload, dict):
            return _finish(db, rid, tenant_id, tool, {}, t0, JSONResponse(
                status_code=400, content={"request_id": rid, "status": "failed", "message_for_agent": "Malformed request."}))
        bad = FORBIDDEN_BODY_KEYS & set(payload)
        if bad:
            log.warning(json.dumps({"event": "tenancy_key_rejected", "request_id": rid, "keys": sorted(bad)}))
            return _finish(db, rid, tenant_id, tool, payload, t0, JSONResponse(
                status_code=400, content={"request_id": rid, "status": "rejected", "message_for_agent": "Invalid request."}))
        req_model, fn = TOOLS[tool]
        try:
            req = req_model.model_validate(payload)
        except ValidationError as e:
            return _finish(db, rid, tenant_id, tool, payload, t0, JSONResponse(
                status_code=422, content={"request_id": rid, "status": "failed",
                                          "message_for_agent": "Missing or invalid details; ask the caller again.",
                                          "errors": [f"{'.'.join(map(str, x['loc']))}: {x['type']}" for x in e.errors()]}))

        def run():
            s = SessionLocal()
            try:
                return fn(s, tenant_id, rid, req)
            finally:
                s.close()
        try:
            resp = await asyncio.wait_for(run_in_threadpool(run), timeout=SETTINGS.tool_timeout_s)
            out = JSONResponse(content=resp.model_dump())
        except asyncio.TimeoutError:
            out = JSONResponse(status_code=504, content={
                "request_id": rid, "status": "failed",
                "message_for_agent": "System is slow. Do NOT say it is done. Offer a callback."})
        except Exception:  # noqa: BLE001  logged with stack, never swallowed silently
            log.exception("tool_error request_id=%s tool=%s", rid, tool)
            out = JSONResponse(status_code=500, content={
                "request_id": rid, "status": "failed",
                "message_for_agent": "Something went wrong. Do NOT say it is done. Offer a callback."})
        return _finish(db, rid, tenant_id, tool, payload, t0, out, interaction_id=req.interaction_id)
    finally:
        db.close()


def _finish(db, rid, tenant_id, tool, payload, t0, resp: JSONResponse, interaction_id: str = ""):
    ms = (time.perf_counter() - t0) * 1000
    body = json.loads(resp.body)
    salt = SETTINGS.phone_hash_salt
    db.add(ToolCallLog(request_id=rid, tenant_id=tenant_id, tool=tool, interaction_id=interaction_id,
                       status=body.get("status", str(resp.status_code)), latency_ms=ms,
                       request_json=redact(payload, salt), response_json=redact(body, salt)))
    db.commit()
    log.info(json.dumps({"event": "tool_call", "request_id": rid, "tool": tool, "tenant": tenant_id,
                         "status": body.get("status"), "ms": round(ms, 1), "interaction_id": interaction_id}))
    resp.headers["x-request-id"] = rid
    return resp


@app.post("/webhooks/sarvam/call-complete")
async def sarvam_call_complete(request: Request):
    """Post-call webhook. Sarvam's WebhookConfig supports only {url, metadata}; metadata is echoed in the body.
    The shared token therefore travels in the body (metadata.tvl_webhook_token), not the URL. See decision 0003."""
    rid = "wh_" + uuid.uuid4().hex[:12]
    raw = await request.body()
    db = SessionLocal()
    try:
        _capture(db, rid, request, raw)
        try:
            p = json.loads(raw)
        except ValueError:
            raise HTTPException(status_code=400, detail="bad request")
        token = ((p.get("metadata") or {}).get("tvl_webhook_token") or "") if isinstance(p, dict) else ""
        cred = match_credential(db, token, "webhook") if token else None
        if cred is None:
            log.info(json.dumps({"event": "webhook_auth_failed", "request_id": rid}))
            raise HTTPException(status_code=401, detail="unauthorized")
        iid = str(p.get("interaction_id") or "")
        if not iid:
            raise HTTPException(status_code=400, detail="bad request")
        existing = db.get(CallRecord, iid)
        if existing is not None and existing.tenant_id != cred.tenant_id:
            log.warning(json.dumps({"event": "webhook_cross_tenant_conflict", "request_id": rid}))
            raise HTTPException(status_code=409, detail="conflict")
        salt = SETTINGS.phone_hash_salt
        rec = CallRecord(
            interaction_id=iid, tenant_id=cred.tenant_id, app_id=str(p.get("app_id", "")), app_version=int(p.get("app_version") or 0),
            deployment_id=str(p.get("deployment_id", "")),
            agent_phone_number=salted_hash(str(p.get("agent_phone_number", "")), salt),
            caller_hash=salted_hash(str(p.get("user_phone_number", "")), salt),
            duration_s=float(p.get("duration") or 0.0), start_datetime=str(p.get("start_datetime") or ""),
            end_datetime=str(p.get("end_datetime") or ""),
            transcript=(p.get("interaction_transcript") or []) if SETTINGS.store_call_transcripts else [],
            final_variables=redact(p.get("final_agent_variables") or {}, salt),
            raw=redact({k: v for k, v in p.items() if k != "metadata"}, salt))
        db.merge(rec)          # idempotent per interaction_id (Sarvam supports webhook retries)
        db.commit()
        return {"ok": True, "request_id": rid}
    finally:
        db.close()
