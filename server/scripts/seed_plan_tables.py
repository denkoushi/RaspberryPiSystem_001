#!/usr/bin/env python3
"""Seed production_plan_entries and standard_time_entries tables from JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed plan tables with sample data.")
    parser.add_argument(
        "--dsn",
        default="postgresql://app:app@localhost:15432/sensordb",
        help="PostgreSQL DSN (default: %(default)s)",
    )
    parser.add_argument(
        "--plan-file",
        default="/srv/RaspberryPiSystem_001/server/config/production-plan.sample.json",
        help="JSON file for production plan entries",
    )
    parser.add_argument(
        "--standard-file",
        default="/srv/RaspberryPiSystem_001/server/config/standard-times.sample.json",
        help="JSON file for standard times",
    )
    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate tables before inserting",
    )
    return parser.parse_args()


def load_entries(path: str | Path) -> list[dict]:
    file_path = Path(path).expanduser()
    if not file_path.exists():
        return []
    with file_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        entries = data.get("entries", [])
    else:
        entries = data
    if not isinstance(entries, list):
        return []
    return [entry for entry in entries if isinstance(entry, dict)]


def seed_table(conn, table: str, entries: list[dict], truncate: bool) -> int:
    if not entries:
        return 0
    with conn.cursor() as cur:
        if truncate:
            cur.execute(f"TRUNCATE {table}")
        payloads = [(Jsonb(entry),) for entry in entries]
        cur.executemany(
            f"INSERT INTO {table} (payload) VALUES (%s)",
            payloads,
        )
    return len(entries)


def main() -> None:
    args = parse_args()
    plan_entries = load_entries(args.plan_file)
    standard_entries = load_entries(args.standard_file)
    with psycopg.connect(args.dsn) as conn:
        inserted_plan = seed_table(
            conn,
            "production_plan_entries",
            plan_entries,
            args.truncate,
        )
        inserted_std = seed_table(
            conn,
            "standard_time_entries",
            standard_entries,
            args.truncate,
        )
        conn.commit()
    print(f"production_plan_entries inserted: {inserted_plan}")
    print(f"standard_time_entries inserted: {inserted_std}")


if __name__ == "__main__":
    main()
