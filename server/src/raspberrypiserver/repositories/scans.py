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


class DatabaseScanRepository:
    """
    Placeholder repository that represents the future database-backed implementation.

    For現在の段階では実際の DB 書き込みを行わず、内部バッファに保持しつつ
    「TODO: persist」ログを残す実装とする。
    """

    def __init__(self, dsn: str, buffer_size: int = 500) -> None:
        self._dsn = dsn
        self._buffer: Deque[Dict] = deque(maxlen=buffer_size)

    @property
    def dsn(self) -> str:
        return self._dsn

    def save(self, payload: Dict) -> None:
        # TODO: replace with actual INSERT/UPSERT against PostgreSQL
        self._buffer.append(payload)

    def recent(self, limit: int = 10) -> Iterable[Dict]:
        if limit <= 0:
            return []
        return list(self._buffer)[-limit:]
