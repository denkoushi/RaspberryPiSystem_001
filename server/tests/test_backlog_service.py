"""Tests for backlog draining and database scan repository behavior."""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from raspberrypiserver.repositories.scans import DatabaseScanRepository
from raspberrypiserver.services.backlog import BacklogDrainService


class _DummyCursor:
    def __init__(self, store: Dict[str, Any], rows_returned: int = 0) -> None:
        self._store = store
        self._rows = rows_returned

    def __enter__(self) -> "_DummyCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        """No-op exit."""

    def execute(self, query: Any, params: Tuple[Any, ...] | None = None) -> None:
        self._store["query"] = query
        self._store["params"] = params

    def fetchone(self) -> Tuple[int]:
        return (self._rows,)


class _DummyConnection:
    def __init__(self, store: Dict[str, Any], rows_returned: int = 0) -> None:
        self._store = store
        self._rows = rows_returned
        self._store["committed"] = False

    def __enter__(self) -> "_DummyConnection":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        """No-op exit."""

    def cursor(self) -> _DummyCursor:
        self._store["cursor_called"] = True
        return _DummyCursor(self._store, self._rows)

    def commit(self) -> None:
        self._store["committed"] = True


def test_backlog_drain_invokes_database_function() -> None:
    calls: Dict[str, Any] = {}

    def fake_connect(dsn: str) -> _DummyConnection:
        calls["dsn"] = dsn
        return _DummyConnection(calls, rows_returned=5)

    service = BacklogDrainService(
        dsn="postgresql://example",
        limit=25,
        connect=fake_connect,
    )
    drained = service.drain_once()

    assert calls["dsn"] == "postgresql://example"
    assert calls["cursor_called"] is True
    assert calls["params"] == (25,)
    assert drained == 5
    assert calls["committed"] is True


def test_backlog_drain_skips_when_not_configured() -> None:
    service = BacklogDrainService(dsn="")
    assert service.drain_once() == 0


def test_database_scan_repository_persists_payload() -> None:
    calls: Dict[str, Any] = {}

    def fake_connect(dsn: str) -> _DummyConnection:
        calls["dsn"] = dsn
        return _DummyConnection(calls)

    repo = DatabaseScanRepository(
        dsn="postgresql://example",
        buffer_size=10,
        connect_factory=fake_connect,
    )
    payload = {"order_code": "TEST-001", "location_code": "RACK-A1"}

    repo.save(payload)

    assert calls["dsn"] == "postgresql://example"
    assert calls["cursor_called"] is True
    assert calls["committed"] is True
    assert len(list(repo.recent(1))) == 1
    stored = calls["params"][0].obj
    assert stored["order_code"] == "TEST-001"
    assert stored["location_code"] == "RACK-A1"


def test_backlog_drain_handles_exception() -> None:
    def failing_connect(_dsn: str):
        raise RuntimeError("boom")  # noqa: TRY003

    service = BacklogDrainService(dsn="postgresql://example", connect=failing_connect)
    assert service.drain_once(25) == 0


def test_backlog_count_returns_pending() -> None:
    calls: Dict[str, Any] = {}

    def fake_connect(dsn: str) -> _DummyConnection:
        calls["dsn"] = dsn
        return _DummyConnection(calls, rows_returned=3)

    service = BacklogDrainService(dsn="postgresql://example", connect=fake_connect)
    count = service.count_backlog()

    assert calls["dsn"] == "postgresql://example"
    assert calls["cursor_called"] is True
    assert calls.get("params") in (None, ())
    assert count == 3


def test_backlog_count_skips_when_unconfigured() -> None:
    service = BacklogDrainService(dsn="")
    assert service.count_backlog() == 0
