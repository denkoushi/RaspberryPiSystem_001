from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Callable


ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DEFAULT_STATE_PATH = Path(
    os.environ.get("MIRRORCTL_STATE_PATH", "~/.onsitelogistics/mirrorctl_state.json")
).expanduser()
DEFAULT_AUDIT_PATH = Path(
    os.environ.get("MIRRORCTL_AUDIT_PATH", "~/.onsitelogistics/mirrorctl_audit.log")
).expanduser()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.strftime(ISO_FORMAT)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            return datetime.strptime(value, ISO_FORMAT).replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _same_day(existing: str | None, current: datetime) -> bool:
    parsed = _parse_iso(existing)
    if not parsed:
        return False
    return parsed.date() == current.date()


@dataclass
class MirrorctlState:
    enabled: bool = True
    last_success_at: str | None = None
    last_failure_at: str | None = None
    last_update_at: str | None = None
    consecutive_success_days: int = 0
    consecutive_failure_days: int = 0
    pending_failures: int = 0
    notes: str | None = None


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_state(path: Path = DEFAULT_STATE_PATH) -> MirrorctlState:
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        merged = {**asdict(MirrorctlState()), **raw}
        return MirrorctlState(**merged)
    return MirrorctlState()


def save_state(state: MirrorctlState, path: Path = DEFAULT_STATE_PATH) -> None:
    _ensure_parent(path)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(asdict(state), fh, indent=2, ensure_ascii=False)


def update_status(
    success_count: int,
    failure_count: int,
    *,
    path: Path = DEFAULT_STATE_PATH,
) -> MirrorctlState:
    state = load_state(path)
    now = _now()
    changed = False

    if success_count > 0:
        if not _same_day(state.last_success_at, now):
            state.consecutive_success_days += 1
        state.last_success_at = _to_iso(now)
        state.pending_failures = max(state.pending_failures - success_count, 0)
        if failure_count == 0:
            state.consecutive_failure_days = 0
        changed = True

    if failure_count > 0:
        if not _same_day(state.last_failure_at, now):
            state.consecutive_failure_days += 1
        state.last_failure_at = _to_iso(now)
        if success_count == 0:
            state.consecutive_success_days = 0
        state.pending_failures += failure_count
        changed = True

    if changed:
        state.last_update_at = _to_iso(now)
        save_state(state, path)
    return state


def set_enabled(enabled: bool, *, reason: str | None = None, path: Path = DEFAULT_STATE_PATH) -> MirrorctlState:
    state = load_state(path)
    state.enabled = enabled
    if reason:
        state.notes = reason
    state.last_update_at = _to_iso(_now())
    save_state(state, path)
    return state


def append_audit_entry(message: str, path: Path = DEFAULT_AUDIT_PATH) -> None:
    _ensure_parent(path)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"{_to_iso(_now())} {message}\n")


def state_as_dict(path: Path = DEFAULT_STATE_PATH) -> dict[str, Any]:
    return asdict(load_state(path))


def build_hook(path: Path = DEFAULT_STATE_PATH) -> Callable[[int, int], None]:
    def hook(success: int, failure: int) -> None:
        update_status(success, failure, path=path)

    return hook
