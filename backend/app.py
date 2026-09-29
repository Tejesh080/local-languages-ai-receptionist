"""Tool API for System A (Sarvam Voice Agents HTTP tools) and later System B. Same backend for both."""
from __future__ import annotations
import asyncio
import json
import logging
import os
import time
import uuid
from typing import Callable
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool
from . import schemas as S, service
from .db import Base, SessionLocal, engine
from .models import ToolCallLog, RequestCapture, CallRecord, AgentCredential
from .tenancy import resolve_tenant, redact_headers, source_ip, FORBIDDEN_BODY_KEYS, sha256

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(message)s")
log = logging.getLogger("tvl")
TOOL_TIMEOUT_S = float(os.environ.get("TOOL_TIMEOUT_S", "2.5"))
CAPTURE = os.environ.get("CAPTURE_REQUESTS", "1") == "1"

Base.metadata.create_all(engine)
app = FastAPI(title="telugu-voice-lab tools", version="0.1.0")

TOOLS: dict[str, tuple[type[S.ToolRequest], Callable]] = {
    "get_business_hours": (S.BusinessHoursRequest, service.business_hours),
    "get_service_info": (S.ServiceInfoRequest, service.service_info),
    "lookup_customer": (S.LookupCustomerRequest, service.lookup_customer),
    "check_availability": (S.CheckAvailabilityRequest, service.check_availability),
    "create_booking": (S.CreateBookingRequest, service.create_booking),
    "request_callback": (S.RequestCallbackRequest, service.request_callback),
}


def _capture(db, rid: str, request: Request, raw: bytes) -> None:
    if not CAPTURE:
        return
    try:
        body = json.loads(raw) if raw else {}
    except ValueError:
        body = raw.decode("utf-8", "replace")[:20000]
    db.add(RequestCapture(request_id=rid, path=request.url.path, method=request.method, source_ip=source_ip(request),
                          headers=redact_headers(dict(request.headers)), query=dict(request.query_params), body=body))
    db.commit()


@app.get("/healthz")
def healthz():
    return {"ok": True}


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
            tenant_id, cred = resolve_tenant(request, db)
        except HTTPException:
            log.info(json.dumps({"event": "auth_failed", "request_id": rid, "tool": tool, "ip": source_ip(request)}))
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
                status_code=400, content={"request_id": rid, "status": "rejected",
                                          "message_for_agent": "Invalid request."}))
        req_model, fn = TOOLS[tool]
        try:
            req = req_model.model_validate(payload)
        except ValidationError as e:
            return _finish(db, rid, tenant_id, tool, payload, t0, JSONResponse(
                status_code=422, content={"request_id": rid, "status": "failed",
                                          "message_for_agent": "Missing or invalid details; ask the caller again.",
                                          "errors": [f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors()]}))

        def run():
            s = SessionLocal()
            try:
                return fn(s, tenant_id, rid, req)
            finally:
                s.close()
        try:
            resp = await asyncio.wait_for(run_in_threadpool(run), timeout=TOOL_TIMEOUT_S)
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
    safe_req = {k: v for k, v in payload.items() if k != "caller_number"} | (
        {"caller_number_sha256": sha256(payload["caller_number"])[:16]} if payload.get("caller_number") else {})
    db.add(ToolCallLog(request_id=rid, tenant_id=tenant_id, tool=tool, interaction_id=interaction_id,
                       status=body.get("status", str(resp.status_code)), latency_ms=ms, request_json=safe_req, response_json=body))
    db.commit()
    log.info(json.dumps({"event": "tool_call", "request_id": rid, "tool": tool, "tenant": tenant_id,
                         "status": body.get("status"), "ms": round(ms, 1), "interaction_id": interaction_id}))
    resp.headers["x-request-id"] = rid
    return resp


@app.post("/webhooks/sarvam/{hook_secret}")
async def sarvam_call_complete(hook_secret: str, request: Request):
    """Post-call webhook (deployment webhook_config). Tenant derived from the secret in the path."""
    rid = "wh_" + uuid.uuid4().hex[:12]
    raw = await request.body()
    db = SessionLocal()
    try:
        _capture(db, rid, request, raw)
        cred = db.query(AgentCredential).filter_by(secret_sha256=sha256(hook_secret), active=True).one_or_none()
        if not cred:
            raise HTTPException(status_code=401, detail="unauthorized")
        p = json.loads(raw)
        salt = os.environ.get("PHONE_HASH_SALT", "change-me")
        rec = CallRecord(interaction_id=p["interaction_id"], tenant_id=cred.tenant_id, app_id=p.get("app_id", ""),
                         app_version=p.get("app_version", 0) or 0, deployment_id=p.get("deployment_id", ""),
                         agent_phone_number=p.get("agent_phone_number", ""),
                         caller_hash=sha256(salt + p.get("user_phone_number", ""))[:24],
                         duration_s=p.get("duration", 0.0) or 0.0, start_datetime=p.get("start_datetime") or "",
                         end_datetime=p.get("end_datetime") or "", transcript=p.get("interaction_transcript") or [],
                         final_variables=p.get("final_agent_variables") or {},
                         raw={k: v for k, v in p.items() if k != "user_phone_number"})
        db.merge(rec)
        db.commit()
        return {"ok": True, "request_id": rid}
    finally:
        db.close()
