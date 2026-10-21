from __future__ import annotations

import base64
import hashlib
import json
import queue
import re
import threading
import time
import uuid
from urllib.parse import parse_qs, urlsplit

from websockets.exceptions import ConnectionClosed
from websockets.sync.server import ServerConnection, serve

from pricetyper.runtime_paths import resource_root

YOUTUBE_HOSTS = frozenset(
    {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
)
TIKTOK_HOSTS = frozenset({"tiktok.com", "www.tiktok.com", "m.tiktok.com"})


def extension_origin_from_manifest() -> str:
    """Pin the local bridge to the extension ID derived from its manifest key."""
    manifest_path = resource_root() / "browser_extension" / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        public_key = base64.b64decode(manifest["key"], validate=True)
    except (OSError, KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"NumberTyper cannot verify its browser extension ID; check {manifest_path}"
        ) from exc

    digest = hashlib.sha256(public_key).digest()[:16]
    extension_id = "".join(
        chr(ord("a") + nibble) for byte in digest for nibble in (byte >> 4, byte & 0x0F)
    )
    return f"chrome-extension://{extension_id}"


class BrowserTabSource:
    """Receive fixed-size PCM chunks from the user's Chromium tab-capture extension."""

    SAMPLE_RATE = 16_000
    CHUNK_MS = 40
    CHUNK_BYTES = SAMPLE_RATE * CHUNK_MS // 1000 * 2

    def __init__(
        self,
        port: int = 8765,
        chunk_ms: int = 40,
        queue_max_chunks: int = 50,
        expected_hosts: set[str] | frozenset[str] | None = None,
        expected_tiktok_live: bool = False,
        extension_origin: str | None = None,
    ):
        if chunk_ms != self.CHUNK_MS:
            raise ValueError("Browser tab PCM chunks must be exactly 40 ms")
        self.requested_port = port
        self.port = port
        self.queue_max_chunks = queue_max_chunks
        self.expected_hosts = (
            frozenset(host.lower() for host in expected_hosts)
            if expected_hosts is not None
            else None
        )
        self.expected_tiktok_live = expected_tiktok_live
        self.extension_origin = extension_origin or extension_origin_from_manifest()
        self._chunks: queue.Queue[tuple[bytes, int]] = queue.Queue(
            maxsize=queue_max_chunks
        )
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._client_lock = threading.Lock()
        self._websocket_lock = threading.Lock()
        self._pending_lock = threading.Lock()
        self._pending_actions: dict[str, queue.Queue[dict]] = {}
        self._active_websocket: ServerConnection | None = None
        self._session_lock = threading.Lock()
        self._session: dict | None = None
        self._server = None
        self._thread: threading.Thread | None = None
        self._startup_error: BaseException | None = None
        self._connected = threading.Event()
        self._overflow_count = 0
        self._overflow_lock = threading.Lock()

    @property
    def connected(self) -> bool:
        return self._connected.is_set()

    @property
    def session(self) -> dict | None:
        with self._session_lock:
            return dict(self._session) if self._session is not None else None

    @property
    def tiktok_live_connected(self) -> bool:
        session = self.session
        return bool(
            self.connected
            and self.expected_tiktok_live
            and session
            and session["host"] in TIKTOK_HOSTS
            and re.fullmatch(r"/@[^/]+/live/?", session["path"])
        )

    @property
    def overflow_count(self) -> int:
        with self._overflow_lock:
            return self._overflow_count

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._ready_event.clear()
        self._startup_error = None
        self._thread = threading.Thread(
            target=self._serve, name="browser-tab-audio-server", daemon=True
        )
        self._thread.start()
        if not self._ready_event.wait(timeout=5):
            self.stop()
            raise RuntimeError(
                "Timed out while starting the local browser audio bridge"
            )
        if self._startup_error is not None:
            error = self._startup_error
            self.stop()
            raise RuntimeError(
                "Could not bind browser audio bridge to "
                f"127.0.0.1:{self.requested_port}: {error}"
            ) from error

    def _serve(self) -> None:
        try:
            server = serve(
                self._handle_client,
                host="127.0.0.1",
                port=self.requested_port,
                origins=[self.extension_origin],
                compression=None,
                max_size=16_384,
                max_queue=2,
                open_timeout=5,
            )
            self._server = server
            self.port = server.socket.getsockname()[1]
            self._ready_event.set()
            server.serve_forever()
        except OSError as exc:
            self._startup_error = exc
            self._ready_event.set()
        finally:
            self._connected.clear()

    def _handle_client(self, websocket: ServerConnection) -> None:
        request = urlsplit(websocket.request.path)
        if request.path != "/audio":
            websocket.close(code=1008, reason="Expected /audio")
            return
        source_host = parse_qs(request.query).get("host", [""])[0].lower()
        source_path = parse_qs(request.query).get("path", [""])[0]
        browser_family = parse_qs(request.query).get("browser", ["chromium"])[0]
        source_tab_id = parse_qs(request.query).get("tab_id", [""])[0]
        if browser_family != "chromium":
            websocket.close(code=1008, reason="Unsupported browser adapter")
            return
        if self.expected_hosts is not None and source_host not in self.expected_hosts:
            websocket.close(code=1008, reason="Audio tab host does not match this mode")
            return
        if self.expected_tiktok_live and source_host in TIKTOK_HOSTS:
            if not re.fullmatch(r"/@[^/]+/live/?", source_path):
                websocket.close(code=1008, reason="Audio tab is not a TikTok Live page")
                return
            if not source_tab_id.isdecimal():
                websocket.close(code=1008, reason="TikTok tab identity is missing")
                return
        if not self._client_lock.acquire(blocking=False):
            websocket.close(code=1013, reason="Another capture is already connected")
            return
        session = {
            "browser": browser_family,
            "tab_id": source_tab_id,
            "host": source_host,
            "path": source_path,
        }
        with self._session_lock:
            self._session = session
        self._active_websocket = websocket
        self._connected.set()
        try:
            for message in websocket:
                if self._stop_event.is_set():
                    return
                if isinstance(message, str):
                    self._handle_action_result(message)
                    continue
                if not isinstance(message, bytes) or len(message) != self.CHUNK_BYTES:
                    websocket.close(
                        code=1003, reason="Expected one 40 ms mono PCM16 chunk"
                    )
                    return
                item = (message, time.perf_counter_ns())
                try:
                    self._chunks.put_nowait(item)
                except queue.Full:
                    try:
                        self._chunks.get_nowait()
                    except queue.Empty:
                        pass
                    with self._overflow_lock:
                        self._overflow_count += 1
                    self._chunks.put_nowait(item)
        except ConnectionClosed:
            pass
        finally:
            self._connected.clear()
            self._active_websocket = None
            with self._session_lock:
                self._session = None
            with self._pending_lock:
                pending = list(self._pending_actions.values())
                self._pending_actions.clear()
            for result_queue in pending:
                try:
                    result_queue.put_nowait(
                        {"ok": False, "error": "Browser tab disconnected"}
                    )
                except queue.Full:
                    pass
            self._client_lock.release()

    def _handle_action_result(self, message: str) -> None:
        try:
            result = json.loads(message)
        except (TypeError, json.JSONDecodeError):
            return
        if not isinstance(result, dict) or result.get("type") != "TAB_ACTION_RESULT":
            return
        action_id = result.get("id")
        if not isinstance(action_id, str):
            return
        with self._pending_lock:
            result_queue = self._pending_actions.get(action_id)
        if result_queue is not None:
            try:
                result_queue.put_nowait(result)
            except queue.Full:
                pass

    def request_tab_action(self, action: dict, timeout: float = 3.0) -> dict:
        if not self.tiktok_live_connected:
            raise RuntimeError("No supported TikTok Live tab is connected")
        websocket = self._active_websocket
        if websocket is None:
            raise RuntimeError("The selected browser tab is disconnected")
        action_id = uuid.uuid4().hex
        result_queue: queue.Queue[dict] = queue.Queue(maxsize=1)
        with self._pending_lock:
            self._pending_actions[action_id] = result_queue
        payload = {"type": "TAB_ACTION", "id": action_id, **action}
        try:
            with self._websocket_lock:
                websocket.send(json.dumps(payload, separators=(",", ":")))
            return result_queue.get(timeout=timeout)
        except queue.Empty as exc:
            raise TimeoutError("The browser did not acknowledge the tab action") from exc
        finally:
            with self._pending_lock:
                self._pending_actions.pop(action_id, None)

    def read(self) -> tuple[bytes, int] | None:
        while not self._stop_event.is_set():
            try:
                return self._chunks.get(timeout=0.25)
            except queue.Empty:
                continue
        return None

    def stop(self) -> None:
        self._stop_event.set()
        server = self._server
        if server is not None:
            server.shutdown(close_connections=True, reason="PriceTyper stopped")
            self._server = None
        if self._thread is not None and self._thread is not threading.current_thread():
            self._thread.join(timeout=2)
        self._thread = None
        self._connected.clear()
        while True:
            try:
                self._chunks.get_nowait()
            except queue.Empty:
                break


__all__ = ["BrowserTabSource"]
