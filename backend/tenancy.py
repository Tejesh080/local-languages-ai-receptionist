"""Server-side tenant derivation. Tenant = f(per-agent bearer secret). Never from the request body."""
from __future__ import annotations
import hashlib
import hmac
import secrets
from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import AgentCredential

FORBIDDEN_BODY_KEYS = {"tenant_id", "tenant", "org_id", "organization_id", "business_id"}


def sha256(v: str) -> str:
    return hashlib.sha256(v.encode()).hexdigest()


def new_secret() -> str:
    return "tvl_" + secrets.token_urlsafe(32)


def source_ip(request: Request, trust_proxy: bool = False) -> str:
    if trust_proxy and request.headers.get("x-forwarded-for"):
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    return request.client.host if request.client else ""


def match_credential(db: Session, secret: str, purpose: str) -> AgentCredential | None:
    digest = sha256(secret.strip())
    for cred in db.scalars(select(AgentCredential).where(AgentCredential.active.is_(True), AgentCredential.purpose == purpose)):
        if hmac.compare_digest(cred.secret_sha256, digest):
            return cred
    return None


def resolve_tenant(request: Request, db: Session, allowed_ips: frozenset[str] = frozenset(),
                   trust_proxy: bool = False) -> tuple[str, str]:
    """Return (tenant_id, credential_label) or raise 401. Only `tools` credentials are accepted here.
    Optional source-IP allowlist (Sarvam documents 4.213.167.70)."""
    if allowed_ips and source_ip(request, trust_proxy) not in allowed_ips:
        raise HTTPException(status_code=401, detail="unauthorized")
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="unauthorized")
    cred = match_credential(db, auth.split(" ", 1)[1], "tools")
    if cred is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return cred.tenant_id, cred.label


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
