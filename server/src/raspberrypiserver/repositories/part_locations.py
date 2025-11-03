"""Repositories for part locations."""

from __future__ import annotations

import logging
from typing import Iterable, Protocol

import psycopg
from psycopg.rows import dict_row

from .scans import InMemoryScanRepository, ScanRepository

logger = logging.getLogger(__name__)


class PartLocationRepository(Protocol):
    """Protocol for listing part locations."""

    def list(self, limit: int = 200) -> Iterable[dict]:  # noqa: D401
        """Return recent part locations."""


class DatabasePartLocationRepository:
    """PostgreSQL-backed part location repository."""

    def __init__(self, dsn: str, connect=psycopg.connect) -> None:
        self.dsn = dsn
        self._connect = connect

    def list(self, limit: int = 200) -> Iterable[dict]:
        if not self.dsn:
            logger.debug("PartLocationRepository skipped: DSN not configured")
            return []

        try:
            with self._connect(self.dsn) as conn, conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT order_code, location_code, device_id, updated_at
                    FROM part_locations
                    ORDER BY updated_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
                return list(rows)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch part locations: %s", exc)
            return []


class InMemoryPartLocationRepository:
    """In-memory location repository based on scan repository buffer."""

    def __init__(self, scan_repository: ScanRepository) -> None:
        self._scan_repository = scan_repository

    def list(self, limit: int = 200) -> Iterable[dict]:
        if isinstance(self._scan_repository, InMemoryScanRepository):
            return list(self._scan_repository.recent(limit))
        return []
