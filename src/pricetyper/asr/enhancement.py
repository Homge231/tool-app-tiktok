from __future__ import annotations

from pathlib import Path

import numpy as np

DEFAULT_DENOISER_MODEL = Path(__file__).resolve().parents[3] / "models" / "dpdfnet_baseline.onnx"


def load_denoiser(model_path: Path = DEFAULT_DENOISER_MODEL):
    try:
        import sherpa_onnx
    except ImportError as exc:
        raise RuntimeError(
            "Thiếu sherpa-onnx. Cài bằng: "
            '.\\.venv\\Scripts\\python.exe -m pip install -e ".[robust-asr]"'
        ) from exc
    if not model_path.is_file():
        raise RuntimeError(
            "Thiếu model DPDFNet. Chạy: .\\.venv\\Scripts\\python.exe "
            "scripts\\download_robust_asr_models.py"
        )

    config = sherpa_onnx.OfflineSpeechDenoiserConfig(
        model=sherpa_onnx.OfflineSpeechDenoiserModelConfig(
            dpdfnet=sherpa_onnx.OfflineSpeechDenoiserDpdfNetModelConfig(
                model=str(model_path),
                attenuation_limit_db=12.0,
            ),
            num_threads=1,
            debug=False,
            provider="cpu",
        )
    )
    if not config.validate():
        raise RuntimeError(f"Cấu hình DPDFNet không hợp lệ: {config}")
    return sherpa_onnx.OfflineSpeechDenoiser(config)


def enhance(denoiser, samples: np.ndarray, sample_rate: int = 16_000) -> np.ndarray:
    waveform = np.ascontiguousarray(samples, dtype=np.float32)
    result = denoiser(waveform, sample_rate)
    if result.sample_rate != sample_rate:
        raise RuntimeError(
            f"DPDFNet trả sample rate {result.sample_rate}, cần {sample_rate} Hz"
        )
    return np.ascontiguousarray(result.samples, dtype=np.float32)
