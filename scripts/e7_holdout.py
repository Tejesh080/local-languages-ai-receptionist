"""Run the E7 HOLDOUT set ONCE per frozen resolver version. Refuses to re-run (no tuning against the holdout)."""
from __future__ import annotations
import datetime as dt, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from entities import resolver_version
from entities.resolver import resolve_name, resolve_vehicle
from benchmark.e7.holdout_set import NAME_CASES, SERVICE_CASES, REG_CASES
from benchmark.scoring.stats import describe
from scripts.e7_synthetic import PEOPLE, SVC, REGS, evaluate


def main() -> None:
    rv = resolver_version()
    out = ROOT / f"docs/results/E7-holdout-{rv}.md"
    log = ROOT / "docs/results/E7-holdout-attempts.log"
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain", "entities"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    if out.exists():
        raise SystemExit(f"Holdout already evaluated for {rv}. It is single-use; write a new holdout set to evaluate again.")
    if dirty:
        raise SystemExit("entities/ has uncommitted changes: commit (freeze) the resolver before the holdout run")
    with open(log, "a") as f:
        f.write(f"{dt.datetime.now().isoformat(timespec='seconds')} run resolver={rv} git={commit}\n")
    L = [f"# E7 HOLDOUT (single run): resolver {rv}, git {commit}, {dt.date.today()}", "",
         "Synthetic text perturbations written before this run and not used for tuning. NOT evidence of real-STT robustness;",
         "the decisive E7 evaluation is on real E4 transcripts.", ""]
    for label, cases, fn in (("Person names", NAME_CASES, lambda t: resolve_name(t, PEOPLE)),
                             ("Services", SERVICE_CASES, lambda t: resolve_name(t, SVC, confirm_threshold=0.78)),
                             ("Vehicle registrations", REG_CASES, lambda t: resolve_vehicle(t, REGS))):
        m = evaluate(cases, fn)
        tn = m["target_n"]
        L += [f"## {label} (N={m['n']}: {tn} targets, {m['ambiguous_n']} ambiguous, {m['distractor_n']} unknown)", "",
              f"- {describe(m['top1'], tn, 'Top-1 correct')}", f"- {describe(m['top3'], tn, 'Top-3 recall')}",
              f"- Decisions on targets: auto {m['auto']}, confirm {m['confirm']}, clarify {m['clarify']}, no_match {m['no_match']}",
              f"- {describe(m['clarify'] + m['confirm'], tn, 'Needed a confirmation or clarification turn')}",
              f"- {describe(m['after_one_clarification'], tn, 'Correct after one clarification (simulated truthful caller)')}",
              f"- {describe(m['ambiguous_handled'], m['ambiguous_n'], 'Ambiguous inputs sent to clarification')}",
              f"- {describe(m['distractor_rejected'], m['distractor_n'], 'Unknown entities rejected (not matched to a record)')}",
              f"- {describe(m['silent_wrong'], m['n'], 'SILENT WRONG resolutions')}", ""]
        fails = []
        for text, truth in cases:
            r = fn(text)
            best = r.best.id if r.best else None
            ok = (best == truth and r.decision != "no_match") if isinstance(truth, str) else \
                 (r.decision in ("clarify", "no_match") or (r.decision == "confirm" and best in truth)) if isinstance(truth, set) else \
                 (r.decision == "no_match" or best is None or best not in {c.id for c in PEOPLE + SVC + REGS})
            if not ok:
                fails.append(f"  - `{text}` expected {truth} got {r.decision}/{best}")
        L += (["Failures (recorded, NOT fixed against this set):"] + fails + [""]) if fails else ["No failures observed in this set.", ""]
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
