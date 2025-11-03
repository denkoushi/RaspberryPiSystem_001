"""Broadcast utilities (Socket.IO placeholder)."""

from __future__ import annotations

import logging
from typing import Any, Dict, Protocol

logger = logging.getLogger(__name__)


class BroadcastService(Protocol):
    """Protocol for emitting events to connected clients."""

    def emit(self, event: str, payload: Dict[str, Any]) -> None:  # noqa: D401
        """Emit an event with payload."""


class SocketIOBroadcastService:
    """Placeholder Socket.IO broadcaster."""

    def __init__(self, socketio=None, namespace: str = "/scans", default_event: str | None = None) -> None:
        self._socketio = socketio
        self._namespace = namespace
        self._default_event = default_event

    def emit(self, event: str, payload: Dict[str, Any]) -> None:
        actual_event = event or self._default_event
        if self._socketio is None:
            logger.debug("SocketIO not configured; skipping broadcast for %s", actual_event)
            return
        try:
            self._socketio.emit(actual_event, payload, namespace=self._namespace)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Socket.IO emit failed: %s", exc)
