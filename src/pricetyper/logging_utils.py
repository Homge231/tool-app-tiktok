from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any


class JsonlLogger:
    def __init__(self, directory: str | Path, level: str = "INFO"):
        Path(directory).mkdir(parents=True, exist_ok=True)
        self.path = (
            Path(directory)
            / f"session-{datetime.now().astimezone():%Y%m%d-%H%M%S}.jsonl"
        )
        self.level = getattr(logging, level.upper(), logging.INFO)
        self._lock = Lock()

    def log(self, event: str, **fields: Any) -> None:
        if event.startswith(("asr_", "parse")):
            severity = logging.DEBUG
        elif event in {
            "audio_gap",
            "audio_overflow",
            "audio_silent",
            "send_unverified",
            "failsafe",
            "send_cancelled",
        }:
            severity = logging.WARNING
        elif event in {"error", "send_failed"}:
            severity = logging.ERROR
        else:
            severity = logging.INFO
        if severity < self.level:
            return
        record = {
            "ts": datetime.now().astimezone().isoformat(),
            "t_ns": time.perf_counter_ns(),
            "ev": event,
            **fields,
        }
        with self._lock, self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
