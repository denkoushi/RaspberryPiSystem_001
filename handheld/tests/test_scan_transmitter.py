from pathlib import Path
import sys
import types


class _DummyInputDevice:
    def __init__(self, *_, **__):
        pass

    def read_one(self):
        return None

    def grab(self):
        pass

    def ungrab(self):
        pass

    def close(self):
        pass


fake_evdev = types.SimpleNamespace(
    InputDevice=_DummyInputDevice,
    categorize=lambda event: event,
    ecodes=types.SimpleNamespace(EV_KEY=1),
)
sys.modules.setdefault("evdev", fake_evdev)


class _DummyEPD:
    height = 250
    width = 122

    def init(self):
        pass

    def display(self, *_args, **__kwargs):
        pass

    def displayPartBaseImage(self, *_args, **__kwargs):
        pass

    def displayPartial(self, *_args, **__kwargs):
        pass

    def getbuffer(self, image):
        return image

    def sleep(self):
        pass


fake_epd_module = types.SimpleNamespace(epd2in13_V4=types.SimpleNamespace(EPD=_DummyEPD))
sys.modules.setdefault("waveshare_epd", fake_epd_module)
sys.modules.setdefault("waveshare_epaper", fake_epd_module)

from handheld.scripts.handheld_scan_display import ScanTransmitter


def _make_config(tmp_path: Path) -> dict:
    return {
        "api_url": "http://example.com/api",
        "api_token": "dummy",
        "device_id": "HANDHELD-TEST",
        "queue_db_path": str(tmp_path / "queue.db"),
    }


def test_send_or_queue_reports_success_and_failure(tmp_path: Path) -> None:
    calls: list[tuple[int, int]] = []

    tx = ScanTransmitter(_make_config(tmp_path), mirrorctl_hook=lambda ok, ng: calls.append((ok, ng)))
    tx._post = lambda url, payload: True  # type: ignore[attr-defined]
    assert tx.send_or_queue("http://example.com/api", {"scan_id": "1"}) is True

    tx._post = lambda url, payload: False  # type: ignore[attr-defined]
    assert tx.send_or_queue("http://example.com/api", {"scan_id": "2"}) is False

    assert calls == [(1, 0), (0, 1)]
    assert tx.queue_size() == 1


def test_drain_reports_success_and_failure(tmp_path: Path) -> None:
    calls: list[tuple[int, int]] = []
    tx = ScanTransmitter(_make_config(tmp_path), mirrorctl_hook=lambda ok, ng: calls.append((ok, ng)))

    # enqueue two payloads manually
    tx.enqueue("http://example.com/api", {"scan_id": "1"})
    tx.enqueue("http://example.com/api", {"scan_id": "2"})

    outcomes = [True, False]

    def fake_post(url, payload):
        return outcomes.pop(0)

    tx._post = fake_post  # type: ignore[attr-defined]
    processed = tx.drain()
    assert processed is True
    assert calls == [(1, 1)]
