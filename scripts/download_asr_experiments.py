from __future__ import annotations

import argparse
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"
GIPFORMER_REVISION = "dd9227dcd8705c13f33bdbe59728d546ab94480f"
STREAMING_REVISION = "c122fdc21cea4894fd775e9d3fe66ebbc787e26b"
GIPFORMER_REPO = "g-group-ai-lab/gipformer1.5-68M-rnnt"
STREAMING_REPO = "hynt/Zipformer-30M-RNNT-Streaming-6000h"


def download_file(repo: str, revision: str, remote_name: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and target.stat().st_size:
        print(f"Already present: {target.name}")
        return
    url = f"https://huggingface.co/{repo}/resolve/{revision}/{remote_name}"
    temporary = target.with_suffix(target.suffix + ".part")
    request = urllib.request.Request(
        url, headers={"User-Agent": "NumberTyper-ASR-benchmark/0.1"}
    )
    try:
        with (
            urllib.request.urlopen(request, timeout=90) as response,
            temporary.open("wb") as output,
        ):
            shutil.copyfileobj(response, output)
        if not temporary.stat().st_size:
            raise RuntimeError(f"Downloaded file is empty: {remote_name}")
        temporary.replace(target)
        print(f"Downloaded: {target.name} ({target.stat().st_size:,} bytes)")
    finally:
        temporary.unlink(missing_ok=True)


def download_gipformer() -> None:
    print("Gipformer 1.5 INT8 · MIT · local benchmark model")
    directory = MODELS / "gipformer1.5-68M-rnnt"
    for name in (
        "encoder.int8.onnx",
        "decoder.int8.onnx",
        "joiner.int8.onnx",
        "tokens.txt",
    ):
        download_file(GIPFORMER_REPO, GIPFORMER_REVISION, name, directory / name)


def download_streaming_zipformer() -> None:
    print(
        "Zipformer streaming chunk-16 · CC-BY-NC-ND-4.0 · "
        "local evaluation only; do not package, modify, or redistribute"
    )
    directory = MODELS / "hynt-zipformer-30M-rnnt-streaming-6000h-chunk16"
    suffix = "epoch-31-avg-11-chunk-16-left-128.fp16.onnx"
    files = (
        (f"encoder-{suffix}", f"encoder-{suffix}"),
        (f"decoder-{suffix}", f"decoder-{suffix}"),
        (f"joiner-{suffix}", f"joiner-{suffix}"),
        # Upstream's config.json is actually the token table consumed by Sherpa.
        ("config.json", "tokens.txt"),
    )
    for remote_name, local_name in files:
        download_file(
            STREAMING_REPO,
            STREAMING_REVISION,
            remote_name,
            directory / local_name,
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Tải model ASR thử nghiệm vào models/ (không đưa vào installer)."
    )
    parser.add_argument("--gipformer", action="store_true", help="Gipformer 1.5 INT8")
    parser.add_argument(
        "--streaming-zipformer",
        action="store_true",
        help="Zipformer Vietnamese RNNT streaming, chunk 16",
    )
    args = parser.parse_args()
    if not args.gipformer and not args.streaming_zipformer:
        parser.error(
            "Chọn ít nhất một model: --gipformer và/hoặc --streaming-zipformer"
        )
    if args.gipformer:
        download_gipformer()
    if args.streaming_zipformer:
        download_streaming_zipformer()
    print(f"Local benchmark models are under: {MODELS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
