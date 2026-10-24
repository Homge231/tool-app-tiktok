from __future__ import annotations

from pathlib import Path

from pricetyper.asr.vosk_engine import VoskEngine
from pricetyper.asr.zipformer_engine import (
    DEFAULT_MIN_SILENCE_DURATION,
    ZipformerEngine,
)


def create_asr_engine(
    config,
    *,
    emit_partials=True,
    vad_min_silence_duration=DEFAULT_MIN_SILENCE_DURATION,
):
    if config.asr.engine == "zipformer":
        return ZipformerEngine(
            Path(config.asr.zipformer_model_dir),
            Path(config.asr.vad_model_path),
            emit_partials=emit_partials,
            vad_min_silence_duration=vad_min_silence_duration,
        )
    return VoskEngine(
        config.asr.model_path,
        config.audio.sample_rate,
        config.asr.words,
        config.asr.max_alternatives,
    )
