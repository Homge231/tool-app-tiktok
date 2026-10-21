param(
    [switch]$AsrCompare,
    [ValidateSet('base', 'small', 'medium')]
    [string]$WhisperModel = 'small'
)

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
$guiArgs = @('-m', 'pricetyper', 'gui', '--youtube-test')
if ($AsrCompare) {
    & $python -c 'import faster_whisper' *> $null
    if ($LASTEXITCODE -ne 0) {
        throw 'ASR benchmark needs faster-whisper and sherpa-onnx. Install with: .\.venv\Scripts\python.exe -m pip install -e ".[robust-asr]"'
    }
    $zipformer = Join-Path $projectRoot 'models\sherpa-onnx-zipformer-vi-30M-int8-2026-02-09\encoder.int8.onnx'
    $denoiser = Join-Path $projectRoot 'models\dpdfnet_baseline.onnx'
    $vosk = Join-Path $projectRoot 'models\vosk-model-small-vn-0.4'
    if (-not (Test-Path -LiteralPath $zipformer) -or -not (Test-Path -LiteralPath $denoiser)) {
        throw 'ASR benchmark models are missing. Download them with: .\.venv\Scripts\python.exe scripts\download_robust_asr_models.py'
    }
    if (-not (Test-Path -LiteralPath $vosk)) {
        throw "Vietnamese Vosk baseline model was not found at $vosk. Install it to run the comparison benchmark."
    }
    $guiArgs += @('--asr-compare', '--whisper-model', $WhisperModel)
}
& $python @guiArgs
exit $LASTEXITCODE
