"""Service layer for tool management (loans) operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable

import psycopg
from psycopg import sql


class ToolManagementError(Exception):
    """Base exception for tool management failures."""


class LoanNotFoundError(ToolManagementError):
    """Raised when a requested loan record does not exist."""


@dataclass
class ToolManagementService:
    """Database-backed helper for listing/manipulating tool loans."""

    dsn: str
    connect: Callable[..., psycopg.Connection] = psycopg.connect

    def _ensure_dsn(self) -> str:
        if not self.dsn:
            raise ToolManagementError("tool management DSN is not configured")
        return self.dsn

    def list_open_loans(self, limit: int = 100) -> list[dict]:
        self._ensure_dsn()
        limit_value = max(1, min(int(limit or 0) if isinstance(limit, int) else 100, 1000))
        query = sql.SQL(
            """
            SELECT l.id,
                   l.tool_uid,
                   COALESCE(t.name, l.tool_uid) AS tool_name,
                   l.borrower_uid,
                   COALESCE(u.full_name, l.borrower_uid) AS borrower_name,
                   l.loaned_at
              FROM loans l
         LEFT JOIN tools t ON t.uid = l.tool_uid
         LEFT JOIN users u ON u.uid = l.borrower_uid
             WHERE l.returned_at IS NULL
          ORDER BY l.loaned_at DESC
             LIMIT %s
            """
        )
        with self.connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(query, (limit_value,))
            rows = cur.fetchall()
        return [
            {
                "id": row[0],
                "tool_uid": row[1],
                "tool_name": row[2],
                "borrower_uid": row[3],
                "borrower_name": row[4],
                "loaned_at": _format_dt(row[5]),
            }
            for row in rows
        ]

    def list_recent_history(self, limit: int = 50) -> list[dict]:
        self._ensure_dsn()
        limit_value = max(1, min(int(limit or 0) if isinstance(limit, int) else 50, 500))
        query = sql.SQL(
            """
            SELECT CASE WHEN l.returned_at IS NULL THEN '貸出' ELSE '返却' END AS action,
                   COALESCE(t.name, l.tool_uid) AS tool_name,
                   COALESCE(u.full_name, l.borrower_uid) AS borrower_name,
                   l.loaned_at,
                   l.returned_at
              FROM loans l
         LEFT JOIN tools t ON t.uid = l.tool_uid
         LEFT JOIN users u ON u.uid = l.borrower_uid
          ORDER BY COALESCE(l.returned_at, l.loaned_at) DESC
             LIMIT %s
            """
        )
        with self.connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(query, (limit_value,))
            rows = cur.fetchall()
        return [
            {
                "action": row[0],
                "tool_name": row[1],
                "borrower_name": row[2],
                "loaned_at": _format_dt(row[3]),
                "returned_at": _format_dt(row[4]),
            }
            for row in rows
        ]

    def manual_return(self, loan_id: int) -> dict:
        self._ensure_dsn()
        if loan_id is None:
            raise ValueError("loan_id is required")
        query = sql.SQL(
            """
            UPDATE loans
               SET returned_at = NOW(),
                   return_user_uid = COALESCE(return_user_uid, borrower_uid)
             WHERE id=%s AND returned_at IS NULL
         RETURNING tool_uid, borrower_uid, return_user_uid
            """
        )
        with self.connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(query, (loan_id,))
            row = cur.fetchone()
            if not row:
                raise LoanNotFoundError(f"loan_id={loan_id} not found or already returned")
        return {
            "loan_id": loan_id,
            "tool_uid": row[0],
            "borrower_uid": row[1],
            "return_user_uid": row[2],
        }

    def delete_open_loan(self, loan_id: int) -> dict:
        self._ensure_dsn()
        select_query = sql.SQL(
            """
            SELECT l.tool_uid,
                   COALESCE(t.name, l.tool_uid) AS tool_name
              FROM loans l
         LEFT JOIN tools t ON t.uid = l.tool_uid
             WHERE l.id=%s AND l.returned_at IS NULL
            """
        )
        with self.connect(self.dsn) as conn, conn.cursor() as cur:
            cur.execute(select_query, (loan_id,))
            row = cur.fetchone()
            if not row:
                raise LoanNotFoundError(f"loan_id={loan_id} not found or already closed")
            cur.execute("DELETE FROM loans WHERE id=%s", (loan_id,))
        return {"loan_id": loan_id, "tool_uid": row[0], "tool_name": row[1]}


def _format_dt(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.astimezone().isoformat()
