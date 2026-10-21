from __future__ import annotations

import wave
from types import SimpleNamespace

from pricetyper import cli
from pricetyper.config import AppConfig


def test_record_captures_requested_sample_count_and_writes_pcm_wav(tmp_path, monkeypatch, capsys):
    class FakeSource:
        def __init__(self, device, sample_rate, chunk_ms):
            self.sample_rate = sample_rate
            self.stopped = False

        def start(self):
            pass

        def read(self):
            # Return 40 ms chunks; the requested 60 ms should trim the last one.
            return b'\x01\x00' * 640, 0

        def stop(self):
            self.stopped = True

    source = FakeSource('default', 16000, 40)
    monkeypatch.setattr(cli, 'LoopbackSource', lambda *args: source)
    output = tmp_path / 'record.wav'

    result = cli._record(SimpleNamespace(seconds=0.06, out=output, device=None), AppConfig())

    assert result == 0
    assert source.stopped
    with wave.open(str(output), 'rb') as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == 16000
        assert wav.getnframes() == 960
    assert 'Recorded 0.06s' in capsys.readouterr().out
