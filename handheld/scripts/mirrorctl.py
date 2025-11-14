#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from handheld.src import mirrorctl_client


def cmd_status(args: argparse.Namespace) -> None:
    data = mirrorctl_client.state_as_dict()
    if getattr(args, "json", False):
        json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
    else:
        print(f"mirrorctl enabled : {data['enabled']}")
        print(f"last_success_at   : {data['last_success_at']}")
        print(f"last_failure_at   : {data['last_failure_at']}")
        print(f"pending_failures  : {data['pending_failures']}")
        print(f"success_days      : {data['consecutive_success_days']}")
        print(f"failure_days      : {data['consecutive_failure_days']}")
        print(f"last_update_at    : {data['last_update_at']}")
        if data.get("notes"):
            print(f"notes             : {data['notes']}")


def cmd_enable(args: argparse.Namespace) -> None:
    mirrorctl_client.set_enabled(True, reason=args.note)
    cmd_status(argparse.Namespace(json=False))


def cmd_disable(args: argparse.Namespace) -> None:
    mirrorctl_client.set_enabled(False, reason=args.note)
    cmd_status(argparse.Namespace(json=False))


def cmd_update(args: argparse.Namespace) -> None:
    mirrorctl_client.update_status(args.success, args.failure)
    cmd_status(argparse.Namespace(json=False))


def cmd_audit(args: argparse.Namespace) -> None:
    mirrorctl_client.append_audit_entry(args.message)
    print("audit entry added")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="mirrorctl helper CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    status_cmd = sub.add_parser("status", help="Show current mirrorctl status")
    status_cmd.add_argument("--json", action="store_true", help="Print JSON output")
    status_cmd.set_defaults(func=cmd_status)

    enable_cmd = sub.add_parser("enable", help="Enable mirror mode")
    enable_cmd.add_argument("--note", help="Optional note to store with state")
    enable_cmd.set_defaults(func=cmd_enable)

    disable_cmd = sub.add_parser("disable", help="Disable mirror mode")
    disable_cmd.add_argument("--note", help="Optional note to store with state")
    disable_cmd.set_defaults(func=cmd_disable)

    update_cmd = sub.add_parser("update", help="Record send results (success/failure counts)")
    update_cmd.add_argument("--success", type=int, default=0, help="Number of successful sends")
    update_cmd.add_argument("--failure", type=int, default=0, help="Number of failed sends")
    update_cmd.set_defaults(func=cmd_update)

    audit_cmd = sub.add_parser("audit", help="Append an audit log entry")
    audit_cmd.add_argument("--message", required=True, help="Audit message to append")
    audit_cmd.set_defaults(func=cmd_audit)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
