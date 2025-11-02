from pathlib import Path

import tomli_w

from raspberrypiserver.app import create_app, load_configuration


def test_healthz_endpoint():
    app = create_app()
    client = app.test_client()
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json == {
        "status": "ok",
        "app": "RaspberryPiServer",
        "api_prefix": "/api/v1",
    }


def test_custom_config(tmp_path: Path):
    config_path = tmp_path / "config.toml"
    tomli_w.dump(
        {"APP_NAME": "CustomServer", "REST_API_PREFIX": "/api/v2"},
        config_path.open("wb"),
    )

    app = create_app()
    load_configuration(app, config_path=str(config_path))

    assert app.config["APP_NAME"] == "CustomServer"
    assert app.config["REST_API_PREFIX"] == "/api/v2"
