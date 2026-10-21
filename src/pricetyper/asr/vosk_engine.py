from __future__ import annotations

import json
import time
from pathlib import Path

from pricetyper.asr.errors import ModelError
from pricetyper.types import AsrEvent


class VoskEngine:
    def __init__(
        self,
        model_path: str,
        sample_rate: int = 16000,
        words: bool = False,
        max_alternatives: int = 0,
        *,
        grammar: str | None = None,
        model_instance=None,
    ):
        if model_instance is None and not Path(model_path).is_dir():
            raise ModelError(f"Vosk model directory not found: {model_path}")
        try:
            import vosk

            vosk.SetLogLevel(-1)
            self._model = (
                vosk.Model(model_path) if model_instance is None else model_instance
            )
            if grammar is None:
                self._recognizer = vosk.KaldiRecognizer(self._model, sample_rate)
            else:
                self._recognizer = vosk.KaldiRecognizer(
                    self._model, sample_rate, grammar
                )
            self._recognizer.SetWords(words)
            self._recognizer.SetMaxAlternatives(max_alternatives)
        except Exception as exc:
            raise ModelError(
                f"Could not load Vosk model at {model_path}: {exc}"
            ) from exc
        self._last_partial = None

    def feed(self, pcm: bytes, t_audio_ns: int) -> list[AsrEvent]:
        if self._recognizer.AcceptWaveform(pcm):
            text = json.loads(self._recognizer.Result()).get("text", "")
            self._last_partial = None
            return [AsrEvent("final", text, time.perf_counter_ns(), t_audio_ns)]
        text = json.loads(self._recognizer.PartialResult()).get("partial", "")
        if text and text != self._last_partial:
            self._last_partial = text
            return [AsrEvent("partial", text, time.perf_counter_ns(), t_audio_ns)]
        return []

    def reset(self) -> None:
        self._recognizer.Reset()
        self._last_partial = None

    def finish(self, t_audio_ns: int) -> AsrEvent:
        """Flush the unfinished utterance, for bounded offline comparisons."""
        text = json.loads(self._recognizer.FinalResult()).get("text", "")
        self._last_partial = None
        return AsrEvent("final", text, time.perf_counter_ns(), t_audio_ns)
