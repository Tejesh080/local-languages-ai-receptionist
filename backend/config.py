"""Environment configuration. Fails closed: if APP_ENV is unset the app behaves as production."""
from __future__ import annotations
import logging
import os
from dataclasses import dataclass

log = logging.getLogger("tvl.config")
ENVS = {"test", "development", "production"}
CAPTURE_MODES = {"metadata", "full_body_pii_debug"}
PLACEHOLDERS = {"", "change-me", "changeme", "change_me", "secret", "password", "salt", "test", "default", "xxx", "todo"}


class ConfigError(RuntimeError):
    """Raised at startup; message never contains secret values."""


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    phone_hash_salt: str
    capture_mode: str
    store_call_transcripts: bool
    allowed_source_ips: frozenset[str]
    trust_proxy: bool
    tool_timeout_s: float


def _weak(secret: str, min_len: int) -> str | None:
    if secret.strip().lower() in PLACEHOLDERS:
        return "is a placeholder"
    if len(secret) < min_len:
        return f"is shorter than {min_len} characters"
    if len(set(secret)) < 8:
        return "has too little variety"
    return None


def load(env: dict[str, str] | None = None) -> Settings:
    e = os.environ if env is None else env
    app_env = e.get("APP_ENV", "production").strip().lower()
    if app_env not in ENVS:
        raise ConfigError(f"APP_ENV must be one of {sorted(ENVS)}")
    s = Settings(
        app_env=app_env,
        database_url=e.get("DATABASE_URL", "sqlite:///./lab.db"),
        phone_hash_salt=e.get("PHONE_HASH_SALT", ""),
        capture_mode=e.get("CAPTURE_MODE", "metadata"),
        store_call_transcripts=e.get("STORE_CALL_TRANSCRIPTS", "0") == "1",
        allowed_source_ips=frozenset(ip.strip() for ip in e.get("ALLOWED_SOURCE_IPS", "").split(",") if ip.strip()),
        trust_proxy=e.get("TRUST_PROXY", "0") == "1",
        tool_timeout_s=float(e.get("TOOL_TIMEOUT_S", "2.5")),
    )
    problems: list[str] = []
    if s.capture_mode not in CAPTURE_MODES:
        problems.append(f"CAPTURE_MODE must be one of {sorted(CAPTURE_MODES)}")
    if app_env != "test":
        w = _weak(s.phone_hash_salt, 32 if app_env == "production" else 16)
        if w:
            problems.append(f"PHONE_HASH_SALT {w} (generate one: python -c \"import secrets;print(secrets.token_urlsafe(48))\")")
    if app_env == "production":
        if not s.database_url.startswith("postgresql"):
            problems.append("DATABASE_URL must be a PostgreSQL URL in production")
        if s.capture_mode != "metadata":
            problems.append("CAPTURE_MODE=full_body_pii_debug is forbidden in production")
        if s.store_call_transcripts:
            problems.append("STORE_CALL_TRANSCRIPTS=1 is forbidden in production until a retention policy exists")
    if problems:
        raise ConfigError(f"Refusing to start (APP_ENV={app_env}): " + "; ".join(problems))
    if s.capture_mode == "full_body_pii_debug":
        log.warning("CAPTURE_MODE=full_body_pii_debug: request bodies containing PII are being stored. Lab debugging only.")
    return s
