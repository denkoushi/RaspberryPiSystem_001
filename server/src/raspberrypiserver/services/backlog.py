"""Backlog draining utilities."""

from __future__ import annotations

import logging
from typing import Optional

import psycopg

logger = logging.getLogger(__name__)


class BacklogDrainService:
    """Service to drain scan backlog into canonical tables."""

    def __init__(self, dsn: str, limit: int = 100) -> None:
        self.dsn = dsn
        self.limit = limit

    def is_configured(self) -> bool:
        return bool(self.dsn)

    def drain_once(self, limit: Optional[int] = None) -> int:
        if not self.dsn:
            logger.debug("Backlog drain skipped: DSN not configured")
            return 0

        rows = 0
        try:
            with psycopg.connect(self.dsn) as conn, conn.cursor() as cur:
                cur.execute("SELECT drain_scan_backlog(%s)", (limit or self.limit,))
                rows = cur.fetchone()[0]
                conn.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Backlog drain failed: %s", exc)
        return rows
