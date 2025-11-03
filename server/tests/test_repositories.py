from __future__ import annotations

from pathlib import Path

import tomli_w

from raspberrypiserver.app import create_app, initialize_services, load_configuration
from raspberrypiserver.repositories import DatabaseScanRepository, InMemoryScanRepository


def test_inmemory_repository_capacity():
    repo = InMemoryScanRepository(capacity=2)
    repo.save({"order": 1})
    repo.save({"order": 2})
    repo.save({"order": 3})

    assert list(repo.recent()) == [{"order": 2}, {"order": 3}]
    assert list(repo.recent(limit=1)) == [{"order": 3}]
    assert list(repo.recent(limit=0)) == []


class FakeCursor:
    def __init__(self):
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params):
        self.executed.append((query, params))


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()
        self.commit_called = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.commit_called = True


def test_database_repository_selection(tmp_path: Path, monkeypatch):
    config_path = tmp_path / "config.toml"
    tomli_w.dump(
        {
            "SCAN_REPOSITORY_BACKEND": "db",
            "SCAN_REPOSITORY_BUFFER": 5,
            "database": {"dsn": "postgresql://app:app@db/sensordb"},
        },
        config_path.open("wb"),
    )

    fake_conn = FakeConnection()

    app = create_app()
    load_configuration(app, config_path=str(config_path))
    initialize_services(app)

    repo = app.config["SCAN_REPOSITORY"]
    assert isinstance(repo, DatabaseScanRepository)

    # Swap connect factory to avoid real DB access
    repo._connect_factory = lambda dsn: fake_conn  # type: ignore[attr-defined]

    repo.save({"example": True})
    assert list(repo.recent()) == [{"example": True}]
    assert fake_conn.commit_called is True
    assert fake_conn.cursor_obj.executed, "Expected SQL execution"
