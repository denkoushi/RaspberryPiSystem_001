"""Logistics provider implementations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Protocol


class LogisticsProvider(Protocol):
    """Protocol describing a logistics jobs provider."""

    def list_jobs(self, limit: int = 100) -> Iterable[dict]:
        """Return logistics jobs."""


class FileLogisticsProvider:
    """Return logistics jobs from a JSON file."""

    def __init__(self, file_path: str | Path):
        self._path = Path(file_path).expanduser()

    def list_jobs(self, limit: int = 100) -> Iterable[dict]:
        if not self._path.exists():
            return []
        try:
            raw = self._path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            return []
        if isinstance(data, dict):
            items = data.get("items", [])
        else:
            items = data
        return items[: max(1, limit)]
