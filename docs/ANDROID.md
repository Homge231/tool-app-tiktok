# Android manual setup (experimental)

PriceTyper does not run on the phone. The Python app runs on a Windows PC. `scrcpy` mirrors and controls an Android phone; the PC captures the forwarded sound with loopback and types into the visible scrcpy window. This route is experimental until verified on the specific phone and TikTok app version.

## Prerequisites

- Android 11 or newer, a USB cable, Android platform-tools (`adb`), and the official `scrcpy` release.
- Enable Developer options and USB debugging yourself. When prompted, approve the PC's debugging key on the phone.
- `adb devices` must show exactly the intended device as `device`. If more than one device is listed, set `sender.adb.serial` explicitly.
- On Android 11, unlock the device before starting scrcpy. Android 12 or newer is the expected path for audio forwarding.

## Mirror and confirm audio

Start scrcpy manually:

```powershell
scrcpy --require-audio
```

Open TikTok Live in the phone app and confirm its sound reaches the PC. `--require-audio` makes scrcpy report an audio capture failure instead of silently continuing video-only. Audio forwarding depends on Android version and app behavior; a TikTok app may restrict playback capture.

## Configure desktop typing

Set `mode: android_scrcpy`, `audio.source: loopback`, and `sender.type: desktop` in `config.yaml`. Keep the scrcpy window visible, in the foreground, and at the same size after calibration. Run `pricetyper calibrate --target chat`; if `output.send_mode: click_button`, also run `pricetyper calibrate --target send`.

First test with `run.dry_run: true`. Confirm the recognized price and coordinates. Then disarm, turn dry-run off, focus the intended TikTok chat field, and arm with F8. Press F8 again to stop sending. F10 exits immediately.

## ADB sender fallback

Use `mode: android_adb`, `sender.type: adb` only if desktop typing through scrcpy is incompatible with the device. Configure `sender.adb.chat_xy`, a serial if needed, and—when using button mode—`sender.adb.send_xy`. Calibrate coordinates on the device display itself, not the PC desktop. The implementation uses `adb shell input`; speed and keyboard behavior vary and remain unverified until measured on the target device.

## Known limits

- Android 10 and earlier do not provide the scrcpy audio-forwarding path used here.
- ENTER may not submit TikTok chat on every app version; use a calibrated send button if needed.
- Default scrcpy keyboard injection may not enter text in every app. The `--keyboard=uhid` fallback is device-dependent.
- The PC loopback captures all system output. Mute unrelated PC applications during use.
- Do not automate payment or checkout. This tool only types the recognized price into the chat input.
