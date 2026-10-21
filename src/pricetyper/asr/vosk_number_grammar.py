"""Experimental finite phrase grammar for a narrow Vietnamese number benchmark."""

from __future__ import annotations

import json


def number_phrases() -> tuple[str, ...]:
    """Return common spoken forms for 1–20 and short thousand-count phrases."""
    ones = [
        "một",
        "hai",
        "ba",
        "bốn",
        "tư",
        "năm",
        "lăm",
        "sáu",
        "bảy",
        "bẩy",
        "tám",
        "chín",
    ]
    forms = {
        1: ["một"],
        2: ["hai"],
        3: ["ba"],
        4: ["bốn", "tư"],
        5: ["năm"],
        6: ["sáu"],
        7: ["bảy", "bẩy"],
        8: ["tám"],
        9: ["chín"],
        10: ["mười"],
    }
    for number in range(11, 20):
        forms[number] = [
            f"mười {word}"
            for word in ones
            if word not in ("một", "bốn", "tư", "năm", "bảy", "bẩy")
        ]
    forms.update(
        {
            11: ["mười một"],
            12: ["mười hai"],
            13: ["mười ba"],
            14: ["mười bốn", "mười tư"],
            15: ["mười lăm"],
            16: ["mười sáu"],
            17: ["mười bảy"],
            18: ["mười tám"],
            19: ["mười chín"],
            20: ["hai mươi"],
        }
    )

    phrases: list[str] = []
    for variants in forms.values():
        phrases.extend(variants)
        phrases.extend(f"{variant} nghìn" for variant in variants)
        phrases.extend(f"rồi {variant} nghìn" for variant in variants)
        phrases.extend(f"{variant} nghìn rồi" for variant in variants)
    for first in forms.values():
        for second in forms.values():
            phrases.extend(
                f"{left} nghìn rồi {right} nghìn" for left in first for right in second
            )
            phrases.extend(
                f"{left} nghìn {right} nghìn" for left in first for right in second
            )
    canonical_count = [forms[number][0] for number in range(1, 21)]
    for start in range(len(canonical_count)):
        for end in range(start + 1, len(canonical_count)):
            phrases.append(" ".join(canonical_count[start : end + 1]))
    return tuple(dict.fromkeys([*phrases, "[unk]"]))


NUMBER_PHRASES = number_phrases()
NUMBER_GRAMMAR_JSON = json.dumps(NUMBER_PHRASES, ensure_ascii=False)
