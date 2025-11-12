import importlib
import sys
from types import SimpleNamespace

import pytest


@pytest.fixture
def viewer_module(monkeypatch, tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    log_path = tmp_path / "logs" / "document_viewer.log"
    monkeypatch.setenv("VIEWER_LOCAL_DOCS_DIR", str(docs_dir))
    monkeypatch.setenv("VIEWER_API_BASE", "http://example.com/base/")
    monkeypatch.setenv("VIEWER_API_TOKEN", " token-value ")
    monkeypatch.setenv("VIEWER_SOCKET_BASE", "http://example.com/socket/")
    monkeypatch.setenv("VIEWER_SOCKET_PATH", "custom")
    monkeypatch.setenv("VIEWER_SOCKET_AUTO_OPEN", "0")
    monkeypatch.setenv("VIEWER_SOCKET_EVENTS", "scan.ingested, scan_update")
    monkeypatch.setenv("VIEWER_ACCEPT_DEVICE_IDS", "HANDHELD-01, HANDHELD-02")
    monkeypatch.setenv("VIEWER_ACCEPT_LOCATION_CODES", "RACK-A1, RACK-A2")
    monkeypatch.setenv("VIEWER_LOG_PATH", str(log_path))

    sys.modules.pop("app.viewer", None)
    module = importlib.import_module("app.viewer")
    module = importlib.reload(module)
    return SimpleNamespace(module=module, docs_dir=docs_dir, log_path=log_path)


def _read_log(viewer_module) -> str:
    for handler in viewer_module.module.LOGGER.handlers:
        try:
            handler.flush()
        except Exception:  # pragma: no cover - flush best effort
            pass
    if viewer_module.log_path.exists():
        return viewer_module.log_path.read_text()
    return ""


def test_documents_dir_override(viewer_module):
    docs_dir = viewer_module.docs_dir
    assert docs_dir.exists()
    assert viewer_module.module.DOCUMENTS_DIR == docs_dir.resolve()

    pdf_path = docs_dir / "Sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    result = viewer_module.module.find_document_filename("sample")
    assert result == "Sample.pdf"


def test_index_injects_config(viewer_module):
    client = viewer_module.module.app.test_client()
    response = client.get("/")
    assert response.status_code == 200

    html = response.data.decode("utf-8")
    assert "http://example.com/base" in html  # trailing slash trimmed
    assert '"socketAutoOpen": false' in html
    assert "HANDHELD-01" in html
    assert "RACK-A1" in html
    assert "scan.ingested" in html
    assert "scan_update" in html

    assert viewer_module.module.SOCKET_AUTO_OPEN is False
    assert viewer_module.module.ACCEPT_DEVICE_IDS == ["HANDHELD-01", "HANDHELD-02"]
    assert viewer_module.module.ACCEPT_LOCATION_CODES == ["RACK-A1", "RACK-A2"]
    assert viewer_module.module.SOCKET_EVENTS == ["scan.ingested", "scan_update"]


def test_api_documents_endpoint(viewer_module):
    docs_dir = viewer_module.docs_dir
    pdf_path = docs_dir / "Testpart.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    client = viewer_module.module.app.test_client()
    response = client.get("/api/documents/testpart")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["found"] is True
    assert payload["filename"] == "Testpart.pdf"
    assert payload["url"].startswith("/documents/Testpart.pdf?v=")

    # ensure serving also logs
    serve_response = client.get("/documents/Testpart.pdf")
    assert serve_response.status_code == 200

    log_text = _read_log(viewer_module)
    assert "Document lookup success: testpart -> Testpart.pdf" in log_text
    assert "Document served: Testpart.pdf" in log_text


def test_api_documents_not_found(viewer_module):
    client = viewer_module.module.app.test_client()
    response = client.get("/api/documents/unknown")
    assert response.status_code == 404
    payload = response.get_json()
    assert payload["found"] is False
    log_text = _read_log(viewer_module)
    assert "Document not found: unknown" in log_text


def test_serve_document_invalid_path_logs_warning(viewer_module):
    client = viewer_module.module.app.test_client()
    response = client.get("/documents/../../etc/passwd")
    assert response.status_code == 404
    log_text = _read_log(viewer_module)
    assert "Invalid document access attempt: ../../etc/passwd" in log_text


def test_api_socket_events_logs_payload(viewer_module):
    client = viewer_module.module.app.test_client()
    response = client.post(
        "/api/socket-events",
        json={"event": "scan.ingested", "payload": {"order_code": "T-1"}},
    )
    assert response.status_code == 201
    log_text = _read_log(viewer_module)
    assert "Socket.IO event: scan.ingested" in log_text
    assert "'order_code': 'T-1'" in log_text


def test_api_socket_events_rejects_non_json(viewer_module):
    client = viewer_module.module.app.test_client()
    response = client.post("/api/socket-events", data="not-json", headers={"Content-Type": "text/plain"})
    assert response.status_code == 400
