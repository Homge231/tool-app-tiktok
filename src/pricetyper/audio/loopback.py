from __future__ import annotations

import time


class AudioDeviceError(RuntimeError):
    """The selected system loopback device could not be opened."""


class AudioRateError(AudioDeviceError):
    """Loopback could not initialize at the required sample rate."""


class LoopbackSource:
    def __init__(self, device: str = 'default', sample_rate: int = 16000, chunk_ms: int = 40):
        self.device, self.sample_rate, self.chunk_ms = device, sample_rate, chunk_ms
        self._recorder = None

    def start(self) -> None:
        try:
            import soundcard as sc
            if self.device == 'default':
                speaker = sc.default_speaker()
            else:
                speaker = next((s for s in sc.all_speakers() if self.device.casefold() in s.name.casefold()), None)
            if speaker is None:
                raise AudioDeviceError(f'No speaker matches {self.device!r}')
            mic = sc.get_microphone(id=speaker.name, include_loopback=True)
            try:
                self._recorder = mic.recorder(samplerate=self.sample_rate, channels=1)
                self._recorder.__enter__()
            except Exception as exc:
                raise AudioRateError(f'Could not initialize loopback at {self.sample_rate} Hz: {exc}') from exc
        except AudioDeviceError:
            raise
        except Exception as exc:
            raise AudioDeviceError(f'Could not start 16000 Hz loopback capture: {exc}') from exc

    def read(self) -> tuple[bytes, int] | None:
        if self._recorder is None:
            raise RuntimeError('source is not started')
        import numpy as np
        try:
            samples = self._recorder.record(numframes=self.sample_rate * self.chunk_ms // 1000)
        except Exception as exc:
            raise AudioDeviceError(str(exc)) from exc
        pcm = (np.clip(samples[:, 0], -1, 1) * 32767).astype(np.int16).tobytes()
        return pcm, time.perf_counter_ns()

    def stop(self) -> None:
        if self._recorder is not None:
            self._recorder.__exit__(None, None, None)
            self._recorder = None
