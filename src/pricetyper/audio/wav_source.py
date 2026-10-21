from __future__ import annotations

import time
import wave
from pathlib import Path


class AudioFormatError(ValueError):
    """WAV does not match the PriceTyper PCM format."""


class WavSource:
    def __init__(self, path: str | Path, chunk_ms: int = 40, speed: float = 1.0):
        self.path, self.chunk_ms, self.speed = Path(path), chunk_ms, speed
        self._wav = None

    def start(self) -> None:
        self._wav = wave.open(str(self.path), 'rb')
        if self._wav.getnchannels() != 1 or self._wav.getsampwidth() != 2 or self._wav.getframerate() != 16000 or self._wav.getcomptype() != 'NONE':
            self._wav.close()
            self._wav = None
            raise AudioFormatError('WAV must be uncompressed PCM 16-bit mono at 16000 Hz')

    def read(self) -> tuple[bytes, int] | None:
        if self._wav is None:
            raise RuntimeError('source is not started')
        pcm = self._wav.readframes(16000 * self.chunk_ms // 1000)
        if not pcm:
            return None
        if self.speed > 0:
            time.sleep((len(pcm) // 2) / 16000 / self.speed)
        return pcm, time.perf_counter_ns()

    def stop(self) -> None:
        if self._wav is not None:
            self._wav.close()
            self._wav = None
