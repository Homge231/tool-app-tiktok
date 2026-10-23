from __future__ import annotations

from dataclasses import dataclass

from pricetyper.parsing.gate import GateCfg, gate
from pricetyper.parsing.vi_number import parse_all


@dataclass
class DeciderCfg:
    hold_complete_ms: int = 120
    hold_open_ms: int = 350
    cooldown_same_s: float = 10.0
    cooldown_any_s: float = 1.5
    max_per_min: int = 10
    shorthand: bool = True
    k_tokens: tuple[str, ...] = ('k', 'ca', 'ka')


@dataclass
class Decision:
    t_ms: int
    value: int
    action: str
    reason: str
    t_audio: int = 0


@dataclass
class Pending:
    value: int
    text: str
    t_change: int
    hold: int
    t_audio: int


class Decider:
    def __init__(
        self,
        gate_cfg: GateCfg | None = None,
        cfg: DeciderCfg | None = None,
        armed: bool = False,
        candidate_scope: str = "price",
        draft_only: bool = False,
    ):
        if candidate_scope not in {"number", "price"}:
            raise ValueError("candidate_scope must be 'number' or 'price'")
        self.gate_cfg, self.cfg, self.armed = gate_cfg or GateCfg(), cfg or DeciderCfg(), armed
        self.candidate_scope = candidate_scope
        self.draft_only = draft_only
        self.pending: Pending | None = None
        self.handled: set[int] = set()
        self.sent: list[tuple[int, int]] = []

    def _decide(self, pending: Pending, t_ms: int) -> Decision:
        c, value = self.cfg, pending.value
        if not self.draft_only:
            if any(
                v == value and t_ms - sent_at < c.cooldown_same_s * 1000
                for sent_at, v in self.sent
            ):
                return Decision(t_ms, value, 'skip', 'cooldown_same', pending.t_audio)
            if self.sent and t_ms - self.sent[-1][0] < c.cooldown_any_s * 1000:
                return Decision(t_ms, value, 'skip', 'cooldown_any', pending.t_audio)
            if (
                sum(t_ms - sent_at < 60000 for sent_at, _ in self.sent)
                >= c.max_per_min
            ):
                return Decision(t_ms, value, 'skip', 'rate_limit', pending.t_audio)
        if not self.armed:
            return Decision(t_ms, value, 'skip', 'disarmed', pending.t_audio)
        if not self.draft_only:
            self.sent.append((t_ms, value))
        return Decision(t_ms, value, 'send', 'ok', pending.t_audio)

    def _release(self, now: int) -> list[Decision]:
        pending = self.pending
        if pending is not None and now - pending.t_change >= pending.hold:
            self.pending = None
            self.handled.add(pending.value)
            return [self._decide(pending, now)]
        return []

    def on_event(self, kind: str, text: str, t_ms: int, t_audio: int = 0) -> list[Decision]:
        parsed = parse_all(
            text,
            self.cfg.shorthand,
            self.cfg.k_tokens,
            split_count_sequence=self.candidate_scope == "number",
        )
        spans = (
            parsed
            if self.candidate_scope == "number"
            else gate(text, parsed, self.gate_cfg)
        )
        candidate = spans[-1] if spans else None
        final = kind == 'final'
        if candidate is None or candidate.value in self.handled:
            self.pending = None
        else:
            hold = 0 if candidate.closed or final else (self.cfg.hold_open_ms if candidate.extendable else self.cfg.hold_complete_ms)
            if self.pending is None or self.pending.value != candidate.value or self.pending.text != text:
                self.pending = Pending(candidate.value, text, t_ms, hold, t_audio)
            else:
                self.pending.hold = hold
            result = self._release(t_ms)
            if final:
                self.handled.clear()
                self.pending = None
            return result
        result = self._release(t_ms)
        if final:
            self.handled.clear()
            self.pending = None
        return result

    def tick(self, t_ms: int) -> list[Decision]:
        return self._release(t_ms)
