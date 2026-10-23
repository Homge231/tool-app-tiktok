# Android app prototype (M9)

This is a native Kotlin APK for Android 11 and later. It is separate from the Windows/scrcpy Android route in `docs/ANDROID.md`.

## What it does

- Requests Android MediaProjection and captures playback audio filtered to the configured TikTok package UID. It never falls back to microphone or system-wide loopback.
- Runs Silero VAD and Zipformer-VI locally. Audio remains in memory; the APK declares no Internet permission.
- Parses finalized Vietnamese ASR text using the same number-first rules as the Python app and shows the latest recognized candidate in the foreground notification.
- Starts disarmed with dry-run enabled. For real actions, the user must enable NumberTyper phone typing in Android Accessibility settings, turn dry-run off, and arm in the app.
- The accessibility service checks the active package and the focused editable node. It does not read node text, chat rows, or comments. `ACTION_SET_TEXT` replaces the focused field's existing draft, so the user must keep the TikTok chat field empty before arming. Enter dispatch is an unverified request; it does not prove a visible comment.
- Includes cooldowns, a 10 actions/minute limit, one-shot action handling, a bounded audio queue, and disarm on interruption, queue overflow, capture failure, or ASR stall. It never auto-rearms.

## Build a debug APK

Install Android SDK Platform 36, Build Tools 36.0.0, Java 17 or newer, then run in PowerShell:

```powershell
# Run the first command from the repository root.
.\scripts\fetch_android_runtime.ps1
cd android
.\gradlew.bat assembleDebug
```

The script downloads the sherpa-onnx 1.13.8 Android AAR from its official GitHub release and checks the published SHA-256. The Gradle task copies model files from the ignored repository `models/` directory into generated build assets. Required files are:

- `models/sherpa-onnx-zipformer-vi-30M-int8-2026-02-09/{encoder.int8.onnx,decoder.onnx,joiner.int8.onnx,tokens.txt}`
- `models/silero_vad.onnx`

Weights and generated assets are not committed. The APK is written to `android/app/build/outputs/apk/debug/app-debug.apk`.

## First run

1. Install and open NumberTyper. This build targets the global TikTok package `com.zhiliaoapp.musically`.
2. Start audio capture and approve Android's RECORD_AUDIO and MediaProjection prompts.
3. Open TikTok Live. Leave dry-run on to check recognition first. If TikTok disallows playback capture, Android supplies no app audio; the app reports silence and does not switch sources.
4. For real typing, enable **NumberTyper phone typing** under Android Accessibility settings. Focus the TikTok chat input and leave it empty.
5. Turn dry-run off, arm explicitly, and keep TikTok in the foreground. Stop with the app button or the foreground notification action; both disarm.

## Acceptance limits

This prototype has not been tested on a physical phone. MediaProjection support for TikTok audio, Zipformer speed/accuracy on the device, the focused input selector, and TikTok's handling of Enter are unverified. TikTok can block playback capture. Accessibility typing may fail on a specific app version or device. No browser, device, recognition accuracy, or end-to-end latency acceptance is claimed until recorded for that exact device and TikTok version.
