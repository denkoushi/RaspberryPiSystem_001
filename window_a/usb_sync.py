"""Window A USB sync helper.

旧システムで使用していた USB 同期スクリプトはまだ移植されていないため、
現時点では最小限のスタブを提供する。将来 `scripts/usb_sync.sh` などの
実装が追加された際は、本モジュールで呼び分ける。
"""

from __future__ import annotations

import logging
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List

LOGGER = logging.getLogger(__name__)
SCRIPT_CANDIDATES: List[Path] = [
    Path(__file__).resolve().parent / "scripts" / "usb_sync.sh",
    Path(__file__).resolve().parent / "scripts" / "usb_sync.py",
]


def run_usb_sync(device: str = "/dev/sda1") -> Dict[str, Any]:
    """Run USB sync script if available, otherwise return a stub result."""

    custom_cmd = os.environ.get("WINDOW_A_USB_SYNC_CMD")
    command: List[str] | None = None

    if custom_cmd:
        command = shlex.split(custom_cmd)
    else:
        for candidate in SCRIPT_CANDIDATES:
            if candidate.exists():
                command = [str(candidate)]
                break

    if command:
        env = os.environ.copy()
        env.setdefault("USB_SYNC_DEVICE", device)
        try:
            proc = subprocess.run(
                command + [device],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
        except Exception as exc:  # pragma: no cover - unexpected runtime failure
            LOGGER.exception("usb_sync command failed: %s", exc)
            return {
                "returncode": 1,
                "stdout": "",
                "stderr": str(exc),
                "steps": ["command=%s" % " ".join(command)],
            }

        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "steps": [
                "command=%s" % " ".join(command),
                f"exitcode={proc.returncode}",
            ],
        }

    message = (
        "usb_sync script is not available in this repository yet. "
        "Device request was accepted but no action was taken."
    )
    LOGGER.warning(message)
    return {
        "returncode": 1,
        "stdout": "",
        "stderr": message,
        "steps": [
            f"device={device}",
            "WINDOW_A_USB_SYNC_CMD not set",
            "scripts/usb_sync.sh not found",
        ],
    }
