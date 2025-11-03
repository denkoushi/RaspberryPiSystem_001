from pathlib import Path

from handheld.src.retry_queue import save_queue, load_queue
from handheld.src.retry_loop import retry_failed_sends


def test_retry_loop(tmp_path: Path):
    queue_file = tmp_path / "queue.json"
    save_queue([
        {"payload": 1, "metadata": {"retries": 0}},
        {"payload": 2, "metadata": {"retries": 0}},
    ], path=queue_file)

    def send_func(item):
        return item["payload"] == 1

    mirrorctl_calls = []

    retry_failed_sends(
        send_func,
        batch_size=2,
        path=queue_file,
        mirrorctl_hook=lambda ok, ng: mirrorctl_calls.append((ok, ng)),
    )

    queue = load_queue(queue_file)
    assert len(queue) == 1
    assert queue[0]["payload"] == 2
    assert queue[0]["metadata"]["retries"] == 1
    assert mirrorctl_calls == [(1, 1)]
