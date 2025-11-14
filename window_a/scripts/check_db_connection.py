#!/usr/bin/env python3
"""Connectivity checker for the Window A PostgreSQL dependency."""

from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path
from typing import Sequence

import psycopg

from db_config import apply_env_file, build_db_config


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify network + auth connectivity against the configured PostgreSQL DSN.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        help="Optional KEY=VALUE file (e.g. config/window-a.env) to load before connecting.",
    )
    parser.add_argument(
        "--dsn",
        help="Override DATABASE_URL/DB_* values with an explicit DSN.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Connection timeout in seconds (default: 5).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    env = dict()
    if args.env_file:
        env = apply_env_file(str(args.env_file))
    if args.dsn:
        env["DATABASE_URL"] = args.dsn

    cfg = build_db_config(env if env else None)
    host = cfg["host"]
    port = cfg["port"]

    try:
        resolved = {info[4][0] for info in socket.getaddrinfo(host, None)}
    except socket.gaierror as exc:
        resolved = {f"(name resolution failed: {exc})"}

    summary = (
        f"target={host}:{port} dbname={cfg['dbname']} user={cfg['user']} "
        f"resolved={','.join(sorted(resolved))}"
    )

    try:
        with psycopg.connect(**cfg, connect_timeout=args.timeout) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT current_database(), current_user, inet_server_addr(), "
                    "inet_server_port(), version()"
                )
                row = cur.fetchone()
        print("status=ok", summary)
        print(
            "server_db=%s server_user=%s server_addr=%s server_port=%s version=%s"
            % tuple(row)
        )
        return 0
    except Exception as exc:  # pylint: disable=broad-except
        print("status=error", summary)
        print(f"error={exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
