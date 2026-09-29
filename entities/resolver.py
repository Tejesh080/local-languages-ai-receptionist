"""Candidate resolution against tenant data. Policy: never silently auto-resolve critical or ambiguous entities."""
from __future__ import annotations
from dataclasses import dataclass, field
from rapidfuzz import fuzz
from .normalize import (name_tokens, phonetic_key, normalize_phone, normalize_vehicle_reg, partial_vehicle_reg,
                        base, to_latin)

CRITICAL = {"phone", "vehicle_reg", "date", "time", "price"}


@dataclass
class Candidate:
    id: str
    label: str
    aliases: list[str] = field(default_factory=list)


@dataclass
class Scored:
    candidate: Candidate
    score: float
    basis: str


@dataclass
class Resolution:
    decision: str                 # "auto" | "confirm" | "clarify" | "no_match"
    top: list[Scored]
    reason: str

    @property
    def best(self) -> Candidate | None:
        return self.top[0].candidate if self.top else None


def _name_score(observed: str, cand: Candidate) -> tuple[float, str]:
    obs_tokens = name_tokens(observed)
    if not obs_tokens:
        return 0.0, "empty"
    best = (0.0, "none")
    obs_norm = " ".join(obs_tokens)
    obs_ph = " ".join(phonetic_key(t) for t in obs_tokens)
    for form in [cand.label, *cand.aliases]:
        toks = name_tokens(form)
        norm = " ".join(toks)
        ph = " ".join(phonetic_key(t) for t in toks)
        if obs_norm == norm:
            return 1.0, "exact"
        if obs_ph == ph:
            best = max(best, (0.93, "phonetic_equal"))
        # partial names ("Reddy garu") match on token subset, penalised so they never auto-resolve alone
        if set(obs_ph.split()) <= set(ph.split()):
            best = max(best, (0.86 if len(obs_tokens) < len(toks) else 0.93, "phonetic_subset"))
        best = max(best, (0.9 * fuzz.ratio(obs_ph, ph) / 100, "phonetic_fuzzy"),
                   (0.85 * fuzz.token_set_ratio(obs_norm, norm) / 100, "latin_fuzzy"))
    return best


def resolve_name(observed: str, candidates: list[Candidate], *, auto_threshold: float = 0.99,
                 confirm_threshold: float = 0.80, margin: float = 0.08) -> Resolution:
    scored = sorted((Scored(c, *_name_score(observed, c)) for c in candidates), key=lambda s: -s.score)
    top = [s for s in scored if s.score > 0.5][:3]
    if not top or top[0].score < confirm_threshold * 0.9:
        return Resolution("no_match", top, "no candidate close enough; ask caller to repeat or spell")
    close = [s for s in top if top[0].score - s.score < margin]
    if len(close) > 1:
        return Resolution("clarify", close, "multiple close candidates; ask a distinguishing question")
    if top[0].score >= auto_threshold and top[0].basis == "exact":
        return Resolution("auto", top[:1], "exact match on label or alias")
    return Resolution("confirm", top[:1], f"single best candidate ({top[0].basis}); confirm with caller")


def resolve_vehicle(observed: str, known_regs: list[Candidate]) -> Resolution:
    """Registrations are critical: exact valid match -> confirm (read back char by char); never 'auto'."""
    reg = normalize_vehicle_reg(observed)
    if reg:
        for c in known_regs:
            if c.label == reg:
                return Resolution("confirm", [Scored(c, 1.0, "exact_valid")], "known vehicle; read back to confirm")
        return Resolution("confirm", [Scored(Candidate(reg, reg), 0.9, "valid_new")],
                          "valid format, not on file; read back character by character")
    partial = partial_vehicle_reg(observed)
    scored = sorted((Scored(c, fuzz.ratio(partial, c.label) / 100, "partial_fuzzy") for c in known_regs),
                    key=lambda s: -s.score)
    top = [s for s in scored if s.score >= 0.6][:3]
    if len(top) == 1 or (top and (len(top) == 1 or top[0].score - top[1].score >= 0.15)):
        return Resolution("confirm", top[:1], "partial match to a vehicle on file; read back character by character")
    if top:
        return Resolution("clarify", top, "several vehicles partially match; ask for the full number")
    return Resolution("no_match", [], "could not form a registration; ask caller to repeat slowly")


def resolve_phone(observed: str) -> Resolution:
    p = normalize_phone(observed)
    if p:
        return Resolution("confirm", [Scored(Candidate(p, p), 1.0, "valid_format")], "read back grouped digits")
    return Resolution("no_match", [], "not a valid 10-digit Indian mobile; ask again")
