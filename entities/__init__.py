"""Deterministic Telugu/Tenglish entity normalization and resolution (no LLM)."""
import hashlib as _h
from pathlib import Path as _P


def normalization_version() -> str:
    """Content hash of the normalization code; stored with every scored result."""
    root = _P(__file__).parent
    return "norm-" + _h.sha256(b"".join((root / f).read_bytes() for f in ("normalize.py", "dates.py", "telugu.py"))).hexdigest()[:12]


def resolver_version() -> str:
    root = _P(__file__).parent
    return "res-" + _h.sha256(b"".join((root / f).read_bytes() for f in ("normalize.py", "dates.py", "telugu.py", "resolver.py"))).hexdigest()[:12]
