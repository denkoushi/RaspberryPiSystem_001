#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(git rev-parse --show-toplevel)"
cat "$ROOT_DIR/handheld/docs/patches/2025-11-07-handheld-payload.patch"
