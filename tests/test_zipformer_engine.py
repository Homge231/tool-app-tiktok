from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from pricetyper.asr.zipformer_engine import VAD_WINDOW_SIZE, ZipformerEngine


class FakeRecognizer:
    def __init__(self):
        self.decode_calls = 0

    def create_stream(self):
        return SimpleNamespace(accept_waveform=lambda *_args: None, result=None)

    def decode_stream(self, stream):
        self.decode_calls += 1
        stream.result = SimpleNamespace(text="hai nghìn")


class FakeVad:
    def __init__(self, finalize_after_second_window=False):
        self.windows = []
        self.detected = False
        self.current_segment = SimpleNamespace(samples=np.ones(8_000, dtype=np.float32))
        self.completed = []
        self.finalize_after_second_window = finalize_after_second_window

    def accept_waveform(self, samples):
        self.windows.append(np.asarray(samples).copy())
        if len(self.windows) == 1:
            self.detected = True
        elif self.finalize_after_second_window:
            self.detected = False
            self.completed.append(
                SimpleNamespace(samples=np.ones(9_000, dtype=np.float32))
            )

    def is_speech_detected(self):
        return self.detected

    def empty(self):
        return not self.completed

    @property
    def front(self):
        return self.completed[0]

    def pop(self):
        self.completed.pop(0)

    def flush(self):
        if self.detected:
            self.detected = False
            self.completed.append(
                SimpleNamespace(samples=np.ones(9_000, dtype=np.float32))
            )

    def reset(self):
        self.windows.clear()
        self.completed.clear()
        self.detected = False


class ContinuousSpeechVad:
    def __init__(self):
        self.detected = False
        self.active_samples = 0
        self.completed = []
        self.accepted_windows = 0
        self.reset_calls = 0

    @property
    def current_segment(self):
        return SimpleNamespace(samples=np.zeros(self.active_samples, dtype=np.float32))

    def accept_waveform(self, samples):
        self.detected = True
        self.active_samples += len(samples)
        self.accepted_windows += 1

    def is_speech_detected(self):
        return self.detected

    def empty(self):
        return not self.completed

    @property
    def front(self):
        return self.completed[0]

    def pop(self):
        self.completed.pop(0)

    def flush(self):
        if self.detected and self.active_samples:
            self.completed.append(
                SimpleNamespace(samples=np.zeros(self.active_samples, dtype=np.float32))
            )
            self.detected = False

    def reset(self):
        self.detected = False
        self.active_samples = 0
        self.reset_calls += 1


class BufferedVadAfterSoftLimit(ContinuousSpeechVad):
    def is_speech_detected(self):
        return False


def pcm_chunk():
    return np.zeros(640, dtype=np.int16).tobytes()


def test_zipformer_vad_adapter_emits_provisional_then_final_text():
    vad = FakeVad(finalize_after_second_window=True)
    engine = ZipformerEngine(recognizer=FakeRecognizer(), vad=vad)

    partial = engine.feed(pcm_chunk(), 1_000_000_000)
    final = engine.feed(pcm_chunk(), 1_040_000_000)

    assert [(event.kind, event.text) for event in partial] == [("partial", "hai nghìn")]
    assert [(event.kind, event.text) for event in final] == [("final", "hai nghìn")]
    assert all(len(window) == VAD_WINDOW_SIZE for window in vad.windows)


def test_zipformer_finish_flushes_the_last_open_utterance():
    vad = FakeVad()
    engine = ZipformerEngine(recognizer=FakeRecognizer(), vad=vad)
    partial = engine.feed(pcm_chunk(), 1_000_000_000)

    final = engine.finish(1_040_000_000)

    assert partial and partial[0].kind == "partial"
    assert [(event.kind, event.text) for event in final] == [("final", "hai nghìn")]
    assert engine.finish(1_080_000_000) == []


def test_zipformer_engine_rejects_odd_pcm_byte_count():
    engine = ZipformerEngine(recognizer=FakeRecognizer(), vad=FakeVad())

    with pytest.raises(ValueError, match="complete PCM16"):
        engine.feed(b"\x00", 1)


def test_zipformer_can_skip_repeated_partial_decodes():
    recognizer = FakeRecognizer()
    engine = ZipformerEngine(recognizer=recognizer, vad=FakeVad(), emit_partials=False)

    for index in range(5):
        assert engine.feed(pcm_chunk(), 1_000_000_000 + index * 40_000_000) == []

    assert recognizer.decode_calls == 0


def test_long_continuous_speech_rolls_over_as_preview_not_final():
    recognizer = FakeRecognizer()
    vad = ContinuousSpeechVad()
    engine = ZipformerEngine(
        recognizer=recognizer,
        vad=vad,
        emit_partials=False,
        max_active_speech_seconds=0.064,
    )

    first = engine.feed(pcm_chunk(), 1_000_000_000)
    second = engine.feed(pcm_chunk(), 1_040_000_000)
    after_rollover = engine.feed(pcm_chunk(), 1_080_000_000)

    assert first == []
    assert [(event.kind, event.text) for event in second] == [("partial", "hai nghìn")]
    assert after_rollover == []
    assert vad.reset_calls == 1
    assert vad.accepted_windows == 3
    assert recognizer.decode_calls == 1


def test_long_vad_buffer_rolls_over_even_after_activity_flag_clears():
    recognizer = FakeRecognizer()
    vad = BufferedVadAfterSoftLimit()
    engine = ZipformerEngine(
        recognizer=recognizer,
        vad=vad,
        emit_partials=False,
        max_active_speech_seconds=0.032,
    )

    events = engine.feed(pcm_chunk(), 1_000_000_000)

    assert [(event.kind, event.text) for event in events] == [("partial", "hai nghìn")]
    assert vad.reset_calls == 1
    assert recognizer.decode_calls == 1
