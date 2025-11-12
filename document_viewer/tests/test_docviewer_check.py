import json
from types import SimpleNamespace

import pytest

import scripts.docviewer_check as checker


class DummyResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = json.dumps(self._payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise checker.requests.HTTPError(f"status={self.status_code}", response=self)

    def json(self):
        return self._payload


def test_fetch_document_success(monkeypatch):
    def fake_get(url, headers, timeout):
        assert url == "http://example/api/documents/testpart"
        assert headers["Authorization"] == "Bearer token"
        assert timeout == 5.0
        return DummyResponse(payload={"found": True, "filename": "test.pdf"})

    monkeypatch.setattr(checker.requests, "get", fake_get)
    headers = checker.build_headers("token")
    result = checker.fetch_document("http://example", "testpart", headers, 5.0)
    assert result["found"] is True


def test_check_local_file(tmp_path):
    pdf = tmp_path / "Sample.pdf"
    pdf.write_bytes(b"pdf")
    assert checker.check_local_file(str(tmp_path), "Sample.pdf")
    assert not checker.check_local_file(str(tmp_path), "Missing.pdf")


def test_main_success(monkeypatch, tmp_path, capsys):
    pdf = tmp_path / "Testpart.pdf"
    pdf.write_bytes(b"pdf")
    dummy = DummyResponse(payload={"found": True, "filename": "Testpart.pdf"})

    def fake_get(url, headers, timeout):
        return dummy

    monkeypatch.setattr(checker.requests, "get", fake_get)

    args = SimpleNamespace(
        api_base="http://example",
        token="tok",
        part="Testpart",
        docs_dir=str(tmp_path),
        timeout=2.0,
        raw=False,
    )
    monkeypatch.setattr(checker, "parse_args", lambda: args)
    checker.main()
    out = capsys.readouterr().out
    assert "Local file check: OK" in out
