def format_audio_level(rms: float) -> str:
    state = "Gần như im lặng" if rms < 10 else "Có tín hiệu"
    return f"{state} · RMS {rms:.1f}"
