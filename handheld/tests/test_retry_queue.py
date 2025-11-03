from pathlib import Path

from handheld.src.retry_queue import enqueue, load_queue, dequeue, save_queue


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
