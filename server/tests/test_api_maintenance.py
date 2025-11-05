from flask.testing import FlaskClient

from raspberrypiserver.app import create_app
from raspberrypiserver.services.backlog import BacklogDrainService


class FakeDrainService:
    def __init__(self, drained: int = 5, default_limit: int = 50) -> None:
        self.limit = default_limit
        self._drained = drained
        self.last_limit = None
        self._pending = 0

    def is_configured(self) -> bool:
        return True

    def drain_once(self, limit=None) -> int:
        self.last_limit = limit
        return self._drained

    def count_backlog(self) -> int:
        return self._pending

    def set_pending(self, value: int) -> None:
        self._pending = value


def test_drain_backlog_requires_service():
    app = create_app()
    client: FlaskClient = app.test_client()

    resp = client.post("/api/v1/admin/drain-backlog")

    assert resp.status_code == 503
    assert resp.get_json()["status"] == "skipped"


def test_drain_backlog_runs_service_with_custom_limit():
    app = create_app()
    fake_service = FakeDrainService(drained=3, default_limit=25)
    app.config["BACKLOG_DRAIN_SERVICE"] = fake_service

    client: FlaskClient = app.test_client()
    resp = client.post("/api/v1/admin/drain-backlog?limit=10")

    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"status": "ok", "drained": 3, "limit": 10}
    assert fake_service.last_limit == 10


def test_drain_backlog_accepts_json_payload():
    app = create_app()
    fake_service = FakeDrainService(drained=2, default_limit=99)
    app.config["BACKLOG_DRAIN_SERVICE"] = fake_service

    client: FlaskClient = app.test_client()
    resp = client.post("/api/v1/admin/drain-backlog", json={"limit": 15})

    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"status": "ok", "drained": 2, "limit": 15}
    assert fake_service.last_limit == 15


def test_backlog_status_disabled_when_no_service():
    app = create_app()
    client: FlaskClient = app.test_client()

    resp = client.get("/api/v1/admin/backlog-status")

    assert resp.status_code == 200
    assert resp.get_json() == {
        "status": "disabled",
        "pending": 0,
        "auto_drain_on_ingest": 0,
    }


def test_backlog_status_reports_metrics():
    app = create_app()
    fake_service = FakeDrainService(default_limit=75)
    fake_service.set_pending(42)
    app.config["BACKLOG_DRAIN_SERVICE"] = fake_service
    app.config["AUTO_DRAIN_ON_INGEST"] = 15

    client: FlaskClient = app.test_client()
    resp = client.get("/api/v1/admin/backlog-status")

    assert resp.status_code == 200
    assert resp.get_json() == {
        "status": "ok",
        "pending": 42,
        "drain_limit": 75,
        "auto_drain_on_ingest": 15,
    }


def test_admin_drain_backlog_uses_real_service():
    rows = [
        (1, "ORD-1", "LOC-1", "DEV-1"),
        (2, None, "LOC-MISSING", None),
    ]

    class FakeCursor:
        def __init__(self, conn):
            self.conn = conn
            self.select_done = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, query, params=None):
            self.conn.queries.append((str(query), params))
            if "DELETE" in str(query):
                self.conn.deleted_ids = params[0]
            if "INSERT INTO" in str(query):
                self.conn.insert_params.append(params)

        def fetchall(self):
            if not self.select_done:
                self.select_done = True
                return rows
            return []

    class FakeConnection:
        def __init__(self):
            self.queries = []
            self.deleted_ids = None
            self.insert_calls = []
            self.committed = False
            self.insert_params: list = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            return FakeCursor(self)

        def commit(self):
            self.committed = True

    connections: list[FakeConnection] = []

    def fake_connect(_dsn: str) -> FakeConnection:
        conn = FakeConnection()
        connections.append(conn)
        return conn

    app = create_app()
    service = BacklogDrainService(
        dsn="postgresql://example",
        limit=10,
        connect=fake_connect,
    )
    app.config["BACKLOG_DRAIN_SERVICE"] = service

    client: FlaskClient = app.test_client()
    resp = client.post("/api/v1/admin/drain-backlog")

    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok", "drained": 1, "limit": 10}

    assert connections, "expected BacklogDrainService to open a connection"
    conn = connections[0]
    assert any("INSERT INTO" in query for query, _ in conn.queries)
    assert conn.deleted_ids == [1]
    assert conn.committed is True


def test_backlog_status_handles_service_errors():
    def failing_connect(_dsn: str):
        raise RuntimeError("connection refused")

    app = create_app()
    broken_service = BacklogDrainService(
        dsn="postgresql://app:app@localhost:15432/sensordb",
        limit=33,
        connect=failing_connect,
    )
    app.config["BACKLOG_DRAIN_SERVICE"] = broken_service
    app.config["AUTO_DRAIN_ON_INGEST"] = 5

    client: FlaskClient = app.test_client()
    resp = client.get("/api/v1/admin/backlog-status")

    assert resp.status_code == 200
    assert resp.get_json() == {
        "status": "ok",
        "pending": 0,
        "drain_limit": 33,
        "auto_drain_on_ingest": 5,
    }
