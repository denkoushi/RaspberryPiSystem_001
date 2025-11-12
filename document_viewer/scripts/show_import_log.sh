#!/usr/bin/env bash
# Show DocumentViewer import log with optional filtering.

set -euo pipefail

LOG_FILE=${LOG_FILE:-/var/log/document-viewer/import.log}
LINES=${LINES:-40}
FILTER=${FILTER:-}

if [[ ! -f "${LOG_FILE}" ]]; then
  echo "Log file not found: ${LOG_FILE}" >&2
  exit 1
fi

if [[ -n "${FILTER}" ]]; then
  sudo tail -n "${LINES}" "${LOG_FILE}" | grep -i -- "${FILTER}"
else
  sudo tail -n "${LINES}" "${LOG_FILE}"
fi
