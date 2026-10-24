from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from pricetyper.asr.errors import ModelError
from pricetyper.types import AsrEvent

SAMPLE_RATE = 16_000
MODEL_NAME = "sherpa-onnx-zipformer-vi-30M-int8-2026-02-09"
DEFAULT_MODEL_DIR = Path(__file__).resolve().parents[3] / "models" / MODEL_NAME
DEFAULT_VAD_MODEL = Path(__file__).resolve().parents[3] / "models" / "silero_vad.onnx"
VAD_WINDOW_SIZE = 512
DEFAULT_MIN_SILENCE_DURATION = 0.25
PARTIAL_INTERVAL_NS = 400_000_000
PARTIAL_MIN_SAMPLES = int(SAMPLE_RATE * 0.45)
MAX_ACTIVE_SPEECH_SECONDS = 12.0
VAD_BUFFER_SECONDS = 20.0


def _load_sherpa_onnx():
    try:
        import sherpa_onnx
    except ImportError as exc:
        raise ModelError(
            "Thiếu sherpa-onnx. Cài bằng: "
            ".\\.venv\\Scripts\\python.exe -m pip install -e ."
        ) from exc
    return sherpa_onnx


def load_zipformer(model_dir: Path = DEFAULT_MODEL_DIR):
    sherpa_onnx = _load_sherpa_onnx()

    encoder = model_dir / "encoder.int8.onnx"
    decoder = model_dir / "decoder.onnx"
    joiner = model_dir / "joiner.int8.onnx"
    tokens = model_dir / "tokens.txt"
    model_files = (encoder, decoder, joiner, tokens)
    missing = [path.name for path in model_files if not path.is_file()]
    if missing:
        raise ModelError(
            "Thiếu model Zipformer-VI ("
            + ", ".join(missing)
            + "). Chạy: .\\.venv\\Scripts\\python.exe "
            "scripts\\download_robust_asr_models.py"
        )

    try:
        return sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=str(encoder),
            decoder=str(decoder),
            joiner=str(joiner),
            tokens=str(tokens),
            num_threads=1,
            sample_rate=SAMPLE_RATE,
            feature_dim=80,
            modeling_unit="cjkchar",
            provider="cpu",
        )
    except Exception as exc:
        raise ModelError(f"Không thể khởi tạo Zipformer-VI: {exc}") from exc


def load_silero_vad(
    model_path: Path = DEFAULT_VAD_MODEL,
    *,
    min_silence_duration: float = DEFAULT_MIN_SILENCE_DURATION,
):
    sherpa_onnx = _load_sherpa_onnx()
    if not model_path.is_file():
        raise ModelError(
            f"Thiếu model Silero VAD tại {model_path}. Chạy: "
            ".\\.venv\\Scripts\\python.exe scripts\\download_robust_asr_models.py"
        )

    if min_silence_duration <= 0:
        raise ValueError("min_silence_duration must be positive")

    silero = sherpa_onnx.SileroVadModelConfig(
        model=str(model_path),
        threshold=0.5,
        min_silence_duration=min_silence_duration,
        min_speech_duration=0.12,
        window_size=VAD_WINDOW_SIZE,
        max_speech_duration=MAX_ACTIVE_SPEECH_SECONDS,
    )
    config = sherpa_onnx.VadModelConfig(
        silero_vad=silero,
        sample_rate=SAMPLE_RATE,
        num_threads=1,
        provider="cpu",
    )
    try:
        return sherpa_onnx.VoiceActivityDetector(config, VAD_BUFFER_SECONDS)
    except Exception as exc:
        raise ModelError(f"Không thể khởi tạo Silero VAD: {exc}") from exc


def transcribe_zipformer(recognizer, samples: np.ndarray) -> str:
    waveform = np.ascontiguousarray(samples, dtype=np.float32)
    if waveform.size == 0:
        return ""
    stream = recognizer.create_stream()
    stream.accept_waveform(SAMPLE_RATE, waveform)
    recognizer.decode_stream(stream)
    return stream.result.text.strip()


class ZipformerEngine:
    """Run offline Zipformer on Silero-VAD utterances from streaming PCM chunks.

    Zipformer-VI is an offline model, so interim results re-decode the active
    VAD segment periodically; a final event is emitted when VAD closes it.
    Callers may disable partial re-decodes when only finalized utterances matter.
    """

    finish_on_stop = True

    def __init__(
        self,
        model_dir: Path = DEFAULT_MODEL_DIR,
        vad_model_path: Path = DEFAULT_VAD_MODEL,
        *,
        recognizer=None,
        vad=None,
        emit_partials: bool = True,
        max_active_speech_seconds: float = MAX_ACTIVE_SPEECH_SECONDS,
        vad_min_silence_duration: float = DEFAULT_MIN_SILENCE_DURATION,
    ):
        if max_active_speech_seconds <= 0:
            raise ValueError("max_active_speech_seconds must be positive")
        self._recognizer = (
            load_zipformer(model_dir) if recognizer is None else recognizer
        )
        self._vad = (
            load_silero_vad(
                vad_model_path,
                min_silence_duration=vad_min_silence_duration,
            )
            if vad is None
            else vad
        )
        self.emit_partials = emit_partials
        self._max_active_speech_samples = int(SAMPLE_RATE * max_active_speech_seconds)
        self._pending = np.empty(0, dtype=np.float32)
        self._last_partial = ""
        self._last_partial_audio_ns: int | None = None
        self._last_audio_ns = 0
        self._stopped = False

    def _transcribe_segment(self, samples: np.ndarray) -> str:
        return transcribe_zipformer(self._recognizer, samples)

    @property
    def speech_active(self) -> bool:
        """Expose VAD activity for UI health checks without touching the recognizer."""
        return bool(self._vad.is_speech_detected())

    def _make_event(self, kind: str, text: str, t_audio_ns: int) -> AsrEvent:
        return AsrEvent(kind, text, time.perf_counter_ns(), t_audio_ns)

    def _drain_completed(
        self, t_audio_ns: int, *, event_kind: str = "final"
    ) -> list[AsrEvent]:
        events = []
        while not self._vad.empty():
            # sherpa-onnx exposes front as a SpeechSegment property, unlike
            # empty()/pop(), which are methods.
            segment = self._vad.front
            text = self._transcribe_segment(segment.samples)
            self._vad.pop()
            self._last_partial = ""
            self._last_partial_audio_ns = None
            if text:
                events.append(self._make_event(event_kind, text, t_audio_ns))
        return events

    def _roll_over_long_speech(self, t_audio_ns: int) -> list[AsrEvent]:
        """Bound continuous speech without treating an arbitrary cut as final."""
        self._vad.flush()
        events = self._drain_completed(t_audio_ns, event_kind="partial")
        self._vad.reset()
        self._last_partial = ""
        self._last_partial_audio_ns = None
        return events

    def _accept_window(self, window: np.ndarray, t_audio_ns: int) -> list[AsrEvent]:
        self._vad.accept_waveform(np.ascontiguousarray(window, dtype=np.float32))
        events = self._drain_completed(t_audio_ns)
        # Check the current segment before trusting the VAD activity flag. A
        # long uninterrupted segment must be bounded even if the detector's
        # state has already crossed its soft max-duration threshold.
        segment = self._vad.current_segment
        samples = np.asarray(segment.samples, dtype=np.float32)
        if samples.size >= self._max_active_speech_samples:
            return events + self._roll_over_long_speech(t_audio_ns)
        if not self._vad.is_speech_detected():
            return events
        if not self.emit_partials:
            return events
        if samples.size < PARTIAL_MIN_SAMPLES:
            return events
        if (
            self._last_partial_audio_ns is not None
            and t_audio_ns - self._last_partial_audio_ns < PARTIAL_INTERVAL_NS
        ):
            return events

        text = self._transcribe_segment(samples)
        self._last_partial_audio_ns = t_audio_ns
        if text and text != self._last_partial:
            self._last_partial = text
            events.append(self._make_event("partial", text, t_audio_ns))
        return events

    def feed(self, pcm: bytes, t_audio_ns: int) -> list[AsrEvent]:
        if self._stopped:
            return []
        if len(pcm) % 2:
            raise ValueError("Zipformer input must contain complete PCM16 samples")
        self._last_audio_ns = t_audio_ns
        samples = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
        if samples.size:
            self._pending = np.concatenate((self._pending, samples))

        events = []
        while self._pending.size >= VAD_WINDOW_SIZE:
            window = self._pending[:VAD_WINDOW_SIZE]
            self._pending = self._pending[VAD_WINDOW_SIZE:]
            events.extend(self._accept_window(window, t_audio_ns))
        return events

    def finish(self, t_audio_ns: int | None = None) -> list[AsrEvent]:
        if self._stopped:
            return []
        self._stopped = True
        event_time = t_audio_ns or self._last_audio_ns or time.perf_counter_ns()
        completed = []
        if self._pending.size:
            padded = np.pad(self._pending, (0, VAD_WINDOW_SIZE - self._pending.size))
            self._pending = np.empty(0, dtype=np.float32)
            completed.extend(self._accept_window(padded, event_time))
        self._vad.flush()
        completed.extend(self._drain_completed(event_time))
        return [event for event in completed if event.kind == "final"]

    def reset(self) -> None:
        self._vad.reset()
        self._pending = np.empty(0, dtype=np.float32)
        self._last_partial = ""
        self._last_partial_audio_ns = None
        self._last_audio_ns = 0
        self._stopped = False
