#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${1:-}" ]]; then
  echo "Usage: $0 <dsn>"
  exit 1
fi

dsn="$1"

dir="$(dirname "$0")/.."
psql "$dsn" -f "$dir/config/schema.sql"
