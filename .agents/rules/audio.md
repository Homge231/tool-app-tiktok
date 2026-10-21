---
description: Rules for selected-tab audio capture and ASR input
globs:
  - "src/pricetyper/audio/**"
  - "src/pricetyper/asr/**"
  - "browser_extension/**"
  - "src/pricetyper/ui/**"
---

- YouTube and the separate TikTok Web prototype capture only audio from the browser tab the user explicitly selects and starts. Do not substitute the microphone or system-wide speaker mix.
- Keep tab capture user-initiated and visible. Do not inspect video frames, page DOM, comments, chat, cookies, or account data.
- Route captured tab audio to the configured local ASR engine (Zipformer-VI by default; Vosk is a benchmark baseline) and, separately, back to the user's audio output so capture does not unexpectedly silence playback. Recognition input must not be derived from the output volume or microphone.
- Normalize audio to mono PCM int16 at 16 kHz before feeding the existing pipeline; use bounded queues and report overflow.
- Show a persistent, prominent UI warning for selected-tab disconnects, dropped audio, 30 seconds without signal, and pipeline worker errors. Disarm and reset ASR on audio gaps; never auto-rearm after recovery. Clear the silence warning only when audio returns; other warnings remain until acknowledged or the connection is restored.
- In TikTok Web, if VAD reports active speech but no ASR result arrives for 15 seconds, disarm and show a persistent audible warning. Clear the ASR-stall warning only after an ASR result returns; never auto-rearm.
- In TikTok final-only mode, disable repeated offline Zipformer partial re-decodes so ASR does not starve the live audio queue. Bound any still-open VAD segment at 12 seconds; a forced flush/reset is preview-only (`partial`), never a send-eligible final.
- If the ASR audio queue fills, discard stale queued chunks, mark an audio-generation gap, disarm, and reset the ASR before consuming the newest chunk. The first final after that gap must be downgraded to preview-only; report the overflow in the UI rather than silently continuing with discontinuous speech.
- The current small Vosk model is a baseline, not acceptance for noisy livestream audio. Evaluate Northern, Central, and Southern Vietnamese speech, music/noise, and overlapping speakers with labeled clips before claiming robustness.
- Treat speech enhancement/noise suppression, speech/music or speaker source separation, overlap detection/diarization, and speech recognition as separate stages. Any enhancement must be A/B tested against raw tab PCM for price exact-match accuracy; do not assume denoising can separate simultaneous speakers.
- If overlap or recognition uncertainty remains, abstain from emitting a price candidate. Diarization labels who spoke when; it does not by itself recover clean audio for each speaker.
- Keep robust-ASR evaluation local. Use temporary/in-memory audio or user-provided fixtures outside version control; commit only synthetic tests, labels that disclose no personal data, and aggregate metrics—not captured livestream recordings.
- Keep capture local. Do not write raw video audio to disk or send it to a remote service. A local bridge must bind only to loopback and accept the browser extension origin/protocol expected by the prototype.
- In `--youtube-test` mode, force disarmed/dry-run behavior and `NullSender`; never instantiate a real sender or navigate to TikTok.
- In `--tiktok-web`, accept only a TikTok Live tab (`/@username/live`) and keep audio local/in memory. The extension must not read page content, chat, comments, cookies, or credentials.
- Cross-browser work must use a browser-specific capture adapter behind the shared PCM/audio pipeline. A browser is supported only when the adapter captures audio from the exact user-selected tab and passes a real-browser check; if tab-specific audio is unavailable, show an unsupported state. Do not substitute microphone or system-wide loopback to claim tab capture.
- Keep browser/OS capability checks and the verified compatibility matrix in `docs/BROWSER_COMPATIBILITY.md`; browser family or WebExtension compatibility alone does not prove tab-audio support.
- Automated audio tests use synthetic PCM or fixtures. A real YouTube playback check is manual and may only claim the exact URL/device/browser tested.
