"""
Repository abstraction for scan ingestion.

This module defines a minimal interface to allow swapping implementations
when database integration is ready. For now it keeps recent payloads in memory
and exposes hooks for future persistence.
"""

from __future__ import annotations

from collections import deque
from typing import Deque, Dict, Iterable, Protocol


class ScanRepository(Protocol):
    """Protocol defining scan repository behavior."""

    def save(self, payload: Dict) -> None:  # noqa: D401
        """Persist a scan payload."""

    def recent(self, limit: int = 10) -> Iterable[Dict]:
        """Return most recent payloads (debug/testing aid)."""


class InMemoryScanRepository:
    """Simple in-memory storage for development/testing."""

    def __init__(self, capacity: int = 100) -> None:
        self._items: Deque[Dict] = deque(maxlen=capacity)

    def save(self, payload: Dict) -> None:
        self._items.append(payload)

    def recent(self, limit: int = 10) -> Iterable[Dict]:
        if limit <= 0:
            return []
        return list(self._items)[-limit:]
