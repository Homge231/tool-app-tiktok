# PriceTyper implementation status

Updated: 2026-10-24

## Session update — 2026-10-24

TikTok Web candidate handling now accepts only the last parsed number from 100 through 999 inclusive; if the final number is outside that range, the whole ASR event is ignored rather than falling back to an earlier number in the same utterance. The GUI now uses a **Tự động gửi @+số** checkbox: checked selects the TikTok send-button path; unchecked keeps continuous fill-only replacement. Selecting the mode while dry-run is on does not enable a real sender. Real actions still require turning dry-run off and pressing F8 while disarmed.

Files changed: `src/pricetyper/decision/decider.py`, `src/pricetyper/pipeline.py`, `src/pricetyper/ui/gui.py`, `.agents/rules/parser.md`, `.agents/rules/senders.md`, `docs/SPEC.md`, `docs/PROTOTYPE_TIKTOK_WEB.md`, `docs/TECH_STACK.md`, `docs/BROWSER_COMPATIBILITY.md`, `docs/IMPLEMENTATION_STATUS.md`, and `README.md`. `git diff --check` is the only check run so far. Automated tests, app restart, browser interaction, live TikTok use, and installer rebuild were not run; the existing open window must be restarted to load the changed Python code. The checkbox and number-range behavior have not been manually verified in the GUI.

## Session update — 2026-10-23

The current TikTok GUI preselects auto-submit of `@<number>` after a successful tab probe. Dry-run remains enabled and the action remains disarmed until the user disables dry-run and presses F8; fill-only remains available. The Windows preview installer and model smoke check were recorded in the preceding session; artifact and hash are in `second-brain/Current-State.md`. No new build, browser run, live TikTok action, or latency/accuracy measurement was performed in this documentation update. Actual comment appearance, current browser compatibility, exact-number accuracy, sub-1-second end-to-end latency, and four-hour stability remain unaccepted.

## User-reported TikTok check — 2026-10-23

The user reports that a TikTok comment appeared with the recognized number. The input showed `@123` before submission, but the displayed comment omitted `@`. The user then provided a screenshot showing a separate manually entered `@1` comment displayed in the same TikTok Live chat. This proves `@1` can appear in that session and rules out a blanket claim that TikTok always strips `@`; it does not show whether NumberTyper's inserted value was preserved by the page's input state. Browser, app, and extension versions were not provided, so this remains partial user-reported evidence and does not establish browser compatibility or repeatable formatting behavior. The current source prefixes numeric sender text with `@`; the extension validates the `@`-prefixed payload and confirms the same text in the input before dispatching Enter. No new live action, build, or automated check was run in this follow-up.

Follow-up code change: the extension now yields one JavaScript microtask after inserting text, then checks the exact input text before any Enter dispatch. This is intended to let page input handlers update before submission; it has not been tested against TikTok or a packaged build. The comment-rendering issue remains unresolved until a new manual check.

## M8 continuous fill-only replacement — 2026-10-23

Fill-only decisions no longer use same-number cooldown, any-number cooldown, or the per-minute send cap. The ASR/parser always keeps the recognized number as a raw numeric value, such as `12`. Fill-only writes that plain number and replaces an existing numeric draft; submit mode formats it as `@12`, requires an empty field, and retains cooldowns and the per-minute cap. The GUI replaces the send checkbox with mutually exclusive “Chỉ điền số · thay số cũ” and “Gửi @+số bằng Enter” radio options; dry-run remains a separate safety control, and F8/F10 behavior is unchanged. Updated project docs to match this distinction.

Checks run: `node --check browser_extension/service-worker.js`, Python `py_compile` for `decider.py`, `pipeline.py`, and `gui.py`, and `git diff --check` all passed. Automated tests were not run. No app GUI launch, browser extension reload, TikTok interaction, or packaged build was performed, so field replacement and the updated controls still need a manual check in the user's browser.

For cross-session project memory, open `second-brain/` as an Obsidian vault and follow `second-brain/00-Start-Here.md`. This vault summarizes context; the technical docs remain the detailed source of truth.

This file tracks code present in the workspace separately from acceptance evidence. “Implemented” does not mean verified on a live browser, audio device, or phone.

| Milestone | Code present | Acceptance status |
|---|---|---|
| M0 | package skeleton, Pydantic configuration, example YAML, CLI command declarations, JSONL logger, shared types | Core config and CLI tests pass. M0 remains partial because later module and hardware checks are outstanding. |
| M1 | Vietnamese number parser, context gate, decision hold/cooldown/rate-limit logic | Parser, gate, and decider reference cases pass. Price values are normalized to đồng: bare numbers stay literal, while `nghìn`/`ngàn`/`k` multiply by 1,000. |
| M2 | WAV and loopback sources, record command, 16 kHz PCM WAV validation; record now captures the requested sample count and trims the final chunk | Passed on this Windows audio device: `record --seconds 10` created a 10.00 s, mono, PCM 16-bit, 16 kHz WAV (160,000 frames). The 16 kHz device path worked, so the conditional 48→16 kHz fallback was not needed or exercised. |
| M3 | Zipformer-VI + Silero VAD default engine, Vosk baseline, audio/ASR/decision/sender threads, replay, JSONL events, truth-based latency report | Partial. Unit tests and a local-model silence smoke check pass. No labeled WAV replay or precision/recall dataset has been run. Gipformer 1.5 and third-party Zipformer streaming are optional local benchmark lanes only; they do not replace the core. |
| M4 | Playwright, desktop, ADB and null senders; controller; F8/F10; local fake page; sender and replay latency commands | Partial. Local fake-page sender now passes with Edge; no interactive F8/F10 acceptance has been run. |
| M5 | Tkinter status/control window, calibrate, discover | Partial. Manual §7.2 checklist has not been run. |
| M6 | ADB fallback and Android setup guide | Not verified. No Android device/scrcpy session was available for acceptance. |
| M7 | Historical TikTok Web/Edge pilot with local tab audio, final-only decisions, Playwright sender and dry-run default | Earlier focused fake-page/protocol/CLI/extension checks passed; no TikTok account or livestream was opened. Its separate Edge profile is no longer used by the current GUI send path. |
| M8 | Chromium extension session carries selected-tab audio and performs number actions in the same tab | TikTok accepts only the last parsed number from 100–999; automatic sending is selectable with a checkbox, and unchecked mode fills only. The extension uses the same-tab send-button path. Dry-run remains on and F8 is required to arm. This change has not been tested in the GUI or browser. No browser has passed current capture/action acceptance. One user-reported comment appeared without `@` although the input showed `@123`; repeatable rendering and browser compatibility are unresolved. Exact-number accuracy and under-1-second end-to-comment latency are not accepted. Firefox/Safari/mobile and packaged onboarding remain unsupported. See `docs/BROWSER_COMPATIBILITY.md`. |
| M9 | Native Android APK for TikTok audio recognition and optional focused-field typing | Debug APK built with Gradle 8.13, Android SDK 36, and the local Zipformer-VI/Silero models. No Android device is connected; TikTok capture, ASR accuracy, focused-field behavior, and Enter acceptance are unverified. See `docs/ANDROID_APP.md`. |
| P1 Windows installer | PyInstaller one-directory app, NSIS per-user installer, first-run extension guide and local data paths | Rebuilt on 2026-10-22. Executable/model smoke check passed; NSIS produced the installer. The finish-page option launches the setup assistant, including after first run; the user still confirms Load unpacked because this preview is not in a browser store. Installer install/uninstall smoke was not run because a NumberTyper Start Menu folder already exists. No clean-account/browser acceptance, full native/transitive SBOM, or public release clearance. See `docs/SPRINT_P1_WINDOWS_INSTALLER.md`. |

## Optional ASR candidate experiment — 2026-10-22

Added local download and benchmark scripts for Gipformer 1.5 INT8 and a true online Zipformer Vietnamese RNNT (chunk 16). The currently selected Zipformer-VI remains the only app core. Candidate downloads live under ignored `models/`; the streaming weights are CC-BY-NC-ND-4.0 and excluded from installer/release. The benchmark decodes selected intervals from local media in memory, reports number parsing and chunk timing, and never creates a sender.

An earlier run on the user-provided Edge screen recording, 00:07–00:14, gave current Zipformer `[3000, 4000, 5, 6000]` in 134 ms, Gipformer `[6000]` in 156 ms, and streaming Zipformer `[3]` in 367 ms with RTF 0.052. The second paced run is recorded in `docs/ASR_ROBUSTNESS.md` (151/179/388 ms). Streaming began returning partial text at 1.12 s of clip audio, but did not output the full count. The referenced source-video label `[1000, 2000, 3000, 4000]` is not aligned to this screen recording's 00:00–00:07 interval, so neither run has a valid exact-number score. This is exploratory evidence only; it does not support changing the app core or claiming the 0.7–0.8 s target. See `docs/ASR_ROBUSTNESS.md` for commands, detailed output, and the remaining label-alignment requirement.

## Immediate work before relying on live sending

1. Run the suite under Python 3.12 when available. In this workspace, `.venv` uses Python 3.14 and the latest full suite run on 2026-10-22 reports **166 passed**. Python 3.14 satisfies `requires-python >=3.12`, but does not replace the documented Python 3.12 reference environment.
2. Run a labeled local WAV replay with `--dry-run` and collect precision/recall results. The model is present and initializes; the earlier hardware record check passed and its temporary WAV was deleted after format validation.
3. The Playwright fake-page case passed with installed Edge in the M7 checks; no TikTok page was opened.
4. Review §7.2 GUI checklist and test F8/F10.
5. Measure real audio/ASR latency and precision/recall using a labeled WAV before any live use.
6. Record device-specific Android findings for U3, U4, U10 and U14.

The repository does not yet claim full v1 acceptance. The Android user guide and Antigravity guidance in §13–§19 are documentation; they do not establish device or platform compatibility.

## M9 Android APK prototype — 2026-10-23

Added the standalone Kotlin project under `android/`, using MediaProjection playback capture filtered by the TikTok package UID, local sherpa-onnx Zipformer-VI + Silero VAD, a number-first parser port, and an explicitly enabled AccessibilityService that types only into a focused editable node. Dry-run starts on, the app starts disarmed, action failures are not retried, and the service does not read node text/chat/comment content. Native runtime AAR and model weights are excluded from Git; `scripts/fetch_android_runtime.ps1` downloads the pinned sherpa-onnx 1.13.8 AAR and checks SHA-256 before the build task copies local model assets.

`android/app/build/outputs/apk/debug/app-debug.apk` built successfully (161,954,330 bytes; SHA-256 `D4A128D5866E820A643334E08B4F58EA0175A943B102C581870CF67D149E2EA5`). APK inspection confirmed the five required model assets, ONNX Runtime and sherpa JNI libraries for arm64-v8a, armeabi-v7a, x86 and x86_64; unused sherpa C/C++ API libraries are excluded. Permission inspection showed RECORD_AUDIO, FOREGROUND_SERVICE, FOREGROUND_SERVICE_MEDIA_PROJECTION, POST_NOTIFICATIONS and no INTERNET permission. Build output warned that the included native libraries could not be stripped and were packaged as-is. `adb devices -l` found no connected devices, so no install, TikTok audio, ASR, Accessibility input, Enter, accuracy, or latency check was run. Do not treat this APK as device-accepted.

On-device re-review — 2026-10-23: the user screenshot shows the app's “Không mở được TikTok với package ID hiện tại” status. Source review confirms the app hard-codes `com.zhiliaoapp.musically` and `openTikTok()` reports this when Android returns no launcher intent. The actual installed TikTok package/launcher was not queried, so a package mismatch is a possibility, not a confirmed root cause. A fresh SDK `adb devices -l` check listed no device; playback capture, ASR, focused-field typing, and Enter remain untested on the user's phone.

## P1 Windows personal preview — 2026-10-21

The Windows 64-bit build now uses PyInstaller one-directory packaging and an NSIS per-user installer. The installer includes the app/runtime, local Zipformer-VI and Silero VAD resources, Vietnamese Chromium extension popup, first-run guide, Start Menu shortcut, optional Desktop shortcut, and uninstaller. Config, first-run marker, startup/crash logs and runtime logs resolve under `%LOCALAPPDATA%\NumberTyper`; uninstall leaves that user data intact. The extension bridge validates the exact ID computed from the key in its bundled manifest rather than accepting any Chromium extension origin.

Local artefact before the licensing follow-up: `dist/NumberTyper-Setup-0.1.0-preview.exe` (SHA-256 `B48EA7F4FC8E76256083E9C134B4E2D8EF08E62512C7D96F5C745F9558F15C4F`). A new build is recorded later in this section. It is a personal, non-commercial preview. The upstream Zipformer model card says CC BY-NC-ND 4.0; confirm the rights for the exact ONNX release files and complete the transitive dependency SBOM before public distribution, particularly commercial distribution.

### Rebuild and browser setup assistant — 2026-10-22

The NSIS finish page now has an optional **Thiết lập extension trong trình duyệt** checkbox. Selecting it launches `NumberTyper.exe --setup-extension`, which reopens the browser helper even if first-run setup was previously completed. The helper opens the selected browser's extension page and the bundled extension folder together. The browser's **Developer mode → Load unpacked** confirmation remains manual; no browser policy or silent installation is applied.

The app bundle and installer were rebuilt with Python 3.14.5 x64. The build script's packaged executable/model smoke check passed (`SMOKE CHECK OK: local ASR and VAD models loaded`); NSIS produced the installer. Launching the new executable with `--setup-extension` opened a responding window titled `NumberTyper — thiết lập extension trình duyệt`. No browser page or livestream was opened from that window. Installer install/uninstall smoke was not run: the safe smoke script detects an existing NumberTyper Start Menu folder and refuses to overwrite it. This is not a clean-machine install acceptance.

Current local installer: `dist/NumberTyper-Setup-0.1.0-preview.exe` (SHA-256 `AED42DE9BA2D957C9D10E3B88FB09EF8AD2262A2FE2FF19ED2DF76F311434AAD`). The extension ZIP hash remains `7C1402F77A9648F9749580EC50D5536B8E19CAA140ABAADC3BC7BA7669BC95F6`.

Checks actually run:

- `.venv\Scripts\python.exe -m pytest -q` → **154 passed**.
- `node --check browser_extension\popup.js`, `node --check browser_extension\service-worker.js`, and `node --test tests\test_browser_extension_fill_only.cjs tests\test_browser_extension_popup.cjs` → syntax OK; **12 passed**, including the Vietnamese popup status/control case.
- Targeted Ruff lint on changed Python modules/tests → passed; Ruff formatting checks on the new `windows_entry.py` and `runtime_paths.py` → passed.
- PyInstaller build on Windows 11, Python 3.14.5 x64, PyInstaller 6.20.0; bundled executable smoke check from `C:\Windows\System32` loaded Zipformer and VAD successfully.
- First-run wizard and TikTok GUI window titles were opened and closed locally without a browser or sender; app stayed windowed with no PowerShell console.
- `scripts\smoke_installer.ps1` → per-user install, Start Menu shortcut, installed executable/model check from a different working directory, and uninstall cleanup all passed. No existing NumberTyper install/shortcut was present before this check.
- PowerShell parser and Python AST checks passed for the build scripts and PyInstaller spec.

Not run / not accepted: clean Windows account or Windows 10 VM; a browser-store installation; manual Edge/Chrome/Cốc Cốc tab-audio and same-tab action; TikTok Live fill/Enter; ASR accuracy/overlap benchmark; end-to-end comment appearance below one second; signing/SmartScreen; full dependency-license/SBOM audit. The installer is therefore useful as a local personal preview but is not a public store-ready release. See `docs/SPRINT_P1_WINDOWS_INSTALLER.md` and `docs/BROWSER_COMPATIBILITY.md`.

## P1 first-run wizard and extension-store preparation — 2026-10-21

The first-run wizard now detects common Edge/Chrome/Cốc Cốc installation paths, lets the user choose a browser, opens its extension manager, opens the bundled extension folder, and copies that folder path. For an unlisted Chromium browser, the user can select its executable. The wizard clearly states that the current preview still needs manual unpacked-extension loading, and explains that dry-run must be disabled before F8 has an effect. It does not attempt silent extension installation.

Prepared the Chrome Web Store first-submission materials locally: `scripts/package_browser_extension.ps1`, `docs/EXTENSION_STORE_LISTING_VI.md`, and `docs/PRIVACY_POLICY_VI_DRAFT.md`. The package script emits `dist/NumberTyper-Tab-Audio-0.1.0.zip` and checks that the ZIP contains the required MV3 files and no obvious private-key files. The current extension ID derived from the manifest public key is `bjhbdndjhpiakgohbjdpclikllfnecjp`. The package and policy have not been submitted or hosted; the publisher must verify the store-assigned ID before release.

Current local artefacts:

- Installer at first-run update: `dist/NumberTyper-Setup-0.1.0-preview.exe`, SHA-256 `B48EA7F4FC8E76256083E9C134B4E2D8EF08E62512C7D96F5C745F9558F15C4F` (superseded by the licensing follow-up build below).
- Extension ZIP: `dist/NumberTyper-Tab-Audio-0.1.0.zip`, SHA-256 `7C1402F77A9648F9749580EC50D5536B8E19CAA140ABAADC3BC7BA7669BC95F6`.

Checks actually run for this update:

- `.venv\Scripts\python.exe -m pytest -q` → **157 passed**.
- `node --check` for extension popup/service worker and `node --test tests\test_browser_extension_fill_only.cjs tests\test_browser_extension_popup.cjs` → **12 passed**.
- Targeted Ruff lint/format and PowerShell parser checks for both build scripts → passed.
- `scripts\build_windows.ps1 -NsisPath ...\makensis.exe` on Windows 11/Python 3.14.5 x64 → PyInstaller build, packaged ASR/VAD model smoke check, extension ZIP generation, and NSIS installer compilation passed.
- `scripts\smoke_installer.ps1` for this new installer → **not run**: its safety preflight detected a NumberTyper install or shortcut in the current Windows account and refused to overwrite it. The existing install was left untouched. The earlier smoke result above applies to the previous artefact only.

Still open: manual visual review of the updated wizard; installation test on a clean Windows account/VM; publisher account, public privacy-policy URL, store submission/review; live browser capture/action check; full dependency/model license and SBOM review. P0.1 accuracy and the under-one-second comment-appearance target remain unaccepted.

### P1 packaging and license audit — 2026-10-21

The current Windows app entry point uses the Chromium extension bridge, not the legacy desktop-control sender. `DesktopSender` now loads PyAutoGUI only when that sender is actually prepared, and `NumberTyper.spec` excludes PyAutoGUI and its desktop-control dependency group from the Windows app bundle. The source project still retains those legacy sender modules/dependencies. PyInstaller Analysis for the rebuilt app has no PyAutoGUI/MouseInfo/PyMsgBox/PyGetWindow/PyScreeze/Pyperclip/PyRect/pytweening modules. The bundle's analyzed Python components are listed in `docs/THIRD_PARTY_NOTICES.md`.

The refreshed local installer is `dist/NumberTyper-Setup-0.1.0-preview.exe`, SHA-256 `4362B29E28BED3A14FAF69744F577646D3EB3C0DACF2714B40CC991EB3EAEA2D`. It was generated from the new PyInstaller bundle (including the updated notice file) and NSIS script. PyInstaller build completed successfully on Windows 11 / Python 3.14.5 x64. The NSIS installer compiled and was written to `dist/`. The final Analysis scan found 25 package roots and none of the eight excluded desktop-control roots; the bundled notice file was confirmed to be the updated one. PyInstaller emitted unresolved-optional-module warnings for `pycparser.lextab`, `pycparser.yacctab`, and `tzdata`; their effect was not checked.

This was a build only. The rebuilt executable was not launched, the installer was not run, and no tests were run. The previous artifact's startup/install evidence does not automatically apply to this changed package. The license review remains partial: the exact model-file permissions, native linked dependency notices, full runtime license texts, and a complete artifact-derived SBOM are still open. The model license prevents treating this preview as cleared for commercial release.

## M7 TikTok Web/Edge pilot — historical baseline, 2026-10-20

The explicit `gui --tiktok-web` mode uses a dedicated Edge persistent profile with the unpacked tab-audio extension. The extension accepts TikTok Live paths only and sends PCM locally to the existing Zipformer pipeline. The mode starts dry-run/disarmed; its prepare action explicitly leaves dry-run, opens/prepares Edge without arming, and F8 is still required to enable sending. F10 remains the emergency stop. The sender validates the active TikTok host/live URL and the configured visible input before each send. Only finalized ASR events create send decisions; partial text remains preview-only. YouTube mode continues to force `NullSender`.

The `run-tiktok-web.ps1` launcher checks the local Zipformer package and models. `discover --tiktok-web` opens the dedicated Edge profile, allows the user to open a Live page manually, and reads visible input attributes only. No chat contents, comments, credentials, cookies, or recordings are read/persisted. Automated tests remain restricted to the local fake page.

Focused checks at that time: `.venv\Scripts\python.exe -m pytest -q tests/test_pipeline_final_send.py tests/test_browser_tab.py tests/test_senders_fake_page.py tests/test_cli.py` → **15 passed**; `node --test tests/test_browser_extension_popup.cjs` → **4 passed**; `.venv\Scripts\python.exe -m pytest -q` → **137 passed**; `compileall -q src tests` passed. These results predate the M8 changes below. No manual GUI, actual extension-in-Edge, TikTok login, real Live comment submission, or end-to-end latency test was run. Under-1-second comment appearance and ASR price accuracy are not established.

## M8 Chromium bridge — fill-only baseline, 2026-10-20

The TikTok GUI now creates a `BrowserExtensionSender` bound to the same `BrowserTabSource` session that delivers audio. The extension reports a Chromium family marker and selected tab ID/host/path. The local bridge can send a probe or numeric draft-fill request back over that same WebSocket; the extension verifies the active tab is still the same TikTok Live host/path and fills only when exactly one configured visible input matches. If the extension session disconnects after preparation, the GUI disarms, returns to dry-run, and replaces the sender with `NullSender`. The fill-only action does not dispatch Enter, click a submit button, or accept a `send` action.

The extension fill acknowledgement means the browser ran the fill action; it does not establish that the ASR number was correct. A non-empty input is left untouched and reported as an error. A user screenshot from Cốc Cốc (browser version unknown) shows a TikTok Live tab, the bridge connected, recognized speech visible in the app, and the earlier input probe failing with `No visible chat input matched the configured selectors.` The default selector now includes editable contenteditable elements, role textboxes, text inputs, and textareas; the probe error reports visible input attributes only. A later user screenshot showed `60` in the input and a reported ~2 second delay, but the run was not controlled and did not establish that a comment was submitted or appeared. This patch has not yet been retested in the user's browser. Cốc Cốc, Chrome, and Edge remain unaccepted until the current capture/probe/fill path is checked. The local bridge still accepts a Chromium extension-origin pattern rather than a published PriceTyper extension ID; lock it to the official identity and review IPC authentication before distribution. Store installation/onboarding, Firefox/Safari, mobile, exact-number accuracy, and end-to-end fill latency remain unfinished.

Checks run for the fill-only change: `node --check browser_extension/service-worker.js` and `node --check browser_extension/popup.js` passed; `node --test tests/test_browser_extension_fill_only.cjs tests/test_browser_extension_popup.cjs` → **7 passed**; `python -m py_compile` for the changed Python modules passed; `python -m compileall -q src tests` passed; full `python -m pytest -q` → **137 passed**. The new bridge regression confirms draft fill emits no click/submit-key event, rejects the `send` action, and leaves a non-empty input untouched.

Not run: manual GUI/extension acceptance, browser tab audio/fill, any TikTok interaction, and labeled ASR/latency benchmark. No action was dispatched to TikTok during development. The user-reported ~2 second observation is not controlled. The GUI timing begins at the chunk that closes VAD and excludes the VAD trailing-silence wait (configured at 250 ms); it is not a measure of last spoken syllable to filled input. Do not claim the ≤700 ms target or exact-number accuracy until labeled timing and accuracy are measured separately. The stale pre-change PriceTyper window was closed so it cannot keep running its older submit-capable code; reload the extension and relaunch the app before trying the fill-only version.

## M8 number-first and opt-in submit update — 2026-10-20

TikTok Web decisions now use number scope rather than the price gate, so a finalized `SỐ CHÍN` can produce `9` even though the general price minimum is 1,000. A clearly ascending spoken count is split into individual numbers; the last number in a finalized ASR event is the action candidate. The app UI is branded NumberTyper in this workflow.

The TikTok extension remains fill-only by default. After the selected Live tab and one visible input pass the probe, a disarmed-only checkbox can opt into submitting: the extension fills the number, verifies that the input contains that number, and dispatches one Enter keydown. A non-empty input is refused. No action is retried. The bridge reports Enter dispatch as `send_unverified`; it cannot verify that TikTok accepted or displayed the comment because the app does not inspect chat.

Checks run for this update: Python `py_compile` for changed modules passed; `node --check browser_extension/service-worker.js` passed; `node --test tests/test_browser_extension_fill_only.cjs tests/test_browser_extension_popup.cjs` → **9 passed**; focused pytest for number decisions, final-only pipeline, and extension sender → **9 passed**; full `.venv\Scripts\python.exe -m pytest -q` → **142 passed**. Automated tests used mocks and the local fake page only; no TikTok page or comment action was used.

Follow-up GUI launch check: `.venv\Scripts\python.exe -m pricetyper gui --tiktok-web` opened a responding window titled `NumberTyper — TikTok Web · Zipformer-VI` (2026-10-20). The window was left open in its default dry-run/disarmed state; no browser tab was connected and no comment action was attempted. This proves startup/model initialization on this workstation only, not live capture or sending.

Not run: loading the updated extension in Edge/Cốc Cốc/Chrome, manual fill/Enter check, labeled accuracy benchmark, and end-to-end latency benchmark. The prototype does not meet or guarantee comment appearance under 1 second. The current offline Zipformer emits a final only after VAD closes the utterance (250 ms configured trailing silence), then inference and local browser action add time; TikTok/network delivery is outside local control. Sending earlier from partial results could reduce waiting but risks sending a number that later changes, so it remains disabled. Exact-number quality under music, accent variation, and overlapping voices still needs labeled data.

## P0 YouTube recognition prototype

| Item | Status | Evidence |
|---|---|---|
| Python tab-audio bridge | Implemented; unit checked | `BrowserTabSource` binds to `127.0.0.1`, accepts only the extension Origin and fixed 40 ms PCM16 frames, and uses a bounded queue. The protocol tests pass. |
| Browser capture extension | Implemented; regression checked; browser acceptance not run | A reported popup error came from reading `chrome.tabCapture.getMediaStreamId()` as an object; Chrome returns a stream-ID string. The popup now forwards that string and reports an actionable error for an empty ID. `node --test tests/test_browser_extension_popup.cjs` passes (2 tests); JavaScript syntax and manifest JSON checks pass. Real-browser capture still needs a manual retest. |
| Primary recognition engine | Implemented; local unit/smoke checks pass; live speech unverified | Zipformer-VI INT8 is now the default local engine for app, replay, and YouTube test. Silero VAD segments audio; active speech is periodically re-decoded for provisional text. Vosk stays available as a benchmark baseline or explicit `asr.engine: vosk` option. `pytest -q`: 122 passed, 1 skipped. Loaded local Zipformer/VAD and processed 2 seconds of synthetic silence with no transcript event. This is integration evidence, not evidence that Zipformer is more accurate on the user's livestream samples. |
| Recognition-only GUI | Number-first behavior implemented and unit checked; live-tab acceptance remains unverified | `gui --youtube-test` forces `browser_tab`, disarmed state, and `NullSender`; it now displays parser numbers without the price gate or currency formatting. Send controls and F8/F10 are unavailable in this mode. The currently running process predates this UI change and must be restarted to show the new title/labels. |
| PowerShell prototype launcher | Updated; launch not run | `run-youtube-test.ps1` checks sherpa-onnx and local Zipformer/VAD files; it checks Vosk only for the optional comparison benchmark. |
| Spoken-number recognition from YouTube | Qualitatively failed on earlier samples | The user identified [YouTube video IYH-W2ZK6kk](https://www.youtube.com/watch?v=IYH-W2ZK6kk) as the source used for testing and reported that from beginning to end only some words were correct and most were wrong. One recurring confusion was spoken `một` recognized as `mộ` or `mã`. An earlier screenshot showed `Bridge đã kết nối`, PCM RMS `2492.7`, finalized text `âm ô đỏ qua ta áo cháy`, and partial text `máu mồm messi`. This confirms non-silent PCM reached the app in that run and records qualitative ASR failures, but there is no timestamped ground-truth transcript to calculate WER or exact-number accuracy. The video page could not be fetched from the inspection environment. Older session logs also contain `audio_silent` events. A labeled comparison is still required before making accuracy claims. |
| Local raw/denoised ASR benchmark | Harness implemented; one labeled overlap sample measured; P0.1 not accepted | The benchmark compares raw/DPDFNet with Vosk, faster-whisper `small`, and Zipformer-VI 30M INT8. A 2-second segment from the user's local YouTube screen capture was evaluated in RAM with the user's labels `[2000, 3000]`, `overlap`, accent unknown, and number-only scoring. All six model/branch outputs missed both expected numbers; raw Zipformer also produced one false number (`3`). Strict preview abstained as required for a manually labeled overlap. Full results and timing/RAM caveats are recorded below. One segment is not a representative corpus and cannot establish P50/P95 or robustness. |
| Output-volume independence and no-send/manual audio check | Not run | Requires the manual browser/audio workflow in `docs/PROTOTYPE_YOUTUBE.md`. |

Prototype checks from the earlier workspace run: `pytest -q` reported **102 passed, 1 skipped**, with **44 parser cases** at that time; those counts predate the explicit benchmark labels and shorthand parser additions below. The current regression suite is re-run and recorded in the latest change report. These checks do not establish accuracy on YouTube audio or the 0.7–0.8 second comment-appearance target.

Latest Zipformer-engine update: `.venv\Scripts\python.exe -m pytest -q` reports **122 passed, 1 skipped**; focused Ruff checks for the new ASR engine/tests pass; `compileall -q src tests` passes; PowerShell parser accepts `run-youtube-test.ps1`. A local 2-second synthetic-silence smoke check loaded Zipformer/VAD and emitted no transcript. The separate price gate still defaults to 1,000₫; number-first YouTube preview does not use it.

### Number-first UI correction — 2026-10-20

The user screenshot showed finalized ASR text `SỐ CHÍN` but no displayed value. `parse_all("SỐ CHÍN")` produces `9`; the YouTube GUI had displayed only spans accepted by the price gate. In the screenshot, the minimum was already set to 1, so the decisive rejection was the gate's previous-token exclusion for `số`; with the default 1,000 minimum, that threshold would reject it as well. The pipeline now has a number preview scope that displays the latest raw parsed value without price min/max, context, countdown, or anchored-price filtering. The YouTube UI is titled NumberTyper, labels values as numbers, removes the price-bound fields, and shows no currency symbol. The normal price gate, decider, and sender path remain separate; YouTube still forces `NullSender` and disarmed mode.

Checks for this update: focused parser/pipeline/display tests **60 passed**; full `.venv\Scripts\python.exe -m pytest -q` **124 passed, 1 skipped**; `compileall -q src tests` passed. Ruff reported seven pre-existing broad-exception/empty-handler findings in unchanged code; no new lint-specific edits were made. The updated GUI was not relaunched or visually verified, and no new live audio was benchmarked. The earlier screenshot confirms the ASR phrase for that instance, not broader number-recognition accuracy.

The launcher and GUI process were started after the VAD fix. CUA exposed only the Codex in-app browser; `edge` was unavailable for direct inspection/control. The app bridge listened at `127.0.0.1:8765` and its log recorded one `audio_start` at 14:09:58 +07, so at least one chunk arrived through the extension path. No ASR partial/final was logged; a later socket check showed no active extension client. The chunk's speech/RMS level and selected-tab identity could not be checked. Therefore live speech recognition, output-volume independence, and no-send behavior remain unverified. Do not use TikTok or enable sending for P0.

### Spoken counting sequence regression — 2026-10-20

For the user-provided transcript `số chín và một hai ba bốn năm sáu bảy tám chín`, the default parser previously grouped the spoken sequence as `1234` and `5678`; although its last candidate was `9`, intermediate number-preview values were wrong. Number preview now opts into splitting a consecutive ascending sequence beginning with `một` into individual spans, so this case yields `[9, 1, 2, 3, 4, 5, 6, 7, 8, 9]` and displays the latest candidate `9`. The default price parser stays unchanged, preserving its digit-by-digit shorthand conventions. A labeled audio/ASR run of this transcript has not been performed; this regression verifies parser and pipeline behavior only.

Checks for this update: full `.venv\Scripts\python.exe -m pytest -q` **127 passed, 1 skipped**; `compileall -q src tests` passed; Ruff E/F checks passed with E501 excluded for pre-existing long lines in the parser; format check passed for the already-formatted GUI/pipeline/display/log-test files. A whole-file Ruff format check on the legacy parser/parser-test files would rewrite many existing lines, so those files were left unformatted. No live YouTube capture or audio/ASR benchmark was run.

## M8 audio overload and long-speech stability — 2026-10-20

The user reported that TikTok tab input stopped after about 10 seconds and shared a Sherpa warning: its 320,000-sample circular buffer (20 seconds at 16 kHz) reached capacity; the warning itself says the original data was copied and no data was lost. Review of the earlier app session `session-20261020-222041.jsonl` found 382 pipeline `audio_overflow` events over about 44.5 seconds, with only one `audio_start` and no ASR/error events. That log supports sustained ASR queue backlog, but does not prove the browser capture disconnected or establish that this was the same run as the screenshot.

The TikTok Zipformer path now disables repeated partial re-decodes, bounds an open VAD segment at 12 seconds, and emits any forced segment as preview-only. If the app audio queue fills, it clears stale chunks, advances the audio generation, disarms, resets ASR at the next generation, and suppresses the first final after the gap. This preserves fresh audio while refusing a send decision derived from a broken transcript. A regression also verifies the long-buffer cap when the VAD activity flag has already cleared.

Checks run: full `.venv\Scripts\python.exe -m pytest -q` → **148 passed**; `py_compile` passed for all changed Python modules; targeted Ruff lint passed; Ruff format check passed. No Edge/TikTok/browser capture retest was performed, so the user's approximately 10-second symptom is not yet accepted as fixed. The app must be restarted to load these Python changes. The 12-second forced segment remains preview-only and cannot produce a send action.

## M8 visible runtime health warnings — 2026-10-20

The GUI now displays a dismissible in-app banner for tab capture disconnects, browser-bridge or ASR queue audio gaps, 30 seconds without an audio signal, and pipeline/sender errors. Audio gaps clear stale queued chunks, advance the ASR generation, disarm, and leave the first final after the gap preview-only. A recovered bridge is reported as reconnected but remains disarmed. Sustained silence clears its banner when signal returns. Pipeline worker failures show an error banner and a stopped status instead of appearing to remain in the listening state. Warnings are rate-limited per gap reason to keep a long session's UI readable.

Checks run: focused pipeline and BrowserTabSource tests → **13 passed**; full `.venv\Scripts\python.exe -m pytest -q` → **150 passed**; `py_compile` passed; targeted Ruff lint and format checks passed. No manual Tk window, Edge extension disconnect/reconnect, or four-hour soak test was run. This feature informs the user; it does not automatically reconnect a browser extension or establish four-hour uptime.

## P0.1 ASR robustness

| Item | Status | Evidence |
|---|---|---|
| Vietnamese accents, music/noise, and overlapping speakers | Raw/DPDFNet + Vosk/Whisper/Zipformer benchmark harness implemented; one overlap sample measured; robustness not evaluated or accepted | See `docs/ASR_ROBUSTNESS.md` and the run record below. There is still no labeled corpus across Northern/Central/Southern accents and clean/music/noise conditions. No automatic overlap detector or validated accuracy/false-emission target exists. One sample cannot support P50/P95 or real-time claims. |

### P0.1 run record — 2026-10-20

The post-fix live-browser retest remains incomplete. CUA lists only the Codex in-app browser and Codex MCP Apps, although an Edge process is running with a YouTube title. The app process has the Zipformer title and its bridge listens at `127.0.0.1:8765`. A new session log recorded one `audio_start` at 14:19:47 +07, indicating a frame arrived through the extension path, but no ASR partial/final was logged; the client was no longer connected at inspection. The chunk's speech/RMS level and selected-tab identity could not be checked, so this does not pass live speech or tab-specific acceptance. The earlier 14:09:58 +07 `audio_start` was likewise only a connection/frame indication.

A new labeled sample is pending capture: YouTube `Xx-pt9WH5p0`, 00:00–00:07, expected numbers `[1000, 2000, 3000, 4000]`, accent unknown, no music, with a second voice reported. Whether the voices overlap is unspecified. No result is recorded for this sample because the Edge tab is not exposed to CUA and no complete in-memory capture reached the benchmark. Do not count this as an evaluated segment.

The local, user-provided YouTube screen recording was decoded in memory and only its recording-offset 00:06–00:08 segment was passed to the local benchmark. The user had identified this short passage as “hai nghìn, ba nghìn” with a second voice saying “rồi, rồi”; the label used was numbers `[2000, 3000]`, overlap, accent unknown, number-only. Since the complete word sequence is not labeled for overlapping speech, WER/CER was not used. Audio was neither saved nor uploaded; no sender was constructed.

| Branch / model | Transcript | Parsed numbers | Exact labels | Missed | Extra | ASR ms | Enhancement ms |
|---|---|---:|---:|---:|---:|---:|---:|
| Raw / Vosk | `rồi` | — | No | 2 | 0 | 1480.2 | 0 |
| Raw / Whisper small | `Nói` | — | No | 2 | 0 | 2273.6 | 0 |
| Raw / Zipformer-VI | `RỒI BA MẸ` | 3 | No | 2 | 1 | 51.9 | 0 |
| DPDFNet / Vosk | `rồi` | — | No | 2 | 0 | 151.4 | 131.7 |
| DPDFNet / Whisper small | `Nói` | — | No | 2 | 0 | 2198.4 | 131.7 |
| DPDFNet / Zipformer-VI | `RỒI` | — | No | 2 | 0 | 54.6 | 131.7 |

All six rows were 0/1 exact for this segment. The strict preview abstained on the overlap label. Model load times for this invocation were Whisper 1470 ms, Zipformer 826 ms, DPDFNet 77 ms, and Vosk 449 ms. Process working set was 578.7 MiB after model load and 693.6 MiB after comparison; peak working set was not recorded. These are one-process, one-sample measurements, not app-wide memory acceptance. Inference was performed after capture had stopped; these per-segment times are not live speech-to-candidate latency. P50/P95 are not reported for a single segment.

## M8 TikTok input selector refinement — 2026-10-21

The user supplied TikTok's visible chat-field markup, including `data-e2e="room-chat-input-field"` and `contenteditable="plaintext-only"`. The extension sender now tries that specific selector before generic editable controls. The extension evaluates selectors in order: it uses the first selector with one visible editable match, refuses if that selector has multiple matches, and only falls back when a more specific selector has no visible match. This avoids a generic editable field elsewhere on the page making a known chat input ambiguous. Probe still does not read input values or comment/chat history.

Checks run: `.venv\Scripts\python.exe -m pytest -q` → **150 passed**; `.venv\Scripts\python.exe -m pytest -q -rs tests/test_senders_fake_page.py` → **4 passed**; `node --check browser_extension/service-worker.js` passed; `node --test tests/test_browser_extension_fill_only.cjs tests/test_browser_extension_popup.cjs` → **11 passed**; targeted Ruff check and format check passed. The selector cases use fake DOM/protocol evidence only. No live TikTok/browser probe, audio capture, draft fill, Enter dispatch, ASR accuracy, or latency check was run. Installer/onboarding and sub-1-second comment appearance remain unaccepted.

## P0.1 number-constrained Vosk feasibility check — 2026-10-21

An initial in-memory experiment compared unrestricted Vosk against a manually constructed 622-phrase Vosk grammar on the user-provided recording offset 00:06–00:08. Both missed both numbers. It was not an app integration or acceptance run; the integrated follow-up is recorded below.

### Benchmark-only integration follow-up — 2026-10-21

Added `Vosk số` as an optional fourth lane in the YouTube ASR comparison window. It shares the Vosk acoustic model with the unrestricted baseline, uses a generated finite grammar for common readings 1–20, contiguous counting sequences, and phrases with `nghìn`/`rồi`, and is scored on both raw and DPDFNet audio. It is excluded from the three-core-model consensus. Zipformer remains the app's configured primary engine. The live/TikTok sender path is unchanged.

The same in-memory 00:06–00:08 overlap segment with labels `[2000, 3000]` was re-run with the final 1,341-phrase grammar. It produced: Vosk `rồi`, no numbers, 1295.9 ms; Vosk number grammar `rồi`, no numbers, 31.0 ms; Zipformer `RỒI BA MẸ`, parsed `[3]`, 44.2 ms. Model and recognizer setup are excluded from these inference measurements. All three miss the two expected labels; Zipformer also has one extra parsed candidate. One segment is not a valid latency distribution or accuracy claim. Audio was not written to disk.

Checks: .venv\Scripts\python.exe -m pytest -q → 161 passed; focused ASR comparison tests passed (19 tests); Ruff check passed; compileall -q src tests passed; Ruff format check passed for the new Vosk engine/grammar files. No TikTok/live interaction or send action was run.

## M8 GUI refresh freeze after successful fill — 2026-10-22

The reported symptom was that `Nghe được` and the tab RMS meter stopped refreshing after F8 enabled number filling, while a recognized number could still be filled. Code review found a deterministic UI failure path: a successful draft event includes `error=None`, but the Tk poll called `.startswith()` on that value. The callback then exited before scheduling its next poll, leaving the ASR/audio indicators and displayed state stale while pipeline workers continued. The local session log showed successful draft events followed by later pipeline decisions, which is consistent with a stopped UI poll; it does not provide a captured Tk exception traceback.

The UI now treats absent/None error text as an ordinary successful draft, keeps the poll callback scheduled even if one UI update fails, logs and shows the error, and disarms on an unexpected polling exception. Regression tests cover None error text and the unverified-Enter marker. This does not stop audio/ASR on F8; it keeps recognition independent from the action toggle.

Checks run: full `.venv\Scripts\python.exe -m pytest -q` → **170 passed**; focused GUI, pipeline logging, and extension-sender checks → **15 passed**; Ruff formatting passed; Ruff `E/F/I` checks passed with the repository's existing `E501` long-line exclusions. A broader check of `gui.py` still reports 10 pre-existing `BLE001`/`S110` findings elsewhere in that module. The updated separate executable passed `--smoke-check` (exit 0; local ASR/VAD loaded), and NSIS built `dist/NumberTyper-Setup-0.1.0-preview-ui-fix.exe` (SHA-256 `B3B6BC1908B58B9E31A32AC8895FD1670AD47BB503F352343019457E77A74334`). The installer was not run over the currently active app/browser session. No live TikTok/extension session was manipulated for this fix. Manual verification with the user's browser remains needed; the running older executable must be restarted to load the fix.


## M8 automatic TikTok submit and tab-audio liveness — 2026-10-24

The user screenshot showed that the previous synthetic Enter left `@<number>` in TikTok's input instead of submitting it. The user supplied the exact send-control selector `[data-e2e="room-chat-send-btn"]`. Submit mode now verifies `@<ASCII digits>` in the selected input and clicks exactly one visible, enabled instance of that control near the input; it does not send a synthetic Enter or retry. If the control is missing or ambiguous before filling, the action is rejected without changing the input. The GUI keeps submit selected after a successful tab probe, but actions still require dry-run off and F8. The click acknowledgement is not proof that TikTok displayed the comment.

The customer additionally reported that voice stops after about five minutes while the app remains open. Source review found no five-minute timer. The existing code disarms on a disconnected bridge, audio queue overflow, an ASR stall during active speech, or three sender failures. It did not detect the separate condition where the WebSocket remained connected but PCM chunks stopped. The source now marks audio stale after two seconds without chunks; the GUI reports an audio gap, resets ASR, disarms, and instructs the user to restart capture. It never re-arms automatically. The extension also stops and reports capture if its tab-audio track ends. The reported five-minute event was not reproduced, so the underlying browser/device cause remains unknown.

Checks run: Node syntax checks passed for `service-worker.js` and `offscreen.js`; the fake DOM submit tests passed (**2 passed**), including one exact button click and refusal when duplicate send controls are visible; `.venv\Scripts\python.exe -m pytest -q tests\test_browser_tab_audio_stall.py` passed (**1 passed**); `compileall` passed. No current TikTok/browser capture or submit check has been run. The development app was restarted with `run-tiktok-web.ps1` and its NumberTyper window is running. The code and status were pushed to `origin/master` in commits `ef52c67` and the follow-up status commit.
