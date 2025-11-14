from flask.testing import FlaskClient

from raspberrypiserver.app import create_app


def test_production_plan_empty_by_default():
    app = create_app()
    client: FlaskClient = app.test_client()

    resp = client.get("/api/v1/production-plan")

    assert resp.status_code == 200
    assert resp.get_json() == {"entries": []}


def test_standard_times_empty_by_default():
    app = create_app()
    client: FlaskClient = app.test_client()

    resp = client.get("/api/v1/standard-times")

    assert resp.status_code == 200
    assert resp.get_json() == {"entries": []}


def test_production_plan_uses_configured_provider():
    app = create_app()

    class FakeProvider:
        def __init__(self):
            self.limit = None

        def list_entries(self, limit=200):
            self.limit = limit
            return [{"製番": "PLAN-XYZ"}]

    app.config["PRODUCTION_PLAN_PROVIDER"] = FakeProvider()
    client: FlaskClient = app.test_client()

    resp = client.get("/api/v1/production-plan?limit=5")

    assert resp.status_code == 200
    assert resp.get_json()["entries"][0]["製番"] == "PLAN-XYZ"
    assert app.config["PRODUCTION_PLAN_PROVIDER"].limit == 5


def test_standard_times_uses_provider():
    app = create_app()

    class FakeProvider:
        def list_entries(self, limit=200):
            return [{"工程名": "加工"}]

    app.config["STANDARD_TIME_PROVIDER"] = FakeProvider()
    client: FlaskClient = app.test_client()

    resp = client.get("/api/v1/standard-times")

    assert resp.status_code == 200
    assert resp.get_json()["entries"] == [{"工程名": "加工"}]
