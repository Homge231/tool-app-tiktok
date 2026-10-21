from __future__ import annotations

from dataclasses import dataclass

from .vi_number import NumberSpan, tokenize


@dataclass
class GateCfg:
    min_value: int = 1000
    max_value: int = 2_000_000
    exclude_prev: tuple[str, ...] = ('size', 'số', 'ngày', 'tháng', 'lúc', 'giờ', 'mã', 'cỡ')
    exclude_next: tuple[str, ...] = ('cái', 'chiếc', 'người', 'bạn', 'kg', 'cm', 'mét', 'tuổi', 'giờ', 'phút', 'giây', 'ngày', 'tháng', 'tiếng', 'phần', 'lần')
    countdown_filter: bool = True
    gate_mode: str = 'any_number'
    anchor_before: tuple[str, ...] = ('giá', 'chỉ', 'chốt', 'lấy', 'còn', 'bán')
    anchor_after: tuple[str, ...] = ('k', 'ca', 'ka', 'nghìn', 'ngàn', 'đồng')


def monotonic_step1(digits: str) -> bool:
    if len(digits) < 3:
        return False
    differences = {int(b) - int(a) for a, b in zip(digits, digits[1:])}
    return differences in ({1}, {-1})


def gate(text: str, spans: list[NumberSpan], cfg: GateCfg) -> list[NumberSpan]:
    tokens, passed = tokenize(text), []
    for span in spans:
        if not cfg.min_value <= span.value <= cfg.max_value:
            continue
        previous = tokens[span.start - 1] if span.start else None
        following = tokens[span.end] if span.end < len(tokens) else None
        if previous in cfg.exclude_prev or following in cfg.exclude_next:
            continue
        if cfg.countdown_filter and span.kind == 'digits' and monotonic_step1(span.digits):
            continue
        if cfg.gate_mode == 'anchored' and not (
            span.unit or (span.start and any(t in cfg.anchor_before for t in tokens[max(0, span.start - 2):span.start]))
            or following in cfg.anchor_after
        ):
            continue
        passed.append(span)
    return passed
