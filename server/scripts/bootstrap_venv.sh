#!/usr/bin/env bash
# Bootstrap or refresh the local virtual environment for RaspberryPiServer.
# This script creates server/.venv if needed and installs dependencies in editable mode.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"

PYTHON_BIN=""
for candidate in python3.12 python3.11 python3; do
  if command -v "${candidate}" >/dev/null 2>&1; then
    version="$(${candidate} -c 'import sys; print(".".join(str(x) for x in sys.version_info[:2]))')"
    major="${version%%.*}"
    minor="${version##*.}"
    if (( major > 3 )) || { (( major == 3 )) && (( minor >= 11 )); }; then
      PYTHON_BIN="${candidate}"
      break
    fi
  fi
done

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "[bootstrap_venv] Python 3.11+ is required. Install python3.11 and retry."
  exit 1
fi

if [[ -n "${VIRTUAL_ENV:-}" ]]; then
  echo "[bootstrap_venv] Please deactivate the current virtualenv (${VIRTUAL_ENV}) before running."
  exit 1
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "[bootstrap_venv] Creating virtual environment at ${VENV_DIR} using ${PYTHON_BIN}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
else
  echo "[bootstrap_venv] Reusing existing virtual environment at ${VENV_DIR}"
fi

ACTIVATE="${VENV_DIR}/bin/activate"
if [[ ! -f "${ACTIVATE}" ]]; then
  echo "[bootstrap_venv] Missing activate script (${ACTIVATE}). Removing broken venv."
  rm -rf "${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

echo "[bootstrap_venv] Activating virtual environment"
# shellcheck disable=SC1090
source "${ACTIVATE}"

echo "[bootstrap_venv] Upgrading pip/setuptools/wheel"
python -m pip install --upgrade pip setuptools wheel >/dev/null

echo "[bootstrap_venv] Installing project in editable mode with dev extras"
pip install -e "${PROJECT_ROOT}[dev]"

echo "[bootstrap_venv] Environment ready. To activate later, run:"
echo "  source ${VENV_DIR}/bin/activate"
