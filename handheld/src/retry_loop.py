from __future__ import annotations

from typing import Callable, Dict, List

from .retry_queue import dequeue, update_retry_status, enqueue


def retry_failed_sends(send_func: Callable[[Dict], bool], batch_size: int = 10, path=...):
    batch: List[Dict] = dequeue(batch_size, path)
    for item in batch:
        success = send_func(item)
        update_retry_status(item, success=success)
        if not success:
            enqueue(item, path)
