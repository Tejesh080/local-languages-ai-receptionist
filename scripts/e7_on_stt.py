"""E7 part 2: run the resolver on REAL E4 transcripts for person / service / vehicle entities that exist in the tenant data."""
from __future__ import annotations
import json, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entities.resolver import resolve_name, resolve_vehicle
from benchmark.scoring.stats import describe
from scripts.e7_synthetic import PEOPLE, SVC, REGS  # tenant candidates


def main(run_dir: str, manifest: str) -> None:
    items = {json.loads(l)["id"]: json.loads(l) for l in open(manifest, encoding="utf-8")}
    by_label = {c.label: c.id for c in PEOPLE + SVC + REGS}
    m = defaultdict(lambda: defaultdict(int))
    for line in open(Path(run_dir) / "results.jsonl", encoding="utf-8"):
        r = json.loads(line); it = items.get(r["item_id"])
        if not it:
            continue
        hyp = r.get("transcript") or ""
        for e in it["entities"]:
            truth = by_label.get(e["value"])
            if truth is None or e["type"] not in ("person", "service", "vehicle_reg"):
                continue
            res = resolve_vehicle(hyp, REGS) if e["type"] == "vehicle_reg" else resolve_name(hyp, PEOPLE if e["type"] == "person" else SVC)
            k = m[(r["config"], e["type"])]
            k["n"] += 1; k[res.decision] += 1
            k["top1"] += res.best is not None and res.best.id == truth
            k["top3"] += truth in [s.candidate.id for s in res.top]
            k["silent_wrong"] += res.decision == "auto" and (res.best is None or res.best.id != truth)
    for (cfg, et), k in sorted(m.items()):
        print(f"{cfg} {et}: " + "; ".join([describe(k['top1'], k['n'], 'top-1'), describe(k['top3'], k['n'], 'top-3'),
              describe(k['silent_wrong'], k['n'], 'silent wrong')]) + f"; decisions auto {k['auto']} confirm {k['confirm']} clarify {k['clarify']} no_match {k['no_match']}")


if __name__ == "__main__":
    main(*sys.argv[1:])
