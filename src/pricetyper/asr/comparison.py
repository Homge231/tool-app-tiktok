from __future__ import annotations

import queue
import re
import threading
import time
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Callable

from pricetyper.asr.enhancement import enhance
from pricetyper.asr.vosk_engine import VoskEngine
from pricetyper.asr.vosk_number_grammar import NUMBER_GRAMMAR_JSON
from pricetyper.asr.zipformer_engine import transcribe_zipformer
from pricetyper.parsing.gate import GateCfg, gate
from pricetyper.parsing.vi_number import parse_all, tokenize

SAMPLE_RATE = 16_000
PCM_BYTES_PER_SECOND = SAMPLE_RATE * 2
MAX_SEGMENT_SECONDS = 20
VOSK_CHUNK_BYTES = 640 * 2  # the YouTube bridge sends 40 ms of mono PCM16


def word_error_rate(reference: str, hypothesis: str) -> float | None:
    """Return whitespace-token error rate (Vietnamese syllable tokens), or None."""
    reference_tokens = tokenize(unicodedata.normalize("NFC", reference))
    hypothesis_tokens = tokenize(unicodedata.normalize("NFC", hypothesis))
    if not reference_tokens:
        return None

    return _edit_rate(reference_tokens, hypothesis_tokens)


def character_error_rate(reference: str, hypothesis: str) -> float | None:
    """Return normalized character error rate after whitespace/punctuation cleanup."""
    reference_text = " ".join(tokenize(unicodedata.normalize("NFC", reference)))
    hypothesis_text = " ".join(tokenize(unicodedata.normalize("NFC", hypothesis)))
    reference_chars = list(reference_text)
    hypothesis_chars = list(hypothesis_text)
    if not reference_chars:
        return None
    return _edit_rate(reference_chars, hypothesis_chars)


def _edit_rate(reference_tokens: list, hypothesis_tokens: list) -> float:
    previous = list(range(len(hypothesis_tokens) + 1))
    for ref_index, ref_token in enumerate(reference_tokens, start=1):
        current = [ref_index]
        for hyp_index, hyp_token in enumerate(hypothesis_tokens, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[hyp_index] + 1,
                    previous[hyp_index - 1] + (ref_token != hyp_token),
                )
            )
        previous = current
    return previous[-1] / len(reference_tokens)


def _gate_config(config) -> GateCfg:
    decision = config.decision
    return GateCfg(
        decision.min_value,
        decision.max_value,
        tuple(decision.exclude_prev),
        tuple(decision.exclude_next),
        decision.countdown_filter,
        decision.gate_mode,
        tuple(decision.anchor_before),
        tuple(decision.anchor_after),
    )


def price_values(text: str, config) -> list[int]:
    """Return the configured, gated candidate values from one transcript."""
    spans = parse_all(text, config.parser.shorthand, config.parser.k_tokens)
    return [span.value for span in gate(text, spans, _gate_config(config))]


def extracted_values(text: str, config, scoring_scope: str) -> list[int]:
    """Extract either every parsed number or only values accepted as prices."""
    spans = parse_all(text, config.parser.shorthand, config.parser.k_tokens)
    if scoring_scope == "number":
        return [span.value for span in spans]
    if scoring_scope == "price":
        return [span.value for span in gate(text, spans, _gate_config(config))]
    raise ValueError("Phạm vi chấm phải là 'number' hoặc 'price'")


def parse_reference_prices(value: str) -> list[int]:
    """Parse explicit positive integer labels, independent of the ASR parser."""
    normalized = value.strip().lower()
    if normalized in {"không có", "không có số", "không có giá"}:
        return []
    if not normalized:
        raise ValueError(
            'Nhập số/giá chuẩn (ví dụ 140; 110), hoặc nhập "không có".'
        )

    prices = []
    for item in normalized.split(";"):
        item = item.strip()
        if not re.fullmatch(r"(?:[0-9]+|[0-9]{1,3}(?:\.[0-9]{3})+)", item):
            raise ValueError(
                "Mỗi nhãn phải là số nguyên dương; phân cách nhiều số bằng dấu chấm phẩy."
            )
        price = int(item.replace(".", ""))
        if price <= 0:
            raise ValueError('Nhãn số phải lớn hơn 0; dùng "không có" nếu không có số.')
        prices.append(price)
    return prices


def _transcribe_vosk(pcm: bytes, config, engine: VoskEngine | None = None) -> tuple[str, float, float]:
    started = time.perf_counter_ns()
    if engine is None:
        engine = VoskEngine(
            config.asr.model_path,
            SAMPLE_RATE,
            config.asr.words,
            config.asr.max_alternatives,
        )
        initialized = time.perf_counter_ns()
    else:
        engine.reset()
        initialized = started
    texts: list[str] = []
    last_audio_ns = initialized
    for offset in range(0, len(pcm), VOSK_CHUNK_BYTES):
        chunk = pcm[offset : offset + VOSK_CHUNK_BYTES]
        last_audio_ns = time.perf_counter_ns()
        for event in engine.feed(chunk, last_audio_ns):
            if event.kind == "final" and event.text:
                texts.append(event.text)
    final = engine.finish(last_audio_ns)
    if final.text:
        texts.append(final.text)
    finished = time.perf_counter_ns()
    return (
        " ".join(texts).strip(),
        (initialized - started) / 1e6,
        (finished - initialized) / 1e6,
    )


def _transcribe_whisper(samples, whisper_model) -> tuple[str, float]:
    started = time.perf_counter_ns()
    segments, _info = whisper_model.transcribe(
        samples,
        language="vi",
        task="transcribe",
        beam_size=5,
        condition_on_previous_text=False,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 300},
    )
    text = " ".join(segment.text.strip() for segment in segments).strip()
    return text, (time.perf_counter_ns() - started) / 1e6


def _score_prices(actual: list[int], expected: list[int]) -> dict:
    actual_counts = Counter(actual)
    expected_counts = Counter(expected)
    return {
        "price_exact": actual == expected,
        "missed_prices": sum((expected_counts - actual_counts).values()),
        "false_candidates": sum((actual_counts - expected_counts).values()),
    }


def _make_row(
    text: str,
    reference: str,
    expected_prices: list[int],
    config,
    duration_s: float,
    inference_ms: float,
    *,
    init_ms: float = 0.0,
    enhancement_ms: float = 0.0,
    scoring_scope: str = "price",
) -> dict:
    prices = extracted_values(text, config, scoring_scope)
    return {
        "text": text,
        "prices": prices,
        "scoring_scope": scoring_scope,
        "wer": word_error_rate(reference, text),
        "cer": character_error_rate(reference, text),
        **_score_prices(prices, expected_prices),
        "init_ms": init_ms,
        "inference_ms": inference_ms,
        "enhancement_ms": enhancement_ms,
        "processing_ms": inference_ms + enhancement_ms,
        "realtime_factor": (inference_ms + enhancement_ms) / (duration_s * 1000),
    }


def _consensus(
    rows: dict[str, dict],
    condition: str,
    expected_prices: list[int],
    required_models: int = 3,
) -> dict:
    model_prices = {engine: row["prices"] for engine, row in rows.items()}
    distinct = {tuple(values) for values in model_prices.values()}
    if condition == "overlap":
        reason = "Đoạn được gắn nhãn chồng lấp; luôn abstain trong prototype."
        values = []
        abstained = True
    elif len(model_prices) < required_models:
        reason = "Thiếu model/nhánh bắt buộc để đối chiếu; abstain."
        values = []
        abstained = True
    elif len(distinct) != 1:
        reason = "Ba model không đồng thuận; abstain."
        values = []
        abstained = True
    else:
        reason = "Ba model đồng thuận; chỉ là kết quả thử, không gửi."
        values = list(next(iter(distinct)))
        abstained = False
    return {
        "prices": values,
        "abstained": abstained,
        "reason": reason,
        "model_prices": model_prices,
        **_score_prices(values, expected_prices),
    }


def compare_pcm(
    pcm: bytes,
    reference: str,
    config,
    whisper_model,
    whisper_load_ms: float = 0.0,
    *,
    expected_prices: list[int],
    zipformer_model=None,
    zipformer_load_ms: float = 0.0,
    denoiser=None,
    denoiser_load_ms: float = 0.0,
    vosk_engine: VoskEngine | None = None,
    vosk_load_ms: float = 0.0,
    vosk_number_engine: VoskEngine | None = None,
    vosk_number_load_ms: float = 0.0,
    condition: str = "clean",
    accent: str = "unknown",
    scoring_scope: str = "price",
) -> dict:
    """Compare local ASR engines on raw and optionally enhanced copies of one segment."""
    if not pcm or len(pcm) % 2:
        raise ValueError("The comparison segment must contain complete PCM16 samples")
    if scoring_scope not in {"number", "price"}:
        raise ValueError("Phạm vi chấm phải là 'number' hoặc 'price'")

    duration_s = len(pcm) / PCM_BYTES_PER_SECOND
    import numpy as np

    samples = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
    denoised_samples = None
    enhancement_ms = 0.0
    if denoiser is not None:
        started = time.perf_counter_ns()
        denoised_samples = enhance(denoiser, samples, SAMPLE_RATE)
        enhancement_ms = (time.perf_counter_ns() - started) / 1e6

    branches = {"raw": (samples, pcm, 0.0)}
    if denoised_samples is not None:
        enhanced_pcm = np.clip(denoised_samples * 32768.0, -32768, 32767)
        enhanced_pcm = enhanced_pcm.astype("<i2").tobytes()
        branches["denoised"] = (denoised_samples, enhanced_pcm, enhancement_ms)

    engines: dict[str, dict] = {}
    for branch_name, (branch_samples, branch_pcm, branch_enhancement_ms) in branches.items():
        branch_rows: dict[str, dict] = {}

        if vosk_engine is None:
            vosk_text, vosk_init_ms, vosk_ms = _transcribe_vosk(branch_pcm, config)
        else:
            vosk_text, vosk_init_ms, vosk_ms = _transcribe_vosk(
                branch_pcm, config, vosk_engine
            )
        branch_rows["vosk"] = _make_row(
            vosk_text,
            reference,
            expected_prices,
            config,
            duration_s,
            vosk_ms,
            init_ms=vosk_init_ms,
            enhancement_ms=branch_enhancement_ms,
            scoring_scope=scoring_scope,
        )

        if vosk_number_engine is not None:
            number_text, number_init_ms, number_ms = _transcribe_vosk(
                branch_pcm, config, vosk_number_engine
            )
            branch_rows["vosk_number"] = _make_row(
                number_text,
                reference,
                expected_prices,
                config,
                duration_s,
                number_ms,
                init_ms=number_init_ms + vosk_number_load_ms,
                enhancement_ms=branch_enhancement_ms,
                scoring_scope=scoring_scope,
            )

        whisper_text, whisper_ms = _transcribe_whisper(branch_samples, whisper_model)
        branch_rows["whisper"] = _make_row(
            whisper_text,
            reference,
            expected_prices,
            config,
            duration_s,
            whisper_ms,
            init_ms=whisper_load_ms,
            enhancement_ms=branch_enhancement_ms,
            scoring_scope=scoring_scope,
        )

        if zipformer_model is not None:
            started = time.perf_counter_ns()
            zipformer_text = transcribe_zipformer(zipformer_model, branch_samples)
            zipformer_ms = (time.perf_counter_ns() - started) / 1e6
            branch_rows["zipformer"] = _make_row(
                zipformer_text,
                reference,
                expected_prices,
                config,
                duration_s,
                zipformer_ms,
                init_ms=zipformer_load_ms,
                enhancement_ms=branch_enhancement_ms,
                scoring_scope=scoring_scope,
            )

        engines[branch_name] = branch_rows

    consensus_engines = {"vosk", "whisper", "zipformer"}
    consensuses = {
        branch_name: _consensus(
            {name: row for name, row in rows.items() if name in consensus_engines},
            condition,
            expected_prices,
        )
        for branch_name, rows in engines.items()
    }
    all_rows = {
        f"{engine}/{branch}": row
        for branch, rows in engines.items()
        for engine, row in rows.items()
        if engine in consensus_engines
    }
    consensuses["strict"] = _consensus(
        all_rows, condition, expected_prices, required_models=6
    )
    # Compatibility aliases remain raw-only for existing comparison consumers.
    raw_rows = engines["raw"]
    return {
        "duration_s": duration_s,
        "reference": reference,
        "reference_prices": expected_prices,
        "condition": condition,
        "accent": accent,
        "scoring_scope": scoring_scope,
        "benchmark_group": f"{accent}/{condition}/{scoring_scope}",
        "engines": engines,
        "consensus": consensuses,
        "model_load_ms": {
            "whisper": whisper_load_ms,
            "zipformer": zipformer_load_ms,
            "denoiser": denoiser_load_ms,
            "vosk": vosk_load_ms,
            "vosk_number": vosk_number_load_ms,
        },
        "vosk": raw_rows["vosk"],
        "whisper": raw_rows["whisper"],
        **({"zipformer": raw_rows["zipformer"]} if "zipformer" in raw_rows else {}),
    }


class ASRComparisonSession:
    """Capture one short tab-audio segment in RAM and compare local ASR engines."""

    def __init__(
        self,
        config,
        event_queue: queue.Queue | None = None,
        max_segment_seconds: int = MAX_SEGMENT_SECONDS,
        whisper_model_name: str = "small",
        whisper_model_factory: Callable | None = None,
        zipformer_model_factory: Callable | None = None,
        denoiser_factory: Callable | None = None,
        vosk_model_factory: Callable | None = None,
        vosk_number_engine_factory: Callable | None = None,
        compare_fn: Callable = compare_pcm,
    ):
        self.config = config
        self.events = event_queue or queue.Queue()
        self.max_bytes = max_segment_seconds * PCM_BYTES_PER_SECOND
        self.whisper_model_name = whisper_model_name
        self.whisper_model_factory = whisper_model_factory
        self.zipformer_model_factory = zipformer_model_factory
        self.denoiser_factory = denoiser_factory
        self.vosk_model_factory = vosk_model_factory
        self.vosk_number_engine_factory = vosk_number_engine_factory
        self.compare_fn = compare_fn
        self._lock = threading.Lock()
        self._pcm = bytearray()
        self._active = False
        self._ready = False
        self._busy = False
        self._closed = False
        self._whisper_model = None
        self._whisper_load_ms = 0.0
        self._zipformer_model = None
        self._zipformer_load_ms = 0.0
        self._denoiser = None
        self._denoiser_load_ms = 0.0
        self._vosk_engine = None
        self._vosk_load_ms = 0.0
        self._vosk_number_engine = None
        self._vosk_number_load_ms = 0.0
        self._vosk_model = None
        self._benchmark_samples: dict[str, dict[str, list[dict]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def _emit(self, kind: str, **values) -> None:
        if not self._closed:
            self.events.put({"kind": "comparison_" + kind, **values})

    def start_segment(self) -> None:
        with self._lock:
            if self._closed:
                raise RuntimeError("Comparison window is closed")
            if self._busy or self._active or self._ready:
                raise RuntimeError(
                    "Finish or discard the current comparison segment first"
                )
            self._pcm.clear()
            self._active = True
        self._emit("status", state="recording", message="Đang giữ audio trong RAM…")

    def feed_audio(self, pcm: bytes, _audio_ns: int) -> None:
        reached_limit = False
        with self._lock:
            if not self._active:
                return
            remaining = self.max_bytes - len(self._pcm)
            if remaining > 0:
                self._pcm.extend(pcm[:remaining])
            if len(self._pcm) >= self.max_bytes:
                self._active = False
                self._ready = True
                reached_limit = True
        if reached_limit:
            self._emit(
                "status",
                state="ready",
                message=(
                    f"Đã chốt giới hạn {self.max_bytes // PCM_BYTES_PER_SECOND} giây. "
                    "Nhập transcript và nhãn số/giá chuẩn rồi bấm So sánh."
                ),
            )

    def stop_and_compare(
        self,
        reference: str,
        expected_prices: list[int],
        condition: str = "clean",
        accent: str = "unknown",
        scoring_scope: str = "price",
    ) -> float:
        if not reference.strip():
            raise ValueError("Nhập transcript chuẩn để tính WER/CER")
        if any(type(price) is not int or price <= 0 for price in expected_prices):
            raise ValueError("Danh sách nhãn phải chứa số nguyên dương")
        if scoring_scope not in {"number", "price"}:
            raise ValueError("Phạm vi chấm phải là 'number' hoặc 'price'")
        with self._lock:
            if self._busy:
                raise RuntimeError("Đang so sánh đoạn trước")
            if not self._active and not self._ready:
                raise RuntimeError("Chưa có đoạn audio; hãy bấm Bắt đầu đoạn trước")
            self._active = False
            self._ready = False
            pcm = bytes(self._pcm)
            self._busy = True
        duration_s = len(pcm) / PCM_BYTES_PER_SECOND
        if duration_s < 0.25:
            with self._lock:
                self._pcm.clear()
                self._busy = False
            raise ValueError("Đoạn quá ngắn; hãy thu ít nhất 0,25 giây")
        self._emit(
            "status",
            state="working",
            message="Đang chạy Vosk, Whisper, Zipformer và DPDFNet local…",
        )
        threading.Thread(
            target=self._compare_worker,
            args=(
                pcm,
                reference.strip(),
                list(expected_prices),
                condition,
                accent,
                scoring_scope,
            ),
            name="asr-comparison",
            daemon=True,
        ).start()
        return duration_s

    def _get_whisper_model(self):
        if self._whisper_model is not None:
            return self._whisper_model
        started = time.perf_counter_ns()
        if self.whisper_model_factory is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise RuntimeError(
                    "Thiếu faster-whisper. Cài bằng: "
                    '.\\.venv\\Scripts\\python.exe -m pip install -e ".[robust-asr]"'
                ) from exc
            factory = WhisperModel
        else:
            factory = self.whisper_model_factory
        self._whisper_model = factory(
            self.whisper_model_name,
            device="cpu",
            compute_type="int8",
        )
        self._whisper_load_ms = (time.perf_counter_ns() - started) / 1e6
        return self._whisper_model

    def _get_zipformer_model(self):
        if self._zipformer_model is not None:
            return self._zipformer_model
        started = time.perf_counter_ns()
        if self.zipformer_model_factory is None:
            from pricetyper.asr.zipformer_engine import load_zipformer

            factory = load_zipformer
        else:
            factory = self.zipformer_model_factory
        self._zipformer_model = factory()
        self._zipformer_load_ms = (time.perf_counter_ns() - started) / 1e6
        return self._zipformer_model

    def _get_denoiser(self):
        if self._denoiser is not None:
            return self._denoiser
        started = time.perf_counter_ns()
        if self.denoiser_factory is None:
            from pricetyper.asr.enhancement import load_denoiser

            factory = load_denoiser
        else:
            factory = self.denoiser_factory
        self._denoiser = factory()
        self._denoiser_load_ms = (time.perf_counter_ns() - started) / 1e6
        return self._denoiser

    def _get_vosk_engine(self):
        if self._vosk_engine is not None:
            return self._vosk_engine
        started = time.perf_counter_ns()
        if self.vosk_model_factory is not None:
            self._vosk_engine = self.vosk_model_factory(
                self.config.asr.model_path,
                SAMPLE_RATE,
                self.config.asr.words,
                self.config.asr.max_alternatives,
            )
        else:
            model = self._get_vosk_model()
            self._vosk_engine = VoskEngine(
                self.config.asr.model_path,
                SAMPLE_RATE,
                self.config.asr.words,
                self.config.asr.max_alternatives,
                model_instance=model,
            )
        self._vosk_load_ms = (time.perf_counter_ns() - started) / 1e6
        return self._vosk_engine

    def _get_vosk_model(self):
        if self._vosk_model is not None:
            return self._vosk_model
        started = time.perf_counter_ns()
        try:
            import vosk
        except ImportError as exc:
            raise RuntimeError(
                "Thiếu Vosk. Cài dependency của prototype rồi thử lại."
            ) from exc
        vosk.SetLogLevel(-1)
        self._vosk_model = vosk.Model(self.config.asr.model_path)
        self._vosk_load_ms = (time.perf_counter_ns() - started) / 1e6
        return self._vosk_model

    def _get_vosk_number_engine(self):
        if self._vosk_number_engine is not None:
            return self._vosk_number_engine
        started = time.perf_counter_ns()
        if self.vosk_number_engine_factory is not None:
            self._vosk_number_engine = self.vosk_number_engine_factory(
                self.config.asr.model_path,
                SAMPLE_RATE,
                self.config.asr.words,
                self.config.asr.max_alternatives,
                grammar=NUMBER_GRAMMAR_JSON,
            )
        else:
            model = self._get_vosk_model()
            self._vosk_number_engine = VoskEngine(
                self.config.asr.model_path,
                SAMPLE_RATE,
                self.config.asr.words,
                self.config.asr.max_alternatives,
                grammar=NUMBER_GRAMMAR_JSON,
                model_instance=model,
            )
        self._vosk_number_load_ms = (time.perf_counter_ns() - started) / 1e6
        return self._vosk_number_engine

    @staticmethod
    def _percentile(values: list[float], percentile: float) -> float | None:
        if not values:
            return None
        ordered = sorted(values)
        index = max(0, int(len(ordered) * percentile + 0.999999) - 1)
        return ordered[min(index, len(ordered) - 1)]

    def _record_benchmark(self, result: dict) -> dict:
        condition = result.get("benchmark_group", result["condition"])
        for branch, rows in result["engines"].items():
            for engine, row in rows.items():
                key = f"{engine}/{branch}"
                self._benchmark_samples[condition][key].append(
                    {
                        "exact": row["price_exact"],
                        "missed": row["missed_prices"],
                        "false": row["false_candidates"],
                        "latency_ms": row["processing_ms"],
                    }
                )
        for branch, row in result["consensus"].items():
            key = f"consensus/{branch}"
            denoising_latency_ms = result["engines"].get("denoised", {}).get(
                "vosk", {}
            ).get("enhancement_ms", 0.0)
            if branch == "strict":
                latency_ms = sum(
                    row_data["inference_ms"]
                    for branch_rows in result["engines"].values()
                    for engine_name, row_data in branch_rows.items()
                    if engine_name in {"vosk", "whisper", "zipformer"}
                ) + denoising_latency_ms
            else:
                latency_ms = sum(
                    engine_row["inference_ms"]
                    for engine_row in result["engines"][branch].values()
                ) + result["engines"][branch].get("vosk", {}).get("enhancement_ms", 0.0)
            self._benchmark_samples[condition][key].append(
                {
                    "exact": row["price_exact"],
                    "missed": row["missed_prices"],
                    "false": row["false_candidates"],
                    "latency_ms": latency_ms,
                }
            )

        summary = {}
        for key, records in self._benchmark_samples[condition].items():
            latencies = [record["latency_ms"] for record in records]
            summary[key] = {
                "segments": len(records),
                "exact": sum(record["exact"] for record in records),
                "missed": sum(record["missed"] for record in records),
                "false": sum(record["false"] for record in records),
                "p50_ms": self._percentile(latencies, 0.50),
                "p95_ms": self._percentile(latencies, 0.95),
            }
        return summary

    def _compare_worker(
        self,
        pcm: bytes,
        reference: str,
        expected_prices: list[int],
        condition: str,
        accent: str,
        scoring_scope: str,
    ) -> None:
        result = None
        error = None
        try:
            model = self._get_whisper_model()
            zipformer = self._get_zipformer_model()
            denoiser = self._get_denoiser()
            vosk_engine = self._get_vosk_engine()
            vosk_number_engine = self._get_vosk_number_engine()
            result = self.compare_fn(
                pcm,
                reference,
                self.config,
                model,
                whisper_load_ms=self._whisper_load_ms,
                zipformer_model=zipformer,
                zipformer_load_ms=self._zipformer_load_ms,
                denoiser=denoiser,
                denoiser_load_ms=self._denoiser_load_ms,
                vosk_engine=vosk_engine,
                vosk_load_ms=self._vosk_load_ms,
                vosk_number_engine=vosk_number_engine,
                vosk_number_load_ms=self._vosk_number_load_ms,
                condition=condition,
                accent=accent,
                expected_prices=expected_prices,
                scoring_scope=scoring_scope,
            )
            result["benchmark_summary"] = (
                self._record_benchmark(result)
                if "engines" in result and "condition" in result
                else {}
            )
        except Exception as exc:  # noqa: BLE001 - report model/runtime failures in the UI worker.
            error = str(exc)
        finally:
            with self._lock:
                self._pcm.clear()
                self._busy = False
        if error is not None:
            self._emit("error", message=error)
        elif result is not None:
            self._emit("result", result=result)

    def discard_segment(self) -> None:
        with self._lock:
            if self._busy:
                return
            self._active = False
            self._ready = False
            self._pcm.clear()
        self._emit(
            "status",
            state="idle",
            message="Đã bỏ đoạn thử; audio đã được xóa khỏi bộ nhớ.",
        )

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._active = False
            self._ready = False
            self._pcm.clear()
            self._whisper_model = None
            self._zipformer_model = None
            self._denoiser = None
            self._vosk_engine = None
            self._vosk_number_engine = None
            self._vosk_model = None
