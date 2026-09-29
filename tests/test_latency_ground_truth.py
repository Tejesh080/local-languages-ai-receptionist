import asyncio, os, wave
import pytest
import websockets
from audio.vad import speech_bounds
from benchmark.segments import derive, sha256_file
from benchmark.replay import make_plan, Timeline, send_paced, endpoint_latency, latency_summary
from tests.fakes import tone, silence, sarvam_handler, deepgram_handler

RATE = 8000


def _wav(path, pcm):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(pcm)


def test_speech_end_is_before_file_end_when_trailing_silence_exists():
    pcm = silence(300) + tone(1000) + silence(1500)          # like a recorder file: 1.5 s trailing silence
    b = speech_bounds(pcm, RATE)
    file_end = len(pcm) // 2
    assert b.end_sample < file_end
    assert abs(b.end_sample - int(1.3 * RATE)) <= RATE * 0.04  # within two 20 ms frames of the true end
    assert abs(b.start_sample - int(0.3 * RATE)) <= RATE * 0.04


def test_derived_segment_keeps_raw_immutable(tmp_path):
    raw = tmp_path / "raw.wav"; _wav(raw, tone(800) + silence(1500))
    before = sha256_file(raw)
    meta = derive(str(raw), speech_end_sample=int(0.8 * RATE), trailing_ms=500, out_root=str(tmp_path / "derived"))
    assert sha256_file(raw) == before and meta["raw_sha256"] == before
    assert meta["derived_samples"] == int(0.8 * RATE) + int(0.5 * RATE)
    with pytest.raises(ValueError):
        derive(str(raw), speech_end_sample=10**9, trailing_ms=500, out_root=str(tmp_path / "d2"))


def test_plan_puts_a_chunk_boundary_exactly_on_speech_end():
    pcm = tone(1234) + silence(500)
    p = make_plan(pcm, RATE, 100, speech_end_sample=int(1.234 * RATE))
    sent = sum(len(c) for c in p.chunks[: p.speech_end_chunk + 1]) // 2
    assert sent == int(1.234 * RATE)
    assert b"".join(p.chunks) == pcm


def test_timeline_uses_one_clock_and_schedule():
    t = [100.0]
    tl = Timeline(clock=lambda: t[0])

    async def fake_sleep(d):
        t[0] += d

    async def fake_send(_):
        t[0] += 0.001                                         # socket handoff takes 1 ms
    p = make_plan(tone(1000) + silence(500), RATE, 100, speech_end_sample=RATE)
    asyncio.run(send_paced(p, fake_send, tl, sleep=fake_sleep))
    assert tl.t0 == 100.0
    assert abs(tl.t_speech_end_sent - (100.0 + 0.9 + 0.001)) < 1e-6   # chunk 9 scheduled at 0.9 s, sent +1 ms
    ms, flag = endpoint_latency(tl, [tl.t_speech_end_sent + 0.25])
    assert flag is None and abs(ms - 250) < 1e-6


async def _run_sarvam(port, handler, pcm, speech_end):
    os.environ["SARVAM_API_KEY"] = "test-key"; os.environ["SARVAM_RT_URL"] = f"ws://127.0.0.1:{port}/speech-to-text-realtime/ws"
    import importlib, benchmark.providers.sarvam_rt as m
    importlib.reload(m)
    async with websockets.serve(handler, "127.0.0.1", port):
        return await m.transcribe(make_plan(pcm, RATE, 100, speech_end), {"model": "saaras:v4", "timeout_margin_s": 5}, ["Kukatpally"])


def test_latency_is_measured_from_speech_end_not_file_end():
    recorder_trailing = silence(1500)                         # what the old method wrongly counted as speech time
    raw = tone(600) + recorder_trailing
    speech_end = int(0.6 * RATE)
    seen = {}
    res = asyncio.run(_run_sarvam(8765, sarvam_handler(final_delay_ms=150, seen=seen),
                                  raw[: speech_end * 2] + silence(1000), speech_end))
    assert not res.errors, res.errors
    assert res.latency_flag is None
    # fake provider endpoints on the first silent chunk (sent 100 ms after speech end) then waits 150 ms
    assert 200 <= res.final_after_speech_end_ms <= 450, res.final_after_speech_end_ms
    assert res.billed_seconds == pytest.approx(1.6, abs=0.01)          # string-typed float parsed
    assert res.session["request_id"] == "fake-req-1" and "keyterms=" in seen["path"] and "saaras%3Av4" in seen["path"]
    assert seen["headers"]["api-subscription-key"] == "test-key"
    old_method = res.final_ms[-1] - (len(raw) / 2 / RATE) * 1000        # final minus WAV duration incl. 1.5 s silence
    assert old_method < res.final_after_speech_end_ms - 1000, "old method understates latency by >1 s here"


def test_final_before_speech_end_is_flagged_not_counted():
    res = asyncio.run(_run_sarvam(8766, sarvam_handler(premature=True), tone(800) + silence(500), int(0.8 * RATE)))
    assert res.latency_flag == "final_before_speech_end" and res.final_after_speech_end_ms is None
    s = latency_summary([res.__dict__, {"final_after_speech_end_ms": 300.0, "latency_flag": None}])
    assert s["n_valid"] == 1 and s["flags"] == {"final_before_speech_end": 1} and s["p50"] == 300.0
    with pytest.raises(AssertionError):
        latency_summary([{"final_after_speech_end_ms": -40.0, "latency_flag": None}])


def test_sarvam_keyterm_rules():
    from benchmark.providers.sarvam_rt import build_url
    with pytest.raises(ValueError):
        build_url({"model": "saaras:v3-realtime"}, ["Kukatpally"], RATE)
    with pytest.raises(ValueError):
        build_url({"model": "saaras:v4"}, ["x"] * 51, RATE)
    assert "mode=codemix" in build_url({"model": "saaras:v4", "mode": "codemix"}, [], RATE)


def test_deepgram_adapter_same_reference():
    os.environ["DEEPGRAM_API_KEY"] = "dg-test"; os.environ["DEEPGRAM_URL"] = "ws://127.0.0.1:8767/v1/listen"
    import importlib, benchmark.providers.deepgram as m
    importlib.reload(m)
    seen = {}

    async def go():
        async with websockets.serve(deepgram_handler(150, seen), "127.0.0.1", 8767):
            return await m.transcribe(make_plan(tone(600) + silence(1000), RATE, 100, int(0.6 * RATE)),
                                      {"model": "nova-3", "language": "te", "timeout_margin_s": 5}, ["Kukatpally"])
    res = asyncio.run(go())
    assert not res.errors and res.latency_flag is None and 200 <= res.final_after_speech_end_ms <= 450
    assert seen["headers"]["authorization"] == "Token dg-test" and "language=te" in seen["path"] and "keyterm=Kukatpally" in seen["path"]
    assert res.session["model_info"] == {"name": "nova-3"} and res.billed_seconds == pytest.approx(1.6, abs=0.01)
