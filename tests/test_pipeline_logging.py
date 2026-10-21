from __future__ import annotations

import threading
from types import SimpleNamespace

import pytest

from pricetyper.config import AppConfig
from pricetyper.pipeline import Pipeline


class MemoryLogger:
    def __init__(self):
        self.records = []

    def log(self, event, **fields):
        self.records.append((event, fields))


def test_comparison_mode_omits_transcript_text_from_asr_and_parse_logs():
    reference_text = "giá ba trăm nghìn"
    event = SimpleNamespace(
        kind="final", text=reference_text, t_audio_ns=1_000_000, t_ns=2_000_000
    )

    class FakeAsr:
        def feed(self, _pcm, _audio_ns):
            return [event]

    logger = MemoryLogger()
    config = AppConfig()
    controller = SimpleNamespace(stop_event=threading.Event(), armed=threading.Event())
    pipeline = Pipeline(
        source=None,
        asr=FakeAsr(),
        sender=None,
        config=config,
        controller=controller,
        logger=logger,
        log_transcript_text=False,
    )
    pipeline.audio_q.put((b"\x00\x00", 1))
    pipeline.audio_q.put(None)
    pipeline._asr_loop()
    pipeline._decide_loop()

    text_records = [
        fields
        for name, fields in logger.records
        if name.startswith("asr_") or name == "parse"
    ]
    assert text_records
    assert all("text" not in fields for fields in text_records)

    parsed = next(fields for name, fields in logger.records if name == "parse")
    assert parsed["passed"] == [300000]
    assert pipeline.ui_q.get_nowait()["kind"] == "asr"
    assert pipeline.ui_q.get_nowait() == {
        "kind": "parse",
        "event_kind": "final",
        "candidate": 300000,
        "asr_chunk_delay_ms": 1.0,
    }


def test_pipeline_flushes_zipformer_final_event_when_audio_source_ends():
    final = SimpleNamespace(
        kind="final", text="hai nghìn", t_audio_ns=1_000_000, t_ns=2_000_000
    )

    class FlushAsr:
        finish_on_stop = True

        def feed(self, _pcm, _audio_ns):
            return []

        def finish(self, _audio_ns):
            return [final]

    logger = MemoryLogger()
    config = AppConfig()
    controller = SimpleNamespace(stop_event=threading.Event(), armed=threading.Event())
    pipeline = Pipeline(
        source=None,
        asr=FlushAsr(),
        sender=None,
        config=config,
        controller=controller,
        logger=logger,
    )
    pipeline.audio_q.put((b"\x00\x00", 1_000_000))
    pipeline.audio_q.put(None)

    pipeline._asr_loop()
    pipeline._decide_loop()

    assert ("asr_final", {"text": "hai nghìn"}) in logger.records
    assert any(name == "parse" for name, _fields in logger.records)


def test_audio_queue_overflow_clears_backlog_and_disarms():
    class OverflowController:
        def __init__(self):
            self.armed = threading.Event()
            self.armed.set()
            self.stop_event = threading.Event()
            self.disarm_calls = 0

        def disarm(self):
            self.disarm_calls += 1
            self.armed.clear()

    logger = MemoryLogger()
    controller = OverflowController()
    config = AppConfig()
    config.audio.queue_max_chunks = 2
    pipeline = Pipeline(
        source=None,
        asr=None,
        sender=None,
        config=config,
        controller=controller,
        logger=logger,
        send_final_only=True,
    )
    pipeline.audio_q.put((b"old-1", 1, 0))
    pipeline.audio_q.put((b"old-2", 2, 0))

    pipeline._put_audio((b"new", 3))

    assert pipeline.audio_q.qsize() == 1
    assert pipeline.audio_q.get_nowait() == (b"new", 3, 1)
    assert controller.disarm_calls == 1
    assert any(name == "audio_overflow" for name, _fields in logger.records)
    warning = pipeline.ui_q.get_nowait()
    assert warning["kind"] == "health_warning"
    assert warning["code"] == "audio_gap"


def test_report_audio_gap_warns_and_disarms_for_bridge_queue_overflow():
    class GapController:
        def __init__(self):
            self.armed = threading.Event()
            self.armed.set()
            self.stop_event = threading.Event()
            self.disarm_calls = 0

        def disarm(self):
            self.disarm_calls += 1
            self.armed.clear()

    controller = GapController()
    logger = MemoryLogger()
    config = AppConfig()
    pipeline = Pipeline(
        source=None,
        asr=None,
        sender=None,
        config=config,
        controller=controller,
        logger=logger,
    )
    pipeline.audio_q.put((b"stale", 1, 0))

    pipeline.report_audio_gap(
        reason="browser_bridge_queue_full",
        message="Audio bị rơi.",
        dropped_chunks=3,
    )

    assert pipeline.audio_q.empty()
    assert pipeline._audio_generation == 1
    assert controller.disarm_calls == 1
    warning = pipeline.ui_q.get_nowait()
    assert warning["kind"] == "health_warning"
    assert warning["message"] == "Audio bị rơi."
    assert any(name == "audio_overflow" for name, _fields in logger.records)


def test_sustained_silence_emits_warning_then_recovery_notice():
    class SilentThenActiveSource:
        def __init__(self):
            self.items = [
                (b"\x00\x00" * 640, 1_000_000_000),
                (b"\x00\x00" * 640, 31_000_000_000),
                (b"\xff\x7f" * 640, 31_100_000_000),
                None,
            ]

        def start(self):
            pass

        def read(self):
            return self.items.pop(0)

        def stop(self):
            pass

    config = AppConfig()
    pipeline = Pipeline(
        source=SilentThenActiveSource(),
        asr=None,
        sender=None,
        config=config,
        controller=SimpleNamespace(
            stop_event=threading.Event(), armed=threading.Event()
        ),
        logger=MemoryLogger(),
    )

    pipeline._audio_loop()

    notices = list(pipeline.ui_q.queue)
    assert notices[0]["kind"] == "health_warning"
    assert notices[0]["code"] == "silent_audio"
    assert notices[1] == {
        "kind": "health_recovered",
        "code": "silent_audio",
        "message": "Đã nhận lại tín hiệu audio.",
    }


def test_first_final_after_audio_gap_is_preview_only_and_resets_asr():
    final = SimpleNamespace(kind="final", text="hai nghìn", t_audio_ns=2, t_ns=3)

    class ResetAsr:
        def __init__(self):
            self.reset_calls = 0

        def reset(self):
            self.reset_calls += 1

        def feed(self, _pcm, _audio_ns):
            return [final]

    asr = ResetAsr()
    config = AppConfig()
    controller = SimpleNamespace(stop_event=threading.Event(), armed=threading.Event())
    pipeline = Pipeline(
        source=None,
        asr=asr,
        sender=None,
        config=config,
        controller=controller,
        logger=MemoryLogger(),
        candidate_scope="number",
        send_final_only=True,
    )
    pipeline.audio_q.put((b"pcm", 1, 1))
    pipeline.audio_q.put(None)

    pipeline._asr_loop()

    assert asr.reset_calls == 1
    assert pipeline.event_q.get_nowait().kind == "partial"
    assert pipeline.event_q.get_nowait() is pipeline._event_stop


@pytest.mark.parametrize(
    ("text", "minimum", "expected_values"),
    [
        ("SỐ CHÍN", 1, [9]),
        ("CHÍN", 1000, [9]),
        (
            "SỐ CHÍN VÀ MỘT HAI BA BỐN NĂM SÁU BẢY TÁM CHÍN",
            1000,
            [9, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        ),
    ],
)
def test_number_preview_bypasses_the_price_gate_for_spoken_counting_numbers(
    text, minimum, expected_values
):
    event = SimpleNamespace(
        kind="final", text=text, t_audio_ns=1_000_000, t_ns=2_000_000
    )

    class FakeAsr:
        def feed(self, _pcm, _audio_ns):
            return [event]

    logger = MemoryLogger()
    config = AppConfig()
    config.decision.min_value = minimum
    controller = SimpleNamespace(stop_event=threading.Event(), armed=threading.Event())
    pipeline = Pipeline(
        source=None,
        asr=FakeAsr(),
        sender=None,
        config=config,
        controller=controller,
        logger=logger,
        candidate_scope="number",
    )
    pipeline.audio_q.put((b"\x00\x00", 1_000_000))
    pipeline.audio_q.put(None)

    pipeline._asr_loop()
    pipeline._decide_loop()

    parsed = next(fields for name, fields in logger.records if name == "parse")
    assert parsed["passed"] == []  # the default price gate rejects the phrase
    assert parsed["candidate_scope"] == "number"
    assert parsed["displayed"] == expected_values
    pipeline.ui_q.get_nowait()  # ASR transcript
    assert pipeline.ui_q.get_nowait() == {
        "kind": "parse",
        "event_kind": "final",
        "candidate": expected_values[-1],
        "asr_chunk_delay_ms": 1.0,
    }
