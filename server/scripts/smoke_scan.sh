#!/usr/bin/env bash
# Run a lightweight end-to-end scan submission against the local server.
# Steps:
#   1. Ensure no existing server process is listening on the target port.
#   2. Start `python -m raspberrypiserver.app` in the background.
#   3. Invoke client_window_a/scripts/send_scan.py to POST a scan payload.
#   4. Shut down the temporary server and report the outcome.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
PORT="${PORT:-8501}"
API_BASE="${API_BASE:-http://127.0.0.1:${PORT}}"
ORDER_CODE="${ORDER_CODE:-SMOKE-$(date +%s)}"
LOCATION_CODE="${LOCATION_CODE:-RACK-SM}"
DEVICE_ID="${DEVICE_ID:-HANDHELD-SMOKE}"
SEND_SCRIPT="${PROJECT_ROOT}/../client_window_a/scripts/send_scan.py"
LOG_FILE="${PROJECT_ROOT}/tmp/smoke_server.log"

cleanup() {
  local status=$?
  if [[ -n "${SERVER_PID:-}" ]] && ps -p "${SERVER_PID}" >/dev/null 2>&1; then
    kill "${SERVER_PID}" >/dev/null 2>&1 || true
    wait "${SERVER_PID}" 2>/dev/null || true
  fi
  echo "[smoke_scan] Logs:"
  [[ -f "${LOG_FILE}" ]] && tail -n 20 "${LOG_FILE}"
  rm -f "${LOG_FILE}"
  return "${status}"
}
trap cleanup EXIT

if [[ ! -f "${VENV_DIR}/bin/activate" ]]; then
  echo "[smoke_scan] Missing virtualenv at ${VENV_DIR}. Run scripts/bootstrap_venv.sh first."
  exit 1
fi

if lsof -i :"${PORT}" >/dev/null 2>&1; then
  echo "[smoke_scan] Port ${PORT} already in use; aborting."
  exit 1
fi

mkdir -p "$(dirname "${LOG_FILE}")"

echo "[smoke_scan] Starting server on port ${PORT}"
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"
python -m raspberrypiserver.app >"${LOG_FILE}" 2>&1 &
SERVER_PID=$!
sleep 3

if ! ps -p "${SERVER_PID}" >/dev/null 2>&1; then
  echo "[smoke_scan] Server failed to start"
  exit 1
fi

echo "[smoke_scan] Posting scan via ${SEND_SCRIPT}"
python "${SEND_SCRIPT}" \
  --api "${API_BASE}" \
  --order "${ORDER_CODE}" \
  --location "${LOCATION_CODE}" \
  --device "${DEVICE_ID}"

echo "[smoke_scan] Completed successfully"
