"""Station configuration helper for Window A.

This module replaces the legacy implementation that lived in the
`tool-management-system02` repository. For now it keeps the data in a JSON file
under `window_a/config/station_config.json`, but the API surface remains the
same (load/save functions) so the Flask app can continue to call it without
changes.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_CONFIG = {
    "process": None,
    "source": "manual",
    "available": [],
}

DEFAULT_PATH = Path(__file__).resolve().parent / "config" / "station_config.json"


def _resolve_path(path: Optional[str] = None) -> Path:
    override = path or os.environ.get("WINDOW_A_STATION_CONFIG")
    return Path(override).expanduser() if override else DEFAULT_PATH


def load_station_config(path: Optional[str] = None) -> Dict[str, Any]:
    """Load station configuration from JSON; fall back to defaults."""
    config_path = _resolve_path(path)
    if not config_path.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with config_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (ValueError, OSError):
        return DEFAULT_CONFIG.copy()

    # ensure mandatory keys exist
    normalized = DEFAULT_CONFIG.copy()
    normalized.update({k: data.get(k) for k in DEFAULT_CONFIG})
    return normalized


def save_station_config(
    process: Optional[str] = None,
    available: Optional[List[Dict[str, Any]]] = None,
    source: Optional[str] = None,
    path: Optional[str] = None,
) -> Dict[str, Any]:
    """Save station configuration to JSON and return the stored value."""
    config_path = _resolve_path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config = load_station_config(path)

    if process is not None:
        config["process"] = process
    if available is not None:
        config["available"] = available
    if source is not None:
        config["source"] = source

    with config_path.open("w", encoding="utf-8") as fh:
        json.dump(config, fh, ensure_ascii=False, indent=2)

    return config
