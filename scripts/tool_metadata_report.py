"""Classify what Sarvam actually sends on HTTP tool calls, from captured requests. Writes docs/experiments/sarvam-tool-metadata.md."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.db import SessionLocal
from backend.models import RequestCapture

SARVAM_IP = "4.213.167.70"
def _present(v) -> bool:
    return bool(v.get("present")) if isinstance(v, dict) else bool(v)


FIELDS = {  # field -> how to detect it in a capture (bodies are redacted by default: presence, not values)
    "Authorization (our bearer secret)": lambda c: "authorization" in {k.lower() for k in c.headers},
    "Signature / HMAC header from Sarvam": lambda c: any(any(s in k.lower() for s in ("signature", "hmac", "x-sarvam")) for k in c.headers),
    "Any x-sarvam-* or platform header": lambda c: any(k.lower().startswith("x-sarvam") for k in c.headers),
    "User-Agent": lambda c: "user-agent" in {k.lower() for k in c.headers},
    "Source IP == documented Sarvam IP": lambda c: c.source_ip == SARVAM_IP or SARVAM_IP in str(c.headers.get("x-forwarded-for", "")),
    "Caller number (User Identifier)": lambda c: isinstance(c.body, dict) and _present(c.body.get("caller_number")),
    "Interaction / call ID": lambda c: isinstance(c.body, dict) and bool(c.body.get("interaction_id")),
    "Called number (our DID)": lambda c: any(k in str(c.body).lower() or k in str(c.headers).lower() for k in ("agent_phone_number", "called", "to_number", "did")),
    "Agent ID": lambda c: any(k in str(c.headers).lower() + str(c.body).lower() for k in ("app_id", "agent_id")),
    "Deployment ID": lambda c: "deployment" in str(c.headers).lower() + str(c.body).lower(),
    "Tool call ID": lambda c: "tool_call_id" in str(c.headers).lower() + str(c.body).lower(),
    "Unexpected extra body fields": lambda c: isinstance(c.body, dict) and bool(set(c.body) - {"interaction_id", "caller_number", "service", "phone", "date_expression", "time_expression", "advisor", "slot_id", "customer_phone", "customer_name", "vehicle_reg", "caller_confirmed", "reason", "preferred_time"}),
}


def main(out: str = "docs/experiments/sarvam-tool-metadata.md") -> None:
    db = SessionLocal()
    caps = [c for c in db.query(RequestCapture).all() if c.path.startswith("/tools/")]
    n = len(caps)
    lines = ["# Sarvam tool-call metadata (MEASURED from captured requests)", "",
             f"Captured tool requests: N={n}. Secrets redacted before storage.", "",
             "| Field | Classification | Seen in |", "|---|---|---|"]
    for name, test in FIELDS.items():
        hits = sum(1 for c in caps if test(c))
        cls = "UNKNOWN (no captures)" if n == 0 else ("VERIFIED" if hits else "ABSENT")
        lines.append(f"| {name} | {cls} | {hits}/{n} |")
    if caps:
        hdrs = sorted({k.lower() for c in caps for k in c.headers})
        unknown = sorted({k for c in caps if isinstance(c.body, dict) for k, v in c.body.items() if isinstance(v, dict) and v.get("unknown_field")})
        lines += ["", "## All header names observed", ", ".join(hdrs),
                  "", "## Body field names we did not define (values never stored)", ", ".join(unknown) or "none",
                  "", "## Source IPs observed", ", ".join(sorted({c.source_ip for c in caps}))]
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
