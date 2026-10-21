from __future__ import annotations

import re
import time

from pricetyper.senders.desktop_sender import SenderPrepareError
from pricetyper.types import SendResult

DEFAULT_CHAT_INPUT_SELECTORS = [
    '[data-e2e="room-chat-input-field"]',
    '[contenteditable]:not([contenteditable="false"])',
    '[role="textbox"]',
    "textarea:not([disabled]):not([readonly])",
    'input:not([type]), input[type="text"], input[type="search"]',
]


class BrowserExtensionSender:
    """Fill or submit a number in the TikTok Live tab supplying audio."""

    name = "browser_extension"

    def __init__(self, source, config, *, submit_enabled: bool = False):
        self.source = source
        self.selectors = list(
            config.chat_input_selectors or DEFAULT_CHAT_INPUT_SELECTORS
        )
        self.submit_enabled = submit_enabled
        self._prepared_session: tuple[str, str, str] | None = None

    @property
    def draft_only(self) -> bool:
        return not self.submit_enabled

    def prepare(self) -> None:
        session = self.source.session
        if not self.source.tiktok_live_connected or session is None:
            raise SenderPrepareError(
                "Connect the PriceTyper extension to a TikTok Live tab first"
            )
        result = self.source.request_tab_action(
            {
                "action": "probe",
                "selectors": self.selectors,
            }
        )
        if not result.get("ok"):
            raise SenderPrepareError(
                result.get("error") or "No unique visible chat input was found"
            )
        self._prepared_session = (
            session["tab_id"],
            session["host"],
            session["path"],
        )

    def send(self, text: str) -> SendResult:
        start = time.perf_counter_ns()
        if not text.isascii() or not re.fullmatch(r"[0-9]+", text):
            raise ValueError("browser extension sender accepts ASCII digits only")
        session = self.source.session
        current_session = (
            (session["tab_id"], session["host"], session["path"])
            if session is not None
            else None
        )
        if (
            not self.source.tiktok_live_connected
            or current_session is None
            or current_session != self._prepared_session
        ):
            return SendResult(
                False,
                start,
                time.perf_counter_ns(),
                "The prepared TikTok Live tab is no longer connected",
            )
        try:
            action_name = "submit" if self.submit_enabled else "draft"
            result = self.source.request_tab_action(
                {
                    "action": action_name,
                    "text": text,
                    "selectors": self.selectors,
                }
            )
        except Exception as exc:  # noqa: BLE001 - bridge/runtime failures must disarm without retry
            return SendResult(False, start, time.perf_counter_ns(), str(exc))
        if not result.get("ok"):
            return SendResult(
                False,
                start,
                time.perf_counter_ns(),
                result.get("error") or "The browser rejected the tab action",
            )
        expected_delivery = (
            "enter_dispatched_unverified"
            if self.submit_enabled
            else "draft_filled_unsubmitted"
        )
        if result.get("delivery") != expected_delivery:
            return SendResult(
                False,
                start,
                time.perf_counter_ns(),
                "The browser did not acknowledge the requested tab action",
            )
        if self.submit_enabled:
            return SendResult(
                True,
                start,
                time.perf_counter_ns(),
                "send_unverified: Enter was dispatched; comment appearance is not confirmed",
            )
        return SendResult(True, start, time.perf_counter_ns())

    def close(self) -> None:
        self._prepared_session = None


__all__ = ["DEFAULT_CHAT_INPUT_SELECTORS", "BrowserExtensionSender"]
