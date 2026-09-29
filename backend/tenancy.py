"""Server-side tenant derivation. Tenant = f(per-agent bearer secret). Never from the request body."""
from __future__ import annotations
import hashlib
import hmac
import os
import secrets
from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import AgentCredential

FORBIDDEN_BODY_KEYS = {"tenant_id", "tenant", "org_id", "organization_id", "business_id"}
_ALLOWED_IPS = {ip.strip() for ip in os.environ.get("ALLOWED_SOURCE_IPS", "").split(",") if ip.strip()}
_TRUST_PROXY = os.environ.get("TRUST_PROXY", "0") == "1"


def sha256(v: str) -> str:
    return hashlib.sha256(v.encode()).hexdigest()


def new_secret() -> str:
    return "tvl_" + secrets.token_urlsafe(32)


def source_ip(request: Request) -> str:
    if _TRUST_PROXY and request.headers.get("x-forwarded-for"):
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    return request.client.host if request.client else ""


def resolve_tenant(request: Request, db: Session) -> tuple[str, str]:
    """Return (tenant_id, credential_label) or raise 401. Optional source-IP allowlist (Sarvam documents 4.213.167.70)."""
    if _ALLOWED_IPS and source_ip(request) not in _ALLOWED_IPS:
        raise HTTPException(status_code=401, detail="unauthorized")
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="unauthorized")
    digest = sha256(auth.split(" ", 1)[1].strip())
    for cred in db.scalars(select(AgentCredential).where(AgentCredential.active.is_(True))):
        if hmac.compare_digest(cred.secret_sha256, digest):
            return cred.tenant_id, cred.label
    raise HTTPException(status_code=401, detail="unauthorized")


def redact_headers(headers: dict[str, str]) -> dict[str, str]:
    out = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in {"authorization", "x-api-key", "api-key", "cookie", "proxy-authorization", "api-subscription-key"}:
            scheme = v.split(" ", 1)[0] if " " in v else ""
            out[k] = f"{scheme} [REDACTED sha256:{sha256(v)[:8]} len:{len(v)}]".strip()
        else:
            out[k] = v
    return out
