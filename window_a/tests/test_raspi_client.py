from __future__ import annotations

from unittest import mock
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from raspi_client import (  # type: ignore  # noqa: E402
    RaspiServerClient,
    RaspiServerAuthError,
    RaspiServerClientError,
    RaspiServerConfigError,
)


def test_client_requires_configuration():
    client = RaspiServerClient(base_url="")
    with pytest.raises(RaspiServerConfigError):
        client.get_json("/healthz")


def test_get_json_success(monkeypatch):
    client = RaspiServerClient(base_url="http://example.com", api_token="abc")
    fake_response = mock.Mock()
    fake_response.status_code = 200
    fake_response.json.return_value = {"status": "ok"}
    monkeypatch.setattr("requests.request", lambda **kwargs: fake_response)

    payload = client.get_json("/healthz")
    assert payload["status"] == "ok"


def test_get_json_auth_error(monkeypatch):
    client = RaspiServerClient(base_url="http://example.com")
    fake_response = mock.Mock()
    fake_response.status_code = 401
    fake_response.text = "Unauthorized"
    monkeypatch.setattr("requests.request", lambda **kwargs: fake_response)

    with pytest.raises(RaspiServerAuthError):
        client.get_json("/healthz")


def test_post_json_invalid_json(monkeypatch):
    client = RaspiServerClient(base_url="http://example.com")
    fake_response = mock.Mock()
    fake_response.status_code = 200
    fake_response.json.side_effect = ValueError("no json")
    fake_response.text = "raw"
    monkeypatch.setattr("requests.request", lambda **kwargs: fake_response)

    payload = client.post_json("/api", {"foo": "bar"})
    assert payload == {"status": "raw"}
