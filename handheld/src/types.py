from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScanPayload:
    order_code: str
    location_code: str
    device_id: Optional[str] = None


@dataclass
class RetryItem:
    payload: ScanPayload
    metadata: dict = field(default_factory=dict)
