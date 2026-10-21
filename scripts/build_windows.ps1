param(
    [switch]$SkipInstaller,
    [string]$NsisPath
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
$spec = Join-Path $repoRoot "packaging\windows\NumberTyper.spec"
$distRoot = Join-Path $repoRoot "dist"
$appDist = Join-Path $distRoot "NumberTyper"
$looseExe = Join-Path $distRoot "NumberTyper.exe"
$workRoot = Join-Path $repoRoot "build\windows"
$extensionPackageScript = Join-Path $repoRoot "scripts\package_browser_extension.ps1"
$installerName = "NumberTyper-Setup-0.1.0-preview.exe"
$installerOut = Join-Path $distRoot $installerName
$nsisScriptDir = Join-Path $repoRoot "packaging\windows"

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw "Không tìm thấy .venv. Hãy tạo môi trường và cài requirements-windows-build.txt trước."
}
if (-not (Test-Path -LiteralPath $repoRoot -PathType Container)) {
    throw "Không xác định được thư mục dự án."
}

$pythonVersion = & $python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
if ($LASTEXITCODE -ne 0) { throw "Không đọc được phiên bản Python của môi trường build." }
$pythonMajorMinor = & $python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$pythonMajorMinor -lt [version]"3.12") {
    throw "NumberTyper cần Python 3.12 trở lên để dựng. Đang dùng $pythonVersion."
}
$machine = & $python -c "import platform; print(platform.machine().lower())"
if ($machine -notin @("amd64", "x86_64")) {
    throw "Bộ cài sprint này chỉ hỗ trợ Windows 64-bit. Kiến trúc hiện tại: $machine"
}

$required = @(
    (Join-Path $repoRoot "models\sherpa-onnx-zipformer-vi-30M-int8-2026-02-09\encoder.int8.onnx"),
    (Join-Path $repoRoot "models\sherpa-onnx-zipformer-vi-30M-int8-2026-02-09\decoder.onnx"),
    (Join-Path $repoRoot "models\sherpa-onnx-zipformer-vi-30M-int8-2026-02-09\joiner.int8.onnx"),
    (Join-Path $repoRoot "models\sherpa-onnx-zipformer-vi-30M-int8-2026-02-09\tokens.txt"),
    (Join-Path $repoRoot "models\silero_vad.onnx"),
    (Join-Path $repoRoot "browser_extension\manifest.json"),
    (Join-Path $repoRoot "docs\THIRD_PARTY_NOTICES.md"),
    (Join-Path $repoRoot "docs\INSTALL_VI.md")
)
$missing = @($required | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) })
if ($missing.Count -gt 0) {
    throw "Thiếu tài nguyên bắt buộc:`n$($missing -join "`n")"
}

foreach ($ownedPath in @($appDist, $workRoot)) {
    $fullOwnedPath = [System.IO.Path]::GetFullPath($ownedPath)
    $fullParent = [System.IO.Path]::GetFullPath((Split-Path -Parent $ownedPath))
    if ([System.IO.Path]::GetDirectoryName($fullOwnedPath) -ne $fullParent) {
        throw "Từ chối xóa đường dẫn build ngoài vị trí dự án: $fullOwnedPath"
    }
}
if (Test-Path -LiteralPath $appDist) { Remove-Item -LiteralPath $appDist -Recurse -Force }
if (Test-Path -LiteralPath $workRoot) { Remove-Item -LiteralPath $workRoot -Recurse -Force }
if (Test-Path -LiteralPath $looseExe -PathType Leaf) { Remove-Item -LiteralPath $looseExe -Force }
New-Item -ItemType Directory -Force -Path $workRoot | Out-Null
New-Item -ItemType Directory -Force -Path $distRoot | Out-Null

Push-Location $repoRoot
try {
    & $python -m PyInstaller --noconfirm --clean --distpath $distRoot --workpath $workRoot $spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller thất bại với mã $LASTEXITCODE." }
} finally {
    Pop-Location
}

$appExe = Join-Path $appDist "NumberTyper.exe"
if (-not (Test-Path -LiteralPath $appExe -PathType Leaf)) {
    throw "PyInstaller chạy xong nhưng không tạo NumberTyper.exe."
}
if (Test-Path -LiteralPath $looseExe -PathType Leaf) { Remove-Item -LiteralPath $looseExe -Force }

$smokeData = Join-Path $env:TEMP "NumberTyper-smoke-$PID"
$oldDataOverride = $env:NUMBERTYPER_DATA_DIR
try {
    New-Item -ItemType Directory -Force -Path $smokeData | Out-Null
    $env:NUMBERTYPER_DATA_DIR = $smokeData
    $smoke = Start-Process `
        -FilePath $appExe `
        -ArgumentList "--smoke-check" `
        -WorkingDirectory (Join-Path $env:WINDIR "System32") `
        -WindowStyle Hidden `
        -PassThru
    if (-not $smoke.WaitForExit(180000)) {
        $smoke.Kill()
        throw "Bản dựng không hoàn tất kiểm tra model trong 180 giây."
    }
    if ($smoke.ExitCode -ne 0) {
        $log = Join-Path $smokeData "logs\startup.log"
        $details = if (Test-Path -LiteralPath $log) { Get-Content -LiteralPath $log -Raw } else { "Không có startup.log." }
        throw "Bản dựng thất bại khi nạp model (exit $($smoke.ExitCode)):`n$details"
    }
    $smokeLog = Join-Path $smokeData "logs\startup.log"
    if (-not (Select-String -LiteralPath $smokeLog -SimpleMatch "SMOKE CHECK OK" -Quiet)) {
        throw "Executable trả mã 0 nhưng không ghi xác nhận nạp model vào $smokeLog."
    }
    Write-Host "Kiểm tra executable/model: PASS (khởi chạy ngoài thư mục dự án, không mở GUI hoặc sender)."
} finally {
    if ($null -eq $oldDataOverride) {
        Remove-Item Env:\NUMBERTYPER_DATA_DIR -ErrorAction SilentlyContinue
    } else {
        $env:NUMBERTYPER_DATA_DIR = $oldDataOverride
    }
    $tempRoot = [System.IO.Path]::GetFullPath($env:TEMP).TrimEnd('\')
    $smokePath = [System.IO.Path]::GetFullPath($smokeData)
    if ($smokePath.StartsWith($tempRoot + '\', [System.StringComparison]::OrdinalIgnoreCase) -and
        (Split-Path -Leaf $smokePath).StartsWith("NumberTyper-smoke-", [System.StringComparison]::Ordinal)) {
        if (Test-Path -LiteralPath $smokePath) { Remove-Item -LiteralPath $smokePath -Recurse -Force }
    }
}

if (-not (Test-Path -LiteralPath $extensionPackageScript -PathType Leaf)) {
    throw "Không tìm thấy script đóng gói extension: $extensionPackageScript"
}
& $extensionPackageScript

if ($SkipInstaller) {
    Write-Host "Đã tạo ứng dụng portable: $appExe"
    exit 0
}

$makensisExe = $null
if ($NsisPath) {
    $resolvedNsisPath = (Resolve-Path -LiteralPath $NsisPath -ErrorAction Stop).Path
    if ((Get-Item -LiteralPath $resolvedNsisPath).PSIsContainer) {
        $makensisExe = Join-Path $resolvedNsisPath "makensis.exe"
    } else {
        $makensisExe = $resolvedNsisPath
    }
} else {
    $makensisCommand = Get-Command "makensis.exe" -ErrorAction SilentlyContinue
    if (-not $makensisCommand) { $makensisCommand = Get-Command "makensis" -ErrorAction SilentlyContinue }
    if ($makensisCommand) { $makensisExe = $makensisCommand.Source }
}
if (-not $makensisExe -or -not (Test-Path -LiteralPath $makensisExe -PathType Leaf)) {
    throw "Đã dựng app portable, nhưng chưa tìm thấy makensis (NSIS). Cài NSIS 3.13 rồi chạy lại scripts\build_windows.ps1."
}
if (Test-Path -LiteralPath $installerOut -PathType Leaf) {
    Remove-Item -LiteralPath $installerOut -Force
}

Push-Location $nsisScriptDir
$oldNsisDir = $env:NSISDIR
try {
    $env:NSISDIR = Split-Path -Parent $makensisExe
    & $makensisExe /V2 "NumberTyper.nsi"
    if ($LASTEXITCODE -ne 0) { throw "NSIS thất bại với mã $LASTEXITCODE." }
} finally {
    if ($null -eq $oldNsisDir) {
        Remove-Item Env:\NSISDIR -ErrorAction SilentlyContinue
    } else {
        $env:NSISDIR = $oldNsisDir
    }
    Pop-Location
}

$scriptOutput = Join-Path $nsisScriptDir "NumberTyper-Setup.exe"
if (-not (Test-Path -LiteralPath $scriptOutput -PathType Leaf)) {
    throw "NSIS chạy xong nhưng không tạo tệp cài đặt."
}
Move-Item -LiteralPath $scriptOutput -Destination $installerOut -Force

$installerHash = (Get-FileHash -LiteralPath $installerOut -Algorithm SHA256).Hash
Write-Host "Đã tạo bộ cài preview: $installerOut"
Write-Host "Python build: $pythonVersion x64"
Write-Host "SHA-256: $installerHash"
Write-Host "Đây là bản preview cá nhân; chưa được nghiệm thu trên máy Windows sạch hoặc cửa hàng extension."
