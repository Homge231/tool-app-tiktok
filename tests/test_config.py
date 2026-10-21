import sys
from copy import deepcopy

import pytest
from pydantic import ValidationError

from pricetyper.config import DEFAULTS, AppConfig, load_config, write_local_config


def test_default_config_validates():
    config = AppConfig.model_validate(deepcopy(DEFAULTS))
    assert config.audio.sample_rate == 16000
    assert config.decision.min_value == 1000
    assert config.asr.engine == 'zipformer'


def test_vosk_remains_an_explicitly_selectable_baseline():
    config = deepcopy(DEFAULTS)
    config['asr']['engine'] = 'vosk'
    assert AppConfig.model_validate(config).asr.engine == 'vosk'


def test_browser_tab_requires_fixed_40ms_pcm_chunk():
    config = deepcopy(DEFAULTS)
    config['audio'].update(source='browser_tab', chunk_ms=80)
    with pytest.raises(ValidationError):
        AppConfig.model_validate(config)


def test_config_layers_merge_default_root_then_local(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'config.yaml').write_text('decision:\n  min_value: 20\n', encoding='utf-8')
    (tmp_path / 'config.local.yaml').write_text('decision:\n  max_value: 900\n', encoding='utf-8')
    config = load_config()
    assert (config.decision.min_value, config.decision.max_value) == (20, 900)


def test_explicit_config_resolves_relative_paths_from_config_folder(tmp_path):
    model_dir = tmp_path / "models" / "zipformer"
    model_dir.mkdir(parents=True)
    config_path = tmp_path / "user.yaml"
    config_path.write_text(
        "asr:\n  zipformer_model_dir: models/zipformer\n"
        "run:\n  log_dir: logs\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.asr.zipformer_model_dir == str(model_dir.resolve())
    assert config.run.log_dir == str((tmp_path / "logs").resolve())


def test_frozen_defaults_use_user_data_and_bundled_models(tmp_path, monkeypatch):
    data_dir = tmp_path / "AppData" / "NumberTyper"
    bundle_dir = tmp_path / "bundle"
    bundle_model_dir = (
        bundle_dir / "models" / "sherpa-onnx-zipformer-vi-30M-int8-2026-02-09"
    )
    bundle_model_dir.mkdir(parents=True)
    vad_path = bundle_dir / "models" / "silero_vad.onnx"
    vad_path.parent.mkdir(parents=True, exist_ok=True)
    vad_path.touch()
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundle_dir), raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(data_dir.parent))
    monkeypatch.delenv("NUMBERTYPER_DATA_DIR", raising=False)
    monkeypatch.chdir(tmp_path)

    config = load_config()

    assert config.asr.zipformer_model_dir == str(bundle_model_dir.resolve())
    assert config.asr.vad_model_path == str(vad_path.resolve())
    assert config.run.log_dir == str((data_dir / "logs").resolve())


def test_frozen_local_config_is_written_under_user_data(tmp_path, monkeypatch):
    data_dir = tmp_path / "NumberTyperData"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setenv("NUMBERTYPER_DATA_DIR", str(data_dir))

    write_local_config({"decision": {"min_value": 99}})

    assert "min_value: 99" in (data_dir / "config.local.yaml").read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize('section,values', [
    ('audio', {'chunk_ms': 201}),
    ('audio', {'sample_rate': 48000}),
    ('decision', {'min_value': 0}),
    ('decision', {'max_value': 1_000_000_000}),
    ('decision', {'min_value': 3_000_000, 'max_value': 2_000_000}),
    ('decision', {'hold_open_ms': -1}),
    ('decision', {'cooldown_same_s': -0.1}),
    ('decision', {'max_sends_per_min': 61}),
    ('output', {'template': 'no-price'}),
    ('output', {'template': '{value}₫'}),
    ('run', {'unknown_setting': True}),
])
def test_invalid_configuration_rejected(section, values):
    config = deepcopy(DEFAULTS)
    config[section].update(values)
    with pytest.raises(ValidationError):
        AppConfig.model_validate(config)


def test_mode_and_sender_must_match():
    config = deepcopy(DEFAULTS)
    config['mode'] = 'android_adb'
    with pytest.raises(ValidationError):
        AppConfig.model_validate(config)


def test_adb_template_must_be_digits():
    config = deepcopy(DEFAULTS)
    config['mode'] = 'android_adb'
    config['sender']['type'] = 'adb'
    config['output']['template'] = '{value}k'
    with pytest.raises(ValidationError):
        AppConfig.model_validate(config)
