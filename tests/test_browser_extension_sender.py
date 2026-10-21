from typing import ClassVar

from pricetyper.config import PlaywrightConfig
from pricetyper.senders.browser_extension_sender import BrowserExtensionSender


class FakeBrowserTabSource:
    tiktok_live_connected = True
    session: ClassVar[dict[str, str]] = {
        "tab_id": "17",
        "host": "www.tiktok.com",
        "path": "/@seller/live",
    }

    def __init__(self):
        self.actions = []

    def request_tab_action(self, action):
        self.actions.append(action)
        if action["action"] == "probe":
            return {"ok": True}
        if action["action"] == "draft":
            return {"ok": True, "delivery": "draft_filled_unsubmitted"}
        if action["action"] == "submit":
            return {"ok": True, "delivery": "enter_dispatched_unverified"}
        return {"ok": False, "error": "unexpected action"}


def test_extension_sender_defaults_to_fill_only():
    source = FakeBrowserTabSource()
    sender = BrowserExtensionSender(source, PlaywrightConfig())
    assert sender.selectors[0] == '[data-e2e="room-chat-input-field"]'
    sender.prepare()

    result = sender.send("9")

    assert result.ok
    assert sender.draft_only
    assert [action["action"] for action in source.actions] == ["probe", "draft"]


def test_extension_sender_submit_mode_reports_unverified_enter_dispatch():
    source = FakeBrowserTabSource()
    sender = BrowserExtensionSender(source, PlaywrightConfig(), submit_enabled=True)
    sender.prepare()

    result = sender.send("9")

    assert result.ok
    assert not sender.draft_only
    assert source.actions[-1]["action"] == "submit"
    assert result.error.startswith("send_unverified:")
