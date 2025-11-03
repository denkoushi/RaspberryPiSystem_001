from pathlib import Path

from handheld.src.retry_queue import enqueue, load_queue, dequeue, save_queue, update_retry_status
from handheld.src.types import RetryItem, ScanPayload


def test_enqueue_metadata(tmp_path: Path):
    queue_file = tmp_path / "queue.json"
    enqueue({"payload": {"order_code": "TEST"}}, path=queue_file)

    queue = load_queue(path=queue_file)
    assert queue[0]["metadata"]["status"] == "queued"
    assert queue[0]["metadata"]["retries"] == 0


def test_dequeue(tmp_path: Path):
    queue_file = tmp_path / "queue.json"
    save_queue([
        {"payload": 1},
        {"payload": 2},
    ], path=queue_file)

    batch = dequeue(limit=1, path=queue_file)
    assert batch == [{"payload": 1}]
    remaining = load_queue(path=queue_file)
    assert remaining == [{"payload": 2}]


def test_update_retry_status():
    payload = {"metadata": {"retries": 1}}
    update_retry_status(payload, success=False)
    assert payload["metadata"]["status"] == "queued"
    assert payload["metadata"]["retries"] == 2
    assert "last_retry_at" in payload["metadata"]

    update_retry_status(payload, success=True)
    assert payload["metadata"]["status"] == "sent"


def test_enqueue_dataclass(tmp_path: Path):
    queue_file = tmp_path / "queue.json"
    item = RetryItem(payload=ScanPayload(order_code="DC-1", location_code="R1"))
    enqueue(item, path=queue_file)
    queue = load_queue(path=queue_file)
    assert queue[0]["payload"]["order_code"] == "DC-1"
