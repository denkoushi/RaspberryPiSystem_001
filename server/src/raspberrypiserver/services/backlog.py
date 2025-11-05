"""Backlog draining utilities."""

from __future__ import annotations

import logging
from typing import Iterable, List, Optional, Tuple

import psycopg
from psycopg import sql

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

        requested_limit = limit or self.limit
        if requested_limit <= 0:
            return 0

        drained = 0
        try:
            with self._connect(self.dsn) as conn, conn.cursor() as cur:
                candidates = self._select_candidates(cur, requested_limit)
                if not candidates:
                    logger.debug(
                        "Backlog drain skipped: no rows available (limit=%s)", requested_limit
                    )
                    conn.commit()
                    return 0

                valid_rows = self._upsert_locations(cur, candidates)
                if valid_rows:
                    self._delete_backlog_rows(cur, [row[0] for row in valid_rows])
                    drained = len(valid_rows)
                    logger.info(
                        "Backlog drain succeeded: processed=%s limit=%s table=%s",
                        drained,
                        requested_limit,
                        self.backlog_table,
                    )
                else:
                    logger.warning("No valid backlog rows processed (missing order/location codes)")

                conn.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Backlog drain failed: %s", exc)
        return drained

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

    def _select_candidates(self, cur, limit: int) -> List[Tuple[int, str, str, Optional[str]]]:
        cur.execute(
            sql.SQL(
                """
                SELECT id,
                       payload->>'order_code' AS order_code,
                       payload->>'location_code' AS location_code,
                       payload->>'device_id' AS device_id
                FROM {backlog}
                ORDER BY received_at
                LIMIT %s
                FOR UPDATE SKIP LOCKED
                """
            ).format(backlog=sql.Identifier(self.backlog_table)),
            (limit,),
        )
        rows = cur.fetchall()
        candidates: List[Tuple[int, str, str, Optional[str]]] = []
        for row in rows:
            row_id, order_code, location_code, device_id = row
            if not order_code or not location_code:
                logger.warning(
                    "Skipping backlog row id=%s due to missing order/location (order=%s, location=%s)",
                    row_id,
                    order_code,
                    location_code,
                )
                continue
            candidates.append((row_id, order_code, location_code, device_id))
        return candidates

    def _upsert_locations(
        self,
        cur,
        candidates: Iterable[Tuple[int, str, str, Optional[str]]],
    ) -> List[Tuple[int, str, str, Optional[str]]]:
        processed: List[Tuple[int, str, str, Optional[str]]] = []
        for row_id, order_code, location_code, device_id in candidates:
            cur.execute(
                sql.SQL(
                    """
                    INSERT INTO {target} (order_code, location_code, device_id, updated_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (order_code)
                    DO UPDATE SET
                        location_code = EXCLUDED.location_code,
                        device_id = EXCLUDED.device_id,
                        updated_at = NOW()
                    """
                ).format(target=sql.Identifier(self.target_table)),
                (order_code, location_code, device_id),
            )
            processed.append((row_id, order_code, location_code, device_id))
        return processed

    def _delete_backlog_rows(self, cur, ids: List[int]) -> None:
        if not ids:
            return
        cur.execute(
            sql.SQL("DELETE FROM {backlog} WHERE id = ANY(%s)").format(
                backlog=sql.Identifier(self.backlog_table)
            ),
            (ids,),
        )
