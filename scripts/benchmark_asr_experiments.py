from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from pricetyper.asr.comparison import extracted_values, parse_reference_prices
from pricetyper.asr.experimental_engines import (
    load_gipformer,
    load_streaming_zipformer,
    transcribe_gipformer,
    transcribe_streaming_zipformer,
)
from pricetyper.asr.zipformer_engine import load_zipformer, transcribe_zipformer
from pricetyper.config import AppConfig

SAMPLE_RATE = 16_000
MAX_DURATION_SECONDS = 20


def read_media_segment(path: Path, start_s: float, duration_s: float) -> np.ndarray:
    """Decode one audio interval to mono float32/16 kHz without writing a WAV."""
    try:
        import av
    except ImportError as exc:
        raise RuntimeError(
            "Thiếu PyAV. Cài tùy chọn benchmark bằng: "
            '.\\.venv\\Scripts\\python.exe -m pip install -e ".[asr-benchmark]"'
        ) from exc

    end_s = start_s + duration_s
    chunks: list[np.ndarray] = []
    with av.open(str(path)) as container:
        if not container.streams.audio:
            raise ValueError("Tệp không có audio stream")
        resampler = av.AudioResampler(format="fltp", layout="mono", rate=SAMPLE_RATE)
        for frame in container.decode(audio=0):
            converted = resampler.resample(frame)
            for output_frame in converted:
                if output_frame.pts is None:
                    continue
                frame_start_s = float(output_frame.pts * output_frame.time_base)
                frame_end_s = frame_start_s + output_frame.samples / SAMPLE_RATE
                if frame_end_s <= start_s:
                    continue
                if frame_start_s >= end_s:
                    break
                samples = (
                    output_frame.to_ndarray().reshape(-1).astype(np.float32, copy=False)
                )
                left = max(0, round((start_s - frame_start_s) * SAMPLE_RATE))
                right = min(
                    samples.size,
                    round((end_s - frame_start_s) * SAMPLE_RATE),
                )
                if right > left:
                    chunks.append(samples[left:right].copy())
            if frame.pts is not None and float(frame.pts * frame.time_base) > end_s:
                break

    if not chunks:
        raise ValueError("Không giải mã được audio trong khoảng đã chọn")
    result = np.concatenate(chunks).astype(np.float32, copy=False)
    if result.size > int(duration_s * SAMPLE_RATE) + SAMPLE_RATE // 2:
        result = result[: int(duration_s * SAMPLE_RATE)]
    return np.clip(result, -1.0, 1.0)


def _score(name: str, text: str, elapsed_ms: float, expected: list[int]) -> dict:
    actual = extracted_values(text, AppConfig(), "number")
    expected_counts = {value: expected.count(value) for value in set(expected)}
    actual_counts = {value: actual.count(value) for value in set(actual)}
    missed = sum(
        max(0, count - actual_counts.get(value, 0))
        for value, count in expected_counts.items()
    )
    false = sum(
        max(0, count - expected_counts.get(value, 0))
        for value, count in actual_counts.items()
    )
    print(f"\n{name}")
    print(f"  transcript : {text or '—'}")
    print(f"  numbers    : {actual or '—'}")
    if expected:
        print(f"  exact      : {actual == expected}")
        print(f"  missed/false: {missed}/{false}")
    else:
        print("  exact      : chưa gắn nhãn")
    print(f"  ASR time   : {elapsed_ms:.1f} ms")
    return {
        "actual": actual,
        "exact": actual == expected,
        "missed": missed,
        "false": false,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "So sánh Zipformer hiện tại, Gipformer 1.5 và Zipformer streaming "
            "trên một đoạn media local; audio chỉ nằm trong RAM."
        )
    )
    parser.add_argument(
        "--media", required=True, type=Path, help="Video/audio local đã được gắn nhãn"
    )
    parser.add_argument(
        "--start", type=float, default=0.0, help="Thời điểm bắt đầu, giây"
    )
    parser.add_argument(
        "--duration", type=float, default=7.0, help="Độ dài đoạn, tối đa 20 giây"
    )
    parser.add_argument(
        "--transcript", default="", help="Transcript chuẩn để đối chiếu thủ công"
    )
    parser.add_argument(
        "--numbers",
        default="",
        help='Các số chuẩn, ngăn cách bằng dấu phẩy; ví dụ "1000,2000"',
    )
    parser.add_argument(
        "--chunk-ms",
        type=int,
        default=40,
        help="Kích thước khối audio cho model streaming",
    )
    parser.add_argument(
        "--number-end-ms",
        type=float,
        help="Thời điểm phát âm xong số cuối trong đoạn; dùng cùng --realtime để đo latency ASR",
    )
    parser.add_argument(
        "--realtime",
        action="store_true",
        help="Đưa chunk tới model theo nhịp audio thật để quan sát thời điểm partial xuất hiện",
    )
    args = parser.parse_args()
    if not args.media.is_file():
        parser.error(f"Không tìm thấy media: {args.media}")
    if args.start < 0 or not 0.25 <= args.duration <= MAX_DURATION_SECONDS:
        parser.error("start phải >= 0 và duration phải từ 0,25 đến 20 giây")
    if args.chunk_ms <= 0:
        parser.error("chunk-ms phải lớn hơn 0")
    expected = (
        parse_reference_prices(args.numbers.replace(",", ";")) if args.numbers else []
    )
    if args.number_end_ms is not None:
        if not args.realtime:
            parser.error("--number-end-ms cần --realtime")
        if not expected:
            parser.error("--number-end-ms cần --numbers")
        if args.number_end_ms < 0 or args.number_end_ms > args.duration * 1000:
            parser.error("number-end-ms phải nằm trong đoạn được chọn")
    try:
        samples = read_media_segment(args.media, args.start, args.duration)
        print(
            f"Media local: {args.media.name}; đoạn {args.start:.2f}–"
            f"{args.start + samples.size / SAMPLE_RATE:.2f}s; "
            f"audio {samples.size / SAMPLE_RATE:.2f}s; mono/16 kHz; không ghi WAV."
        )
        if args.transcript:
            print(f"Transcript chuẩn: {args.transcript}")
        print(f"Số chuẩn: {expected or 'chưa nhập'}")

        started = time.perf_counter_ns()
        zipformer = load_zipformer()
        zipformer_load_ms = (time.perf_counter_ns() - started) / 1e6
        started = time.perf_counter_ns()
        zipformer_text = transcribe_zipformer(zipformer, samples)
        zipformer_ms = (time.perf_counter_ns() - started) / 1e6
        _score(
            "Zipformer-VI hiện tại · offline · core giữ nguyên",
            zipformer_text,
            zipformer_ms,
            expected,
        )

        started = time.perf_counter_ns()
        gipformer = load_gipformer()
        gipformer_load_ms = (time.perf_counter_ns() - started) / 1e6
        started = time.perf_counter_ns()
        gipformer_text = transcribe_gipformer(gipformer, samples)
        gipformer_ms = (time.perf_counter_ns() - started) / 1e6
        _score("Gipformer 1.5 INT8 · offline", gipformer_text, gipformer_ms, expected)

        started = time.perf_counter_ns()
        streaming = load_streaming_zipformer()
        streaming_load_ms = (time.perf_counter_ns() - started) / 1e6
        result = transcribe_streaming_zipformer(
            streaming,
            samples,
            chunk_samples=max(1, round(args.chunk_ms * SAMPLE_RATE / 1000)),
            realtime=args.realtime,
        )
        _score(
            "Zipformer-VI streaming · chunk 16 · online",
            result["text"],
            result["decode_total_ms"],
            expected,
        )
        print(
            "  decode p50/p95/max: "
            f"{result['decode_p50_ms']:.1f}/{result['decode_p95_ms']:.1f}/"
            f"{result['decode_max_ms']:.1f} ms; "
            f"RTF={result['realtime_factor']:.3f}; chunks={result['decode_chunks']}"
        )
        if result["snapshots"]:
            print("  partials:")
            for item in result["snapshots"][:8]:
                partial_numbers = extracted_values(item["text"], AppConfig(), "number")
                numbers_suffix = (
                    f" | số: {partial_numbers}"
                    if partial_numbers
                    else " | chưa trích được số"
                )
                print(
                    f"    audio {item['audio_offset_ms']:.0f} ms / "
                    f"wall {item['wall_elapsed_ms']:.0f} ms: "
                    f"{item['text']}{numbers_suffix}"
                )
        else:
            print("  partials: không có text trước cuối đoạn")
        if args.number_end_ms is not None:
            target_number = expected[-1]
            target_snapshot = next(
                (
                    item
                    for item in result["snapshots"]
                    if target_number
                    in extracted_values(item["text"], AppConfig(), "number")
                ),
                None,
            )
            if target_snapshot is None:
                print(f"  target {target_number}: không xuất hiện trong partial")
            else:
                response_ms = target_snapshot["wall_elapsed_ms"] - args.number_end_ms
                print(
                    f"  target {target_number}: xuất hiện lần đầu sau khi đọc số "
                    f"{response_ms:.1f} ms (ASR + parser; cần nhãn thời điểm chính xác)"
                )
        print(
            "\nThời gian nạp model (ms): "
            f"Zipformer {zipformer_load_ms:.1f}, Gipformer {gipformer_load_ms:.1f}, "
            f"streaming {streaming_load_ms:.1f}. Không tính vào ASR time."
        )
        print(
            "\nĐây là benchmark ASR local trên một đoạn media; không đo VAD, "
            "bridge trình duyệt, điền/gửi comment hoặc độ trễ TikTok."
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - command reports local model/media setup errors.
        print(f"Benchmark thất bại: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
