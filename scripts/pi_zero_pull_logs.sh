#!/usr/bin/env bash
# Pi Zero から journalctl / mirrorctl / ネットワーク情報をまとめて取得するスクリプト。

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <pi-zero-host> [--service handheld@tools01.service] [--output ./pi-zero-logs]" >&2
  exit 1
fi

HOST="$1"
shift || true
SERVICE="handheld@tools01.service"
OUT_DIR="./pi-zero-logs"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --service)
      SERVICE="$2"
      shift 2
      ;;
    --output)
      OUT_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
DEST_DIR="${OUT_DIR}/${HOST}-${TIMESTAMP}"
mkdir -p "${DEST_DIR}"

ssh "${HOST}" "sudo mirrorctl status" > "${DEST_DIR}/mirrorctl-status.txt"
ssh "${HOST}" "sudo systemctl status ${SERVICE}" > "${DEST_DIR}/systemctl-status.txt" || true
ssh "${HOST}" "sudo journalctl -u ${SERVICE} -n 200 --no-pager" > "${DEST_DIR}/journalctl-${SERVICE}.log"
ssh "${HOST}" "hostname && uptime && ip addr" > "${DEST_DIR}/system-info.txt"

echo "Logs collected in ${DEST_DIR}"
