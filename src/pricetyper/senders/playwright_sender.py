from __future__ import annotations

import fnmatch
import queue
import threading
import time
from concurrent.futures import Future
from pathlib import Path
from urllib.parse import urlsplit

from pricetyper.senders.desktop_sender import SenderPrepareError
from pricetyper.types import SendResult


class PlaywrightSender:
    name = 'playwright'

    def __init__(
        self,
        config,
        send_mode='enter',
        thread_bound=True,
        extension_path=None,
        expected_hosts=None,
    ):
        self.cfg = config
        self.send_mode = send_mode
        self.thread_bound = thread_bound
        self.extension_path = Path(extension_path).resolve() if extension_path else None
        self.expected_hosts = (
            frozenset(host.lower() for host in expected_hosts)
            if expected_hosts is not None
            else None
        )
        self.playwright = self.context = self.page = self.locator = None
        self._tasks = queue.Queue()
        self._worker = None

    def _call_on_worker(self, fn, *args):
        if not self.thread_bound:
            return fn(*args)
        if self._worker is None:
            self._worker = threading.Thread(target=self._worker_loop, name='playwright-sender', daemon=True)
            self._worker.start()
        future = Future()
        self._tasks.put((fn, args, future))
        return future.result()

    def _worker_loop(self):
        while True:
            task = self._tasks.get()
            if task is None:
                return
            fn, args, future = task
            try:
                future.set_result(fn(*args))
            except BaseException as exc:
                future.set_exception(exc)

    def prepare(self) -> None:
        return self._call_on_worker(self._prepare_impl)

    def _prepare_impl(self) -> None:
        if self.page is not None and self.locator is not None:
            return
        if self.thread_bound and self.send_mode == 'click_button' and not self.cfg.send_button_selector:
            raise SenderPrepareError('sender.playwright.send_button_selector is required for click_button')
        from playwright.sync_api import sync_playwright
        self.playwright = sync_playwright().start()
        try:
            if self.cfg.attach == 'cdp':
                browser = self.playwright.chromium.connect_over_cdp(self.cfg.cdp_url)
                self.context = browser.contexts[0]
            else:
                launch_args = []
                if self.extension_path is not None:
                    if not self.extension_path.is_dir():
                        raise SenderPrepareError(
                            f'Browser extension directory was not found: {self.extension_path}'
                        )
                    extension = str(self.extension_path)
                    launch_args.extend(
                        [
                            f'--disable-extensions-except={extension}',
                            f'--load-extension={extension}',
                        ]
                    )
                self.context = self.playwright.chromium.launch_persistent_context(
                    user_data_dir=self.cfg.user_data_dir, channel=self.cfg.channel,
                    headless=False, no_viewport=True, args=launch_args)
            for page in self.context.pages:
                if fnmatch.fnmatch(page.url, self.cfg.url_pattern.replace('**/', '*/')):
                    self.page = page
                    break
            if self.page is None and self.cfg.live_url:
                self.page = self.context.new_page()
                self.page.goto(self.cfg.live_url)
            if self.page is None:
                deadline = time.monotonic() + 120
                while time.monotonic() < deadline and self.page is None:
                    for page in self.context.pages:
                        if fnmatch.fnmatch(page.url, self.cfg.url_pattern.replace('**/', '*/')):
                            self.page = page
                            break
                    time.sleep(.25)
            if self.page is None:
                raise SenderPrepareError('No live page found before timeout')
            if self.expected_hosts is not None:
                host = (urlsplit(self.page.url).hostname or '').lower()
                if host not in self.expected_hosts:
                    raise SenderPrepareError(
                        f'Active page host {host!r} is not allowed for this sender mode'
                    )
            for selector in self.cfg.chat_input_selectors:
                try:
                    locator = self.page.locator(selector)
                    locator.wait_for(state='visible', timeout=30000)
                    if locator.count() != 1 or not locator.is_visible():
                        continue
                    self.locator = locator
                    break
                except Exception:
                    continue
            if self.locator is None:
                raise SenderPrepareError('No configured chat input selector became visible')
        except SenderPrepareError:
            self._close_impl()
            raise
        except Exception as exc:
            self._close_impl()
            raise SenderPrepareError(f'Playwright sender could not prepare: {exc}') from exc

    def send(self, text: str) -> SendResult:
        return self._call_on_worker(self._send_impl, text)

    def sent_messages_for_test(self):
        return self._call_on_worker(lambda: self.page.evaluate('window.__sent'))

    def _send_impl(self, text: str) -> SendResult:
        if not text.isascii():
            raise ValueError('sender text must contain ASCII characters only')
        start = time.perf_counter_ns()
        try:
            self._validate_active_page()
            if (
                self.locator is None
                or self.locator.count() != 1
                or not self.locator.is_visible()
            ):
                raise SenderPrepareError('The configured chat input is no longer uniquely visible')
            if self.cfg.focus_each_time:
                self.locator.focus()
            self._validate_active_page()
            self.page.keyboard.insert_text(text)
            if self.send_mode == 'enter':
                self.page.keyboard.press('Enter')
            else:
                self.page.locator(self.cfg.send_button_selector).click()
            if self.cfg.verify_after_send:
                time.sleep(.05)
                remaining = self.locator.evaluate('e => (e.value !== undefined ? e.value : e.innerText)')
                if remaining:
                    return SendResult(True, start, time.perf_counter_ns(), 'send_unverified: input still contains text')
            return SendResult(True, start, time.perf_counter_ns())
        except Exception as exc:
            return SendResult(False, start, time.perf_counter_ns(), str(exc))

    def _validate_active_page(self) -> None:
        if self.page is None:
            raise SenderPrepareError('Sender has not been prepared')
        if self.expected_hosts is None:
            return
        host = (urlsplit(self.page.url).hostname or '').lower()
        if host not in self.expected_hosts:
            raise SenderPrepareError(
                f'Active page host {host!r} is not allowed for this sender mode'
            )
        if not fnmatch.fnmatch(self.page.url, self.cfg.url_pattern.replace('**/', '*/')):
            raise SenderPrepareError('Active page is no longer a configured livestream URL')

    def close(self) -> None:
        if self.thread_bound and self._worker is not None:
            try:
                self._call_on_worker(self._close_impl)
            finally:
                self._tasks.put(None)
                self._worker.join(timeout=1)
                self._worker = None
            return
        self._close_impl()

    def _close_impl(self) -> None:
        if self.context is not None and self.cfg.attach != 'cdp':
            try:
                self.context.close()
            except Exception:
                pass
        if self.playwright is not None:
            try:
                self.playwright.stop()
            except Exception:
                pass
        self.context = self.playwright = None
        self.page = self.locator = None
