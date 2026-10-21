$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$zipformer = Join-Path $projectRoot 'models\sherpa-onnx-zipformer-vi-30M-int8-2026-02-09\encoder.int8.onnx'
$vadModel = Join-Path $projectRoot 'models\silero_vad.onnx'

if (-not (Test-Path -LiteralPath $python)) {
    throw "Project Python environment was not found at $python. Create the .venv first."
}
& $python -c 'import sherpa_onnx' *> $null
if ($LASTEXITCODE -ne 0) {
    throw 'Zipformer ASR needs sherpa-onnx. Install with: .\.venv\Scripts\python.exe -m pip install -e .'
}
if (-not (Test-Path -LiteralPath $zipformer) -or -not (Test-Path -LiteralPath $vadModel)) {
    throw 'Zipformer/VAD model files are missing. Download them with: .\.venv\Scripts\python.exe scripts\download_robust_asr_models.py'
}

Set-Location -LiteralPath $projectRoot
& $python -m pricetyper gui --tiktok-web
exit $LASTEXITCODE
