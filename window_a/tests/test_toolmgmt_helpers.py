from __future__ import annotations

from pathlib import Path

from .test_load_plan import _import_app_flask


def _get_app_module():
    repo_root = Path(__file__).resolve().parents[1]
    return _import_app_flask(repo_root)


def test_collect_master_file_status_counts_rows(monkeypatch, tmp_path):
    app_flask = _get_app_module()
    monkeypatch.setattr(app_flask, "TOOLMGMT_MASTER_DIR", tmp_path)
    # users.csv
    (tmp_path / "users.csv").write_text("uid,full_name\nU1,User1\nU2,User2\n", encoding="utf-8")
    (tmp_path / "tool_master.csv").write_text("name\nToolA\n", encoding="utf-8")
    (tmp_path / "tools.csv").write_text("uid,name\nT001,ToolA\n", encoding="utf-8")

    stats = app_flask.collect_master_file_status(tmp_path)
    users_entry = next(item for item in stats if item["filename"] == "users.csv")
    assert users_entry["row_count"] == 2
    assert users_entry["exists"] is True


def test_build_toolmgmt_overview_handles_api(monkeypatch, tmp_path):
    app_flask = _get_app_module()
    monkeypatch.setattr(app_flask, "TOOLMGMT_MASTER_DIR", tmp_path)
    for filename in ("users.csv", "tool_master.csv", "tools.csv"):
        (tmp_path / filename).write_text("placeholder\nvalue\n", encoding="utf-8")

    class DummyClient:
        def __init__(self):
            self.called = False

        def is_configured(self):
            return True

        def get_json(self, path, params=None, allow_statuses=None):  # noqa: ARG002,ARG003
            self.called = True
            return {
                "open_loans": [
                    {"tool_name": "工具A", "borrower_name": "利用者A"}
                ],
                "history": [
                    {"action": "貸出", "tool_name": "工具A"}
                ],
            }

    dummy_client = DummyClient()
    monkeypatch.setattr(app_flask, "_create_raspi_client", lambda: dummy_client)

    view = app_flask.build_toolmgmt_overview()
    assert view["open_loans"][0]["tool_name"] == "工具A"
    assert view["history"][0]["action"] == "貸出"
    assert view["error"] is None
    assert dummy_client.called


def test_build_toolmgmt_overview_handles_connection_error(monkeypatch, tmp_path):
    app_flask = _get_app_module()
    monkeypatch.setattr(app_flask, "TOOLMGMT_MASTER_DIR", tmp_path)

    class DummyClient:
        def is_configured(self):
            return True

        def get_json(self, path, params=None, allow_statuses=None):  # noqa: ARG002,ARG003
            raise app_flask.RaspiServerClientError("db unavailable")

    monkeypatch.setattr(app_flask, "_create_raspi_client", lambda: DummyClient())
    view = app_flask.build_toolmgmt_overview()
    assert "db unavailable" in (view["error"] or "")


def test_proxy_toolmgmt_requires_config(monkeypatch):
    app_flask = _get_app_module()

    class DummyClient:
        def is_configured(self):
            return False

    monkeypatch.setattr(app_flask, "_create_raspi_client", lambda: DummyClient())
    with app_flask.app.app_context():
        response, error_resp, status_code = app_flask._proxy_toolmgmt_request("POST", "/api/v1/loans/1/manual_return")
    assert response is None
    assert status_code == 503
    assert error_resp.get_json()["error"]


def test_proxy_toolmgmt_calls_client(monkeypatch):
    app_flask = _get_app_module()

    class DummyResponse:
        status_code = 200

        def json(self):
            return {"status": "ok"}

    class DummyClient:
        def __init__(self):
            self.last_path = None

        def is_configured(self):
            return True

        def _request(self, method, path, **kwargs):  # noqa: ARG002
            self.last_path = path
            return DummyResponse()

    dummy_client = DummyClient()
    monkeypatch.setattr(app_flask, "_create_raspi_client", lambda: dummy_client)
    with app_flask.app.app_context():
        response, error_resp, status_code = app_flask._proxy_toolmgmt_request("DELETE", "/api/v1/loans/123")
    assert error_resp is None
    assert status_code is None
    assert response.status_code == 200
    assert dummy_client.last_path == "/api/v1/loans/123"
