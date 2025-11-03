"""Utility to seed scan backlog with sample data."""

from __future__ import annotations

import argparse
import json
from typing import Dict

import psycopg


def seed_backlog(dsn: str, payload: Dict[str, str]) -> None:
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO scan_ingest_backlog (payload) VALUES (%s)",
            (json.dumps(payload),),
        )
        conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed scan backlog")
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--order", required=True)
    parser.add_argument("--location", required=True)
    parser.add_argument("--device", default="HANDHELD-01")
    args = parser.parse_args()
    seed_backlog(
        dsn=args.dsn,
        payload={
            "order_code": args.order,
            "location_code": args.location,
            "device_id": args.device,
        },
    )


if __name__ == "__main__":
    main()
