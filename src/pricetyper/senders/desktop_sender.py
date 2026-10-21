from __future__ import annotations

import time

from pricetyper.types import SendResult


class SenderPrepareError(RuntimeError):
    pass


class SenderFailSafeError(RuntimeError):
    pass


def _load_pyautogui():
    """Load the optional desktop-control dependency only when that sender is used."""
    try:
        import pyautogui
    except ImportError as exc:
        raise SenderPrepareError(
            "Desktop sender requires the optional PyAutoGUI dependency."
        ) from exc
    return pyautogui


class DesktopSender:
    name = 'desktop'

    def __init__(self, chat_xy, send_xy=None, click_each_time=True, send_mode='enter'):
        self.chat_xy, self.send_xy = chat_xy, send_xy
        self.click_each_time, self.send_mode = click_each_time, send_mode
        self._pyautogui = None

    def prepare(self) -> None:
        pyautogui = _load_pyautogui()
        self._pyautogui = pyautogui
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = True
        if not self.chat_xy:
            raise SenderPrepareError('sender.desktop.chat_xy must be configured')
        if self.send_mode == 'click_button' and not self.send_xy:
            raise SenderPrepareError('sender.desktop.send_xy is required for click_button')

    def send(self, text: str) -> SendResult:
        if not text.isascii():
            raise ValueError('sender text must contain ASCII characters only')
        pyautogui = self._pyautogui or _load_pyautogui()
        start = time.perf_counter_ns()
        try:
            if self.click_each_time:
                pyautogui.click(*self.chat_xy)
            pyautogui.typewrite(text, interval=0)
            if self.send_mode == 'enter':
                pyautogui.press('enter')
            else:
                pyautogui.click(*self.send_xy)
            return SendResult(True, start, time.perf_counter_ns())
        except pyautogui.FailSafeException as exc:
            raise SenderFailSafeError(str(exc)) from exc
        except Exception as exc:
            return SendResult(False, start, time.perf_counter_ns(), str(exc))

    def close(self) -> None:
        pass
