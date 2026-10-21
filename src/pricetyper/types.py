from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class AsrEvent:
    kind: Literal['partial', 'final']
    text: str
    t_ns: int
    t_audio_ns: int


@dataclass(frozen=True)
class SendCommand:
    value: int
    text: str
    t_audio_ns: int
    t_decided_ns: int


@dataclass(frozen=True)
class SendResult:
    ok: bool
    t_start_ns: int
    t_end_ns: int
    error: str | None = None


class AudioSource(Protocol):
    def start(self) -> None: ...
    def read(self) -> tuple[bytes, int] | None: ...
    def stop(self) -> None: ...


class AsrEngine(Protocol):
    def feed(self, pcm: bytes, t_audio_ns: int) -> list[AsrEvent]: ...
    def reset(self) -> None: ...


class Sender(Protocol):
    name: str
    def prepare(self) -> None: ...
    def send(self, text: str) -> SendResult: ...
    def close(self) -> None: ...
