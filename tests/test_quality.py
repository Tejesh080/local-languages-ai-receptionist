import csv, hashlib, json, os, wave
from pathlib import Path
import pytest
from tests.fakes import tone, silence
from benchmark.build_manifest import build
from benchmark import quality


def _wav(path, pcm, rate=8000, ch=1):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(ch); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def dataset(tmp_path):
    sess = tmp_path / "rec" / "20261001T100000_CA1"; sess.mkdir(parents=True)
    prompts = tmp_path / "prompts.jsonl"; assign = tmp_path / "assign.json"
    ents = {"P001": [{"type": "phone", "value": "9848012345"}], "P002": [{"type": "vehicle_reg", "value": "TS09EA4521"}],
            "P003": [{"type": "phone", "value": "12345"}], "P004": [{"type": "time", "value": "17:30"}],
            "P005": [{"type": "date", "value": "tomorrow"}]}
    prompts.write_text("\n".join(json.dumps({"id": k, "text": "x", "partition": "unseen", "style": "tenglish", "entities": v})
                                 for k, v in ents.items()) + "\n")
    assign.write_text(json.dumps({"speakers": {"SPK01": [{"n": i + 1, "prompt_id": f"P00{i+1}", "condition": "quiet_room"} for i in range(5)]}}))
    audio = {1: tone(900) + silence(1500), 2: tone(900) + silence(1500), 3: tone(900) + silence(1500),
             4: silence(3000), 5: b""}
    lines = [json.dumps({"event": "session", "speaker_code": "1001", "params": {}, "vad": {}})]
    for n, pcm in audio.items():
        f = sess / f"SPK1001_{n:02d}.wav"
        sha = _wav(f, pcm)
        end = 800 * 8 // 1 * 9 if n <= 3 else None
        lines.append(json.dumps({"event": "utterance", "n": n, "file": f.name, "sha256": sha, "sample_rate": 8000,
                                 "speech_end_sample": 7200 if n <= 3 else None, "speech_start_sample": 0,
                                 "file_end_sample": len(pcm) // 2, "end_reason": "silence", "mark_method": "ack"}))
    (sess / "session.jsonl").write_text("\n".join(lines) + "\n")
    spk = tmp_path / "speakers.csv"
    spk.write_text("speaker_code,region,gender,age_band,carrier,consent_ref\n1001,telangana,female,25-34,jio,WA-1\n")
    raw = tmp_path / "raw.jsonl"
    build(str(tmp_path / "rec"), str(spk), str(raw), prompts, assign)
    return tmp_path, raw, sess


def test_flags_and_blocking_gate(dataset, monkeypatch):
    tmp, raw, sess = dataset
    monkeypatch.setattr(quality, "ROOT", tmp)
    st = quality.run(str(raw), None, 1500, str(tmp))
    report = (tmp / "dataset-quality-report.md").read_text()
    assert "Analysis manifest NOT written" in report and not (tmp / "e3_analysis.jsonl").exists()
    blocked = {i.split("_")[-1] for i in st["unresolved_blocking"]}
    assert blocked == {"03.wav", "04.wav", "05.wav"}          # invalid phone annotation, silence only, empty
    assert "entity_invalid_phone" in report and "no_speech_detected" in report and "empty" in report


def test_exclusions_need_reasons_and_raw_is_untouched(dataset, monkeypatch):
    tmp, raw, sess = dataset
    monkeypatch.setattr(quality, "ROOT", tmp)
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sess.glob("*.wav")}
    ex = tmp / "exclusions.csv"
    ex.write_text("item_id,reason,excluded_by,date\n" + f"{sess.name}/SPK1001_03.wav,,me,2026-10-01\n")
    with pytest.raises(SystemExit):
        quality.run(str(raw), str(ex), 1500, str(tmp))
    rows = [f"{sess.name}/SPK1001_0{n}.wav,{r},shivam,2026-10-01" for n, r in ((3, "bad phone annotation"), (4, "no speech"), (5, "empty file"))]
    ex.write_text("item_id,reason,excluded_by,date\n" + "\n".join(rows) + "\n")
    st = quality.run(str(raw), str(ex), 1000, str(tmp))          # standardized 1.0 s trailing silence differs from raw 1.5 s
    assert st["n_analysis"] == 2 and not st["unresolved_blocking"]
    items = [json.loads(l) for l in open(tmp / "e3_analysis.jsonl")]
    for it in items:
        assert it["speech_end_sample"] < it["file_end_sample"]
        assert Path(it["derived_path"]).exists() and it["raw_sha256"] != it["derived_sha256"]
    after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sess.glob("*.wav")}
    assert before == after


def test_tampered_raw_is_blocking(dataset, monkeypatch):
    tmp, raw, sess = dataset
    monkeypatch.setattr(quality, "ROOT", tmp)
    f = sess / "SPK1001_01.wav"; os.chmod(f, 0o644)
    _wav(f, tone(900) + silence(1400))                          # modified after collection
    build(str(tmp / "rec"), str(tmp / "speakers.csv"), str(raw), tmp / "prompts.jsonl", tmp / "assign.json")
    st = quality.run(str(raw), None, 1500, str(tmp))
    assert any(i.endswith("SPK1001_01.wav") for i in st["unresolved_blocking"])
    assert "sha_mismatch_raw_modified" in (tmp / "dataset-quality-report.md").read_text()
