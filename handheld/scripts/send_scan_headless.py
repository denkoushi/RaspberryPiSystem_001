#!/usr/bin/env python3
"""
Utility CLI to enqueue and transmit a scan payload without the handheld UI/GPIO stack.

This is a stopgap "Plan B" tool that reuses ScanTransmitter so we can verify the
Pi Zero -> Pi5 -> Window A -> DocumentViewer pipeline even when the Waveshare
e-paper stack is unavailable (e.g., running headless or during CI).
"""

import argparse
import logging
import uuid
from pathlib import Path

from handheld.scripts.handheld_scan_display import load_config
from handheld.src.retry_loop import ScanTransmitter


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send a single scan payload using the handheld queue logic (headless)"
    )
    parser.add_argument("--order", required=True, help="Order code (A code)")
    parser.add_argument("--location", required=True, help="Location code (B code)")
    parser.add_argument(
        "--device",
        default="HANDHELD-ZERO",
        help="Device ID reported in the payload (default: HANDHELD-ZERO)",
    )
    parser.add_argument(
        "--config",
        help="Optional path to config.json (otherwise follows handheld load order)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Python logging level (default: INFO)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    config = load_config(args.config)
    transmitter = ScanTransmitter(config)

    payload = {
        "order_code": args.order,
        "location_code": args.location,
        "device_id": args.device,
        "metadata": {
            "scan_id": str(uuid.uuid4()),
        },
    }

    logging.info("Queueing payload: %s", payload)
    transmitter.enqueue(payload)
    transmitter.drain()
    logging.info("Queue drained. Pending size: %s", transmitter.queue_size())


if __name__ == "__main__":
    main()
