from flask.testing import FlaskClient

from raspberrypiserver.app import create_app
from raspberrypiserver.services import LoanNotFoundError


def test_tool_loans_requires_service() -> None:
    app = create_app()
    client: FlaskClient = app.test_client()

    resp = client.get("/api/loans")

    assert resp.status_code == 503
    assert resp.get_json()["error"] == "tool_management_unavailable"


def test_tool_loans_returns_data() -> None:
    app = create_app()

    class FakeService:
        def __init__(self):
            self.open_limit = None
            self.history_limit = None

        def list_open_loans(self, limit=100):
            self.open_limit = limit
            return [{"id": 1, "tool_name": "ドライバー"}]

        def list_recent_history(self, limit=50):
            self.history_limit = limit
            return [{"action": "貸出", "tool_name": "ドライバー"}]

    fake = FakeService()
    app.config["TOOLMGMT_SERVICE"] = fake
    client: FlaskClient = app.test_client()

    resp = client.get("/api/v1/loans?open_limit=5&history_limit=2")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["open_loans"][0]["tool_name"] == "ドライバー"
    assert fake.open_limit == 5
    assert fake.history_limit == 2


def test_tool_loans_manual_return_success() -> None:
    app = create_app()

    class FakeService:
        def manual_return(self, loan_id):
            self.loan_id = loan_id
            return {"tool_uid": "T001", "borrower_uid": "U001"}

    app.config["TOOLMGMT_SERVICE"] = FakeService()
    client: FlaskClient = app.test_client()

    resp = client.post("/api/v1/loans/1/manual_return")

    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_tool_loans_manual_return_not_found() -> None:
    app = create_app()

    class FakeService:
        def manual_return(self, loan_id):  # noqa: ARG002
            raise LoanNotFoundError()

    app.config["TOOLMGMT_SERVICE"] = FakeService()
    client: FlaskClient = app.test_client()

    resp = client.post("/api/v1/loans/999/manual_return")

    assert resp.status_code == 404


def test_tool_loans_delete_route() -> None:
    app = create_app()

    class FakeService:
        def delete_open_loan(self, loan_id):
            self.loan_id = loan_id
            return {"tool_uid": "T001", "tool_name": "ハンマー"}

    app.config["TOOLMGMT_SERVICE"] = FakeService()
    client: FlaskClient = app.test_client()

    resp = client.delete("/api/loans/5")

    assert resp.status_code == 200
    assert resp.get_json()["status"] == "deleted"


def test_tool_loans_create_route() -> None:
    app = create_app()

    class FakeService:
        def __init__(self):
            self.last_args = None

        def create_loan(self, borrower_uid, tool_uid):
            self.last_args = (borrower_uid, tool_uid)
            return {"loan_id": 10, "status": "open"}

    app.config["TOOLMGMT_SERVICE"] = FakeService()
    client: FlaskClient = app.test_client()

    resp = client.post(
        "/api/v1/loans",
        json={"borrower_uid": "u001", "tool_uid": "t001"},
    )

    assert resp.status_code == 201
    data = resp.get_json()
    assert data["loan_id"] == 10
    assert app.config["TOOLMGMT_SERVICE"].last_args == ("u001", "t001")


def test_tool_loans_create_requires_fields() -> None:
    app = create_app()

    class FakeService:
        def create_loan(self, borrower_uid, tool_uid):  # noqa: ARG002
            raise AssertionError("should not be called")

    app.config["TOOLMGMT_SERVICE"] = FakeService()
    client: FlaskClient = app.test_client()

    resp = client.post("/api/loans", json={})

    assert resp.status_code == 400
