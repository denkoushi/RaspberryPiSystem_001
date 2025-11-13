#!/usr/bin/env bash

# Migrated from /Users/tsudatakashi/RaspberryPiServer/scripts/tool-dist-sync.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/server/toolmaster/lib/toolmaster-usb.sh
source "${SCRIPT_DIR}/lib/toolmaster-usb.sh"

# shellcheck disable=SC2034
USB_LOG_FILE="usb_dist_sync.log"
# shellcheck disable=SC2034
USB_LOG_TAG="tool-dist-sync"

DEFAULT_CLIENT_HOME="${TOOLMASTER_CLIENT_HOME:-/home/tools02}"
DEFAULT_CLIENT_ROOT="${DEFAULT_CLIENT_HOME}/RaspberryPiSystem_001"
LOCAL_MASTER_DIR="${LOCAL_MASTER_DIR:-${DEFAULT_CLIENT_ROOT}/window_a/master}"
LOCAL_DOC_DIR="${LOCAL_DOC_DIR:-${DEFAULT_CLIENT_ROOT}/document_viewer/documents}"
IMPORTER_BIN="${IMPORTER_BIN:-/usr/local/bin/document-importer.sh}"
RUN_IMPORTER_AFTER_SYNC="${RUN_IMPORTER_AFTER_SYNC:-0}"

DEVICE=""
MOUNTPOINT=""
DRY_RUN=0

usage() {
  cat <<EOF
Usage: $(basename "$0") [--device /dev/sdX1 | --mountpoint /media/TOOLMASTER-DIST] [--dry-run]

Options:
  --device PATH       Block device to mount
  --mountpoint PATH   Existing mountpoint (skip mounting)
  --dry-run           Show planned operations without modifying data
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --device)
      DEVICE="$2"
      shift 2
      ;;
    --mountpoint)
      MOUNTPOINT="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 64
      ;;
  esac
 done

if [[ -z "${DEVICE}" && -z "${MOUNTPOINT}" ]]; then
  echo "Error: either --device or --mountpoint must be provided" >&2
  usage
  exit 64
fi

USB_MOUNT=""
cleanup() {
  if [[ -n "${USB_MOUNT}" ]]; then
    usb_unmount "${USB_MOUNT}" || true
  fi
}
trap cleanup EXIT

if [[ -n "${DEVICE}" ]]; then
  USB_MOUNT="$(usb_mount_device "${DEVICE}")" || exit 1
else
  USB_MOUNT="${MOUNTPOINT}"
fi

USB_DIST_LABEL="${USB_DIST_LABEL:-TM-DIST}"

if ! usb_validate_role "${USB_MOUNT}" "DIST" "${USB_DIST_LABEL}"; then
  usb_log "err" "validation failed for ${USB_MOUNT}"
  exit 2
fi

sync_dir() {
  local src="$1"
  local dest="$2"
  if [[ ! -d "${src}" ]]; then
    usb_log "warning" "source directory missing: ${src}"
    return 0
  fi
  if [[ ${DRY_RUN} -eq 1 ]]; then
    usb_log "notice" "would rsync ${src} -> ${dest}"
    return 0
  fi
  mkdir -p "${dest}"
  rsync -a --delete --human-readable "${src}/" "${dest}/"
}

sync_dir "${USB_MOUNT}/master" "${LOCAL_MASTER_DIR}"
sync_dir "${USB_MOUNT}/docviewer" "${LOCAL_DOC_DIR}"

if [[ "${RUN_IMPORTER_AFTER_SYNC}" == "1" ]]; then
  if [[ -x "${IMPORTER_BIN}" ]]; then
    usb_log "info" "running importer ${IMPORTER_BIN} ${USB_MOUNT}"
    if "${IMPORTER_BIN}" "${USB_MOUNT}"; then
      usb_log "info" "importer completed for ${USB_MOUNT}"
    else
      usb_log "warning" "importer returned non-zero for ${USB_MOUNT}"
    fi
  else
    usb_log "warning" "importer binary not found: ${IMPORTER_BIN}"
  fi
fi

if [[ ${DRY_RUN} -eq 0 ]]; then
  usb_log "info" "dist sync completed source=${USB_MOUNT}"
else
  usb_log "info" "dist sync dry-run complete source=${USB_MOUNT}"
fi
