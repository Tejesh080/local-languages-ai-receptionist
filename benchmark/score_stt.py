"""Score an E4 run: entity accuracy (raw + normalized) by class and slice, WER/CER, latency, errors.
Slices are reported separately; no single aggregate decides anything."""
from __future__ import annotations
import argparse, json, sys
from collections import defaultdict
from pathlib import Path
import jiwer
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from entities.normalize import for_wer, spoken_digits_to_digits
from benchmark.scoring.entities_match import match
from benchmark.scoring.stats import wilson

NOISY = {"fan_on", "tv_background", "traffic", "car", "handset_outdoors"}


def slices_for(item: dict) -> list[str]:
    s = ["ALL", f"partition:{item['partition']}", f"style:{item['style']}", f"region:{item['region']}"]
    s.append("audio:noisy" if item["condition"] in NOISY else ("audio:speakerphone" if item["condition"] == "speakerphone" else "audio:quiet"))
    return s


def pct(xs, p):
    xs = sorted(x for x in xs if x is not None)
    return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None


def main(run_dir: str, manifest: str) -> str:
    items = {json.loads(l)["id"]: json.loads(l) for l in open(manifest, encoding="utf-8")}
    rows = [json.loads(l) for l in open(Path(run_dir) / "results.jsonl", encoding="utf-8")]
    run = json.load(open(Path(run_dir) / "run.json"))
    ent = defaultdict(lambda: [0, 0, 0])          # (config, slice, etype) -> [n, raw_ok, norm_ok]
    errm = defaultdict(int)                        # (config, etype, kind)
    wer_acc = defaultdict(lambda: [[], [], [], []])  # config, slice -> refs, hyps (raw), refs, hyps (normalized digits)
    lat = defaultdict(lambda: defaultdict(list))
    errs = defaultdict(int)
    for r in rows:
        it = items.get(r["item_id"])
        if not it:
            continue
        cfg, hyp = r["config"], r.get("transcript") or ""
        if r.get("errors"):
            errs[cfg] += 1
        lat[cfg]["first_partial_ms"].append(r.get("first_partial_ms"))
        lat[cfg]["final_after_speech_end_ms"].append(r.get("final_after_speech_end_ms"))
        for sl in slices_for(it):
            w = wer_acc[(cfg, sl)]
            w[0].append(for_wer(it["text_ref"]) or "-"); w[1].append(for_wer(hyp) or "-")
            w[2].append(for_wer(spoken_digits_to_digits(it["text_ref"])) or "-"); w[3].append(for_wer(spoken_digits_to_digits(hyp)) or "-")
            for e in it["entities"]:
                raw, norm, kind = match(e, hyp)
                for key in (e["type"], "ANY_ENTITY"):
                    a = ent[(cfg, sl, key)]; a[0] += 1; a[1] += raw; a[2] += norm
                if sl == "ALL":
                    errm[(cfg, e["type"], kind)] += 1
    configs = sorted({r["config"] for r in rows})
    L = [f"# E4 STT results: run {run['run_id']}", "",
         f"git {run['git_commit'][:10]} | dataset {run['dataset_version']} | N items {run['n_items']} | regions {run['regions']} | "
         f"keyterms sha {run['keyterms_sha']} ({len(run['keyterms'])} known-business terms only) | 8 kHz PCM16 PSTN via Exotel", "",
         "## Critical entities, normalized match (95% Wilson CI), slice ALL", "",
         "| Config | phone | vehicle_reg | date | time | price | person | locality | service | provider errors |", "|---" * 10 + "|"]
    for c in configs:
        cells = []
        for et in ["phone", "vehicle_reg", "date", "time", "price", "person", "locality", "service"]:
            n, _, ok = ent[(c, "ALL", et)]
            cells.append(f"{ok}/{n} ({wilson(ok, n)[0]:.0%}-{wilson(ok, n)[1]:.0%})" if n else "n/a")
        L.append(f"| {c} | " + " | ".join(cells) + f" | {errs[c]} |")
    L += ["", "## Entity accuracy by slice (normalized / raw), all entity types", ""]
    all_slices = sorted({k[1] for k in ent})
    L.append("| Config | " + " | ".join(all_slices) + " |"); L.append("|---" * (len(all_slices) + 1) + "|")
    for c in configs:
        cells = []
        for sl in all_slices:
            n, raw, ok = ent[(c, sl, "ANY_ENTITY")]
            cells.append(f"{ok/n:.0%} / {raw/n:.0%} (n={n})" if n else "n/a")
        L.append(f"| {c} | " + " | ".join(cells) + " |")
    L += ["", "## Keyterm effect by partition (normalized entity accuracy)", ""]
    for base_c, kt_c in [("sarvam_v4", "sarvam_v4_kt"), ("sarvam_v4_codemix", "sarvam_v4_codemix_kt"), ("deepgram_nova3_te", "deepgram_nova3_te_kt")]:
        if base_c in configs and kt_c in configs:
            parts = []
            for p in ("known", "confusable", "unseen"):
                a, b = ent[(base_c, f"partition:{p}", "ANY_ENTITY")], ent[(kt_c, f"partition:{p}", "ANY_ENTITY")]
                if a[0] and b[0]:
                    parts.append(f"{p}: {a[2]/a[0]:.0%} -> {b[2]/b[0]:.0%}")
            L.append(f"- {base_c} -> {kt_c}: " + "; ".join(parts))
    L += ["", "## WER / CER (raw text normalization; digits-normalized in brackets), slice ALL", "", "| Config | WER | CER |", "|---|---|---|"]
    for c in configs:
        w = wer_acc[(c, "ALL")]
        L.append(f"| {c} | {jiwer.wer(w[0], w[1]):.1%} [{jiwer.wer(w[2], w[3]):.1%}] | {jiwer.cer(w[0], w[1]):.1%} [{jiwer.cer(w[2], w[3]):.1%}] |")
    L += ["", "## Latency (replayed at real-time pace; client-side clock)", "", "| Config | first partial p50 / p95 ms | final after speech end p50 / p95 ms |", "|---|---|---|"]
    for c in configs:
        fp, fe = lat[c]["first_partial_ms"], lat[c]["final_after_speech_end_ms"]
        L.append(f"| {c} | {pct(fp,.5)} / {pct(fp,.95)} | {pct(fe,.5)} / {pct(fe,.95)} |")
    L += ["", "## Error matrix (slice ALL): counts by entity type and error kind", "", "| Config | type | ok | missing | wrong_value | invalid_format |", "|---|---|---|---|---|---|"]
    for c in configs:
        for et in sorted({k[1] for k in errm if k[0] == c}):
            L.append(f"| {c} | {et} | " + " | ".join(str(errm[(c, et, k)]) for k in ("ok", "missing", "wrong_value", "invalid_format")) + " |")
    out = "\n".join(L) + "\n"
    (Path(run_dir) / "report.md").write_text(out, encoding="utf-8")
    return out


if __name__ == "__main__":
    a = argparse.ArgumentParser(); a.add_argument("run_dir"); a.add_argument("manifest")
    x = a.parse_args(); print(main(x.run_dir, x.manifest))
