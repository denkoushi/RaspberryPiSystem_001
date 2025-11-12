#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${REPO_ROOT}/lib/toolmaster-usb.sh"

USB_LOG_FILE="usb_dist_export.log"
USB_LOG_TAG="tool-dist-export"

DEFAULT_SERVER_ROOT="/srv/RaspberryPiSystem_001/toolmaster"
SERVER_ROOT="${SERVER_ROOT:-${DEFAULT_SERVER_ROOT}}"
SERVER_MASTER_DIR="${SERVER_MASTER_DIR:-${SERVER_ROOT}/master}"
SERVER_DOC_DIR="${SERVER_DOC_DIR:-${SERVER_ROOT}/docviewer}"

DEVICE=""
DRY_RUN=0
INCLUDE_MASTER=1
INCLUDE_DOC=1

usage() {
  cat <<EOF
Usage: $(basename "$0") --device /dev/sdX1 [--dry-run] [--skip-master] [--skip-doc]
