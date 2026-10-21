from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

LEAD = {'một': 1, 'hai': 2, 'ba': 3, 'bốn': 4, 'năm': 5, 'sáu': 6, 'bảy': 7, 'bẩy': 7, 'tám': 8, 'chín': 9}
ONES_ONLY = {'mốt': 1, 'tư': 4, 'lăm': 5, 'nhăm': 5}
DIGIT_ANY = {**LEAD, **ONES_ONLY, 'không': 0}
TEEN, HUND, HALF = 'mười', 'trăm', 'rưỡi'
TENS = frozenset({'mươi', 'chục'})
ZCONN = frozenset({'linh', 'lẻ'})
THOUSAND = frozenset({'nghìn', 'ngàn'})
DEFAULT_K = frozenset({'k', 'ca', 'ka'})
NUMWORDS = frozenset(DIGIT_ANY) | {TEEN, HUND, HALF} | TENS | ZCONN | THOUSAND
ARABIC = re.compile(r'^([0-9]{1,12})(k?)$')
GROUPED_ARABIC = re.compile(r'(?<!\d)(\d{1,3}(?:[.,]\d{3})+)(k?)(?!\d)')
PROBES = ('chín', 'mươi', 'trăm', 'mười', 'rưỡi', 'linh')


@dataclass(frozen=True)
class NumberSpan:
    value: int
    start: int
    end: int
    kind: str
    unit: bool
    closed: bool
    extendable: bool
    digits: str


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize('NFC', text.lower())
    text = GROUPED_ARABIC.sub(
        lambda match: match.group(1).replace('.', '').replace(',', '') + match.group(2),
        text,
    )
    return ''.join(c if (c.isalnum() or c.isspace()) else ' ' for c in text).split()


def _is_num(token: str) -> bool:
    return token in NUMWORDS or bool(ARABIC.match(token))


def _digit(tokens: list[str], index: int) -> int | None:
    return DIGIT_ANY.get(tokens[index]) if index < len(tokens) else None


def _after_hundred(tokens: list[str], index: int, shorthand: bool) -> tuple[int, int]:
    if index >= len(tokens):
        return 0, index
    word = tokens[index]
    if word == HALF:
        return 50, index + 1
    if word == 'mốt':
        return (10 if shorthand else 1), index + 1
    if word in ZCONN:
        digit = _digit(tokens, index + 1)
        return (digit, index + 2) if digit else (0, index)
    if word == TEEN:
        value, end = 10, index + 1
        digit = _digit(tokens, end)
        return (value + digit, end + 1) if digit else (value, end)
    if word in LEAD and LEAD[word] >= 2 and index + 1 < len(tokens) and tokens[index + 1] in TENS:
        value, end = LEAD[word] * 10, index + 2
        digit = _digit(tokens, end)
        return (value + digit, end + 1) if digit else (value, end)
    if word in LEAD or word == 'không':
        first = DIGIT_ANY[word]
        second = _digit(tokens, index + 1)
        if second is not None:
            return first * 10 + second, index + 2
        if word in LEAD:
            return (first * 10 if shorthand else first), index + 1
    return 0, index


def _read_core(tokens: list[str], index: int, shorthand: bool):
    token, n = tokens[index], len(tokens)
    match = ARABIC.match(token)
    if match:
        value = int(match.group(1))
        has_k = bool(match.group(2))
        return (
            value * 1000 if has_k else value,
            index + 1,
            'arabic',
            match.group(1),
            has_k,
        )
    if token in LEAD and index + 1 < n and tokens[index + 1] == HUND:
        value, end = _after_hundred(tokens, index + 2, shorthand)
        return LEAD[token] * 100 + value, end, 'positional', '', False
    if token == HUND and (
        index == 0
        or (not _is_num(tokens[index - 1]) and tokens[index - 1] != 'phần')
    ):
        value, end = _after_hundred(tokens, index + 1, shorthand)
        return 100 + value, end, 'positional', '', False
    if token == TEEN:
        digit = _digit(tokens, index + 1)
        return (10 + digit, index + 2, 'positional', '', False) if digit else (10, index + 1, 'positional', '', False)
    if token in LEAD and LEAD[token] >= 2 and index + 1 < n and tokens[index + 1] in TENS:
        value, end = LEAD[token] * 10, index + 2
        digit = _digit(tokens, end)
        return (value + digit, end + 1, 'positional', '', False) if digit else (value, end, 'positional', '', False)
    if token in LEAD:
        digits, end = [LEAD[token]], index + 1
        while end < n and tokens[end] in DIGIT_ANY and len(digits) < 4:
            if end + 1 < n and (tokens[end + 1] == HUND or tokens[end + 1] in TENS):
                break
            digits.append(DIGIT_ANY[tokens[end]])
            end += 1
        value_text = ''.join(map(str, digits))
        kind = 'digits' if len(digits) > 1 else 'positional'
        return int(value_text), end, kind, value_text if len(digits) > 1 else '', False
    return None


def _extendable(tokens: list[str], shorthand: bool, kind: str, digits: str) -> bool:
    if kind == 'arabic' or (kind == 'digits' and len(digits) >= 3):
        return False
    return any((parsed := _read_core(tokens + [probe], 0, shorthand)) is not None and parsed[1] == len(tokens) + 1 for probe in PROBES)


def _read_count_sequence(
    tokens: list[str], index: int, k_tokens: frozenset[str]
) -> tuple[list[NumberSpan], int] | None:
    """Read an explicit ascending count (một, hai, ba...) as separate values."""
    if index >= len(tokens) or tokens[index] != "một":
        return None

    spans = []
    cursor = index
    expected = 1
    while cursor < len(tokens) and LEAD.get(tokens[cursor]) == expected:
        spans.append(
            NumberSpan(
                expected,
                cursor,
                cursor + 1,
                "positional",
                False,
                True,
                False,
                "",
            )
        )
        cursor += 1
        expected += 1

    if len(spans) < 2:
        return None
    if cursor < len(tokens) and (
        _is_num(tokens[cursor]) or tokens[cursor] in k_tokens
    ):
        return None
    return spans, cursor


def parse_all(
    text: str,
    shorthand: bool = True,
    k_tokens: Iterable[str] = DEFAULT_K,
    *,
    split_count_sequence: bool = False,
) -> list[NumberSpan]:
    tokens, out, index = tokenize(text), [], 0
    k_tokens = frozenset(k_tokens)
    while index < len(tokens):
        if split_count_sequence:
            sequence = _read_count_sequence(tokens, index, k_tokens)
            if sequence is not None:
                spans, index = sequence
                out.extend(spans)
                continue
        parsed = _read_core(tokens, index, shorthand)
        if parsed is None:
            index += 1
            continue
        value, end, kind, digits, unit = parsed
        if end < len(tokens) and tokens[end] in k_tokens:
            value, unit, end = value * 1000, True, end + 1
        elif end < len(tokens) and tokens[end] in THOUSAND:
            unit, end = True, end + 1
            if end < len(tokens) and _is_num(tokens[end]):
                following = _read_core(tokens, end, shorthand)
                has_separate_unit = False
                if following is not None:
                    following_end = following[1]
                    has_separate_unit = following[4] or (
                        following_end < len(tokens)
                        and tokens[following_end] in (THOUSAND | k_tokens)
                    )
                if not has_separate_unit:
                    while end < len(tokens) and _is_num(tokens[end]):
                        end += 1
                    index = end
                    continue
            value *= 1000
        closed = unit or end < len(tokens)
        out.append(NumberSpan(value, index, end, kind, unit, closed, not closed and _extendable(tokens[index:end], shorthand, kind, digits), digits))
        index = end
    return out
