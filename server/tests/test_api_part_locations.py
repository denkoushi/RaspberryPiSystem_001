from flask.testing import FlaskClient

from raspberrypiserver.app import create_app


def test_part_locations_returns_entries_memory():
    app = create_app()
    # populate in-memory scan repository
    repo = app.config["SCAN_REPOSITORY"]
    repo.save({"order_code": "A", "location_code": "R1"})
    repo.save({"order_code": "B", "location_code": "R2"})

    client: FlaskClient = app.test_client()
    resp = client.get("/api/v1/part-locations")

    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["entries"]) >= 2
    codes = [entry["order_code"] for entry in data["entries"]]
    assert "A" in codes and "B" in codes


def test_part_locations_uses_custom_repository(monkeypatch):
    app = create_app()

    class FakeRepo:
        def list(self, limit=200):
            return [
                {
                    "order_code": "X",
                    "location_code": "R9",
                    "device_id": "D1",
                    "updated_at": None,
                }
            ]

    app.config["PART_LOCATION_REPOSITORY"] = FakeRepo()

    client: FlaskClient = app.test_client()
    resp = client.get("/api/v1/part-locations?limit=10")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data == {
        "entries": [
            {
                "order_code": "X",
                "location_code": "R9",
                "device_id": "D1",
                "updated_at": None,
            }
        ]
    }
