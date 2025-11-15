#!/usr/bin/env python3
"""Import Window A tool master CSV files into PostgreSQL."""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import psycopg

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from db_config import apply_env_file, build_db_config


@dataclass(frozen=True)
class DatasetSpec:
    filename: str
    required_columns: tuple[str, ...]
    friendly_name: str


DATASETS = {
    "users": DatasetSpec(
        filename="users.csv",
        required_columns=("uid", "full_name"),
        friendly_name="ユーザー一覧",
    ),
    "tool_master": DatasetSpec(
        filename="tool_master.csv",
        required_columns=("name",),
        friendly_name="工具マスタ",
    ),
    "tools": DatasetSpec(
        filename="tools.csv",
        required_columns=("uid", "name"),
        friendly_name="工具割当",
    ),
}


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import Window A master CSV files into PostgreSQL tables.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Optional KEY=VALUE file (e.g. config/window-a.env) containing DATABASE_URL.",
    )
    parser.add_argument(
        "--master-dir",
        type=Path,
        default=REPO_ROOT / "master",
        help="Directory that contains users.csv / tool_master.csv / tools.csv "
             "(default: window_a/master).",
    )
    parser.add_argument(
        "--dsn",
        help="Explicit PostgreSQL DSN (overrides DATABASE_URL/DB_*).",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate target tables before importing.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse CSV files and show planned actions without modifying the database.",
    )
    return parser.parse_args(argv)


def load_csv(path: Path, spec: DatasetSpec) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        missing = [col for col in spec.required_columns if col not in headers]
        if missing:
            raise ValueError(
                f"{spec.friendly_name} の必須列が不足しています: {missing} (found={headers})"
            )
        rows = []
        for row in reader:
            normalized = {col: (row.get(col) or "").strip() for col in spec.required_columns}
            if any(normalized.values()):
                rows.append(normalized)
        return rows


def ensure_tables(conn: psycopg.Connection) -> None:
    statements: Iterable[str] = (
        """
        CREATE TABLE IF NOT EXISTS users(
            uid TEXT PRIMARY KEY,
            full_name TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tool_master(
            id BIGSERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS tools(
            uid TEXT PRIMARY KEY,
            name TEXT NOT NULL REFERENCES tool_master(name) ON UPDATE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS loans(
            id BIGSERIAL PRIMARY KEY,
            tool_uid TEXT NOT NULL,
            borrower_uid TEXT NOT NULL,
            loaned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            return_user_uid TEXT,
            returned_at TIMESTAMPTZ
        )
        """,
    )
    with conn.cursor() as cur:
        for sql in statements:
            cur.execute(sql)
    conn.commit()


def truncate_tables(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE loans, tools, tool_master, users RESTART IDENTITY CASCADE")
    conn.commit()


def import_users(conn: psycopg.Connection, rows: list[dict[str, str]]) -> int:
    if not rows:
        return 0
    count = 0
    with conn.cursor() as cur:
        for row in rows:
            if not row["uid"] or not row["full_name"]:
                continue
            cur.execute(
                """
                INSERT INTO users(uid, full_name)
                VALUES (%s, %s)
                ON CONFLICT (uid) DO UPDATE SET full_name = EXCLUDED.full_name
                """,
                (row["uid"], row["full_name"]),
            )
            count += 1
    conn.commit()
    return count


def import_tool_master(conn: psycopg.Connection, rows: list[str]) -> int:
    if not rows:
        return 0
    count = 0
    with conn.cursor() as cur:
        for name in rows:
            if not name:
                continue
            cur.execute(
                """
                INSERT INTO tool_master(name)
                VALUES (%s)
                ON CONFLICT (name) DO NOTHING
                """,
                (name,),
            )
            count += 1
    conn.commit()
    return count


def import_tools(conn: psycopg.Connection, rows: list[dict[str, str]]) -> int:
    if not rows:
        return 0
    count = 0
    with conn.cursor() as cur:
        for row in rows:
            if not row["uid"] or not row["name"]:
                continue
            cur.execute(
                """
                INSERT INTO tools(uid, name)
                VALUES (%s, %s)
                ON CONFLICT (uid) DO UPDATE SET name = EXCLUDED.name
                """,
                (row["uid"], row["name"]),
            )
            count += 1
    conn.commit()
    return count


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)

    env = None
    if args.env_file:
        env = apply_env_file(str(args.env_file))
    if args.dsn:
        env = dict(env or {})
        env["DATABASE_URL"] = args.dsn

    cfg = build_db_config(env)
    master_dir = args.master_dir
    datasets = {}
    for key, spec in DATASETS.items():
        path = master_dir / spec.filename
        try:
            datasets[key] = load_csv(path, spec)
        except Exception as exc:  # pylint: disable=broad-except
            print(f"[ERROR] {spec.friendly_name}: {exc}", file=sys.stderr)
            return 2

    derived_tool_master = sorted(
        {
            row.get("name", "")
            for row in datasets["tool_master"]
        }
        | {
            row.get("name", "")
            for row in datasets["tools"]
        }
    )
    derived_tool_master = [name for name in derived_tool_master if name]

    print(f"[INFO] users: {len(datasets['users'])} rows")
    print(f"[INFO] tool_master: {len(derived_tool_master)} unique names")
    print(f"[INFO] tools: {len(datasets['tools'])} rows")
    if args.dry_run:
        print("[INFO] Dry-run mode: no database changes were made.")
        return 0

    with psycopg.connect(**cfg) as conn:
        ensure_tables(conn)
        if args.truncate:
            truncate_tables(conn)
        inserted_users = import_users(conn, datasets["users"])
        inserted_master = import_tool_master(conn, derived_tool_master)
        inserted_tools = import_tools(conn, datasets["tools"])

    print(f"[DONE] users={inserted_users} tool_master={inserted_master} tools={inserted_tools}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
