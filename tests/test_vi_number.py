import pytest

from pricetyper.parsing.vi_number import parse_all

F, T = False, True
CASES = [
    ('một trăm chín mươi chín', T, [(199, F, F, F)]),
    ('một trăm chín mươi chín nha', T, [(199, F, T, F)]),
    ('Một trăm chín mươi chín, nha!', T, [(199, F, T, F)]),
    ('chín chín ca', T, [(99000, T, T, F)]),
    ('chín mươi chín k', T, [(99000, T, T, F)]),
    ('hai trăm', T, [(200, F, F, T)]),
    ('hai trăm rưỡi', T, [(250, F, F, F)]),
    ('ba trăm năm', T, [(350, F, F, T)]),
    ('ba trăm năm', F, [(305, F, F, T)]),
    ('một trăm hai', T, [(120, F, F, T)]),
    ('một trăm hai', F, [(102, F, F, T)]),
    ('một trăm bốn', T, [(140, F, F, T)]),
    ('một bốn không', T, [(140, F, F, F)]),
    ('trăm bốn', T, [(140, F, F, T)]),
    ('một một không', T, [(110, F, F, F)]),
    ('trăm mốt', T, [(110, F, F, F)]),
    ('một trăm mốt', T, [(110, F, F, F)]),
    ('một trăm mốt', F, [(101, F, F, F)]),
    ('một trăm linh năm', T, [(105, F, F, F)]),
    ('một trăm lẻ năm', T, [(105, F, F, F)]),
    ('một trăm không năm', T, [(105, F, F, F)]),
    ('hai trăm linh', T, [(200, F, T, F)]),
    ('hai mươi', T, [(20, F, F, T)]),
    ('hai mươi lăm', T, [(25, F, F, F)]),
    ('hai lăm', T, [(25, F, F, T)]),
    ('hai mốt', T, [(21, F, F, T)]),
    ('mười lăm', T, [(15, F, F, F)]),
    ('mười', T, [(10, F, F, T)]),
    ('một hai chín', T, [(129, F, F, F)]),
    ('chín chín chín', T, [(999, F, F, F)]),
    ('199', T, [(199, F, F, F)]),
    ('199k', T, [(199000, T, T, F)]),
    ('199 k', T, [(199000, T, T, F)]),
    ('hai trăm nghìn', T, [(200000, T, T, F)]),
    ('hai nghìn ba nghìn', T, [(2000, T, T, F), (3000, T, T, F)]),
    ('hai nghìn, 3 nghìn', T, [(2000, T, T, F), (3000, T, T, F)]),
    ('một', T, [(1, F, F, T)]),
    ('100.000', T, [(100000, F, F, F)]),
    ('100,000', T, [(100000, F, F, F)]),
    ('100.000 nghìn', T, [(100000000, T, T, F)]),
    ('100.000 ngàn', T, [(100000000, T, T, F)]),
    ('300 nghìn', T, [(300000, T, T, F)]),
    ('một nghìn hai trăm', T, []),
    ('áo này giá một trăm chín mươi chín nghìn nha mọi người', T, [(199000, T, T, F)]),
    ('hai trăm năm mươi', T, [(250, F, F, T)]),
    ('một trăm mười lăm', T, [(115, F, F, F)]),
    ('một trăm hai mốt', T, [(121, F, F, F)]),
    ('hai trăm ba mươi lăm', T, [(235, F, F, F)]),
    ('một trăm hai ba', T, [(123, F, F, F)]),
    ('năm chục', T, [(50, F, F, T)]),
    ('một trăm phần trăm cotton', T, [(100, F, T, F)]),
    ('không trăm', T, []),
    ('áo này hai trăm rưỡi quần kia ba trăm', T, [(250, F, T, F), (300, F, F, T)]),
]


@pytest.mark.parametrize('text,shorthand,expected', CASES)
def test_parse(text, shorthand, expected):
    got = [
        (s.value, s.unit, s.closed, s.extendable) for s in parse_all(text, shorthand)
    ]
    assert got == expected


def test_number_after_the_word_so_is_still_extracted():
    assert [span.value for span in parse_all("SỐ CHÍN")] == [9]


def test_number_preview_splits_an_explicit_ascending_count_sequence():
    text = "số chín và một hai ba bốn năm sáu bảy tám chín"

    # Price parsing keeps the existing digit-by-digit interpretation.
    assert [span.value for span in parse_all(text)] == [9, 1234, 5678, 9]
    # Number preview treats the spoken count as individual values.
    assert [
        span.value for span in parse_all(text, split_count_sequence=True)
    ] == [9, 1, 2, 3, 4, 5, 6, 7, 8, 9]
