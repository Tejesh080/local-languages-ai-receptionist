"""E7 DEVELOPMENT-set evaluation (resolver on hand-written perturbations used during development). Not independent.
Holdout: scripts/e7_holdout.py. Real transcripts: scripts/e7_on_stt.py."""
Part 2 (scripts/e7_on_stt.py) runs the same resolver on real E4 transcripts once they exist."""
from __future__ import annotations
import subprocess, sys, datetime as dt
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entities.resolver import Candidate, resolve_name, resolve_vehicle
from benchmark.scoring.stats import describe
from backend.seed import ADVISORS, CUSTOMERS, SERVICES

PEOPLE = [Candidate(a, n, [te]) for a, n, te in ADVISORS] + [Candidate(c, n) for c, n, _, _ in CUSTOMERS]
SVC = [Candidate(code, en, [te, *aliases]) for code, en, te, aliases, *_ in SERVICES]
REGS = [Candidate(reg, reg) for _, _, _, vs in CUSTOMERS for reg, _ in vs]

from benchmark.e7.dev_set import NAME_CASES, SERVICE_CASES, REG_CASES  # noqa: E402  DEVELOPMENT set


def evaluate(cases, resolver):
    m = defaultdict(int)
    for text, truth in cases:
        r = resolver(text)
        ids = [s.candidate.id for s in r.top]
        best = r.best.id if r.best else None
        m["n"] += 1
        if isinstance(truth, set):
            m["ambiguous_n"] += 1
            m["ambiguous_handled"] += r.decision in ("clarify", "no_match") or (r.decision == "confirm" and best in truth)
            m["silent_wrong"] += r.decision == "auto"
            continue
        if truth is None:
            m["distractor_n"] += 1
            m["distractor_rejected"] += best is None or r.decision == "no_match" or best not in {c.id for c in PEOPLE + SVC + REGS}
            m["silent_wrong"] += r.decision == "auto"
            continue
        m["target_n"] += 1
        m["top1"] += best == truth
        m["top3"] += truth in ids
        m["auto"] += r.decision == "auto"
        m["confirm"] += r.decision == "confirm"
        m["clarify"] += r.decision == "clarify"
        m["no_match"] += r.decision == "no_match"
        m["silent_wrong"] += r.decision == "auto" and best != truth
        # simulated caller answers the clarification truthfully
        m["after_one_clarification"] += (r.decision in ("auto", "confirm") and best == truth) or (r.decision == "clarify" and truth in ids)
    return m


def main(out="docs/results/E7-resolver-synthetic.md"):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip() or "uncommitted"
    L = [f"# E7 part 1: entity resolver on SYNTHETIC perturbations ({dt.date.today()}, git {commit})", "",
         "Status: MEASURED on hand-written text perturbations, NOT on STT output. It tests the resolver logic and policy only.",
         "Real-transcript E7 runs after E4 (scripts/e7_on_stt.py).", ""]
    for label, cases, fn in (("Person names", NAME_CASES, lambda t: resolve_name(t, PEOPLE)),
                             ("Services", SERVICE_CASES, lambda t: resolve_name(t, SVC, confirm_threshold=0.78)),
                             ("Vehicle registrations", REG_CASES, lambda t: resolve_vehicle(t, REGS))):
        m = evaluate(cases, fn)
        tn = m["target_n"]
        L += [f"## {label} (N={m['n']}: {tn} targets, {m['ambiguous_n']} ambiguous-by-design, {m['distractor_n']} distractors)", "",
              f"- {describe(m['top1'], tn, 'Top-1 candidate correct')}",
              f"- {describe(m['top3'], tn, 'Top-3 recall')}",
              f"- Decisions on targets: auto {m['auto']}, confirm {m['confirm']}, clarify {m['clarify']}, no_match {m['no_match']}",
              f"- {describe(m['after_one_clarification'], tn, 'Correct after one clarification (simulated truthful caller)')}",
              f"- {describe(m['ambiguous_handled'], m['ambiguous_n'], 'Ambiguous inputs sent to clarification (not silently picked)')}" if m["ambiguous_n"] else "",
              f"- {describe(m['distractor_rejected'], m['distractor_n'], 'Unknown entities NOT matched to an existing record')}" if m["distractor_n"] else "",
              f"- {describe(m['silent_wrong'], m['n'], 'SILENT WRONG resolutions')}", ""]
    Path(out).write_text("\n".join(x for x in L if x is not None) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
