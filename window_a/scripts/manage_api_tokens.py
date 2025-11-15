#!/usr/bin/env python3
"""CLI helper for managing Window A API tokens."""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

from api_token_store import (
    API_TOKEN_FILE,
    API_TOKEN_HEADER,
    issue_token,
    list_tokens,
    revoke_token,
)


def _print(data) -> None:
    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def cmd_list(args: argparse.Namespace) -> None:
    tokens = list_tokens(with_token=args.reveal)
    payload = {
        "file": str(API_TOKEN_FILE),
        "header": API_TOKEN_HEADER,
        "count": len(tokens),
        "tokens": tokens,
    }
    _print(payload)


def cmd_issue(args: argparse.Namespace) -> None:
    entry = issue_token(
        station_id=args.station_id,
        token=args.token,
        keep_existing=args.keep_existing,
        note=args.note,
    )
    _print(
        {
            "message": "token issued",
            "file": str(API_TOKEN_FILE),
            "entry": entry,
        }
    )


def cmd_revoke(args: argparse.Namespace) -> None:
    revoked = revoke_token(args.token)
    _print(
        {
            "message": "token revoked" if revoked else "token not found",
            "file": str(API_TOKEN_FILE),
            "token": args.token,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage Window A API tokens stored in config/api_tokens.json"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ls = sub.add_parser("list", help="Show tokens (masked by default)")
    ls.add_argument("--reveal", action="store_true", help="Show full token values")
    ls.set_defaults(func=cmd_list)

    issue = sub.add_parser("issue", help="Create a new token for a station")
    issue.add_argument("station_id", help="Station identifier (e.g., window-a-01)")
    issue.add_argument("--token", help="Explicit token value (defaults to random)")
    issue.add_argument(
        "--keep-existing",
        action="store_true",
        help="Do not revoke existing tokens for the same station",
    )
    issue.add_argument("--note", help="Optional note")
    issue.set_defaults(func=cmd_issue)

    revoke = sub.add_parser("revoke", help="Revoke an existing token by value")
    revoke.add_argument("token", help="Exact token to revoke")
    revoke.set_defaults(func=cmd_revoke)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
