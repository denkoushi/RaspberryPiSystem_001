#!/usr/bin/env python3
"""Utility to drain scan_ingest_backlog into part_locations."""

from __future__ import annotations

import argparse
import os

from raspberrypiserver.services.backlog import BacklogDrainService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Drain backlog table")
    parser.add_argument(
        "--dsn",
        default=os.environ.get("RPI_DB_DSN", "postgresql://app:app@localhost:15432/sensordb"),
        help="Database DSN (default: RPI_DB_DSN env or local DSN)",
    )
    parser.add_argument("--limit", type=int, default=50, help="Max rows to drain per run")
    parser.add_argument("--table", default="scan_ingest_backlog", help="Backlog table name")
    parser.add_argument("--target", default="part_locations", help="Target table name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    service = BacklogDrainService(
        dsn=args.dsn,
        limit=args.limit,
        backlog_table=args.table,
        target_table=args.target,
    )
    processed = service.drain_once()
    print(f"drained rows: {processed}")


if __name__ == "__main__":
    main()
