
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def _ensure_socketio_stub():
    try:
        importlib.import_module("flask_socketio")
        return
    except Exception:  # pragma: no cover - fall back to stub
        sys.modules.pop("flask_socketio", None)

    class DummySocketIO:
        def __init__(self, *args, **kwargs):
            pass

        def init_app(self, app, **kwargs):
            return app

        def emit(self, *args, **kwargs):
            return None

    def _emit(*args, **kwargs):
        return None

    sys.modules["flask_socketio"] = SimpleNamespace(SocketIO=DummySocketIO, emit=_emit)


def _ensure_psycopg_stub():
    try:
        importlib.import_module("psycopg")
        return
    except ModuleNotFoundError:
        pass

    class DummyConnection:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("psycopg stub does not provide real connections")

    sys.modules["psycopg"] = SimpleNamespace(connect=DummyConnection)


def _ensure_smartcard_stub():
    try:
        importlib.import_module("smartcard")
        return
    except ModuleNotFoundError:
        pass

    class DummyCardRequest:
        def __init__(self, *args, **kwargs):
            pass

        def waitforcardevent(self, *args, **kwargs):
            raise RuntimeError("smartcard stub does not integrate with hardware")

    smartcard_module = SimpleNamespace(CardRequest=DummyCardRequest, util=SimpleNamespace(toHexString=lambda data: "".join(data)))
    sys.modules["smartcard"] = smartcard_module
    sys.modules["smartcard.CardRequest"] = SimpleNamespace(CardRequest=DummyCardRequest)
    sys.modules["smartcard.util"] = SimpleNamespace(toHexString=lambda data: "".join(str(x) for x in data))


def _ensure_usb_sync_stub():
    try:
        importlib.import_module("usb_sync")
        return
    except ModuleNotFoundError:
        pass

    class DummyUsbSync:
        def __call__(self, *args, **kwargs):
            return None

    sys.modules["usb_sync"] = SimpleNamespace(run_usb_sync=DummyUsbSync())


def _ensure_station_config_stub():
    try:
        importlib.import_module("station_config")
        return
    except ModuleNotFoundError:
        pass

    def _load_station_config(path=None):
        return {}

    def _save_station_config(config, path=None):
        return True

    sys.modules["station_config"] = SimpleNamespace(
        load_station_config=_load_station_config,
        save_station_config=_save_station_config,
    )


def _ensure_raspi_client_stub():
    try:
        importlib.import_module("raspi_client")
        return
    except ModuleNotFoundError:
        pass

    class DummyClient:
        def __init__(self, *args, **kwargs):
            self.base_url = "http://stub"

        def is_configured(self):
            return False

        def get_json(self, *args, **kwargs):
            raise RuntimeError("raspi_client stub")

    class DummyError(Exception):
        pass

    sys.modules["raspi_client"] = SimpleNamespace(
        RaspiServerClient=DummyClient,
        RaspiServerAuthError=DummyError,
        RaspiServerClientError=DummyError,
        RaspiServerConfigError=DummyError,
    )


def _import_app_flask(repo_root: Path):
    sys.path.insert(0, str(repo_root))
    _ensure_socketio_stub()
    _ensure_psycopg_stub()
    _ensure_smartcard_stub()
    _ensure_usb_sync_stub()
    _ensure_station_config_stub()
    _ensure_raspi_client_stub()
    if "app_flask" in sys.modules:
        return importlib.reload(sys.modules["app_flask"])
    return importlib.import_module("app_flask")


def test_build_production_view_requires_config(monkeypatch, tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.delenv("RASPI_SERVER_BASE", raising=False)
    app_flask = _import_app_flask(repo_root)

    view = app_flask.build_production_view()
    assert view["plan_entries"] == []
    assert "configured" in (view["plan_error"] or "")


def test_build_production_view_remote_success(monkeypatch, tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    app_flask = _import_app_flask(repo_root)

    class StubClient:
        def __init__(self):
            self.base_url = "http://raspi.local"

        def is_configured(self):
            return True

        def get_json(self, path, **kwargs):
            if path == "/api/v1/production-plan":
                return {
                    "entries": [
                        {
                            "納期": "2025-01-05",
                            "個数": "20",
                            "部品番号": "PART-001",
                            "部品名": "テスト部品",
                            "製番": "JOB-XYZ",
                            "工程名": "切削",
                        }
                    ],
                    "updated_at": "2025-01-05T00:00:00Z",
                    "error": None,
                }
            if path == "/api/v1/standard-times":
                return {
                    "entries": [
                        {
                            "部品名": "テスト部品",
                            "機械標準工数": "10",
                            "製造オーダー番号": "JOB-XYZ",
                            "部品番号": "PART-001",
                            "工程名": "切削",
                        }
                    ],
                    "updated_at": "2025-01-05T00:00:00Z",
                    "error": None,
                }
            raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(app_flask, "_create_raspi_client", lambda: StubClient())

    production_view = app_flask.build_production_view()

    assert production_view["plan_entries"][0]["納期"] == "2025-01-05"
    assert production_view["standard_entries"][0]["部品番号"] == "PART-001"
    assert production_view["plan_error"] is None


def test_build_production_view_remote_error(monkeypatch, tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    app_flask = _import_app_flask(repo_root)

    class FailingClient:
        def __init__(self):
            self.base_url = "http://raspi.local"

        def is_configured(self):
            return True

        def get_json(self, path, **kwargs):
            raise app_flask.RaspiServerClientError("network unavailable")

    monkeypatch.setattr(app_flask, "_create_raspi_client", lambda: FailingClient())

    production_view = app_flask.build_production_view()

    assert production_view["plan_entries"] == []
    assert "network" in (production_view["plan_error"] or "")


def test_fetch_part_locations_remote(monkeypatch, tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    app_flask = _import_app_flask(repo_root)

    class StubClient:
        base_url = "http://raspi.local"

        def is_configured(self):
            return True

        def get_json(self, path, **kwargs):
            assert path == "/api/v1/part-locations"
            return {
                "entries": [
                    {
                        "order_code": "JOB-1",
                        "location_code": "RACK-1",
                        "device_id": "pi-zero",
                        "last_scan_id": "scan-123",
                        "scanned_at": "2025-01-05T12:00:00Z",
                        "updated_at": "2025-01-05T12:00:00Z",
                    }
                ]
            }

    monkeypatch.setattr(app_flask, "_create_raspi_client", lambda: StubClient())

    items = app_flask.fetch_part_locations(limit=5)

    assert len(items) == 1
    assert items[0]["order_code"] == "JOB-1"
    assert items[0]["location_code"] == "RACK-1"
