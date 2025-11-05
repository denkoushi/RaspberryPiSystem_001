#!/usr/bin/env python3
"""
Send a test scan payload to RaspberryPiServer.

Example:
    source ~/RaspberryPiSystem_001/server/.venv/bin/activate
    python client_window_a/scripts/send_scan.py \
      --order TEST-900 --location RACK-Z9 --device HANDHELD-01
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

DEFAULT_API_BASE = "http://127.0.0.1:8501"


@dataclass
class ScanPayload:
    order_code: str
    location_code: str
    device_id: str | None = None

    def as_dict(self) -> dict[str, str]:
        data = {
            "order_code": self.order_code,
            "location_code": self.location_code,
        }
        if self.device_id:
            data["device_id"] = self.device_id
        return data


def generate_default_codes() -> tuple[str, str]:
    suffix = int(time.time())
    order = f"TEST-{suffix}"
    location = f"RACK-{suffix % 100:02d}"
    return order, location


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send scan payload to RaspberryPiServer.")
    parser.add_argument("--api", dest="api_base", default=os.environ.get("API_BASE", DEFAULT_API_BASE))
    parser.add_argument("--order", dest="order_code")
    parser.add_argument("--location", dest="location_code")
    parser.add_argument("--device", dest="device_id", default=os.environ.get("DEVICE_ID"))
    parser.add_argument("--token", dest="token", default=os.environ.get("API_TOKEN"))
    parser.add_argument("--dry-run", action="store_true", help="Print payload without sending")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    order = args.order_code
    location = args.location_code

    if not order or not location:
        generated_order, generated_loc = generate_default_codes()
        order = order or generated_order
        location = location or generated_loc

    payload = ScanPayload(order_code=order, location_code=location, device_id=args.device_id)
    print("=== Send Scan Payload ===")
    print(f"API base   : {args.api_base}")
    print(f"Order code : {payload.order_code}")
    print(f"Location   : {payload.location_code}")
    print(f"Device     : {payload.device_id or '(none)'}")

    if args.dry_run:
        print("Dry-run mode. Payload not sent.")
        return 0

    url = f"{args.api_base.rstrip('/')}/api/v1/scans"
    data = json.dumps(payload.as_dict()).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"

    request = urllib.request.Request(url=url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8")
            print(f"Response ({response.status}): {body}")
            return 0
    except urllib.error.HTTPError as exc:
        print(f"HTTP error {exc.code}: {exc.read().decode('utf-8')}", file=sys.stderr)
        return exc.code
    except urllib.error.URLError as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
