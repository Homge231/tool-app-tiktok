from pricetyper.config import AppConfig
from pricetyper.controller import Controller
from pricetyper.pipeline import Pipeline
from pricetyper.senders.null_sender import NullSender
from pricetyper.types import AsrEvent


class MemoryLogger:
    def log(self, *_args, **_kwargs):
        pass


def _commands_for(kind, *, send_final_only, candidate_scope="price", text="giá một nghìn"):
    config = AppConfig()
    controller = Controller(NullSender())
    controller.armed.set()
    pipeline = Pipeline(
        source=object(),
        asr=object(),
        sender=NullSender(),
        config=config,
        controller=controller,
        logger=MemoryLogger(),
        send_final_only=send_final_only,
        candidate_scope=candidate_scope,
    )
    pipeline.event_q.put(AsrEvent(kind, text, 1_000_000, 1_000_000))
    pipeline.event_q.put(pipeline._event_stop)
    pipeline._decide_loop()

    commands = []
    while (item := pipeline.send_q.get_nowait()) is not None:
        commands.append(item)
    return commands


def test_tiktok_final_only_mode_never_sends_partial_candidate():
    assert _commands_for("partial", send_final_only=True) == []


def test_tiktok_final_only_mode_sends_candidate_after_final_event():
    commands = _commands_for("final", send_final_only=True)
    assert [command[0] for command in commands] == [1000]


def test_tiktok_number_scope_can_send_a_single_digit_below_price_minimum():
    commands = _commands_for(
        "final",
        send_final_only=True,
        candidate_scope="number",
        text="SỐ CHÍN",
    )

    assert [command[0] for command in commands] == [9]
