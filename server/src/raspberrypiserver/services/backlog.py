"""Backlog draining utilities."""

from __future__ import annotations

import logging
from typing import Optional

import psycopg

logger = logging.getLogger(__name__)


class BacklogDrainService:
    """Service to drain scan backlog into canonical tables."""

    def __init__(
        self,
        dsn: str,
        limit: int = 100,
        backlog_table: str = "scan_ingest_backlog",
        target_table: str = "part_locations",
        connect=psycopg.connect,
    ) -> None:
        self.dsn = dsn
        self.limit = limit
        self.backlog_table = backlog_table
        self.target_table = target_table
        self._connect = connect

    def is_configured(self) -> bool:
        return bool(self.dsn)

    def drain_once(self, limit: Optional[int] = None) -> int:
        if not self.dsn:
            logger.debug("Backlog drain skipped: DSN not configured")
            return 0

        rows = 0
        try:
            with self._connect(self.dsn) as conn, conn.cursor() as cur:
                cur.execute("SELECT drain_scan_backlog(%s)", (limit or self.limit,))
                rows = cur.fetchone()[0]
                conn.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Backlog drain failed: %s", exc)
        return rows

    def count_backlog(self) -> int:
        """Return number of pending backlog records."""
        if not self.dsn:
            logger.debug("Backlog count skipped: DSN not configured")
            return 0

        try:
            with self._connect(self.dsn) as conn, conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) FROM scan_ingest_backlog
                    """
                )
                (count,) = cur.fetchone()
                return int(count)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Backlog count failed: %s", exc)
            return 0
