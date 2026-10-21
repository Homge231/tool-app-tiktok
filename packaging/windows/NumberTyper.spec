# PyInstaller one-directory build for the Vietnamese desktop preview.
from pathlib import Path

from PyInstaller.utils.hooks import collect_dynamic_libs

ROOT = Path(SPECPATH).resolve().parents[1]
SRC = ROOT / "src"
MODEL_DIR = ROOT / "models" / "sherpa-onnx-zipformer-vi-30M-int8-2026-02-09"
EXTENSION_DIR = ROOT / "browser_extension"

def add_directory(source: Path, destination: str):
    return [
        (str(path), str(Path(destination) / path.relative_to(source).parent))
        for path in source.rglob("*")
        if path.is_file()
    ]


datas = [
    *add_directory(MODEL_DIR, "models/sherpa-onnx-zipformer-vi-30M-int8-2026-02-09"),
    (str(ROOT / "models" / "silero_vad.onnx"), "models"),
    *add_directory(EXTENSION_DIR, "browser_extension"),
    (str(ROOT / "docs" / "INSTALL_VI.md"), "docs"),
    (str(ROOT / "docs" / "THIRD_PARTY_NOTICES.md"), "docs"),
]
binaries = collect_dynamic_libs("sherpa_onnx") + collect_dynamic_libs("vosk")
hiddenimports = [
    "sherpa_onnx",
    "sherpa_onnx.lib._sherpa_onnx",
    "websockets.sync.server",
    "websockets.sync.client",
    "yaml",
]

a = Analysis(
    [str(SRC / "pricetyper" / "windows_entry.py")],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # The shipped desktop entry point uses the Chromium extension bridge.
    # Legacy desktop automation and Playwright senders remain available to the
    # source project but are not used by this app build.
    excludes=[
        "matplotlib",
        "scipy",
        "torch",
        "faster_whisper",
        "playwright",
        "pyautogui",
        "mouseinfo",
        "pymsgbox",
        "pygetwindow",
        "pyperclip",
        "pyrect",
        "pyscreeze",
        "pytweening",
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    name="NumberTyper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="NumberTyper",
)
