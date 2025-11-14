#!/usr/bin/env python3
"""Database configuration helpers shared by Window A components."""

from __future__ import annotations

import os
from typing import Mapping, MutableMapping
from urllib.parse import urlparse


def _parse_dsn(url: str) -> dict[str, object]:
    """Convert a PostgreSQL DSN string to psycopg keyword arguments."""
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError(f"unsupported DB scheme: {parsed.scheme}")

    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 5432,
        "dbname": (parsed.path or "/sensordb").lstrip("/") or "sensordb",
        "user": parsed.username or "app",
        "password": parsed.password or "app",
    }


def build_db_config(env: Mapping[str, str] | None = None) -> dict[str, object]:
    """Return psycopg.connect kwargs derived from environment variables."""
    environ: Mapping[str, str] = env or os.environ
    url = environ.get("DATABASE_URL")
    if url:
        return _parse_dsn(url)

    return {
        "host": environ.get("DB_HOST", "127.0.0.1"),
        "port": int(environ.get("DB_PORT", "5432")),
        "dbname": environ.get("DB_NAME", "sensordb"),
        "user": environ.get("DB_USER", "app"),
        "password": environ.get("DB_PASSWORD", "app"),
    }


def apply_env_file(path: str, base_env: MutableMapping[str, str] | None = None) -> dict[str, str]:
    """Return a copy of os.environ updated with values from a simple KEY=VALUE file."""
    env = dict(base_env or os.environ)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for raw in handle:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env[key.strip()] = value.strip()
    except FileNotFoundError:
        raise
    return env

