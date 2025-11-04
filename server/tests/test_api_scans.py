from unittest.mock import MagicMock

from flask.testing import FlaskClient

from raspberrypiserver.app import create_app, socketio


def test_scans_endpoint_echoes_payload():
    app = create_app()
    mock_broadcast = MagicMock()
    app.config["BROADCAST_SERVICE"] = mock_broadcast

    client: FlaskClient = app.test_client()

    payload = {"order_code": "  TEST-001 ", "location_code": "RACK-A1", "device_id": "HANDHELD-01"}
    response = client.post("/api/v1/scans", json=payload)

    assert response.status_code == 202
    assert response.json == {
        "status": "accepted",
        "received": {
            "order_code": "TEST-001",
            "location_code": "RACK-A1",
            "device_id": "HANDHELD-01",
        },
        "app": "RaspberryPiServer",
    }

    mock_broadcast.emit.assert_called_once_with(
        "scan.ingested",
        {
            "order_code": "TEST-001",
            "location_code": "RACK-A1",
            "device_id": "HANDHELD-01",
        },
    )


def test_scans_endpoint_rejects_invalid_payload():
    app = create_app()
    client: FlaskClient = app.test_client()

    response = client.post("/api/v1/scans", json={"location_code": "RACK-A1"})

    assert response.status_code == 400
    assert response.get_json()["reason"] == "missing-order_code"

    response = client.post("/api/v1/scans", data="not-json")
    assert response.status_code == 400
    assert response.get_json()["reason"] == "invalid-json"


def test_scans_endpoint_triggers_auto_drain_when_configured():
    app = create_app()

    class FakeDrain:
        def __init__(self):
            self.called_with = None

        def is_configured(self):
            return True

        def drain_once(self, limit=None):
            self.called_with = limit
            return 7

    drain_service = FakeDrain()
    app.config["BACKLOG_DRAIN_SERVICE"] = drain_service
    app.config["AUTO_DRAIN_ON_INGEST"] = 15

    client: FlaskClient = app.test_client()
    response = client.post("/api/v1/scans", json={"order_code": "X", "location_code": "L"})

    assert response.status_code == 202
    assert response.get_json()["backlog_drained"] == 7
    assert drain_service.called_with == 15


def test_socketio_emission_occurs():
    app = create_app()
    client: FlaskClient = app.test_client()

    test_client = socketio.test_client(app, namespace="/")

    payload = {"order_code": "TEST-SIO", "location_code": "RACK-ZS"}
    response = client.post("/api/v1/scans", json=payload)

    assert response.status_code == 202

    received_packets = test_client.get_received("/")
    events = [pkt for pkt in received_packets if pkt.get("name") == "scan.ingested"]

    assert events, f"expected scan.ingested event, got: {received_packets!r}"
    event_payload = events[0]["args"][0]
    assert event_payload["order_code"] == "TEST-SIO"
    assert event_payload["location_code"] == "RACK-ZS"


def test_scans_endpoint_emits_socket_event():
    app = create_app()
    client: FlaskClient = app.test_client()
    socket_client = socketio.test_client(app, namespace="/")

    payload = {"order_code": "TEST-SOCKET", "location_code": "RACK-S1"}
    response = client.post("/api/v1/scans", json=payload)
    assert response.status_code == 202

    received = socket_client.get_received("/")
    events = [packet for packet in received if packet.get("name") == "scan.ingested"]
    assert events, f"Socket.IO events not received: {received!r}"
    assert events[0]["args"][0]["order_code"] == "TEST-SOCKET"
