# TikTok Web prototype — Chromium extension bridge

This is an experimental Windows desktop mode, separate from the YouTube number-recognition test. The extension supplies audio from the selected tab and performs number actions in that same tab. TikTok is number-first: it bypasses price minimum/context filters, splits a clear count sequence, and considers the last number in finalized ASR text. Partial ASR is display-only. Each TikTok chat action prefixes the recognized value with `@` (for example, `122` becomes `@122`); the app's recognition display remains numeric. TikTok mode preselects automatic Enter submission after the tab is probed; uncheck it to fill only. The app remains disarmed until F8. This removes the former second, dedicated Edge/Playwright profile from the GUI path. The code uses Chromium extension APIs; Chrome, Edge, and Cốc Cốc are not accepted browser combinations until each is manually checked. See `BROWSER_COMPATIBILITY.md` for evidence and unsupported browsers.

The local NumberTyper app runs Zipformer-VI and the number pipeline. Captured audio stays in memory and is not uploaded. TikTok mode starts dry-run and disarmed. It skips repeated Zipformer partial re-decodes to reduce load on the live audio queue. If VAD stays open for 12 seconds, the engine flushes/resets it; that forced segment is preview-only and cannot trigger a comment. The extension action checks that the connected tab remains on the same TikTok Live host and path, and uses ordered selectors that refuse to guess when the selected selector matches more than one visible input. The extension does not read comments or chat history.

## Start the prototype

Run the app from the project folder:

```powershell
.\run-tiktok-web.ps1
```

In a Chromium browser with the extension loaded, open a user-selected TikTok Live page (`/@username/live`), click the NumberTyper extension, and choose **Start capture from this tab**. The app should show that the audio bridge is connected. Click **Kết nối tab TikTok đang nghe** to probe the visible input in that same tab. The default first tries TikTok's specific `[data-e2e="room-chat-input-field"]` selector, then falls back to editable contenteditable elements, textboxes, text inputs, and textareas in that order. It accepts the first selector with exactly one visible editable match; if a selector matches several, it refuses to guess and reports only visible controls' tag and input attributes (never their values or chat content). This selector refinement is covered by local extension tests; it still requires an interactive browser check before claiming TikTok compatibility.

The connect/probe button leaves dry-run, but does not arm actions. Automatic Enter submission of `@<number>` is selected by default; uncheck **Tự gửi comment bằng Enter sau khi nhận số cuối câu** while disarmed to use fill-only mode. Press **F8** to arm; press F8 again to disarm; **F10** is emergency stop. Checking dry-run replaces the sender with `NullSender` and turns submit mode off. If the input is non-empty, the app refuses to overwrite or submit it. After inserting text, the extension yields once to pending page updates and verifies the exact `@<number>` remains in the input before dispatching one Enter event. It does not verify that TikTok displayed the same text.

## Important limits

- A fill acknowledgement only confirms that the extension ran the fill action. In submit mode, the app dispatches a synthetic DOM `KeyboardEvent` (`isTrusted` is false); TikTok may ignore it. The app cannot verify that TikTok accepted or displayed the comment because it does not read chat. Check manually on a permitted test page before relying on it.
- The Windows personal preview is packaged with a first-run setup wizard and per-user installer. The extension still must be loaded manually because there is no store listing; the wizard can open the chosen browser's extension manager and the bundled extension folder.
- The local bridge validates the exact Chromium extension ID derived from the bundled manifest public key (`bjhbdndjhpiakgohbjdpclikllfnecjp`). A store submission must preserve and verify this ID before release. This origin check is not user authentication; the bridge remains loopback-only and is intended for the local preview.
- The bridge currently accepts the Chromium extension origin and uses Chromium `tabCapture`/`scripting`. Firefox, Safari, mobile browsers, Brave, Opera, and Vivaldi are not accepted or claimed as supported until their exact audio and same-tab actions pass checks.
- A legacy `discover --tiktok-web` command is no longer used; the GUI probes the captured tab directly.
- This prototype is not accepted for exact-number accuracy or end-to-end latency. The GUI timing begins at the audio chunk that closes VAD; it excludes the trailing-silence wait and does not represent time from the last spoken syllable. The user-reported ~2 second observation is not a controlled benchmark. The goal is comment appearance under 1 second from the end of the number, but TikTok/network delivery is outside the app's control and cannot be guaranteed. Measure local end-to-action latency separately from exact-number accuracy; neither is accepted yet.
- Automated sender tests must use `tests/fixtures/fake_live.html`, never a real livestream. No real TikTok page is a test fixture.
