import json
from benchmark import score_stt


def test_report_counts_flags_and_aborts(tmp_path):
    items = [{"id": f"i{k}", "text_ref": "నా number 98480 12345", "partition": "unseen", "style": "tenglish",
              "region": "telangana", "condition": "speakerphone", "entities": [{"type": "phone", "value": "9848012345"}]} for k in range(3)]
    man = tmp_path / "m.jsonl"; man.write_text("\n".join(json.dumps(i, ensure_ascii=False) for i in items) + "\n")
    run = tmp_path / "run"; run.mkdir()
    (run / "run.json").write_text(json.dumps({"run_id": "r1", "git_commit": "abc", "dataset_version": "d", "n_items": 3,
                                              "regions": {"telangana": 3}, "keyterms_sha": "k", "keyterms": [], "replay": "standardized"}))
    rows = [{"config": "sarvam_v4", "item_id": "i0", "transcript": "నా number 98480 12345", "final_after_speech_end_ms": 420.0, "latency_flag": None, "first_partial_ms": 300},
            {"config": "sarvam_v4", "item_id": "i1", "transcript": "నా number 98480 12346", "final_after_speech_end_ms": None, "latency_flag": "final_before_speech_end"},
            {"config": "sarvam_v4", "item_id": "i2", "transcript": "", "errors": ["closed:1011"], "final_after_speech_end_ms": None, "latency_flag": "no_final"},
            {"config": "deepgram_nova3_te", "item_id": None, "event": "config_aborted", "reason": "first 5 attempts all failed"}]
    (run / "results.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    rep = score_stt.main(str(run), str(man))
    assert "| sarvam_v4 | 1/3" in rep                                  # phone: 1 of 3 correct, failures kept
    assert "| sarvam_v4 | 1 | 420.0 | 420.0 | 420.0 |" in rep           # only the valid latency enters percentiles
    assert "final_before_speech_end" in rep and "no_final" in rep and "deepgram_nova3_te: first 5" in rep
