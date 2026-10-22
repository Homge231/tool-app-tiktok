from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from pricetyper.asr import experimental_engines as experimental
from pricetyper.asr.errors import ModelError


def _touch_model_files(directory, names):
    directory.mkdir(exist_ok=True)
    for name in names:
        (directory / name).touch()


def test_load_gipformer_uses_local_int8_transducer_files(tmp_path, monkeypatch):
    names = ("encoder.int8.onnx", "decoder.int8.onnx", "joiner.int8.onnx", "tokens.txt")
    _touch_model_files(tmp_path, names)
    calls = []
    fake_sherpa = SimpleNamespace(
        OfflineRecognizer=SimpleNamespace(
            from_transducer=lambda **kwargs: calls.append(kwargs) or "gip-recognizer"
        )
    )
    monkeypatch.setattr(experimental, "_load_sherpa_onnx", lambda: fake_sherpa)

    assert experimental.load_gipformer(tmp_path) == "gip-recognizer"
    assert calls[0]["encoder"].endswith("encoder.int8.onnx")
    assert calls[0]["decoding_method"] == "greedy_search"
    assert calls[0]["provider"] == "cpu"


def test_load_streaming_zipformer_uses_chunk16_online_recognizer(tmp_path, monkeypatch):
    stem = experimental.STREAMING_MODEL_FILE_STEM
    names = (f"encoder-{stem}", f"decoder-{stem}", f"joiner-{stem}", "tokens.txt")
    _touch_model_files(tmp_path, names)
    calls = []
    fake_sherpa = SimpleNamespace(
        OnlineRecognizer=SimpleNamespace(
            from_transducer=lambda **kwargs: calls.append(kwargs) or "online-recognizer"
        )
    )
    monkeypatch.setattr(experimental, "_load_sherpa_onnx", lambda: fake_sherpa)

    assert experimental.load_streaming_zipformer(tmp_path) == "online-recognizer"
    assert "chunk-16-left-128" in calls[0]["encoder"]
    assert calls[0]["model_type"] == "zipformer2"
    assert calls[0]["enable_endpoint_detection"] is False


def test_missing_experiment_model_files_show_download_command(tmp_path):
    with pytest.raises(ModelError, match="download_asr_experiments.py"):
        experimental.load_gipformer(tmp_path)


def test_streaming_transcription_reports_partial_and_decode_timings():
    class FakeStream:
        def __init__(self):
            self.samples = 0

        def accept_waveform(self, _sample_rate, samples):
            self.samples += len(samples)
            self.owner.pending = True

        def input_finished(self):
            pass

    class FakeRecognizer:
        def create_stream(self):
            self.stream = FakeStream()
            self.stream.owner = self
            self.pending = False
            return self.stream

        def is_ready(self, _stream):
            return self.pending

        def decode_stream(self, _stream):
            self.pending = False

        def get_result(self, stream):
            return "một" if stream.samples else ""

    result = experimental.transcribe_streaming_zipformer(
        FakeRecognizer(), np.ones(1280, dtype=np.float32), chunk_samples=640
    )

    assert result["text"] == "một"
    assert result["decode_chunks"] == 2
    assert result["snapshots"][0]["text"] == "một"
    assert result["snapshots"][0]["audio_offset_ms"] == 40
