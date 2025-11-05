"""Backlog drain service と DB リポジトリのテスト."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from raspberrypiserver.repositories.scans import DatabaseScanRepository
from raspberrypiserver.services.backlog import BacklogDrainService


class _StubCursor:
    def __init__(self, conn: "_StubConnection") -> None:
        self._conn = conn
        self._select_mode = True

    def __enter__(self) -> "_StubCursor":  # noqa: D401
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        pass

    def execute(self, query, params=None) -> None:
        self._conn.queries.append((query, params))
        if self._select_mode:
            self._select_mode = False
        else:
            if "INSERT INTO" in str(query):
                self._conn.insert_calls.append(params)
            elif "DELETE FROM" in str(query):
                self._conn.deleted_ids = params[0]

    def fetchall(self):
        rows = self._conn.rows if self._select_mode is False else []
        self._conn.rows_fetched = True
        return rows


class _StubConnection:
    def __init__(self, rows: List[Tuple[int, Optional[str], Optional[str], Optional[str]]]) -> None:
        self.rows = rows
        self.rows_fetched = False
        self.queries: List[Tuple[Any, Any]] = []
        self.insert_calls: List[Tuple[str, str, Optional[str]]] = []
        self.deleted_ids: List[int] | None = None
        self.committed = False

    def __enter__(self) -> "_StubConnection":  # noqa: D401
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        pass

    def cursor(self) -> _StubCursor:
        return _StubCursor(self)

    def commit(self) -> None:
        self.committed = True


def test_backlog_drain_upserts_and_deletes() -> None:
    rows = [
        (1, "ORD-1", "LOC-1", "DEV-1"),
        (2, "ORD-2", "LOC-2", None),
    ]

    conn = _StubConnection(rows)

    def fake_connect(dsn: str) -> _StubConnection:
        assert dsn == "postgresql://example"
        return conn

    service = BacklogDrainService(
        dsn="postgresql://example",
        limit=10,
        connect=fake_connect,
    )

    drained = service.drain_once()

    assert drained == 2
    assert conn.committed is True
    assert len(conn.insert_calls) == 2
    assert conn.insert_calls[0][0:2] == ("ORD-1", "LOC-1")
    assert conn.insert_calls[1][0:2] == ("ORD-2", "LOC-2")
    assert conn.deleted_ids == [1, 2]


def test_backlog_drain_skips_invalid_rows() -> None:
    rows = [
        (1, None, "LOC-1", "DEV-1"),
        (2, "ORD-2", None, None),
        (3, "ORD-3", "LOC-3", None),
    ]
    conn = _StubConnection(rows)

    def fake_connect(_dsn: str) -> _StubConnection:
        return conn

    service = BacklogDrainService(dsn="postgresql://example", connect=fake_connect)
    drained = service.drain_once(5)

    assert drained == 1
    assert conn.deleted_ids == [3]
    assert len(conn.insert_calls) == 1
    assert conn.insert_calls[0][0:2] == ("ORD-3", "LOC-3")


def test_backlog_drain_handles_empty_selection() -> None:
    rows: list[tuple[int, Optional[str], Optional[str], Optional[str]]] = []
    conn = _StubConnection(rows)

    def fake_connect(_dsn: str) -> _StubConnection:
        return conn

    service = BacklogDrainService(dsn="postgresql://example", connect=fake_connect)
    drained = service.drain_once(10)

    assert drained == 0
    assert conn.committed is True
    assert conn.deleted_ids is None


def test_backlog_drain_skips_when_not_configured() -> None:
    service = BacklogDrainService(dsn="")
    assert service.drain_once() == 0


def test_backlog_drain_handles_exception() -> None:
    def failing_connect(_dsn: str):
        raise RuntimeError("boom")  # noqa: TRY003

    service = BacklogDrainService(dsn="postgresql://example", connect=failing_connect)
    assert service.drain_once(25) == 0


class _RepoCursor:
    def __init__(self, store: Dict[str, Any]) -> None:
        self._store = store

    def __enter__(self) -> "_RepoCursor":  # noqa: D401
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        pass

    def execute(self, query, params=None) -> None:
        self._store["query"] = query
        self._store["params"] = params


class _RepoConnection:
    def __init__(self, store: Dict[str, Any]) -> None:
        self._store = store
        self._store["committed"] = False

    def __enter__(self) -> "_RepoConnection":  # noqa: D401
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        pass

    def cursor(self) -> _RepoCursor:
        self._store["cursor_called"] = True
        return _RepoCursor(self._store)

    def commit(self) -> None:
        self._store["committed"] = True


def test_database_scan_repository_persists_payload() -> None:
    calls: Dict[str, Any] = {}

    def fake_connect(dsn: str) -> _RepoConnection:
        calls["dsn"] = dsn
        return _RepoConnection(calls)

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


def test_backlog_count_returns_pending() -> None:
    store: Dict[str, Any] = {}

    class _CountCursor(_RepoCursor):
        def fetchone(self):
            return (3,)

    class _CountConnection(_RepoConnection):
        def cursor(self) -> _CountCursor:
            self._store["cursor_called"] = True
            return _CountCursor(self._store)

    def fake_connect(dsn: str) -> _CountConnection:
        store["dsn"] = dsn
        return _CountConnection(store)

    service = BacklogDrainService(dsn="postgresql://example", connect=fake_connect)
    count = service.count_backlog()

    assert store["dsn"] == "postgresql://example"
    assert store["cursor_called"] is True
    assert count == 3


def test_backlog_count_skips_when_unconfigured() -> None:
    service = BacklogDrainService(dsn="")
    assert service.count_backlog() == 0
