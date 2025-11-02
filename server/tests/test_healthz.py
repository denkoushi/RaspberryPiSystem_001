from raspberrypiserver.app import create_app


def test_healthz_endpoint():
    app = create_app()
    client = app.test_client()
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json == {"status": "ok"}
