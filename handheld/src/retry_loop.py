from __future__ import annotations

from typing import Callable, Dict, List

from pathlib import Path

from .retry_queue import dequeue, update_retry_status, enqueue, QUEUE_FILE


def retry_failed_sends(
    send_func: Callable[[Dict], bool],
    batch_size: int = 10,
    path: Path = QUEUE_FILE,
    mirrorctl_hook: Callable[[int, int], None] | None = None,
):
    batch: List[Dict] = dequeue(batch_size, path)
    success_count = 0
    failure_count = 0

    for item in batch:
        success = send_func(item)
        update_retry_status(item, success=success)
        if not success:
            enqueue(item, path)
            failure_count += 1
        else:
            success_count += 1

    if mirrorctl_hook:
        mirrorctl_hook(success_count, failure_count)
