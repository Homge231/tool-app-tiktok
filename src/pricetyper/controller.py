from __future__ import annotations

import os
import threading
from enum import Enum


class State(str, Enum):
    LISTENING = 'LISTENING'
    ARMED = 'ARMED'
    STOPPED = 'STOPPED'


class Controller:
    def __init__(self, sender, logger=None):
        self.sender, self.logger = sender, logger
        self.armed = threading.Event()
        self.stop_event = threading.Event()
        self._lock = threading.RLock()
        self._callbacks = []
        self.state = State.LISTENING
        self._preparing = False
        self._cancel_arm = False

    def subscribe(self, callback):
        self._callbacks.append(callback)

    def _set_state(self, state: State, cause: str):
        with self._lock:
            if self.state == state:
                return
            self.state = state
            (self.armed.set if state == State.ARMED else self.armed.clear)()
        if self.logger:
            self.logger.log('state', state=state.value, cause=cause)
        for callback in tuple(self._callbacks):
            callback(state)

    def arm(self):
        with self._lock:
            if self.state == State.STOPPED or self.stop_event.is_set():
                raise RuntimeError('Controller is stopped')
            if self.armed.is_set():
                return
            if self._preparing:
                raise RuntimeError('Sender preparation is already in progress')
            self._preparing = True
            self._cancel_arm = False
        try:
            self.sender.prepare()
        finally:
            with self._lock:
                self._preparing = False
        with self._lock:
            if self._cancel_arm or self.state == State.STOPPED or self.stop_event.is_set():
                return
            self._set_state(State.ARMED, 'arm')

    def disarm(self):
        with self._lock:
            if self._preparing:
                self._cancel_arm = True
            if self.state != State.STOPPED:
                self._set_state(State.LISTENING, 'disarm')

    def toggle(self):
        if self.armed.is_set() or self._preparing:
            self.disarm()
        else:
            self.arm()

    def panic(self):
        with self._lock:
            self.armed.clear()
            self._cancel_arm = True
            self.stop_event.set()
            self._set_state(State.STOPPED, 'panic')
        thread = threading.Thread(target=self.sender.close, daemon=True)
        thread.start()
        thread.join(1)
        os._exit(130)
