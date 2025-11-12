#!/usr/bin/env python3
"""Simple health check for the DocumentViewer API.

Usage:
    ./scripts/docviewer_check.py --part TESTPART \
        --api-base http://raspi-server.local:8501 --token raspi-token-20251026

Checks `/api/documents/<part>` endpoint and prints the response JSON.
Optionally verifies that a PDF exists on the local filesystem when
`--docs-dir` is provided.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DocumentViewer API check")
    parser.add_argument(
        "--api-base",
        default=os.getenv("VIEWER_API_BASE", "http://127.0.0.1:8501"),
        help="DocumentViewer API base URL (default: env VIEWER_API_BASE or http://127.0.0.1:8501)",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("VIEWER_API_TOKEN", ""),
        help="Bearer token (default: env VIEWER_API_TOKEN)",
    )
    parser.add_argument(
        "--part",
        required=True,
        help="Part number to query",
    )
    parser.add_argument(
        "--docs-dir",
        help="Optional directory to confirm that <part>.pdf exists",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="HTTP timeout in seconds (default: 5)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print raw JSON without formatting",
    )
    return parser.parse_args()


def build_headers(token: str) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token.strip()}"
    return headers


def fetch_document(api_base: str, part: str, headers: dict[str, str], timeout: float) -> dict[str, Any]:
    url = f"{api_base.rstrip('/')}/api/documents/{part}"
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


def check_local_file(docs_dir: str, filename: str) -> bool:
    path = Path(docs_dir).expanduser().resolve() / filename
    return path.is_file()


def main() -> None:
    args = parse_args()
    headers = build_headers(args.token)

    try:
        result = fetch_document(args.api_base, args.part, headers, args.timeout)
    except requests.HTTPError as exc:
        print(f"HTTP error: {exc}")
        if exc.response is not None:
            print(f"Response: {exc.response.text}")
        raise SystemExit(2) from exc
    except requests.RequestException as exc:  # pragma: no cover - network issues
        print(f"Request failed: {exc}")
        raise SystemExit(3) from exc

    if args.raw:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.docs_dir and result.get("found") and "filename" in result:
        exists = check_local_file(args.docs_dir, result["filename"])
        status = "OK" if exists else "MISSING"
        print(f"Local file check: {status} ({args.docs_dir}/{result['filename']})")
        if not exists:
            raise SystemExit(4)


if __name__ == "__main__":
    main()
