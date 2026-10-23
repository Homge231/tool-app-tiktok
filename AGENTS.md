# PriceTyper agent instructions

## Session continuity — Obsidian second brain

This repository contains an Obsidian vault at `second-brain/`. At the start of each project session, read `second-brain/00-Start-Here.md`, then `Current-State.md`, `Plan.md`, and the latest dated entry in `Timeline.md`. At the end of each session, update the current state and plan and append a dated timeline entry. Record only verified facts; label assumptions, planned work, and unverified behavior explicitly. Keep detailed technical procedures in `docs/` and link to them instead of duplicating them in the vault.

Before changing code, read `docs/SPEC.md` and the relevant rules under `.agents/rules/`. This repository builds a local Python application for Windows. It is not a website or a hosted service.

## Current prototype scope

- The YouTube experiment remains number-first and recognition-only: capture audio from the user-selected browser tab, run local Vietnamese ASR and number parsing, and show the recognized text/numeric value without applying the price gate.
- The legacy M7 `--tiktok-web` path used a dedicated Edge profile. The M8 path uses the Chromium extension bridge to capture audio and act on the same user-selected TikTok Live tab. It is number-first: it bypasses the price minimum/context gate and considers only finalized ASR text. In TikTok mode, auto-submit of `@<number>` is preselected after a successful tab probe; dry-run remains on and the action remains disarmed until the user turns dry-run off and presses F8. Fill-only remains available. The action acknowledgement does not prove that TikTok displayed the comment. No browser, ASR accuracy, or end-to-end latency acceptance is claimed for M8 yet.
- The requested next product target is browser-independent desktop support. Implement browser-specific adapters behind the shared local ASR/number pipeline; support only browser/OS combinations whose selected-tab audio capture and same-tab sender have been tested. Never promise compatibility with every browser by name alone. If a browser cannot provide the selected tab's audio, report it as unsupported rather than silently switching to microphone or system-wide loopback.
- Keep M7 as the tested historical Edge/Windows baseline; M8 is in progress. The compatibility targets and evidence live in `docs/BROWSER_COMPATIBILITY.md`.
- The current small Vosk model is only a baseline; robustness to music, noise, regional accents, and overlapping speakers is an unmet requirement until measured on labeled audio.
- This feature transcribes the audio that is actually playing; it does not translate languages. Evaluate speech enhancement, source separation, overlap detection/diarization, and ASR as distinct stages. Noise suppression alone is not speaker separation.
- When speech overlaps or a number is uncertain, show an uncertainty/no-candidate state instead of guessing. Never treat raw ASR confidence as calibrated without validation.
- In TikTok Web, if VAD reports active speech but no ASR result arrives for 15 seconds, disarm and show a persistent audible warning. Clear the ASR-stall warning only after an ASR result returns; never auto-rearm.
- The YouTube test mode must not open TikTok, inspect page/chat content, or send messages. Force `NullSender`; do not expose a way to turn the test into a real send.
- Keep system-wide speaker loopback available for recording/other documented uses, but do not use it as the YouTube test input. The YouTube path must receive the selected tab's digital audio stream.
- The current development launcher may be a PowerShell command. The eventual public product is a packaged Windows app with a normal installer and shortcut; packaging is a later milestone.

## Project rules

- Implement one milestone from §12 at a time. Do not silently expand scope.
- Keep parser, gate, and decision logic independent from the UI, audio capture, ASR, and senders.
- The default action state is disarmed. F8 toggles the enabled action; F10 is emergency stop. Dry-run must never call a real sender. In TikTok mode, auto-submit of `@<number>` is preselected after a successful tab probe, but requires leaving dry-run and pressing F8. Fill-only remains selectable. Do not imply that synthetic Enter guarantees a visible/accepted comment.
- Do not read or scrape chat, comments, credentials, cookies, or other viewers' data. Do not add evasion, automated checkout, or rate-limit bypass behavior.
- Validate sender preparation before arming. An action failure is not retried. Keep the final armed check immediately before the sender action. A dispatched Enter is an unverified request; do not report the comment as visible without allowed evidence.
- Use the fake local page or NullSender for sender checks. Never use a real livestream as a test fixture.
- YouTube test mode must use YouTube only and keep `NullSender`. The dedicated TikTok Web mode may operate only on a user-opened TikTok Live URL; automated tests must use the local fake page and never a real livestream.
- A code change to parser or decision semantics requires updating `docs/SPEC.md` and corresponding tests.
- Do not claim hardware, browser, Android, or latency acceptance unless that exact check was run and recorded.
- Do not commit model files, logs, configs with personal data, or recordings. Respect `.gitignore`.
- Keep ASR local/offline and process audio in memory. Do not add a remote speech API or persist captured audio unless the user explicitly changes the privacy requirement.

## Completion report

For each milestone, report files changed, requirements addressed, checks actually run and their output, checks not run with reasons, and known remaining work. Keep the diff limited to the active milestone.
