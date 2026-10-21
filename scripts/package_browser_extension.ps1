param(
    [string]$OutputPath
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$extensionDir = Join-Path $repoRoot "browser_extension"
$distDir = Join-Path $repoRoot "dist"
if (-not $OutputPath) {
    $OutputPath = Join-Path $distDir "NumberTyper-Tab-Audio-0.1.0.zip"
}

$manifestPath = Join-Path $extensionDir "manifest.json"
$requiredFiles = @(
    "manifest.json",
    "service-worker.js",
    "offscreen.html",
    "offscreen.js",
    "pcm-worklet.js",
    "popup.html",
    "popup.js"
)
$missing = @($requiredFiles | Where-Object { -not (Test-Path -LiteralPath (Join-Path $extensionDir $_) -PathType Leaf) })
if ($missing.Count -gt 0) {
    throw "Thiếu tệp extension: $($missing -join ', ')"
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.manifest_version -ne 3 -or -not $manifest.key) {
    throw "Manifest phải là MV3 và có public key ổn định trước khi đóng gói."
}

New-Item -ItemType Directory -Force -Path $distDir | Out-Null
$resolvedDist = [System.IO.Path]::GetFullPath($distDir).TrimEnd('\')
$resolvedOutput = [System.IO.Path]::GetFullPath($OutputPath)
if (-not $resolvedOutput.StartsWith($resolvedDist + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Từ chối ghi gói extension ra ngoài thư mục dist: $resolvedOutput"
}
if (Test-Path -LiteralPath $resolvedOutput -PathType Container) {
    throw "Đường dẫn đầu ra là thư mục, không ghi đè: $resolvedOutput"
}
if (Test-Path -LiteralPath $resolvedOutput -PathType Leaf) {
    Remove-Item -LiteralPath $resolvedOutput -Force
}

Compress-Archive -Path (Join-Path $extensionDir "*") -DestinationPath $resolvedOutput -CompressionLevel Optimal

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($resolvedOutput)
try {
    $entryNames = @($archive.Entries | ForEach-Object { $_.FullName.Replace('\', '/') })
    $unexpected = @($entryNames | Where-Object { $_ -match '(^/|\.pem$|private|secret|\.git)' })
    $missingEntries = @($requiredFiles | Where-Object { $_ -notin $entryNames })
    if ($unexpected.Count -gt 0 -or $missingEntries.Count -gt 0) {
        throw "Gói ZIP không hợp lệ. Thiếu: $($missingEntries -join ', '); ngoài dự kiến: $($unexpected -join ', ')"
    }
} finally {
    $archive.Dispose()
}

$publicKey = [Convert]::FromBase64String($manifest.key)
$sha256 = [System.Security.Cryptography.SHA256]::Create()
try { $digest = $sha256.ComputeHash($publicKey) } finally { $sha256.Dispose() }
$extensionId = -join ($digest[0..15] | ForEach-Object {
    $byte = [int]$_
    [char](97 + (($byte -shr 4) -band 15))
    [char](97 + ($byte -band 15))
})
$hash = (Get-FileHash -LiteralPath $resolvedOutput -Algorithm SHA256).Hash
Write-Host "Extension ZIP: $resolvedOutput"
Write-Host "Version: $($manifest.version)"
Write-Host "Extension ID derived from manifest key: $extensionId"
Write-Host "SHA-256: $hash"
Write-Host "Gói chỉ chứa tệp extension; trạng thái cửa hàng vẫn cần publisher submit và review."
