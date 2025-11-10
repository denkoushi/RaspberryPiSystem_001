from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import station_config  # type: ignore  # noqa: E402


def test_load_station_config_returns_defaults_for_missing_file(tmp_path):
    cfg = station_config.load_station_config(path=str(tmp_path / "missing.json"))
    assert cfg["process"] is None
    assert cfg["source"] == "manual"
    assert cfg["available"] == []


def test_save_station_config_writes_json(tmp_path):
    target = tmp_path / "station.json"
    updated = station_config.save_station_config(
        process="cutting",
        available=[{"name": "line1"}],
        source="api",
        path=str(target),
    )
    assert target.exists()
    assert updated["process"] == "cutting"
    assert updated["available"][0]["name"] == "line1"
    assert updated["source"] == "api"

    # load again to ensure persisted values are returned
    loaded = station_config.load_station_config(path=str(target))
    assert loaded == updated
