"""Production plan and standard time providers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Protocol


class PlanProvider(Protocol):
    """Protocol for production plan provider."""

    def list_entries(self, limit: int = 200) -> Iterable[dict]:
        ...


class StandardTimeProvider(Protocol):
    """Protocol for standard time provider."""

    def list_entries(self, limit: int = 200) -> Iterable[dict]:
        ...


class FileJSONProvider:
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
