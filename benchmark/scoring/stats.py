"""Statistical humility helpers: never report 'zero failure rate', report k/N with an upper bound."""
from __future__ import annotations
import math


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def zero_event_upper(n: int, conf: float = 0.95) -> float:
    """Exact one-sided upper bound on the true rate when 0 events were observed in n trials."""
    return 1 - (1 - conf) ** (1 / n) if n else 1.0


def describe(k: int, n: int, what: str) -> str:
    if n == 0:
        return f"{what}: not observed (N=0)"
    if k == 0:
        return f"{what}: 0 observed in N={n} (95% upper bound {zero_event_upper(n):.1%})"
    lo, hi = wilson(k, n)
    return f"{what}: {k}/{n} = {k/n:.1%} (95% CI {lo:.1%}-{hi:.1%})"
