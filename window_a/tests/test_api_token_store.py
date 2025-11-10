from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import api_token_store  # type: ignore  # noqa: E402


def test_issue_and_revoke_token(tmp_path, monkeypatch):
    token_file = tmp_path / "tokens.json"
    monkeypatch.setattr(api_token_store, "API_TOKEN_FILE", token_file)

    entry = api_token_store.issue_token("station-1", token="abc123")
    assert entry["station_id"] == "station-1"
    assert token_file.exists()

    info = api_token_store.get_token_info()
    assert info["station_id"] == "station-1"
    assert info["token"] == "abc123"

    tokens = api_token_store.list_tokens(with_token=False)
    assert tokens[0]["token_preview"]

    api_token_store.revoke_token("abc123")
    assert not api_token_store.get_active_tokens()


def test_keep_existing_token(tmp_path, monkeypatch):
    token_file = tmp_path / "tokens.json"
    monkeypatch.setattr(api_token_store, "API_TOKEN_FILE", token_file)

    first = api_token_store.issue_token("station-x", token="token-a")
    second = api_token_store.issue_token("station-x", token="token-b", keep_existing=True)

    active = api_token_store.get_active_tokens()
    assert len(active) == 2
    assert {a["token"] for a in active} == {"token-a", "token-b"}
    assert first["token"] != second["token"]
