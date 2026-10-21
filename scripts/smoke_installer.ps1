param(
    [string]$InstallerPath = "..\dist\NumberTyper-Setup-0.1.0-preview.exe"
)

$ErrorActionPreference = "Stop"
$installerCandidate = if ([System.IO.Path]::IsPathRooted($InstallerPath)) {
    $InstallerPath
} else {
    Join-Path $PSScriptRoot $InstallerPath
}
$installer = (Resolve-Path -LiteralPath $installerCandidate).Path
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\NumberTyper"
$startMenu = Join-Path ([Environment]::GetFolderPath("Programs")) "NumberTyper"
$desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "NumberTyper.lnk"
if ((Test-Path $regPath) -or (Test-Path $startMenu) -or (Test-Path $desktopShortcut)) {
    throw "Đã có cài đặt/shortcut NumberTyper. Từ chối chạy smoke test để không đè lên dữ liệu hiện có."
}

$tempRoot = [System.IO.Path]::GetFullPath($env:TEMP).TrimEnd("\")
$testId = [guid]::NewGuid().ToString("N")
$installRoot = Join-Path $tempRoot "NumberTyper-Installer-Smoke-$testId"
$smokeData = Join-Path $tempRoot "NumberTyper-Installed-SmokeData-$testId"
if ((Test-Path -LiteralPath $installRoot) -or (Test-Path -LiteralPath $smokeData)) {
    throw "Đường dẫn smoke test đã tồn tại; không ghi đè: $installRoot"
}

$oldDataOverride = $env:NUMBERTYPER_DATA_DIR
$installed = $false
try {
    $setup = Start-Process -FilePath $installer -ArgumentList @("/S", "/D=$installRoot") -Wait -PassThru -WindowStyle Hidden
    if ($setup.ExitCode -ne 0) { throw "Installer trả mã $($setup.ExitCode)." }

    $appExe = Join-Path $installRoot "NumberTyper.exe"
    if (-not (Test-Path -LiteralPath $appExe -PathType Leaf)) {
        throw "Không tìm thấy executable tại đường dẫn cài đã chọn: $appExe"
    }
    $installed = $true
    if (-not (Test-Path -LiteralPath $regPath)) { throw "Installer chưa đăng ký mục gỡ cài đặt." }
    if (-not (Test-Path -LiteralPath (Join-Path $startMenu "NumberTyper.lnk"))) {
        throw "Installer chưa tạo shortcut Menu Bắt đầu."
    }
    if (Test-Path -LiteralPath $desktopShortcut) {
        throw "Shortcut Desktop tùy chọn không được chọn nhưng vẫn được tạo."
    }

    New-Item -ItemType Directory -Force -Path $smokeData | Out-Null
    $env:NUMBERTYPER_DATA_DIR = $smokeData
    $app = Start-Process `
        -FilePath $appExe `
        -ArgumentList "--smoke-check" `
        -WorkingDirectory (Join-Path $env:WINDIR "System32") `
        -WindowStyle Hidden `
        -PassThru
    if (-not $app.WaitForExit(180000)) {
        $app.Kill()
        throw "Ứng dụng đã cài không nạp model trong 180 giây."
    }
    if ($app.ExitCode -ne 0) {
        $startupLog = Join-Path $smokeData "logs\startup.log"
        $details = if (Test-Path -LiteralPath $startupLog) { Get-Content -LiteralPath $startupLog -Raw } else { "Không có startup.log." }
        throw "Ứng dụng đã cài lỗi khi nạp model (exit $($app.ExitCode)):`n$details"
    }
    $startupLog = Join-Path $smokeData "logs\startup.log"
    if (-not (Select-String -LiteralPath $startupLog -SimpleMatch "SMOKE CHECK OK" -Quiet)) {
        throw "Không có xác nhận model trong startup.log."
    }

    $uninstall = Start-Process -FilePath (Join-Path $installRoot "Uninstall.exe") -ArgumentList "/S" -Wait -PassThru -WindowStyle Hidden
    if ($uninstall.ExitCode -ne 0) { throw "Uninstaller trả mã $($uninstall.ExitCode)." }
    $installed = $false
    if ((Test-Path -LiteralPath $installRoot) -or (Test-Path -LiteralPath $regPath) -or (Test-Path -LiteralPath $startMenu)) {
        throw "Gỡ cài đặt chưa dọn thư mục ứng dụng, registry và shortcut."
    }
    Write-Host "INSTALL QA PASS: cài theo user, shortcut Menu Bắt đầu, nạp model từ System32, gỡ sạch."
} finally {
    if ($null -eq $oldDataOverride) {
        Remove-Item Env:\NUMBERTYPER_DATA_DIR -ErrorAction SilentlyContinue
    } else {
        $env:NUMBERTYPER_DATA_DIR = $oldDataOverride
    }
    if ($installed -and (Test-Path -LiteralPath (Join-Path $installRoot "Uninstall.exe"))) {
        Start-Process -FilePath (Join-Path $installRoot "Uninstall.exe") -ArgumentList "/S" -Wait -WindowStyle Hidden
    }
    foreach ($ownedPath in @($installRoot, $smokeData)) {
        $fullPath = [System.IO.Path]::GetFullPath($ownedPath)
        if ($fullPath.StartsWith($tempRoot + "\", [System.StringComparison]::OrdinalIgnoreCase)) {
            if (Test-Path -LiteralPath $fullPath) { Remove-Item -LiteralPath $fullPath -Recurse -Force }
        }
    }
}
