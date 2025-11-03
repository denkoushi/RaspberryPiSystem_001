from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

QUEUE_FILE = Path("/var/lib/handheld/scan_queue.json")


def load_queue(path: Path = QUEUE_FILE) -> List[Dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def save_queue(queue: List[Dict], path: Path = QUEUE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(queue))


def enqueue(payload: Dict, path: Path = QUEUE_FILE) -> None:
    queue = load_queue(path)
    payload.setdefault("metadata", {})
    payload["metadata"].update({
        "queued_at": datetime.utcnow().isoformat(),
        "retries": 0,
        "status": "queued",
    })
    queue.append(payload)
    save_queue(queue, path)


def dequeue(limit: int = 10, path: Path = QUEUE_FILE) -> List[Dict]:
    queue = load_queue(path)
    batch = queue[:limit]
    save_queue(queue[limit:], path)
    return batch
