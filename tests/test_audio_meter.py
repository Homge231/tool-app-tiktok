from pricetyper.ui.audio_meter import format_audio_level


def test_audio_meter_warns_when_signal_is_below_silence_threshold():
    assert format_audio_level(0.0) == "Gần như im lặng · RMS 0.0"
    assert format_audio_level(9.9) == "Gần như im lặng · RMS 9.9"


def test_audio_meter_reports_signal_at_or_above_silence_threshold():
    assert format_audio_level(10.0) == "Có tín hiệu · RMS 10.0"
