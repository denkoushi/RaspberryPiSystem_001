#!/usr/bin/env python3
"""
Utility CLI to enqueue and transmit a scan payload without the handheld UI/GPIO stack.

This is a stopgap "Plan B" tool that reuses ScanTransmitter so we can verify the
Pi Zero -> Pi5 -> Window A -> DocumentViewer pipeline even when the Waveshare
e-paper stack is unavailable (e.g., running headless or during CI).
"""

import argparse
import json
import logging
import os
import sys
import uuid
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CONFIG_SEARCH_PATHS = [
    os.environ.get("ONSITE_CONFIG"),
    "/etc/onsitelogistics/config.json",
    str(ROOT / "handheld" / "config" / "config.json"),
]


def load_config(explicit: str | None = None) -> dict:
    """Simplified loader to avoid importing handheld_scan_display (which needs GPIO)."""
    candidates = [explicit] if explicit else CONFIG_SEARCH_PATHS
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if path.exists():
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)

    raise FileNotFoundError(
        "Config file not found. Set ONSITE_CONFIG or create /etc/onsitelogistics/config.json"
    )


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

    payload = {
        "order_code": args.order,
        "location_code": args.location,
        "device_id": args.device,
        "metadata": {
            "scan_id": str(uuid.uuid4()),
        },
    }

    headers = {
        "Authorization": f"Bearer {config['api_token']}",
        "Content-Type": "application/json",
    }

    target_url = config["api_url"]
    logging.info("POST %s: %s", target_url, payload)
    response = requests.post(target_url, json=payload, headers=headers, timeout=config.get("timeout_seconds", 5))
    response.raise_for_status()
    logging.info("Server responded %s", response.status_code)

    logistics_url = config.get("logistics_api_url")
    if logistics_url:
        logistics_payload = {
            "job_id": f"job-{uuid.uuid4().hex}",
            "part_code": args.order,
            "from_location": config.get("logistics_default_from", "UNKNOWN"),
            "to_location": args.location,
            "status": config.get("logistics_status", "completed"),
            "requested_at": payload["metadata"]["scan_id"],
            "updated_at": payload["metadata"]["scan_id"],
        }
        try:
            logging.info("Posting logistics payload to %s", logistics_url)
            resp = requests.post(logistics_url, json=logistics_payload, headers=headers, timeout=config.get("timeout_seconds", 5))
            resp.raise_for_status()
            logging.info("Logistics API accepted payload")
        except requests.RequestException as exc:
            logging.warning("Logistics API call failed: %s", exc)


if __name__ == "__main__":
    main()
