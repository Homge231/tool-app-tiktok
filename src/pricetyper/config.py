from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from pricetyper.runtime_paths import (
    config_directory,
    is_frozen,
    resolve_log_directory,
    resolve_model_path,
    user_data_dir,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class RunConfig(StrictModel):
    start_armed: bool = False
    dry_run: bool = False
    log_dir: str = 'logs'
    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR'] = 'INFO'
    hotkeys: dict[str, str] = {'toggle': 'f8', 'calibrate': 'f9', 'panic': 'f10'}


class AudioConfig(StrictModel):
    source: Literal['loopback', 'wav', 'browser_tab'] = 'loopback'
    device: str = 'default'
    wav_path: str | None = None
    wav_speed: float = Field(default=1.0, ge=0)
    sample_rate: int = 16000
    chunk_ms: int = Field(default=40, ge=20, le=200)
    queue_max_chunks: int = Field(default=50, ge=1, le=500)

    @model_validator(mode='after')
    def fixed_rate(self):
        if self.sample_rate != 16000:
            raise ValueError('audio.sample_rate must be 16000')
        if self.source == 'browser_tab' and self.chunk_ms != 40:
            raise ValueError('audio.chunk_ms must be 40 when source is browser_tab')
        return self


class AsrConfig(StrictModel):
    engine: Literal['zipformer', 'vosk'] = 'zipformer'
    model_path: str = 'models/vosk-model-small-vn-0.4'
    zipformer_model_dir: str = 'models/sherpa-onnx-zipformer-vi-30M-int8-2026-02-09'
    vad_model_path: str = 'models/silero_vad.onnx'
    words: bool = False
    max_alternatives: int = Field(default=0, ge=0)


class ParserConfig(StrictModel):
    shorthand: bool = True
    k_tokens: list[str] = ['k', 'ca', 'ka']


class DecisionConfig(StrictModel):
    min_value: int = Field(default=1000, ge=1)
    max_value: int = Field(default=2_000_000, ge=1, le=999_999_999)
    gate_mode: Literal['any_number', 'anchored'] = 'any_number'
    anchor_before: list[str] = ['giá', 'chỉ', 'chốt', 'lấy', 'còn', 'bán']
    anchor_after: list[str] = ['k', 'ca', 'ka', 'nghìn', 'ngàn', 'đồng']
    exclude_prev: list[str] = ['size', 'số', 'ngày', 'tháng', 'lúc', 'giờ', 'mã', 'cỡ']
    exclude_next: list[str] = ['cái', 'chiếc', 'người', 'bạn', 'kg', 'cm', 'mét', 'tuổi', 'giờ', 'phút', 'giây', 'ngày', 'tháng', 'tiếng', 'phần', 'lần']
    countdown_filter: bool = True
    hold_complete_ms: int = Field(default=120, ge=0)
    hold_open_ms: int = Field(default=350, ge=0)
    cooldown_same_s: float = Field(default=10.0, ge=0)
    cooldown_any_s: float = Field(default=1.5, ge=0)
    max_sends_per_min: int = Field(default=10, ge=1, le=60)

    @model_validator(mode='after')
    def valid_range(self):
        if self.min_value > self.max_value:
            raise ValueError('decision.min_value must be <= decision.max_value')
        return self


class OutputConfig(StrictModel):
    template: str = '{value}'
    send_mode: Literal['enter', 'click_button'] = 'enter'

    @model_validator(mode='after')
    def valid_template(self):
        if '{value}' not in self.template:
            raise ValueError('output.template must contain {value}')
        try:
            rendered = self.template.format(value=123)
        except (KeyError, IndexError, ValueError) as exc:
            raise ValueError(f'output.template is not a valid format string: {exc}') from exc
        if not rendered.isascii():
            raise ValueError('output.template must produce ASCII text')
        return self


class PlaywrightConfig(StrictModel):
    user_data_dir: str = '.pw-profile'
    channel: str = 'chrome'
    attach: Literal['launch', 'cdp'] = 'launch'
    cdp_url: str = 'http://127.0.0.1:9222'
    live_url: str = ''
    url_pattern: str = '**/@*/live*'
    chat_input_selectors: list[str] = []
    send_button_selector: str = ''
    focus_each_time: bool = False
    verify_after_send: bool = False


class DesktopConfig(StrictModel):
    chat_xy: tuple[int, int] | None = None
    send_xy: tuple[int, int] | None = None
    click_each_time: bool = True


class AdbConfig(StrictModel):
    adb_path: str = 'adb'
    serial: str = ''
    chat_xy: tuple[int, int] | None = None
    send_xy: tuple[int, int] | None = None
    send_keyevent: int = 66


class SenderConfig(StrictModel):
    type: Literal['playwright', 'desktop', 'adb'] = 'playwright'
    playwright: PlaywrightConfig = PlaywrightConfig()
    desktop: DesktopConfig = DesktopConfig()
    adb: AdbConfig = AdbConfig()


class AppConfig(StrictModel):
    version: Literal[1] = 1
    mode: Literal['web', 'android_scrcpy', 'desktop_app', 'android_adb'] = 'web'
    run: RunConfig = RunConfig()
    audio: AudioConfig = AudioConfig()
    asr: AsrConfig = AsrConfig()
    parser: ParserConfig = ParserConfig()
    decision: DecisionConfig = DecisionConfig()
    output: OutputConfig = OutputConfig()
    sender: SenderConfig = SenderConfig()

    @model_validator(mode='after')
    def compatible_sender(self):
        expected = {'web': {'playwright', 'desktop'}, 'android_scrcpy': {'desktop'}, 'desktop_app': {'desktop'}, 'android_adb': {'adb'}}
        if self.sender.type not in expected[self.mode]:
            raise ValueError(f'mode {self.mode} is incompatible with sender.type {self.sender.type}')
        if self.sender.type == 'adb' and not self.output.template.format(value=123).isdigit():
            raise ValueError('ADB output.template must produce digits only')
        return self


DEFAULTS = AppConfig().model_dump(mode='python')


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: str | Path | None = None) -> AppConfig:
    merged = deepcopy(DEFAULTS)
    config_dir = config_directory(path)
    if path is not None:
        primary_config = Path(path).expanduser().resolve()
    else:
        primary_config = config_dir / "config.yaml"
    paths = [primary_config, config_dir / "config.local.yaml"]
    for config_path in paths:
        if config_path.exists():
            try:
                with config_path.open('r', encoding='utf-8') as stream:
                    data = yaml.safe_load(stream) or {}
            except yaml.YAMLError as exc:
                raise ValueError(f'Invalid YAML in {config_path}: {exc}') from exc
            if not isinstance(data, dict):
                raise ValueError(f'{config_path} must contain a YAML mapping')
            merged = _deep_merge(merged, data)

    for name in ("model_path", "zipformer_model_dir", "vad_model_path"):
        merged["asr"][name] = str(resolve_model_path(merged["asr"][name], config_dir))
    merged["run"]["log_dir"] = str(
        resolve_log_directory(merged["run"]["log_dir"], config_dir)
    )
    return AppConfig.model_validate(merged)


def write_local_config(
    updates: dict[str, Any], path: str | Path | None = None
) -> None:
    target = (
        Path(path).expanduser()
        if path is not None
        else (user_data_dir() if is_frozen() else Path.cwd()) / "config.local.yaml"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    current = yaml.safe_load(target.read_text(encoding='utf-8')) if target.exists() else {}
    target.write_text(yaml.safe_dump(_deep_merge(current or {}, updates), allow_unicode=True, sort_keys=False), encoding='utf-8')


__all__ = ['AppConfig', 'DecisionConfig', 'ValidationError', 'load_config', 'write_local_config']
