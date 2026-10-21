from pathlib import Path

from pricetyper.asr import factory
from pricetyper.config import AppConfig


def test_default_factory_selects_zipformer_and_configured_local_models(monkeypatch):
    captured = {}

    class FakeZipformer:
        def __init__(self, model_dir, vad_model_path, *, emit_partials):
            captured["paths"] = (model_dir, vad_model_path)
            captured["emit_partials"] = emit_partials

    monkeypatch.setattr(factory, "ZipformerEngine", FakeZipformer)
    config = AppConfig()

    engine = factory.create_asr_engine(config)

    assert isinstance(engine, FakeZipformer)
    assert captured["paths"] == (
        Path(config.asr.zipformer_model_dir),
        Path(config.asr.vad_model_path),
    )
    assert captured["emit_partials"] is True


def test_factory_can_disable_zipformer_partials_for_final_only_mode(monkeypatch):
    captured = {}

    class FakeZipformer:
        def __init__(self, _model_dir, _vad_model_path, *, emit_partials):
            captured["emit_partials"] = emit_partials

    monkeypatch.setattr(factory, "ZipformerEngine", FakeZipformer)
    engine = factory.create_asr_engine(AppConfig(), emit_partials=False)

    assert isinstance(engine, FakeZipformer)
    assert captured["emit_partials"] is False


def test_factory_can_still_select_vosk_baseline(monkeypatch):
    captured = {}

    class FakeVosk:
        def __init__(self, *args):
            captured["args"] = args

    monkeypatch.setattr(factory, "VoskEngine", FakeVosk)
    config = AppConfig()
    config.asr.engine = "vosk"

    engine = factory.create_asr_engine(config)

    assert isinstance(engine, FakeVosk)
    assert captured["args"] == (
        config.asr.model_path,
        config.audio.sample_rate,
        config.asr.words,
        config.asr.max_alternatives,
    )
