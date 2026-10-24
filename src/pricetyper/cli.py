from __future__ import annotations

import argparse
import fnmatch
import json
import math
import sys
import wave
from pathlib import Path

from pydantic import ValidationError

from pricetyper.asr.errors import ModelError
from pricetyper.asr.factory import create_asr_engine
from pricetyper.audio.browser_tab import TIKTOK_HOSTS, BrowserTabSource
from pricetyper.audio.loopback import AudioDeviceError, AudioRateError, LoopbackSource
from pricetyper.audio.wav_source import AudioFormatError, WavSource
from pricetyper.config import load_config
from pricetyper.controller import Controller, State
from pricetyper.logging_utils import JsonlLogger
from pricetyper.pipeline import Pipeline, PipelineError
from pricetyper.senders.adb_sender import AdbSender
from pricetyper.senders.desktop_sender import DesktopSender, SenderPrepareError
from pricetyper.senders.null_sender import NullSender
from pricetyper.senders.playwright_sender import PlaywrightSender
from pricetyper.ui.hotkeys import register


def _parser():
    parser = argparse.ArgumentParser(
        prog="pricetyper",
        description="Vietnamese livestream number recognition and optional typing tool",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "gui", "calibrate", "discover"):
        cmd = commands.add_parser(name)
        cmd.add_argument("--config", type=Path)
    commands.choices["gui"].add_argument(
        "--youtube-test",
        action="store_true",
        help="capture the active YouTube tab and lock all chat senders",
    )
    commands.choices["gui"].add_argument(
        "--tiktok-web",
        action="store_true",
        help="use the connected Chromium TikTok Live tab; leave dry-run and press F8 to enable sending",
    )
    commands.choices["gui"].add_argument(
        "--asr-compare",
        action="store_true",
        help=(
            "compare local Vosk, Whisper, and Zipformer on a manually "
            "selected YouTube audio segment"
        ),
    )
    commands.choices["gui"].add_argument(
        "--whisper-model",
        choices=("base", "small", "medium"),
        default="small",
        help="multilingual Whisper model used by --asr-compare (default: small)",
    )
    commands.choices["calibrate"].add_argument(
        "--target", choices=("chat", "send"), default="chat"
    )
    commands.choices["discover"].add_argument(
        "--tiktok-web",
        action="store_true",
        help="deprecated: TikTok mode now probes the selected extension tab directly",
    )
    run = commands.choices["run"]
    run.add_argument("--armed", action="store_true")
    run.add_argument("--dry-run", action="store_true")
    replay = commands.add_parser("replay")
    replay.add_argument("--wav", required=True, type=Path)
    replay.add_argument("--config", type=Path)
    replay.add_argument("--speed", type=float)
    replay.add_argument("--dry-run", action="store_true")
    record = commands.add_parser("record")
    record.add_argument("--seconds", required=True, type=float)
    record.add_argument("--out", required=True, type=Path)
    record.add_argument("--device")
    latency = commands.add_parser("latency")
    latency.add_argument("--wav", type=Path)
    latency.add_argument("--truth", type=Path)
    latency.add_argument("--bench-sender", type=int)
    latency.add_argument("--config", type=Path)
    return parser


def _make_sender(config, *, extension_path=None, expected_hosts=None):
    s = config.sender
    if s.type == "playwright":
        return PlaywrightSender(
            s.playwright,
            config.output.send_mode,
            extension_path=extension_path,
            expected_hosts=expected_hosts,
        )
    if s.type == "desktop":
        return DesktopSender(
            s.desktop.chat_xy,
            s.desktop.send_xy,
            s.desktop.click_each_time,
            config.output.send_mode,
        )
    return AdbSender(
        s.adb.adb_path,
        s.adb.serial,
        s.adb.chat_xy,
        s.adb.send_xy,
        s.adb.send_keyevent,
        config.output.send_mode,
    )


def _make_source(config, wav_path=None, speed=None, expected_hosts=None):
    if wav_path is not None or config.audio.source == "wav":
        path = wav_path or config.audio.wav_path
        if not path:
            raise AudioFormatError("audio.wav_path is required")
        return WavSource(
            path,
            config.audio.chunk_ms,
            config.audio.wav_speed if speed is None else speed,
        )
    if config.audio.source == "browser_tab":
        return BrowserTabSource(
            chunk_ms=config.audio.chunk_ms,
            queue_max_chunks=config.audio.queue_max_chunks,
            expected_hosts=expected_hosts,
            expected_tiktok_live=bool(
                expected_hosts and TIKTOK_HOSTS.issubset(expected_hosts)
            ),
        )
    return LoopbackSource(
        config.audio.device, config.audio.sample_rate, config.audio.chunk_ms
    )


def _run_pipeline(config, wav_path=None, speed=None, force_dry=False):
    logger = JsonlLogger(config.run.log_dir, config.run.log_level)
    model = create_asr_engine(config)
    source = _make_source(config, wav_path, speed)
    sender = NullSender() if force_dry or config.run.dry_run else _make_sender(config)
    controller = Controller(sender, logger)
    if force_dry:
        controller._set_state(State.ARMED, "replay_dry_run")
    elif config.run.start_armed:
        controller.arm()
    if not force_dry:
        register(controller, config.run.hotkeys["toggle"], config.run.hotkeys["panic"])
        import threading

        def console_controls():
            while not controller.stop_event.is_set():
                try:
                    command = input("pricetyper> ").strip().lower()
                except EOFError:
                    return
                if command == "on":
                    try:
                        controller.arm()
                    except Exception as exc:  # noqa: BLE001 - show any preparation failure in console
                        print(f"Cannot arm: {exc}", file=sys.stderr)
                elif command == "off":
                    controller.disarm()
                elif command == "status":
                    print(controller.state.value)
                elif command == "quit":
                    controller.disarm()
                    controller.stop_event.set()
                    return

        threading.Thread(
            target=console_controls, name="console-control", daemon=True
        ).start()
    pipeline = Pipeline(source, model, sender, config, controller, logger)
    try:
        pipeline.run()
    except KeyboardInterrupt:
        controller.disarm()
        sender.close()
        return 130
    return 0


def _record(args, config):
    if args.seconds <= 0:
        raise ValueError("--seconds must be greater than zero")
    source = LoopbackSource(
        args.device or config.audio.device,
        config.audio.sample_rate,
        config.audio.chunk_ms,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    target_frames = math.ceil(args.seconds * config.audio.sample_rate)
    frames, captured_frames = [], 0
    source.start()
    try:
        while captured_frames < target_frames:
            item = source.read()
            if item is None:
                break
            pcm = item[0]
            remaining_frames = target_frames - captured_frames
            pcm = pcm[: remaining_frames * 2]
            if not pcm:
                raise AudioDeviceError("Loopback returned an empty audio chunk")
            if len(pcm) % 2:
                raise AudioDeviceError(
                    "Loopback returned a partial 16-bit audio sample"
                )
            frames.append(pcm)
            captured_frames += len(pcm) // 2
    finally:
        source.stop()
    if captured_frames < target_frames:
        raise AudioDeviceError(
            f"Loopback ended after {captured_frames / config.audio.sample_rate:.2f}s; requested {args.seconds:.2f}s"
        )
    with wave.open(str(args.out), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(config.audio.sample_rate)
        wav.writeframes(b"".join(frames))
    duration = captured_frames / config.audio.sample_rate
    print(f"Recorded {duration:.2f}s to {args.out}")
    return 0


def _calibrate(config, target):
    if config.sender.type != "desktop":
        raise SenderPrepareError(
            "Coordinate calibration supports the desktop sender only; configure ADB device coordinates manually"
        )
    import keyboard
    import pyautogui

    key = config.run.hotkeys["calibrate"]
    print(f"Move the pointer to the {target} field and press {key.upper()}...")
    keyboard.wait(key)
    x, y = pyautogui.position()
    from pricetyper.config import write_local_config

    key_name = "chat_xy" if target == "chat" else "send_xy"
    write_local_config({"sender": {config.sender.type: {key_name: [x, y]}}})
    print(f"Saved {key_name}: [{x}, {y}] in config.local.yaml")
    return 0


def _configure_tiktok_web(config):
    config.audio.source = "browser_tab"
    config.run.dry_run = True
    config.run.start_armed = False
    config.decision.cooldown_same_s = 2.0
    config.decision.cooldown_any_s = 0.2


def _discover(config, tiktok_web=False):
    if config.sender.type != "playwright":
        raise SenderPrepareError("discover requires sender.type: playwright")
    if tiktok_web:
        raise SenderPrepareError(
            "TikTok Web now uses the connected extension tab directly; run the GUI, "
            "start capture from the TikTok Live tab, then use its connect/probe button."
        )
    cfg = config.sender.playwright
    sender = PlaywrightSender(cfg, config.output.send_mode, thread_bound=False)
    # Discovery launches/attaches without relying on configured chat selectors.
    old = cfg.chat_input_selectors
    old_live_url = cfg.live_url
    cfg.chat_input_selectors = ["body"]
    cfg.live_url = "about:blank"
    try:
        sender.prepare()
        print(
            "A browser window is ready. Sign in manually if needed, open the livestream, then return here."
        )
        input(
            "Open the livestream, then press Enter here to inspect visible input fields..."
        )
        matching_pages = [
            page
            for page in sender.context.pages
            if fnmatch.fnmatch(page.url, cfg.url_pattern.replace("**/", "*/"))
        ]
        if matching_pages:
            sender.page = matching_pages[0]
        elif sender.page is None or sender.page.url == "about:blank":
            raise SenderPrepareError(
                "No live page found. Check the configured url_pattern and try again."
            )
        elements = sender.page.locator(
            '[contenteditable="true"], textarea, input:not([type="hidden"])'
        ).evaluate_all("""els => els.filter(e => e.getClientRects().length).map((e, i) => {
          const tag = e.tagName.toLowerCase();
          const id = e.id;
          const placeholder = e.getAttribute('placeholder');
          const aria = e.getAttribute('aria-label');
          const dataE2e = e.getAttribute('data-e2e');
          const quote = value => value.replaceAll('\\\\', '\\\\\\\\').replaceAll("'", "\\\\'");
          const suggested = dataE2e ? `[data-e2e='${quote(dataE2e)}']` : id ? `#${CSS.escape(id)}` : aria ? `${tag}[aria-label='${quote(aria)}']` : placeholder ? `${tag}[placeholder='${quote(placeholder)}']` : e.isContentEditable ? `${tag}[contenteditable='true']` : tag;
          const rect = e.getBoundingClientRect();
          return {i: i + 1, tag, id, placeholder, aria, dataE2e, role: e.getAttribute('role'), rect: {x: rect.x, y: rect.y, width: rect.width, height: rect.height}, suggested};
        })""")
        for item in elements:
            print(json.dumps(item, ensure_ascii=False))
        choice = input("Select input indices (comma-separated): ").strip()
        selected = [
            elements[int(value.strip()) - 1]
            for value in choice.split(",")
            if value.strip()
        ]
        selectors = [item["suggested"] for item in selected]
        for selector in selectors:
            if (
                sender.page.locator(selector).count() != 1
                or not sender.page.locator(selector).is_visible()
            ):
                raise SenderPrepareError(
                    f"Proposed selector {selector!r} must match exactly one visible element"
                )
        from pricetyper.config import write_local_config

        write_local_config(
            {"sender": {"playwright": {"chat_input_selectors": selectors}}}
        )
        print(f"Saved selectors {selectors!r} to config.local.yaml")
        return 0
    finally:
        cfg.chat_input_selectors = old
        cfg.live_url = old_live_url
        sender.close()


def _latency(args, config):
    if args.bench_sender is not None:
        if args.bench_sender <= 0:
            raise ValueError("--bench-sender must be a positive integer")
        if config.run.dry_run:
            sender = NullSender()
        else:
            if config.sender.type != "playwright":
                raise SenderPrepareError(
                    "Safe sender benchmark requires Playwright so the active page URL can be checked; use dry-run for NullSender"
                )
            sender = _make_sender(config)
            sender.prepare()
            page_url = (sender.page.url or "").casefold()
            if "tiktok.com" in page_url:
                sender.close()
                raise SenderPrepareError(
                    "Refusing sender benchmark on a TikTok page; use fake_live.html or dry-run"
                )
            local_fake = "fake_live.html" in page_url and (
                page_url.startswith("file:")
                or "127.0.0.1" in page_url
                or "localhost" in page_url
            )
            if not local_fake:
                sender.close()
                raise SenderPrepareError(
                    "Sender benchmark is restricted to tests/fixtures/fake_live.html or dry-run"
                )
        try:
            durations = []
            for _ in range(args.bench_sender):
                result = sender.send("1")
                if not result.ok:
                    raise RuntimeError(f"Sender benchmark failed: {result.error}")
                durations.append((result.t_end_ns - result.t_start_ns) / 1e6)
        finally:
            sender.close()
        durations.sort()
        p50 = durations[(len(durations) - 1) // 2]
        p95 = durations[min(len(durations) - 1, int(len(durations) * 0.95))]
        print(
            f"sender={sender.name} n={len(durations)} P50={p50:.3f} ms P95={p95:.3f} ms"
        )
        return 0

    if not args.wav or not args.truth:
        raise ValueError(
            "latency requires --bench-sender N or both --wav PATH --truth PATH"
        )
    truth = json.loads(args.truth.read_text(encoding="utf-8"))
    if not isinstance(truth, list) or any(
        not isinstance(item, dict)
        or not isinstance(item.get("value"), int)
        or not isinstance(item.get("t_audio_end_ms"), int)
        for item in truth
    ):
        raise ValueError(
            'truth must be a JSON array of {"t_audio_end_ms": integer, "value": integer}'
        )
    from tempfile import TemporaryDirectory

    with TemporaryDirectory(prefix="pricetyper-latency-") as log_dir:
        cfg = config.model_copy(deep=True)
        cfg.run.dry_run = True
        cfg.run.log_level = "DEBUG"
        cfg.run.log_dir = log_dir
        cfg.audio.wav_speed = 1.0
        _run_pipeline(cfg, args.wav, 1.0, force_dry=True)
        log_files = list(Path(log_dir).glob("session-*.jsonl"))
        if not log_files:
            raise RuntimeError("Replay produced no log file")
        rows = [
            json.loads(line)
            for line in log_files[0].read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    start = next(
        (row["t_audio_ns"] for row in rows if row["ev"] == "audio_start"), None
    )
    if start is None:
        raise RuntimeError("Replay log is missing audio_start")
    sends = [row for row in rows if row["ev"] == "send" and row.get("ok") is True]
    truth.sort(key=lambda item: item["t_audio_end_ms"])
    sends.sort(key=lambda item: item["t_ns"])
    unmatched_truth = set(range(len(truth)))
    matched = []
    for send in sends:
        for index in sorted(unmatched_truth):
            label = truth[index]
            delta_ms = (
                send["t_ns"] - (start + label["t_audio_end_ms"] * 1_000_000)
            ) / 1_000_000
            if send.get("value") == label["value"] and 0 <= delta_ms <= 3000:
                matched.append(delta_ms)
                unmatched_truth.remove(index)
                break
    precision = len(matched) / len(sends) if sends else 0.0
    recall = len(matched) / len(truth) if truth else 0.0
    latencies = sorted(matched)
    if latencies:
        p50 = latencies[(len(latencies) - 1) // 2]
        p95 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))]
        print(
            f"precision={precision:.3f} recall={recall:.3f} matched={len(matched)} sends={len(sends)} labels={len(truth)}"
        )
        print(f"latency P50={p50:.1f} ms P95={p95:.1f} ms max={max(latencies):.1f} ms")
    else:
        print(
            f"precision={precision:.3f} recall={recall:.3f} matched=0 sends={len(sends)} labels={len(truth)}"
        )
        print("latency: no matched labels")
    print(f"unmatched_labels={len(unmatched_truth)}")
    return 0


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        config = load_config(getattr(args, "config", None))
        if args.command == "record":
            return _record(args, config)
        if args.command == "calibrate":
            return _calibrate(config, getattr(args, "target", "chat"))
        if args.command == "discover":
            return _discover(config, tiktok_web=args.tiktok_web)
        if args.command == "gui":
            from pricetyper.ui.gui import launch

            if args.youtube_test and args.tiktok_web:
                raise ValueError("--youtube-test and --tiktok-web are separate modes")
            if args.asr_compare and not args.youtube_test:
                raise ValueError("--asr-compare requires --youtube-test")
            if args.youtube_test:
                config.audio.source = "browser_tab"
                config.run.dry_run = True
                config.run.start_armed = False
            return launch(
                config,
                youtube_test=args.youtube_test,
                tiktok_web=args.tiktok_web,
                asr_compare=args.asr_compare,
                whisper_model=args.whisper_model,
            )
        if args.command == "replay":
            return _run_pipeline(config, args.wav, args.speed, force_dry=args.dry_run)
        if args.command == "latency":
            return _latency(args, config)
        if args.command == "run":
            if args.armed:
                config.run.start_armed = True
            if args.dry_run:
                config.run.dry_run = True
            return _run_pipeline(config)
    except ValidationError as exc:
        print("ERR_CONFIG:", file=sys.stderr)
        for error in exc.errors():
            print(
                f"- {'.'.join(map(str, error['loc']))}: {error['msg']}", file=sys.stderr
            )
        return 2
    except ModelError as exc:
        print(f"ERR_MODEL: {exc}", file=sys.stderr)
        return 4
    except AudioRateError as exc:
        print(f"ERR_AUDIO_RATE: {exc}", file=sys.stderr)
        return 3
    except (AudioDeviceError, AudioFormatError) as exc:
        print(f"ERR_AUDIO_DEVICE: {exc}", file=sys.stderr)
        return 3
    except SenderPrepareError as exc:
        print(f"SenderPrepareError: {exc}", file=sys.stderr)
        return 5
    except PipelineError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
