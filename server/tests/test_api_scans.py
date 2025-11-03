from unittest.mock import MagicMock

from flask.testing import FlaskClient

from raspberrypiserver.app import create_app


def test_scans_endpoint_echoes_payload():
    app = create_app()
    mock_broadcast = MagicMock()
    app.config["BROADCAST_SERVICE"] = mock_broadcast

    client: FlaskClient = app.test_client()

    payload = {"order_code": "TEST-001", "location_code": "RACK-A1"}
    response = client.post("/api/v1/scans", json=payload)

    assert response.status_code == 202
    assert response.json == {
        "status": "accepted",
        "received": payload,
        "app": "RaspberryPiServer",
    }

    mock_broadcast.emit.assert_called_once_with("scan.ingested", payload)
