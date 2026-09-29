from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class STTResult:
    transcript: str = ""
    partials: int = 0
    first_partial_ms: float | None = None          # relative to first audio sent (same clock)
    final_ms: list[float] = field(default_factory=list)
    speech_end_sent_ms: float | None = None         # reference point (decision 0002)
    final_after_speech_end_ms: float | None = None
    latency_flag: str | None = None                 # set => excluded from percentiles, counted separately
    provider_endpoint_ms: float | None = None       # provider's own end-of-speech event, relative to speech end
    billed_seconds: float | None = None
    session: dict = field(default_factory=dict)     # request_id, resolved config / model_info (provenance)
    events: dict = field(default_factory=dict)      # counts by event type
    errors: list[str] = field(default_factory=list)
    detected_language: str | None = None
