from __future__ import annotations

import time
from pathlib import Path

import numpy as np

from pricetyper.asr.errors import ModelError
from pricetyper.asr.zipformer_engine import SAMPLE_RATE

ROOT = Path(__file__).resolve().parents[3]
GIPFORMER_DIR = ROOT / "models" / "gipformer1.5-68M-rnnt"
STREAMING_ZIPFORMER_DIR = (
    ROOT / "models" / "hynt-zipformer-30M-rnnt-streaming-6000h-chunk16"
)
STREAMING_CHUNK_SIZE = 16
STREAMING_MODEL_FILE_STEM = "epoch-31-avg-11-chunk-16-left-128.fp16.onnx"


def _load_sherpa_onnx():
    try:
        import sherpa_onnx
    except ImportError as exc:
        raise ModelError(
            "Thiếu sherpa-onnx; cài dependency prototype rồi thử lại."
        ) from exc
    return sherpa_onnx


def _require_files(model_dir: Path, names: tuple[str, ...], label: str) -> None:
    missing = [name for name in names if not (model_dir / name).is_file()]
    if missing:
        raise ModelError(
            f"Thiếu tệp {label} ({', '.join(missing)}). Chạy "
            ".\\.venv\\Scripts\\python.exe scripts\\download_asr_experiments.py "
            "--gipformer hoặc --streaming-zipformer."
        )


def load_gipformer(model_dir: Path = GIPFORMER_DIR):
    """Load Gipformer 1.5 INT8 as an optional offline benchmark model."""
    sherpa_onnx = _load_sherpa_onnx()
    _require_files(
        model_dir,
        ("encoder.int8.onnx", "decoder.int8.onnx", "joiner.int8.onnx", "tokens.txt"),
        "Gipformer 1.5 INT8",
    )
    try:
        return sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=str(model_dir / "encoder.int8.onnx"),
            decoder=str(model_dir / "decoder.int8.onnx"),
            joiner=str(model_dir / "joiner.int8.onnx"),
            tokens=str(model_dir / "tokens.txt"),
            num_threads=1,
            sample_rate=SAMPLE_RATE,
            feature_dim=80,
            decoding_method="greedy_search",
            provider="cpu",
        )
    except Exception as exc:
        raise ModelError(f"Không thể khởi tạo Gipformer 1.5: {exc}") from exc


def transcribe_gipformer(recognizer, samples: np.ndarray) -> str:
    waveform = np.ascontiguousarray(samples, dtype=np.float32)
    if waveform.size == 0:
        return ""
    stream = recognizer.create_stream()
    stream.accept_waveform(SAMPLE_RATE, waveform)
    recognizer.decode_stream(stream)
    return stream.result.text.strip()


def load_streaming_zipformer(model_dir: Path = STREAMING_ZIPFORMER_DIR):
    """Load the chunk-16 Vietnamese online Zipformer for local experiments only."""
    sherpa_onnx = _load_sherpa_onnx()
    encoder = f"encoder-{STREAMING_MODEL_FILE_STEM}"
    decoder = f"decoder-{STREAMING_MODEL_FILE_STEM}"
    joiner = f"joiner-{STREAMING_MODEL_FILE_STEM}"
    # The upstream repository names its token table config.json; it is a
    # tokens.txt-formatted file, not JSON. Copy it under the conventional name.
    _require_files(
        model_dir, (encoder, decoder, joiner, "tokens.txt"), "Zipformer streaming"
    )
    try:
        return sherpa_onnx.OnlineRecognizer.from_transducer(
            encoder=str(model_dir / encoder),
            decoder=str(model_dir / decoder),
            joiner=str(model_dir / joiner),
            tokens=str(model_dir / "tokens.txt"),
            num_threads=1,
            sample_rate=SAMPLE_RATE,
            feature_dim=80,
            decoding_method="greedy_search",
            enable_endpoint_detection=False,
            model_type="zipformer2",
            provider="cpu",
        )
    except Exception as exc:
        raise ModelError(f"Không thể khởi tạo Zipformer streaming: {exc}") from exc


def transcribe_streaming_zipformer(
    recognizer,
    samples: np.ndarray,
    *,
    chunk_samples: int = 640,
    realtime: bool = False,
) -> dict:
    """Decode 40 ms chunks and report when online partial text/numbers appear.

    Audio is supplied and processed in memory. Returned timing is an ASR-only
    offline replay measurement, not end-to-end browser or comment latency.
    """
    if chunk_samples <= 0:
        raise ValueError("chunk_samples must be positive")
    waveform = np.ascontiguousarray(samples, dtype=np.float32)
    stream = recognizer.create_stream()
    started_ns = __import__("time").perf_counter_ns()
    snapshots: list[dict] = []
    last_text = ""
    decode_ms: list[float] = []

    for offset in range(0, waveform.size, chunk_samples):
        end = min(offset + chunk_samples, waveform.size)
        if realtime:
            arrival_ns = started_ns + int(end * 1e9 / SAMPLE_RATE)
            wait_s = (arrival_ns - time.perf_counter_ns()) / 1e9
            if wait_s > 0:
                time.sleep(wait_s)
        stream.accept_waveform(SAMPLE_RATE, waveform[offset:end])
        while recognizer.is_ready(stream):
            decode_started = time.perf_counter_ns()
            recognizer.decode_stream(stream)
            decode_ms.append((time.perf_counter_ns() - decode_started) / 1e6)
        text = recognizer.get_result(stream).strip()
        if text and text != last_text:
            snapshots.append(
                {
                    "text": text,
                    "audio_offset_ms": end * 1000.0 / SAMPLE_RATE,
                    "wall_elapsed_ms": (time.perf_counter_ns() - started_ns) / 1e6,
                }
            )
            last_text = text

    stream.input_finished()
    while recognizer.is_ready(stream):
        decode_started = time.perf_counter_ns()
        recognizer.decode_stream(stream)
        decode_ms.append((time.perf_counter_ns() - decode_started) / 1e6)
    final_text = recognizer.get_result(stream).strip()
    if final_text and (not snapshots or snapshots[-1]["text"] != final_text):
        snapshots.append(
            {
                "text": final_text,
                "audio_offset_ms": waveform.size * 1000.0 / SAMPLE_RATE,
                "wall_elapsed_ms": (time.perf_counter_ns() - started_ns) / 1e6,
            }
        )

    ordered = sorted(decode_ms)
    p50 = ordered[len(ordered) // 2] if ordered else 0.0
    p95 = ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))] if ordered else 0.0
    duration_s = waveform.size / SAMPLE_RATE
    total_decode_ms = sum(decode_ms)
    return {
        "text": final_text,
        "snapshots": snapshots,
        "decode_chunks": len(decode_ms),
        "decode_total_ms": total_decode_ms,
        "decode_p50_ms": p50,
        "decode_p95_ms": p95,
        "decode_max_ms": max(decode_ms, default=0.0),
        "realtime_factor": total_decode_ms / (duration_s * 1000.0)
        if duration_s
        else 0.0,
        "duration_s": duration_s,
    }
