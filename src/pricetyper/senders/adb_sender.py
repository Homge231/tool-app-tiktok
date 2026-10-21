from __future__ import annotations

import subprocess
import time

from pricetyper.senders.desktop_sender import SenderPrepareError
from pricetyper.types import SendResult


class AdbSender:
    name = 'adb'

    def __init__(self, adb_path='adb', serial='', chat_xy=None, send_xy=None, send_keyevent=66, send_mode='enter'):
        self.adb_path, self.serial = adb_path, serial
        self.chat_xy, self.send_xy = chat_xy, send_xy
        self.send_keyevent, self.send_mode = send_keyevent, send_mode

    def _base(self):
        return [self.adb_path, '-s', self.serial]

    def prepare(self) -> None:
        try:
            if not self.serial:
                output = subprocess.run([self.adb_path, 'devices'], capture_output=True, text=True, timeout=3, check=True).stdout
                devices = [line.split()[0] for line in output.splitlines()[1:] if len(line.split()) >= 2 and line.split()[1] == 'device']
                if len(devices) != 1:
                    raise SenderPrepareError(f'Expected exactly one adb device; found {len(devices)}')
                self.serial = devices[0]
            if not self.chat_xy:
                raise SenderPrepareError('sender.adb.chat_xy must be configured')
            if self.send_mode == 'click_button' and not self.send_xy:
                raise SenderPrepareError('sender.adb.send_xy is required for click_button')
            result = subprocess.run(self._base() + ['get-state'], capture_output=True, text=True, timeout=3)
            if result.returncode or result.stdout.strip() != 'device':
                raise SenderPrepareError(f'adb device is not ready: {result.stdout.strip()} {result.stderr.strip()}')
        except SenderPrepareError:
            raise
        except Exception as exc:
            raise SenderPrepareError(f'ADB sender could not prepare: {exc}') from exc

    def send(self, text: str) -> SendResult:
        if not text.isascii() or not text.isdigit():
            raise ValueError('ADB sender accepts only ASCII digits')
        start = time.perf_counter_ns()
        x, y = self.chat_xy
        command = f'input tap {x} {y}; input text {text}; '
        if self.send_mode == 'enter':
            command += f'input keyevent {self.send_keyevent}'
        else:
            sx, sy = self.send_xy
            command += f'input tap {sx} {sy}'
        try:
            subprocess.run(self._base() + ['shell', command], capture_output=True, text=True, timeout=3, check=True)
            return SendResult(True, start, time.perf_counter_ns())
        except Exception as exc:
            return SendResult(False, start, time.perf_counter_ns(), str(exc))

    def close(self) -> None:
        pass
