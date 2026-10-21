from __future__ import annotations


def format_vnd(value: int) -> str:
    """Format an exact đồng amount with Vietnamese thousands separators."""
    return f"{value:,}".replace(",", ".") + " ₫"
