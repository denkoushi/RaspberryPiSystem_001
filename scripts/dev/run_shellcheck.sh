#!/usr/bin/env bash
# Runs shellcheck against the repository's Bash scripts.
# 旧 RaspberryPiServer でも `shellcheck` を用いた lint を運用していたため、
# Docker イメージ (koalaman/shellcheck) を fallback として使用し、開発環境に
# shellcheck が未導入でも同じ結果を得られるようにする。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

default_targets=(
  "scripts/server/toolmaster/lib/toolmaster-usb.sh"
  "scripts/server/toolmaster/tool-ingest-sync.sh"
  "scripts/server/toolmaster/tool-dist-export.sh"
  "scripts/server/toolmaster/tool-backup-export.sh"
  "scripts/server/toolmaster/tool-dist-sync.sh"
  "scripts/dev/run_shellcheck.sh"
)

if [[ $# -gt 0 ]]; then
  targets=("$@")
else
  targets=("${default_targets[@]}")
fi

run_shellcheck() {
  if command -v shellcheck >/dev/null 2>&1; then
    shellcheck "$@"
    return 0
  fi

  if command -v docker >/dev/null 2>&1; then
    docker run --rm -v "${REPO_ROOT}:/work" -w /work koalaman/shellcheck:stable "$@"
    return 0
  fi

  echo "shellcheck is not available (neither host binary nor docker). Please install shellcheck or Docker." >&2
  return 1
}

run_shellcheck "${targets[@]}"
