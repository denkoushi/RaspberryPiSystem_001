"""Utility script to drain scan backlog into part_locations."""

from __future__ import annotations

import argparse
import logging

import psycopg

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


def drain(dsn: str, limit_count: int) -> int:
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT drain_scan_backlog(%s)", (limit_count,))
        processed = cur.fetchone()[0]
        conn.commit()
        return processed


def main() -> None:
    parser = argparse.ArgumentParser(description="Drain scan backlog")
    parser.add_argument("--dsn", required=True, help="PostgreSQL DSN")
    parser.add_argument("--limit", type=int, default=100, help="Records to drain per run")

    args = parser.parse_args()
    processed = drain(args.dsn, args.limit)
    LOGGER.info("Processed %s records", processed)


if __name__ == "__main__":
    main()
