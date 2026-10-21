from __future__ import annotations

import queue
import threading
from types import SimpleNamespace

import numpy as np
import pytest

from pricetyper.asr import comparison
from pricetyper.asr.comparison import (
    PCM_BYTES_PER_SECOND,
    ASRComparisonSession,
    character_error_rate,
    compare_pcm,
    extracted_values,
    parse_reference_prices,
    price_values,
    word_error_rate,
)
from pricetyper.asr.vosk_engine import VoskEngine
from pricetyper.asr.vosk_number_grammar import (
    NUMBER_GRAMMAR_JSON,
    NUMBER_PHRASES,
)
from pricetyper.config import AppConfig
from pricetyper.ui.formatting import format_vnd


def test_word_error_rate_normalizes_punctuation_and_case():
    assert word_error_rate("Giá một trăm, nha!", "giá một trăm") == 0.25


def test_word_error_rate_returns_none_for_empty_reference():
    assert word_error_rate("   ", "có lời nói") is None


def test_character_error_rate_counts_diacritic_difference():
    assert character_error_rate("một", "mộ") == 1 / 3


def test_comparison_prices_use_the_configured_parser_and_gate():
    config = AppConfig()

    assert price_values("áo này giá một trăm chín mươi chín nghìn", config) == [199000]
    assert price_values("giá 1", config) == []
    config.decision.min_value = 1
    assert price_values("giá 1", config) == [1]
    config.decision.min_value = 1000
    assert price_values("giá 100.000", config) == [100000]
    assert price_values("áo này size ba tám", config) == []
    assert price_values("hai nghìn ba nghìn", config) == [2000, 3000]
    assert price_values(
        "RỒI BA NGHÌN BA NGHÌN RỒI BA NGHÌN BỐN NGHÌN RỒI", config
    ) == [3000, 3000, 3000, 4000]

    config.decision.min_value = 1
    assert price_values("một trăm bốn", config) == [140]
    assert price_values("trăm mốt", config) == [110]
    config.decision.min_value = 1000

    config.decision.max_value = 999_999_999
    assert price_values("giá 100.000 nghìn", config) == [100_000_000]


def test_number_scope_ignores_price_minimum_while_price_scope_keeps_it():
    config = AppConfig()
    assert config.decision.min_value == 1000
    assert extracted_values("một trăm bốn", config, "number") == [140]
    assert extracted_values("trăm mốt", config, "number") == [110]
    assert extracted_values("một trăm bốn", config, "price") == []

    with pytest.raises(ValueError, match="number.*price"):
        extracted_values("một trăm bốn", config, "other")


def test_benchmark_truth_is_explicit_and_independent_from_asr_price_parser():
    assert parse_reference_prices("2000; 3000") == [2000, 3000]
    assert parse_reference_prices("2.000; 3.000") == [2000, 3000]
    assert parse_reference_prices("không có") == []
    assert parse_reference_prices("không có số") == []

    with pytest.raises(ValueError, match="phân cách"):
        parse_reference_prices("2000, 3000")
    with pytest.raises(ValueError, match="Nhập số/giá chuẩn"):
        parse_reference_prices("")


def test_missing_recognized_prices_are_not_scored_as_an_empty_truth(monkeypatch):
    monkeypatch.setattr(
        comparison,
        "_transcribe_vosk",
        lambda _pcm, _config: ("rồi rồi", 0.0, 5.0),
    )

    class FakeWhisper:
        def transcribe(self, _samples, **_kwargs):
            return [SimpleNamespace(text=" rồi rồi ")], None

    result = compare_pcm(
        b"\x00\x00" * 16000,
        "hai nghìn ba nghìn rồi rồi",
        AppConfig(),
        FakeWhisper(),
        expected_prices=[2000, 3000],
    )

    assert result["reference_prices"] == [2000, 3000]
    for row in result["engines"]["raw"].values():
        assert row["prices"] == []
        assert row["price_exact"] is False
        assert row["missed_prices"] == 2


def test_vnd_display_uses_dong_not_implicit_thousands():
    assert format_vnd(1) == "1 ₫"
    assert format_vnd(100000) == "100.000 ₫"
    assert format_vnd(100_000_000) == "100.000.000 ₫"


def test_compare_pcm_pins_whisper_to_vietnamese_transcription_and_scores_prices(
    monkeypatch,
):
    monkeypatch.setattr(
        comparison,
        "_transcribe_vosk",
        lambda _pcm, _config: ("giá ba trăm nghìn", 2.0, 12.0),
    )
    call = {}

    class FakeWhisper:
        def transcribe(self, samples, **kwargs):
            call.update(samples=samples, kwargs=kwargs)
            return [SimpleNamespace(text=" giá ba trăm nghìn ")], None

    result = compare_pcm(
        b"\x00\x00" * 16000,
        "giá ba trăm nghìn",
        AppConfig(),
        FakeWhisper(),
        expected_prices=[300000],
    )

    assert call["kwargs"]["language"] == "vi"
    assert call["kwargs"]["task"] == "transcribe"
    assert call["kwargs"]["vad_filter"] is True
    assert result["vosk"]["price_exact"] is True
    assert result["whisper"]["price_exact"] is True
    assert result["whisper"]["wer"] == 0.0
    assert result["whisper"]["cer"] == 0.0


def test_compare_pcm_number_scope_scores_below_default_price_minimum(monkeypatch):
    monkeypatch.setattr(
        comparison,
        "_transcribe_vosk",
        lambda _pcm, _config: ("trăm mốt", 0.0, 5.0),
    )

    class FakeWhisper:
        def transcribe(self, _samples, **_kwargs):
            return [SimpleNamespace(text=" trăm mốt ")], None

    config = AppConfig()
    result = compare_pcm(
        b"\x00\x00" * 16000,
        "trăm mốt",
        config,
        FakeWhisper(),
        expected_prices=[110],
        scoring_scope="number",
    )

    assert result["scoring_scope"] == "number"
    assert result["benchmark_group"].endswith("/number")
    assert result["vosk"]["prices"] == [110]
    assert result["vosk"]["price_exact"] is True


def test_number_grammar_has_narrow_number_and_thousand_phrases():
    assert len(NUMBER_PHRASES) == 1341
    assert "chín" in NUMBER_PHRASES
    assert "mười bốn nghìn" in NUMBER_PHRASES
    assert "rồi hai nghìn" in NUMBER_PHRASES
    assert "một nghìn rồi hai nghìn" in NUMBER_PHRASES
    assert "hai nghìn ba nghìn" in NUMBER_PHRASES
    assert "một hai ba bốn năm sáu bảy tám chín" in NUMBER_PHRASES
    assert NUMBER_PHRASES[-1] == "[unk]"
    assert '"chín"' in NUMBER_GRAMMAR_JSON


def test_vosk_engine_passes_experimental_grammar_to_recognizer(monkeypatch):
    calls = {}

    class FakeRecognizer:
        def __init__(self, model, sample_rate, grammar):
            calls["args"] = (model, sample_rate, grammar)

        def SetWords(self, enabled):
            calls["words"] = enabled

        def SetMaxAlternatives(self, count):
            calls["alternatives"] = count

    fake_vosk = SimpleNamespace(
        SetLogLevel=lambda _level: None,
        KaldiRecognizer=FakeRecognizer,
    )
    monkeypatch.setitem(__import__("sys").modules, "vosk", fake_vosk)
    shared_model = object()

    VoskEngine(
        "unused-model-path",
        grammar=NUMBER_GRAMMAR_JSON,
        model_instance=shared_model,
    )

    assert calls["args"] == (shared_model, 16000, NUMBER_GRAMMAR_JSON)
    assert calls["words"] is False
    assert calls["alternatives"] == 0


def test_comparison_session_shares_one_vosk_model_for_both_recognizers(
    monkeypatch, tmp_path
):
    models = []
    recognizers = []

    class FakeRecognizer:
        def __init__(self, *args):
            self.args = args
            recognizers.append(self)

        def SetWords(self, _enabled):
            pass

        def SetMaxAlternatives(self, _count):
            pass

    fake_vosk = SimpleNamespace(
        SetLogLevel=lambda _level: None,
        Model=lambda path: models.append((path, object())) or models[-1][1],
        KaldiRecognizer=FakeRecognizer,
    )
    monkeypatch.setitem(__import__("sys").modules, "vosk", fake_vosk)
    config = AppConfig()
    config.asr.model_path = str(tmp_path)
    session = ASRComparisonSession(config)

    baseline = session._get_vosk_engine()
    number = session._get_vosk_number_engine()

    assert len(models) == 1
    assert len(recognizers) == 2
    assert baseline._model is number._model
    assert len(recognizers[0].args) == 2
    assert recognizers[1].args[2] == NUMBER_GRAMMAR_JSON
    session.close()


def test_experimental_number_engine_is_scored_but_excluded_from_consensus(
    monkeypatch,
):
    def transcribe(_pcm, _config, engine=None):
        return ("chín", 0.0, 4.0) if engine is number_engine else ("hai nghìn", 0, 5)

    monkeypatch.setattr(comparison, "_transcribe_vosk", transcribe)
    monkeypatch.setattr(
        comparison,
        "transcribe_zipformer",
        lambda _model, _samples: "hai nghìn",
    )
    number_engine = object()

    class FakeWhisper:
        def transcribe(self, _samples, **_kwargs):
            return [SimpleNamespace(text=" hai nghìn ")], None

    class FakeDenoiser:
        def __call__(self, samples, sample_rate):
            return SimpleNamespace(sample_rate=sample_rate, samples=samples.copy())

    result = compare_pcm(
        b"\x00\x00" * 16000,
        "hai nghìn",
        AppConfig(),
        FakeWhisper(),
        expected_prices=[2000],
        zipformer_model=object(),
        denoiser=FakeDenoiser(),
        vosk_engine=object(),
        vosk_number_engine=number_engine,
        scoring_scope="number",
    )

    assert result["engines"]["raw"]["vosk_number"]["prices"] == [9]
    assert result["engines"]["raw"]["vosk_number"]["price_exact"] is False
    assert result["consensus"]["raw"]["prices"] == [2000]
    assert result["consensus"]["strict"]["prices"] == [2000]
    assert set(result["consensus"]["strict"]["model_prices"]) == {
        "vosk/raw",
        "whisper/raw",
        "zipformer/raw",
        "vosk/denoised",
        "whisper/denoised",
        "zipformer/denoised",
    }


def test_compare_pcm_runs_raw_and_denoised_branches_and_scores_false_candidates(
    monkeypatch,
):
    monkeypatch.setattr(
        comparison,
        "_transcribe_vosk",
        lambda pcm, _config, _engine=None: (
            ("giá 100.000", 0.0, 5.0)
            if pcm == b"\x00\x00" * 16000
            else ("giá 200.000", 0.0, 6.0)
        ),
    )
    monkeypatch.setattr(
        comparison,
        "transcribe_zipformer",
        lambda _model, _samples: "giá 100.000",
    )

    class FakeWhisper:
        def transcribe(self, samples, **_kwargs):
            text = " giá 100.000 " if not samples.any() else " giá 200.000 "
            return [SimpleNamespace(text=text)], None

    class FakeDenoiser:
        def __call__(self, _samples, sample_rate):
            return SimpleNamespace(
                sample_rate=sample_rate,
                samples=np.full(16000, 0.25, dtype=np.float32),
            )

    result = comparison.compare_pcm(
        b"\x00\x00" * 16000,
        "giá 100.000",
        AppConfig(),
        FakeWhisper(),
        expected_prices=[100000],
        zipformer_model=object(),
        denoiser=FakeDenoiser(),
    )

    assert set(result["engines"]) == {"raw", "denoised"}
    assert set(result["engines"]["raw"]) == {"vosk", "whisper", "zipformer"}
    assert result["engines"]["raw"]["vosk"]["price_exact"] is True
    assert result["engines"]["denoised"]["vosk"]["missed_prices"] == 1
    assert result["engines"]["denoised"]["vosk"]["false_candidates"] == 1
    assert result["consensus"]["raw"]["abstained"] is False
    assert result["consensus"]["denoised"]["abstained"] is True
    assert result["consensus"]["strict"]["abstained"] is True


def test_consensus_abstains_for_labeled_overlap_even_when_models_agree():
    rows = {
        name: {"prices": [100000]}
        for name in ("vosk", "whisper", "zipformer")
    }

    decision = comparison._consensus(rows, "overlap", [100000])

    assert decision["abstained"] is True
    assert decision["prices"] == []
    assert decision["missed_prices"] == 1


def test_benchmark_summary_accumulates_exact_misses_false_and_latency_percentiles():
    session = ASRComparisonSession(AppConfig())

    def row(exact, missed, false, latency):
        return {
            "price_exact": exact,
            "missed_prices": missed,
            "false_candidates": false,
            "processing_ms": latency,
            "inference_ms": latency,
            "enhancement_ms": 0.0,
        }

    def result(vosk_row):
        engine_rows = {
            "raw": {
                "vosk": vosk_row,
                "whisper": row(True, 0, 0, 12.0),
                "zipformer": row(True, 0, 0, 8.0),
            },
            "denoised": {
                "vosk": row(True, 0, 0, 15.0),
                "whisper": row(True, 0, 0, 13.0),
                "zipformer": row(True, 0, 0, 9.0),
            },
        }
        agreement = {
            branch: {
                "price_exact": True,
                "missed_prices": 0,
                "false_candidates": 0,
            }
            for branch in ("raw", "denoised", "strict")
        }
        return {
            "condition": "clean",
            "engines": engine_rows,
            "consensus": agreement,
        }

    session._record_benchmark(result(row(True, 0, 0, 10.0)))
    summary = session._record_benchmark(result(row(False, 1, 2, 30.0)))

    assert summary["vosk/raw"] == {
        "segments": 2,
        "exact": 1,
        "missed": 1,
        "false": 2,
        "p50_ms": 10.0,
        "p95_ms": 30.0,
    }
    assert summary["consensus/strict"]["p95_ms"] == 87.0
    session.close()


def test_session_keeps_audio_only_during_an_explicit_segment_and_compares_it():
    config = AppConfig()
    events = queue.Queue()
    completed = threading.Event()
    pcm = b"\x00\x00" * 640 * 8
    seen = {}

    def fake_compare(
        captured,
        reference,
        _config,
        model,
        whisper_load_ms=0,
        zipformer_model=None,
        denoiser=None,
        condition="clean",
        expected_prices=None,
        **kwargs,
    ):
        seen.update(
            pcm=captured,
            reference=reference,
            expected_prices=expected_prices,
            model=model,
            whisper_load_ms=whisper_load_ms,
            zipformer_model=zipformer_model,
            denoiser=denoiser,
            vosk_number_engine=kwargs.get("vosk_number_engine"),
            condition=condition,
            accent=kwargs.get("accent"),
            scoring_scope=kwargs.get("scoring_scope"),
        )
        completed.set()
        return {
            "duration_s": len(captured) / PCM_BYTES_PER_SECOND,
            "engines": {},
            "consensus": {},
        }

    session = ASRComparisonSession(
        config,
        event_queue=events,
        whisper_model_factory=lambda *_args, **_kwargs: object(),
        zipformer_model_factory=lambda: object(),
        denoiser_factory=lambda: object(),
        vosk_model_factory=lambda *_args: object(),
        vosk_number_engine_factory=lambda *_args, **_kwargs: object(),
        compare_fn=fake_compare,
    )
    session.feed_audio(pcm, 0)
    assert len(session._pcm) == 0

    session.start_segment()
    session.feed_audio(pcm, 1)
    duration = session.stop_and_compare(
        "giá ba trăm nghìn", [300000], "music_noise", "central", "number"
    )

    assert duration == 0.32
    assert completed.wait(2)
    captured_events = []
    while not any(item["kind"] == "comparison_result" for item in captured_events):
        captured_events.append(events.get(timeout=2))
    assert seen["pcm"] == pcm
    assert seen["reference"] == "giá ba trăm nghìn"
    assert seen["expected_prices"] == [300000]
    assert seen["model"] is not None
    assert seen["zipformer_model"] is not None
    assert seen["denoiser"] is not None
    assert seen["vosk_number_engine"] is not None
    assert seen["condition"] == "music_noise"
    assert seen["accent"] == "central"
    assert seen["scoring_scope"] == "number"
    assert len(session._pcm) == 0
    assert any(item["kind"] == "comparison_result" for item in captured_events)
    session.close()


def test_session_caps_buffered_segment_length():
    events = queue.Queue()
    session = ASRComparisonSession(
        AppConfig(),
        event_queue=events,
        max_segment_seconds=1,
        compare_fn=lambda *_args, **_kwargs: {},
    )
    session.start_segment()
    session.feed_audio(b"\x01\x00" * (PCM_BYTES_PER_SECOND + 100), 0)

    assert len(session._pcm) == PCM_BYTES_PER_SECOND
    statuses = [
        item for item in list(events.queue) if item["kind"] == "comparison_status"
    ]
    assert statuses[-1]["state"] == "ready"
    session.close()
