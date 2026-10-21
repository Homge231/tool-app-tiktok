import pytest

from pricetyper.parsing.gate import GateCfg, gate
from pricetyper.parsing.vi_number import parse_all


VECTORS = [
    ('size ba tám', []),
    ('ba hai một chốt', []),
    ('một hai ba chốt', []),
    ('bốn năm sáu', []),
    ('ba hai chín', [329]),
    ('lúc hai mươi giờ', []),
    ('một trăm phần trăm cotton', []),
    ('hai cái một trăm chín mươi chín', [199]),
    ('chín chín ca', [99000]),
    ('một nghìn hai trăm', []),
    ('áo hai trăm rưỡi quần ba trăm', [250, 300]),
    ('còn năm cái', []),
    ('giá mười', [10]),
    ('giá chín', [9]),
    ('hai nghìn một trăm', []),
]


@pytest.mark.parametrize('text,expected', VECTORS)
def test_gate(text, expected):
    assert [span.value for span in gate(text, parse_all(text), GateCfg(min_value=1))] == expected


def test_default_gate_filters_values_below_one_thousand_vnd():
    cfg = GateCfg()

    assert gate('giá 999', parse_all('giá 999'), cfg) == []
    assert [span.value for span in gate('giá 1.000', parse_all('giá 1.000'), cfg)] == [1000]
    assert [span.value for span in gate('giá một nghìn', parse_all('giá một nghìn'), cfg)] == [1000]
    assert gate('giá chín trăm chín mươi chín', parse_all('giá chín trăm chín mươi chín'), cfg) == []


def test_gate_minimum_can_be_configured_for_a_different_price_range():
    text = 'giá 999'
    assert [span.value for span in gate(text, parse_all(text), GateCfg(min_value=1))] == [999]
