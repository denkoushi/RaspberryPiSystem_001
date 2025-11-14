from pathlib import Path

from handheld.src import mirrorctl_client as mc


def test_update_status_creates_state(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    state = mc.update_status(2, 0, path=state_path)
    assert state.consecutive_success_days == 1
    assert state.pending_failures == 0
    assert state.last_success_at is not None

    state = mc.update_status(0, 3, path=state_path)
    assert state.pending_failures == 3
    assert state.consecutive_failure_days == 1
    assert state.last_failure_at is not None


def test_set_enabled(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    mc.set_enabled(False, reason="maintenance", path=state_path)
    state = mc.load_state(state_path)
    assert state.enabled is False
    assert state.notes == "maintenance"


def test_append_audit_entry(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.log"
    mc.append_audit_entry("test entry", path=audit_path)
    content = audit_path.read_text(encoding="utf-8")
    assert "test entry" in content
