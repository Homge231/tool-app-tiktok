# YouTube recognition prototype

## Purpose

Validate Vietnamese speech recognition and spoken-number extraction before any later integration. The YouTube prototype listens to the user-selected tab, shows the transcript and parsed numeric value, and never sends a message. Number mode displays values without currency symbols or price filtering; `nghìn`, `ngàn`, or `k` still express their numeric multiplier (for example `một nghìn` → `1000`).

## Audio path

1. The user opens the YouTube video in Chrome or Microsoft Edge and clicks the PriceTyper capture extension to start/stop capture for that tab.
2. The extension captures that tab's digital audio stream. It must not read the microphone or the PC-wide speaker mix.
3. The extension preserves playback to the user's headphones/speakers while forwarding mono 16 kHz PCM locally to the Python process.
4. Zipformer-VI transcribes local speech segments; Silero VAD ends a segment after a pause. While speech continues, the app periodically re-decodes the current segment for a provisional partial transcript. The Python GUI keeps finalized text and provisional partials separate. It also shows bridge connectivity separately from the latest PCM RMS level; a connected bridge alone does not prove that non-silent audio is arriving.

The bridge listens only on `127.0.0.1:8765`, accepts one extension-origin WebSocket at `/audio`, and accepts fixed 40 ms PCM16 chunks. The in-memory queue is bounded and drops its oldest chunk if it falls behind. Audio is not written to disk.

## Compare raw/denoised audio and local ASR models

The optional comparison mode runs Vosk, offline Whisper, and Vietnamese Zipformer-VI on the same short segment captured from the selected tab. Each engine receives both the original PCM and a DPDFNet-enhanced copy. This benchmark does not change the default Zipformer-VI recognition path. DPDFNet suppresses some noise; it is not music removal or speaker separation.

1. Install the optional local ASR dependency once:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -e ".[robust-asr]"
   .\.venv\Scripts\python.exe scripts\download_robust_asr_models.py
   ```

2. Launch comparison mode:

   ```powershell
   .\run-youtube-test.ps1 -AsrCompare
   ```

   Or run `.\.venv\Scripts\python.exe -m pricetyper gui --youtube-test --asr-compare` directly. The default Whisper model is multilingual `small`, on CPU with int8 compute; `--whisper-model base` or `medium` can be selected on the direct command.

3. Start the YouTube tab capture with the browser extension and open the ASR benchmark window. Enter the transcript separately from its ground-truth numbers: enter every expected value as a literal number, separated by `;` (for example, `9; 110; 140`), or enter `không có` when no number was spoken. The benchmark does not run its parser on the reference label. **Số được nói** is the default and bypasses the price gate; **Giá qua bộ lọc cấu hình** is a secondary price-specific evaluation. This benchmark selection does not change the main app's number-first behavior. Choose the closest acoustic condition and accent, press **Bắt đầu đoạn** just before the target utterance, then **Dừng & so sánh** just after it. Keep the segment tight; if voices overlap, choose **Chồng lấp giọng — luôn abstain**. WER/CER needs the full audible transcript and is not meaningful as a single ordered transcript for overlapping speech.
4. In the main window, `Số tạm` shows values from the changing ASR partial; they are provisional and may disappear or change. `Số trích được` remains based on finalized speech only. Number mode bypasses the minimum-price threshold and contextual price exclusions, so `SỐ CHÍN` displays `9`. In this mode an explicit count like `một hai ba bốn năm sáu bảy tám chín` is split into `[1, 2, 3, 4, 5, 6, 7, 8, 9]`; for a full transcript `số chín và một hai ba bốn năm sáu bảy tám chín`, the latest displayed candidate is `9`. Price parsing keeps its existing digit-by-digit rules. Values are shown without `₫`. The adjacent ASR chunk delay measures from the browser bridge receiving the input chunk to the recognizer event; it excludes speech-endpoint waiting, decision, sender, network, and chat appearance, so it is not the 0.7–0.8 s end-to-end target.
5. Review raw and denoised tabs. Each model reports transcript, extracted numbers, WER/CER, exact-number result, missed/extra numbers, and segment processing time. The session summary accumulates exact-number count, misses, extra candidates, and P50/P95 by condition; collect multiple labeled segments for meaningful percentiles. The optional price-scoring scope remains separate.
6. The strict agreement preview in the benchmark remains a price-specific comparison across all six outputs (three models × two audio branches). It abstains on disagreement and when the user labels a segment as overlapping. This agreement is not calibrated confidence, and overlap tagging is manual; automatic overlap detection is not implemented. This preview never sends.

The app holds at most 20 seconds of selected-tab PCM in memory and clears the buffer after comparison or discard. It never writes the captured audio or reference phrase to logs; benchmark summaries remain in RAM for the current app session only. First use downloads Whisper weights to the local Hugging Face cache. The setup script downloads the official Zipformer-VI, Silero VAD, and DPDFNet model files into ignored `models/`; the audio is never uploaded. The comparison command is YouTube-only and always forces `NullSender`.

Chrome's `tabCapture` API requires the user to invoke the extension and exposes a `MediaStream` for the current tab. Capturing a tab can stop its normal playback unless the extension routes the stream back to the output. See the [Chrome tabCapture reference](https://developer.chrome.com/docs/extensions/reference/api/tabCapture). Microsoft Edge documents both `tabCapture` and the MV3 `offscreen` API used here; the PriceTyper extension still needs a manual Edge run for acceptance ([Edge API support](https://learn.microsoft.com/en-us/microsoft-edge/extensions/developer-guide/api-support)).

## Safety boundary

- This prototype is YouTube-only. Do not open TikTok during prototype tests.
- Recognition-only: force dry-run and `NullSender`; no real sender may be created or called.
- Do not inspect page DOM, video frames, comments, chat, credentials, or cookies.
- Do not persist raw captured audio. Keep the browser-to-Python bridge on loopback only.

## Development launch

For a new setup, install the project and prepare the local models once:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe scripts\download_robust_asr_models.py
```

From the project root, start the prototype in PowerShell with the direct Python command below. The `run-youtube-test.ps1` launcher checks for the project virtual environment, sherpa-onnx, and local Zipformer/VAD model files; PowerShell's execution policy may require using the direct command instead.

```powershell
.\.venv\Scripts\python.exe -m pricetyper gui --youtube-test
```

Load `browser_extension/` as an unpacked extension in Chrome (`chrome://extensions`) or Edge (`edge://extensions`) using Developer mode → Load unpacked. Open a YouTube video with clear spoken numbers, start the Python GUI, then click the extension and start capture. The GUI should show the recognized text, parsed candidate, and whether the tab bridge is connected. No chat field or send button is involved. If Chrome displays a local-network permission prompt for the loopback WebSocket, allow it for this local test; WebSocket local-network restrictions are being introduced in current Chrome releases ([Chrome release notes](https://developer.chrome.com/release-notes/147)).

### Troubleshooting: “Chrome did not provide an audio stream”

The extension now passes through the string returned by `chrome.tabCapture.getMediaStreamId()`. If the extension had already been loaded before this fix, open `chrome://extensions` or `edge://extensions`, click **Reload** on PriceTyper, close and reopen its popup, then try Start again. If the message persists, record the browser version and the full popup error; the real-browser capture check is still required.

## Acceptance check

Use a video with a known spoken Vietnamese number. Confirm that:

1. Capture starts only after the extension action and stops when requested.
2. Playback continues through speakers/headphones, but changing the output volume does not change the captured transcript.
3. Confirm the tab RMS is above the near-silence threshold while the video is playing.
4. Compare the finalized transcript—not the changing partial text—with the spoken words; the number display uses parsed values from finalized text and does not apply the price gate. Zipformer can still misrecognize speech, especially with music, noise, accents, or fast delivery. A faster benchmark result does not establish higher number accuracy.
5. The run creates no browser sender, sends no message, and writes no raw audio file.

Current user-provided test source: [https://www.youtube.com/watch?v=IYH-W2ZK6kk](https://www.youtube.com/watch?v=IYH-W2ZK6kk). A separate user-reported counting sample covers about 00:06–00:08 and includes two voices, but its previous 9.04-second benchmark entry was not scoreable: the reference omitted audible words and did not contain an explicit number label. Re-run it with the full transcript, expected numbers, and overlap condition before recording accuracy. Record source URL, timestamp, full audible reference where possible, expected numbers, browser, Windows/audio setup, and observed transcript in `docs/IMPLEMENTATION_STATUS.md`. Do not claim recognition accuracy from one clip. Until a valid manual check is recorded, treat the browser extension and real YouTube capture as unverified even if Python unit tests pass.

## Later product packaging

PowerShell is accepted only as a development launcher for this prototype. The public release target is a Windows installer/package that bundles the Python runtime, provides a Start/Desktop shortcut and uninstaller, and does not require the user to open a terminal. Packaging starts after the recognition prototype is accepted.
