from __future__ import annotations

import shutil
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
ZIPFORMER_NAME = "sherpa-onnx-zipformer-vi-30M-int8-2026-02-09"
ZIPFORMER_URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/"
    f"{ZIPFORMER_NAME}.tar.bz2"
)
DPDFNET_URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/"
    "speech-enhancement-models/dpdfnet_baseline.onnx"
)
SILERO_VAD_URL = (
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/"
    "asr-models/silero_vad.onnx"
)
ZIPFORMER_FILES = (
    "encoder.int8.onnx",
    "decoder.onnx",
    "joiner.int8.onnx",
    "tokens.txt",
)


def download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(
        url, headers={"User-Agent": "PriceTyper-local-model-setup/0.1"}
    )
    try:
        with (
            urllib.request.urlopen(request, timeout=60) as response,
            temporary.open("wb") as output,
        ):
            shutil.copyfileobj(response, output)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def extract_required_files(archive_path: Path, model_dir: Path) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)
    wanted = {f"{ZIPFORMER_NAME}/{name}" for name in ZIPFORMER_FILES}
    root = model_dir.resolve()
    with tarfile.open(archive_path, "r:bz2") as archive:
        for member in archive.getmembers():
            if member.name not in wanted or not member.isfile():
                continue
            target = (model_dir / Path(member.name).name).resolve()
            if root not in target.parents:
                raise ValueError(f"Unsafe model archive path: {member.name}")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError(f"Cannot read model archive file: {member.name}")
            with source, target.open("wb") as output:
                shutil.copyfileobj(source, output)

    missing = [name for name in ZIPFORMER_FILES if not (model_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"Model archive did not contain required files: {missing}")


def main() -> int:
    zipformer_dir = MODELS / ZIPFORMER_NAME
    model_archive = MODELS / f"{ZIPFORMER_NAME}.tar.bz2"
    denoiser = MODELS / "dpdfnet_baseline.onnx"
    vad_model = MODELS / "silero_vad.onnx"

    if not all((zipformer_dir / name).is_file() for name in ZIPFORMER_FILES):
        print("Downloading Vietnamese Zipformer-VI INT8 model…")
        download(ZIPFORMER_URL, model_archive)
        extract_required_files(model_archive, zipformer_dir)
        model_archive.unlink(missing_ok=True)
    else:
        print("Zipformer-VI INT8 model is already present.")

    if not denoiser.is_file():
        print("Downloading DPDFNet baseline speech-enhancement model…")
        download(DPDFNET_URL, denoiser)
    else:
        print("DPDFNet baseline model is already present.")

    if not vad_model.is_file():
        print("Downloading Silero VAD model for Zipformer endpointing…")
        download(SILERO_VAD_URL, vad_model)
    else:
        print("Silero VAD model is already present.")

    print(f"Models are ready under: {MODELS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
