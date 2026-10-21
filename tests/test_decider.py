from pricetyper.decision.decider import Decider, DeciderCfg
from pricetyper.parsing.gate import GateCfg


EVENTS = [
    (0, 'partial', 'áo này giá một'),
    (300, 'partial', 'áo này giá một trăm'),
    (500, 'partial', 'áo này giá một trăm chín'),
    (700, 'partial', 'áo này giá một trăm chín mươi'),
    (900, 'partial', 'áo này giá một trăm chín mươi chín'),
    (1000, 'partial', 'áo này giá một trăm chín mươi chín nha'),
    (1400, 'final', 'áo này giá một trăm chín mươi chín nha'),
    (3000, 'partial', 'quần này hai trăm rưỡi'),
    (4200, 'partial', 'size ba tám'),
    (5000, 'partial', 'ba hai một chốt'),
    (6000, 'partial', 'chín chín ca'),
    (6200, 'partial', 'chín chín ca nha ba trăm'),
    (6600, 'final', 'chín chín ca nha ba trăm'),
    (7200, 'partial', 'chín chín ca'),
]
EXPECTED = [
    (1000, 199, 'send', 'ok'),
    (3120, 250, 'send', 'ok'),
    (6000, 99000, 'send', 'ok'),
    (6550, 300, 'skip', 'cooldown_any'),
    (7200, 99000, 'skip', 'cooldown_same'),
]


def run(armed=True):
    decider = Decider(GateCfg(min_value=1), DeciderCfg(), armed=armed)
    events = {t: (kind, text) for t, kind, text in EVENTS}
    result = []
    for t_ms in range(0, 8000, 10):
        out = decider.on_event(events[t_ms][0], events[t_ms][1], t_ms) if t_ms in events else []
        out += decider.tick(t_ms)
        result.extend((d.t_ms, d.value, d.action, d.reason) for d in out)
    return result


def test_trace():
    assert run(armed=True) == EXPECTED


def test_disarmed_never_sends():
    assert all(action == 'skip' for _, _, action, _ in run(armed=False))


def test_number_scope_sends_small_numbers_without_price_gate():
    decider = Decider(
        GateCfg(min_value=1000),
        DeciderCfg(),
        armed=True,
        candidate_scope="number",
    )

    decisions = decider.on_event("final", "SỐ CHÍN", 0, 123)

    assert [(item.value, item.action) for item in decisions] == [(9, "send")]


def test_number_scope_uses_last_number_in_a_spoken_count_sequence():
    decider = Decider(
        GateCfg(min_value=1000),
        DeciderCfg(),
        armed=True,
        candidate_scope="number",
    )

    decisions = decider.on_event(
        "final", "số chín và một hai ba bốn năm sáu bảy tám chín", 0, 123
    )

    assert [(item.value, item.action) for item in decisions] == [(9, "send")]
