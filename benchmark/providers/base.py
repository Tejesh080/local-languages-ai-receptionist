from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class STTResult:
    transcript: str = ""
    partials: int = 0
    first_partial_ms: float | None = None     # from first audio chunk sent
    final_ms: float | None = None             # from first audio chunk sent
    final_after_speech_end_ms: float | None = None  # from end of the real (non-padded) audio
    billed_seconds: float | None = None
    errors: list[str] = field(default_factory=list)
    detected_language: str | None = None
    raw_events: int = 0
