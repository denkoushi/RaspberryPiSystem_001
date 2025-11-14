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
