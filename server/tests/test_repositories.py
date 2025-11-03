from pathlib import Path

import tomli_w

from raspberrypiserver.app import create_app, initialize_services, load_configuration
from raspberrypiserver.repositories import (
    DatabaseScanRepository,
    InMemoryScanRepository,
)


def test_inmemory_repository_capacity():
    repo = InMemoryScanRepository(capacity=2)
    repo.save({"order": 1})
    repo.save({"order": 2})
    repo.save({"order": 3})

    assert list(repo.recent()) == [{"order": 2}, {"order": 3}]
    assert list(repo.recent(limit=1)) == [{"order": 3}]
    assert list(repo.recent(limit=0)) == []


def test_database_repository_selection(tmp_path: Path):
    config_path = tmp_path / "config.toml"
    tomli_w.dump(
        {
            "SCAN_REPOSITORY_BACKEND": "db",
            "SCAN_REPOSITORY_BUFFER": 5,
            "database": {"dsn": "postgresql://app:app@db/sensordb"},
        },
        config_path.open("wb"),
    )

    app = create_app()
    load_configuration(app, config_path=str(config_path))
    initialize_services(app)

    repo = app.config["SCAN_REPOSITORY"]
    assert isinstance(repo, DatabaseScanRepository)
    repo.save({"example": True})
    assert list(repo.recent()) == [{"example": True}]
