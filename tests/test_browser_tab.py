from __future__ import annotations

import pytest
from websockets.exceptions import ConnectionClosed, InvalidStatus
from websockets.sync.client import connect

from pricetyper.audio.browser_tab import (
    BrowserTabSource,
    extension_origin_from_manifest,
)

EXTENSION_ORIGIN = extension_origin_from_manifest()


def test_browser_tab_source_receives_exact_pcm_chunk():
    source = BrowserTabSource(port=0, queue_max_chunks=2)
    source.start()
    try:
        payload = b"\x01\x00" * 640
        with connect(
            f"ws://127.0.0.1:{source.port}/audio",
            origin=EXTENSION_ORIGIN,
            compression=None,
        ) as client:
            client.send(payload)
            received = source.read()
            assert received is not None
            pcm, timestamp_ns = received
            assert pcm == payload
            assert timestamp_ns > 0
            assert source.connected
    finally:
        source.stop()
    assert not source.connected


def test_browser_tab_source_rejects_non_extension_origin():
    source = BrowserTabSource(port=0)
    source.start()
    try:
        with pytest.raises(InvalidStatus):
            connect(
                f"ws://127.0.0.1:{source.port}/audio",
                origin="https://youtube.com",
                compression=None,
            )
    finally:
        source.stop()


def test_browser_tab_source_rejects_other_extension_origin():
    source = BrowserTabSource(port=0)
    source.start()
    other_origin = "chrome-extension://" + ("a" * 32)
    if other_origin == EXTENSION_ORIGIN:
        other_origin = "chrome-extension://" + ("b" * 32)
    try:
        with pytest.raises(InvalidStatus):
            connect(
                f"ws://127.0.0.1:{source.port}/audio",
                origin=other_origin,
                compression=None,
            )
    finally:
        source.stop()


def test_tiktok_mode_accepts_audio_only_from_live_path():
    source = BrowserTabSource(
        port=0,
        expected_hosts={"tiktok.com", "www.tiktok.com", "m.tiktok.com"},
        expected_tiktok_live=True,
    )
    source.start()
    try:
        payload = b"\x02\x00" * 640
        with connect(
            f"ws://127.0.0.1:{source.port}/audio?host=www.tiktok.com&path=%2F%40seller%2Flive&tab_id=7",
            origin=EXTENSION_ORIGIN,
            compression=None,
        ) as client:
            client.send(payload)
            received = source.read()
            assert received is not None and received[0] == payload
    finally:
        source.stop()


def test_tiktok_mode_rejects_non_live_audio_path():
    source = BrowserTabSource(
        port=0,
        expected_hosts={"tiktok.com", "www.tiktok.com", "m.tiktok.com"},
        expected_tiktok_live=True,
    )
    source.start()
    try:
        with connect(
            f"ws://127.0.0.1:{source.port}/audio?host=www.tiktok.com&path=%2F%40seller%2Fvideo%2F123",
            origin=EXTENSION_ORIGIN,
            compression=None,
        ) as client, pytest.raises(ConnectionClosed):
            client.recv(timeout=1)
    finally:
        source.stop()
