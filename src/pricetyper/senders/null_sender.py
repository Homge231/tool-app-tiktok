from __future__ import annotations

import time
from pricetyper.types import SendResult


class NullSender:
    name = 'null'

    def __init__(self):
        self.sent: list[str] = []

    def prepare(self) -> None:
        pass

    def send(self, text: str) -> SendResult:
        start = time.perf_counter_ns()
        self.sent.append(text)
        return SendResult(True, start, time.perf_counter_ns())

    def close(self) -> None:
        pass
