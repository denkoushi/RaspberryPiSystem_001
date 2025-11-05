from __future__ import annotations

import logging
from typing import Any, Dict

import pytest

from raspberrypiserver.services.broadcast import SocketIOBroadcastService


class DummySocket:
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls: list[tuple[str, Dict[str, Any], str]] = []

    def emit(self, event: str, payload: Dict[str, Any], namespace: str | None = None):
        if self.should_fail:
            raise RuntimeError("emit failed")
        self.calls.append((event, payload, namespace or "/"))


def test_emit_uses_default_event_and_logs_success(caplog: pytest.LogCaptureFixture):
    socket = DummySocket()
    service = SocketIOBroadcastService(socketio=socket, namespace="/demo", default_event="scan.ingested")

    caplog.set_level(logging.INFO)
    payload = {"order_code": "X", "location_code": "Y"}
    service.emit("", payload)

    assert socket.calls == [("scan.ingested", payload, "/demo")]
    assert any("Socket.IO emit succeeded" in message for message in caplog.messages)


def test_emit_logs_failure_when_socket_raises(caplog: pytest.LogCaptureFixture):
    socket = DummySocket(should_fail=True)
    service = SocketIOBroadcastService(socketio=socket, namespace="/demo", default_event="scan.ingested")

    caplog.set_level(logging.WARNING)
    payload = {"order_code": "ERR", "location_code": "LOC"}
    service.emit("scan.custom", payload)

    assert any("Socket.IO emit failed" in message for message in caplog.messages)
