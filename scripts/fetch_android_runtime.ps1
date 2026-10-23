$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$targetDir = Join-Path $repoRoot 'android\app\libs'
$target = Join-Path $targetDir 'sherpa-onnx-1.13.8.aar'
$expectedHash = '633c24321e06b1fe79feafa03ea16cbc0f8a286641e2da3559bac91bdb13bd96'
$sourceUrl = 'https://github.com/k2-fsa/sherpa-onnx/releases/download/v1.13.8/sherpa-onnx-1.13.8.aar'

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
if (Test-Path -LiteralPath $target) {
    $existingHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLowerInvariant()
    if ($existingHash -eq $expectedHash) {
        Write-Output "sherpa-onnx Android runtime already verified: $target"
        exit 0
    }
    throw "Existing runtime checksum mismatch: $target"
}

$tempFile = Join-Path $env:TEMP 'sherpa-onnx-1.13.8-android.aar.download'
Invoke-WebRequest -Uri $sourceUrl -OutFile $tempFile
$actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $tempFile).Hash.ToLowerInvariant()
if ($actualHash -ne $expectedHash) {
    throw "Downloaded runtime checksum mismatch: expected $expectedHash, got $actualHash"
}
Move-Item -LiteralPath $tempFile -Destination $target
Write-Output "Verified and installed sherpa-onnx Android runtime: $actualHash"
