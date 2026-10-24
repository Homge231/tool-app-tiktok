# PriceTyper browser compatibility

Updated: 2026-10-24

## Product target

The requested target is a desktop app that works with the browser the user already uses. “Universal” means browser-independent ASR/parser/controller code plus browser-specific capture and input-action adapters. It does not mean every browser automatically supports identical tab-audio APIs. A browser is supported only after NumberTyper can capture the exact user-selected TikTok Live tab, preserve playback, deliver PCM to the local pipeline, and perform the configured number action in that same Live tab. After a successful probe, the user chooses continuous fill-only replacement or automatic submit; submit is preselected. Dry-run remains enabled before preparation and actions remain disarmed until F8. Unsupported combinations must be reported clearly; do not fall back to a microphone or system-wide mix and call it tab capture.

## Current code and evidence

### TikTok submit control — 2026-10-24

The user reported that a prior synthetic Enter left `@<number>` in the chat input without submitting it, and supplied TikTok's send-control markup: `[data-e2e="room-chat-send-btn"]`. The extension now looks for one visible, enabled instance near the selected input, fills and verifies `@<number>`, then clicks the control once. If it cannot identify exactly one control, it leaves the input unchanged. A local DOM regression test covers one click and the ambiguous-control case. This is fake-page evidence only; no current TikTok/browser submit check has been run, so support remains unaccepted.

### User-reported manual check — 2026-10-23

The user reports that a comment appeared with the recognized number, while the input contained `@123` before submission and the displayed comment omitted `@`. The user also supplied a screenshot showing a separately entered `@1` displayed in that TikTok Live chat. This confirms the chat can display `@1` but does not establish what text the page submitted from NumberTyper's synthetic input/Enter path. Browser, app, and extension versions were not recorded. The requested `@<number>` rendering through NumberTyper remains unresolved; this does not pass any browser/OS compatibility row below.

| Browser / family | Current status | Work needed before claiming support |
|---|---|---|
| Microsoft Edge on Windows | The current GUI has a Chromium extension bridge and same-tab fill/submit-button path. The former M7 Edge/Playwright profile remains legacy code. No current Edge extension/audio/action check has been manually accepted. | Load the updated extension and verify selected-tab audio, probe, replacement of a numeric draft in fill-only mode, and automatic submit; record exact version and results. |
| Google Chrome on desktop | The current GUI has a Chromium extension bridge and same-tab fill/submit-button path. No current Chrome extension/audio/action check has been manually accepted. | Load the updated extension and verify selected-tab audio, probe, replacement of a numeric draft in fill-only mode, and automatic submit; record exact version and results. |
| Brave, Vivaldi, Opera, and other Chromium browsers | The extension uses Chromium APIs, but these products and their extension policies are not tested or accepted. | Test each browser/version and its extension-install path. Add an explicit support entry only after checks pass. |
| Cốc Cốc on Windows | User-reported attempt: the extension bridge connected on a TikTok Live tab and the app showed recognized speech; a screenshot later showed a number in the chat input, with an uncontrolled reported delay around 2 seconds. Browser version is unknown, the exact send-button click has not been manually verified, and comment submission was not confirmed. This is not a compatibility pass. | Retest the updated build and verify selected-tab audio, probe, replacement of a numeric draft in fill-only mode, and automatic submit; record exact version and results. |
| Mozilla Firefox | Not supported. Firefox WebExtensions are broadly compatible with Chromium extensions, but the documented `tabs.captureTab()` API returns an image, not tab audio; the current extension also depends on Chromium MV3 `tabCapture`/`offscreen`. | Prototype a separate audio-capture adapter. `getDisplayMedia()` may return an audio track only when the selected surface/browser/OS provides one; verify the track is from the selected tab before considering it an acceptable fallback. |
| Safari on macOS | Not supported. Safari Web Extensions require their own packaging/distribution path, and this project has no tested Safari tab-audio adapter or macOS app. | Build a macOS companion/extension adapter and validate tab audio and same-tab sender end to end. |
| Mobile browsers or embedded in-app browsers | Not supported by the desktop M7 pilot. | Separate mobile milestone and platform-specific acceptance; do not infer support from desktop browser-extension support. |

## Why there is no universal fallback today

The current capture path uses Chromium `tabCapture`: the user invokes the extension for the active tab, then the extension passes a tab media stream to the local app. For TikTok, the same extension connection carries an action request back to that tab. The app records only the tab ID, host, and path needed to bind capture and action; it does not read comments or chat history. Firefox’s documented `tabs.captureTab()` captures a still image. The standard Screen Capture API can request audio, but the returned stream may omit audio depending on browser, selected surface, and operating system; its permission must be granted through a user interaction for each capture. That does not yet meet PriceTyper’s requirement for reliable, selected-tab audio.

ASR/parser keeps the spoken number as a raw numeric value. In fill-only mode, the current extension continuously replaces an empty input or an existing draft made only of ASCII digits with an optional `@` by the plain digits; it leaves arbitrary text untouched. Submit mode requires an empty input, formats the number as `@<number>`, verifies that exact text, and clicks one visible `[data-e2e="room-chat-send-btn"]` in the input's nearby container. The exact input selector `[data-e2e="room-chat-input-field"]` remains first; the extension refuses multiple visible input matches and refuses multiple visible send controls. The click acknowledgement does not prove TikTok accepted or displayed the comment, and browser support must not be inferred from the fake DOM test alone. A customer also reported that tab voice stopped after about five minutes while the app remained open; there is no five-minute timer in the current code, and the cause is not yet confirmed. A two-second missing-PCM watchdog now disarms/resets ASR and shows a warning if the bridge stays connected without audio chunks.

## M8 acceptance outline

1. Keep the local Zipformer/VAD/parser/decision pipeline shared across browser adapters.
2. Detect the connected Chromium extension session and report capture/send capabilities; report unsupported for adapters not implemented.
3. Keep capture user-initiated and tab-specific; audio remains local and in memory.
4. Ensure the action adapter targets the same user-selected TikTok Live tab that produced audio; validate host/path, unique visible input and unique send button immediately before acting. After probe, let the user select continuous fill-only replacement or automatic submit; actions require dry-run off and F8.
5. Use fake pages for automated sender checks. For each browser/OS claimed as supported, record a separate manual extension/audio-bridge check and fake-page test. Never use a real livestream as an automated fixture.
6. Keep all modes disarmed by default, keep YouTube test mode on `NullSender`, do not retry failed actions, and retain F8/F10 safety behavior.
7. Do not claim exact-number accuracy or under-1-second comment appearance from browser compatibility tests. Measure local last-syllable-to-send-button-click latency separately on labeled audio; observe comment appearance manually without reading or scraping chat.

## References

- [Chrome `tabCapture` API](https://developer.chrome.com/docs/extensions/reference/api/tabCapture)
- [Microsoft Edge extension API support](https://learn.microsoft.com/en-us/microsoft-edge/extensions/developer-guide/api-support)
- [Mozilla WebExtensions overview](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions)
- [Mozilla `tabs.captureTab()` API](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/tabs/captureTab)
- [Screen Capture API `getDisplayMedia()`](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getDisplayMedia)
- [Apple Safari Web Extensions](https://developer.apple.com/documentation/safariservices/safari-web-extensions)
- [Playwright browser support](https://playwright.dev/docs/browsers)
