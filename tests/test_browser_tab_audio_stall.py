import time

from pricetyper.audio.browser_tab import BrowserTabSource


def test_browser_tab_source_reports_stalled_audio_after_two_seconds():
    source = BrowserTabSource(extension_origin="chrome-extension://test")
    assert not source.audio_stalled

    source._last_audio_ns = time.monotonic_ns() - source.AUDIO_STALL_NS - 1
    assert source.audio_stalled

    source._last_audio_ns = time.monotonic_ns()
    assert not source.audio_stalled
