"""Production plan and standard time providers."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable, Protocol

import psycopg
from psycopg import sql

logger = logging.getLogger(__name__)


class PlanProvider(Protocol):
    """Protocol for production plan provider."""

    def list_entries(self, limit: int = 200) -> Iterable[dict]:
        ...


class StandardTimeProvider(Protocol):
    """Protocol for standard time provider."""

    def list_entries(self, limit: int = 200) -> Iterable[dict]:
        ...


class FileJSONProvider(PlanProvider, StandardTimeProvider):
    """Generic provider reading entries from a JSON file."""

    def __init__(self, file_path: str | Path):
        self._path = Path(file_path).expanduser()

    def list_entries(self, limit: int = 200) -> Iterable[dict]:
        if not self._path.exists():
            return []
        try:
            content = self._path.read_text(encoding="utf-8")
            data = json.loads(content)
        except (OSError, json.JSONDecodeError):
            return []
        items = data.get("entries") if isinstance(data, dict) else data
        if not isinstance(items, list):
            return []
        return items[: max(1, limit)]


class DatabaseJSONProvider(PlanProvider, StandardTimeProvider):
    """Read plan entries stored as JSON payloads in PostgreSQL tables."""

    def __init__(
        self,
        dsn: str,
        table: str,
        connect=psycopg.connect,
    ) -> None:
        self._dsn = dsn
        self._table = table
        self._connect = connect

    def list_entries(self, limit: int = 200) -> Iterable[dict]:
        if not self._dsn or not self._table:
            return []
        try:
            with self._connect(self._dsn) as conn, conn.cursor() as cur:
                cur.execute(
                    sql.SQL("SELECT payload FROM {} ORDER BY inserted_at DESC LIMIT %s").format(
                        sql.Identifier(self._table)
                    ),
                    (max(1, min(limit, 1000)),),
                )
                rows = cur.fetchall()
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to fetch entries from %s using DB provider: %s",
                self._table,
                exc,
            )
            return []

        entries: list[dict] = []
        for (payload,) in rows:
            if isinstance(payload, dict):
                entries.append(payload)
        return entries
