"""Simple file-based API token store for Window A."""

from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

API_TOKEN_HEADER = os.getenv("WINDOW_A_API_TOKEN_HEADER", "X-API-Token")
API_TOKEN_FILE = Path(
    os.getenv(
        "WINDOW_A_API_TOKEN_FILE",
        Path(__file__).resolve().parent / "config" / "api_tokens.json",
    )
).expanduser()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_file() -> List[Dict[str, Any]]:
    if not API_TOKEN_FILE.exists():
        return []
    try:
        with API_TOKEN_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            return data
    except (OSError, ValueError):
        pass
    return []


def _save_file(entries: List[Dict[str, Any]]) -> None:
    API_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with API_TOKEN_FILE.open("w", encoding="utf-8") as fh:
        json.dump(entries, fh, ensure_ascii=False, indent=2)


def _mask(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    if len(token) <= 6:
        return token[0] + "***"
    return f"{token[:4]}***{token[-2:]}"


def list_tokens(with_token: bool = False) -> List[Dict[str, Any]]:
    entries = []
    for entry in _load_file():
        filtered = {
            "station_id": entry.get("station_id"),
            "created_at": entry.get("created_at"),
            "revoked_at": entry.get("revoked_at"),
            "note": entry.get("note"),
        }
        if with_token:
            filtered["token"] = entry.get("token")
        else:
            filtered["token_preview"] = _mask(entry.get("token"))
        entries.append(filtered)
    return entries


def get_active_tokens() -> List[Dict[str, Any]]:
    return [
        entry
        for entry in _load_file()
        if not entry.get("revoked_at")
    ]


def get_token_info() -> Dict[str, Any]:
    active = get_active_tokens()
    if not active:
        return {"error": "token_not_issued"}
    entry = active[-1]
    return {
        "token": entry.get("token"),
        "token_preview": _mask(entry.get("token")),
        "station_id": entry.get("station_id"),
        "issued_at": entry.get("created_at"),
    }


def issue_token(
    station_id: str,
    token: Optional[str] = None,
    keep_existing: bool = False,
    note: Optional[str] = None,
) -> Dict[str, Any]:
    token_value = token or secrets.token_urlsafe(32)
    entries = _load_file()

    if not keep_existing:
        for entry in entries:
            if not entry.get("revoked_at") and entry.get("station_id") == station_id:
                entry["revoked_at"] = _now_iso()

    entry = {
        "station_id": station_id,
        "token": token_value,
        "note": note,
        "created_at": _now_iso(),
        "revoked_at": None,
    }
    entries.append(entry)
    _save_file(entries)
    return entry


def revoke_token(token: str) -> bool:
    entries = _load_file()
    changed = False
    for entry in entries:
        if entry.get("token") == token and not entry.get("revoked_at"):
            entry["revoked_at"] = _now_iso()
            changed = True
    if changed:
        _save_file(entries)
    return changed
