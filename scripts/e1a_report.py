"""Aggregate the E1A call log + backend tool logs into docs/results/E1A-smoke.md. Failed calls are never dropped."""
from __future__ import annotations
import csv, json, subprocess, sys, datetime as dt
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmark.scoring.stats import describe
from backend.db import SessionLocal
from backend.models import ToolCallLog, Booking, CallRecord


def main(log_csv: str, out: str = "docs/results/E1A-smoke.md", price_per_min: float | None = None) -> None:
    rows = list(csv.DictReader(open(log_csv, encoding="utf-8")))
    n = len(rows)
    num = lambda r, k: int(float(r[k] or 0))
    db = SessionLocal()
    iids = {r["interaction_id"] for r in rows if r["interaction_id"]}
    tools = [t for t in db.query(ToolCallLog).all() if t.interaction_id in iids]
    records = {c.interaction_id: c for c in db.query(CallRecord).all() if c.interaction_id in iids}
    bookings = [b for b in db.query(Booking).all() if b.interaction_id in iids]
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    completed = sum(r["task_completed"].strip().lower() in ("y", "yes", "1", "true") for r in rows)
    calls_with_p0 = sum(num(r, "p0_count") > 0 for r in rows)
    calls_with_p1 = sum(num(r, "p1_count") > 0 for r in rows)
    dur = [records[i].duration_s for i in iids if i in records] or [float(r["duration_s"] or 0) for r in rows]
    status = Counter(t.status for t in tools)
    lat = sorted(t.latency_ms for t in tools)
    pct = lambda p: lat[min(len(lat) - 1, int(p * len(lat)))] if lat else float("nan")
    total_min = sum(dur) / 60
    lines = [f"# E1A results (generated {dt.datetime.now().isoformat(timespec='minutes')}, git {commit})", "",
             f"Calls: N={n}. This is a SMOKE TEST, not production evidence.", "",
             "## Outcomes",
             "- " + describe(completed, n, "Task completed"),
             "- " + describe(calls_with_p0, n, "Calls with a P0 failure"),
             "- " + describe(calls_with_p1, n, "Calls with a P1 failure"),
             f"- P2 failures (total): {sum(num(r, 'p2_count') for r in rows)}",
             f"- Entity errors (total): {sum(len([e for e in r['entity_errors'].split(';') if e.strip()]) for r in rows)}",
             f"- Wrong tool calls: {sum(num(r, 'wrong_tool_calls') for r in rows)}; failed tool calls (manual): {sum(num(r, 'failed_tool_calls') for r in rows)}",
             f"- False cutoffs: {sum(num(r, 'false_cutoffs') for r in rows)}; caller repetitions: {sum(num(r, 'caller_repetitions') for r in rows)}",
             f"- Average call duration: {sum(dur)/len(dur):.0f} s" if dur else "- Average call duration: UNKNOWN",
             f"- Bookings persisted: {len(bookings)}",
             "", "## Backend tool calls (MEASURED server-side)",
             f"- Tool calls: {len(tools)}; by status: {dict(status)}",
             f"- Tool latency p50 {pct(.5):.0f} ms, p95 {pct(.95):.0f} ms (server only; excludes Sarvam and network)",
             "", "## Cost"]
    if price_per_min:
        lines += [f"- Minutes: {total_min:.1f}; at Rs{price_per_min}/min -> Rs{total_min*price_per_min:.0f}",
                  f"- Cost per completed call: Rs{(total_min*price_per_min/completed) if completed else float('nan'):.1f}",
                  f"- Cost per booking: Rs{(total_min*price_per_min/len(bookings)) if bookings else float('nan'):.1f}"]
    else:
        lines += ["- Per-minute price not supplied (pass --price from the dashboard). UNKNOWN."]
    lines += ["", "## By eagerness setting"]
    for eag in sorted({r["eagerness"] for r in rows}):
        sub = [r for r in rows if r["eagerness"] == eag]
        lines.append(f"- {eag or 'unset'}: N={len(sub)}, false cutoffs {sum(num(r, 'false_cutoffs') for r in sub)}, "
                     f"slowest-gap median {sorted(float(r['perceived_slowest_gap_s'] or 0) for r in sub)[len(sub)//2]:.1f} s")
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    import argparse
    a = argparse.ArgumentParser(); a.add_argument("log_csv"); a.add_argument("--price", type=float)
    x = a.parse_args(); main(x.log_csv, price_per_min=x.price)
