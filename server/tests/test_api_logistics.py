from flask.testing import FlaskClient

from raspberrypiserver.app import create_app


def test_logistics_jobs_returns_empty_list_by_default():
    app = create_app()
    client: FlaskClient = app.test_client()

    resp = client.get("/api/logistics/jobs")

    assert resp.status_code == 200
    assert resp.get_json() == {"items": []}


def test_logistics_jobs_uses_provider(monkeypatch):
    app = create_app()

    class FakeProvider:
        def __init__(self):
            self.received_limit = None

        def list_jobs(self, limit=100):
            self.received_limit = limit
            return [
                {
                    "job_id": "JOB-1",
                    "part_code": "ITEM-1",
                    "from_location": "A1",
                    "to_location": "B2",
                    "status": "pending",
                    "updated_at": "2025-11-14T12:00:00Z",
                }
            ]

    provider = FakeProvider()
    app.config["LOGISTICS_PROVIDER"] = provider

    client: FlaskClient = app.test_client()
    resp = client.get("/api/logistics/jobs?limit=5")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["items"][0]["job_id"] == "JOB-1"
    assert provider.received_limit == 5
