# NumberTyper (project package: PriceTyper)

NumberTyper is a local Python project (the package directory remains `pricetyper`). `--youtube-test` is **number-first and recognition-only**. `--tiktok-web` is an experimental Windows mode that uses a Chromium extension to capture audio and act in the same user-selected TikTok Live tab. It starts in dry-run/disarmed mode and defaults to fill-only; an explicit checkbox enables one Enter action after the finalized number is filled. Leaving dry-run still does not arm it, and F8 is required. Both modes use local Zipformer-VI + Silero VAD. ASR accuracy, browser compatibility, TikTok comment appearance, and end-to-end latency have not been accepted. Chromium browsers are implementation targets only; see `docs/BROWSER_COMPATIBILITY.md`. The eventual public release is intended to be installable with a normal shortcut; users should not need Python or PowerShell in that release.

See [docs/PROTOTYPE_YOUTUBE.md](docs/PROTOTYPE_YOUTUBE.md) for number recognition, [docs/PROTOTYPE_TIKTOK_WEB.md](docs/PROTOTYPE_TIKTOK_WEB.md) for the TikTok pilot workflow, and [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) for what has actually been verified. The TikTok mode is a pilot; automated sender checks use only the local fake page and do not establish live comment appearance or latency.

See [docs/TECH_STACK.md](docs/TECH_STACK.md) for the current technology stack, architecture, limitations, source map, and local setup steps.

## Install the personal preview

The Windows 64-bit personal preview installer is built at `dist/NumberTyper-Setup-0.1.0-preview.exe`. It installs per-user, creates a Start Menu shortcut, includes Python and the local ASR/VAD model, and does not require PowerShell or a separate Python install. On first launch, the Vietnamese setup window can open the selected browser's extension manager and bundled extension folder. The current preview still requires manual unpacked loading because the extension is not published in a browser store. The build also prepares `dist/NumberTyper-Tab-Audio-0.1.0.zip` and draft store/privacy materials; they have not been submitted. No browser has passed current end-to-end acceptance yet.

The bundled Zipformer model is marked CC BY-NC-ND 4.0 by its upstream model card. This preview is for personal, non-commercial use only. Do not use it for business or publish a commercial build without the necessary model rights. See [the setup guide](docs/INSTALL_VI.md) and [third-party notices](docs/THIRD_PARTY_NOTICES.md).

The source/developer workflow uses Windows 10/11, Python 3.12 or newer, and a Chromium browser with the unpacked extension. Download the local models into the ignored `models/` folder:

```powershell
py -3.12 -m venv .venv
.venv/Scripts/Activate.ps1
pip install -e ".[dev]"
Copy-Item config.example.yaml config.yaml
python scripts\download_robust_asr_models.py
```

For the optional ASR comparison benchmark, download `vosk-model-small-vn-0.4` from the [official Vosk model list](https://alphacephei.com/vosk/models) and extract it to `models/vosk-model-small-vn-0.4`. Then follow [the prototype workflow](docs/PROTOTYPE_YOUTUBE.md) to start NumberTyper and load the unpacked `browser_extension/` folder into a Chromium browser.

## Commands

YouTube number-recognition mode:

```powershell
.\run-youtube-test.ps1
```

TikTok Web prototype (Chromium extension; initially dry-run and disarmed):

```powershell
.\run-tiktok-web.ps1
```

Open the Live page in a Chromium browser and start capture from the NumberTyper extension. In the app, connect/probe that same tab; it remains disarmed until F8. The app defaults to fill-only; enable the Enter-submit checkbox while disarmed if you want automatic submission. F10 is emergency stop. `discover --tiktok-web` is deprecated because the extension probes the selected tab. Automated sender checks use a local fake page and must not be run against a real livestream.

The YouTube launcher and extension workflow are documented in `docs/PROTOTYPE_YOUTUBE.md`.

Rebuild the Windows preview with `scripts/build_windows.ps1`. It runs the PyInstaller build, a local model-load smoke check, creates the extension store ZIP, and compiles the NSIS installer if NSIS is installed or passed with `-NsisPath`. `scripts/smoke_installer.ps1` performs a reversible per-user install/uninstall check only if no NumberTyper install/shortcuts already exist.

See [docs/SPEC.md](docs/SPEC.md) for the supplied technical specification, including the added Antigravity workflow in §§13–19. See [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) for milestone progress and checks that remain.
