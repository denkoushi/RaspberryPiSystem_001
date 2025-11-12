#!/usr/bin/env bash

# Migrated from /Users/tsudatakashi/RaspberryPiServer/scripts/tool-dist-sync.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${REPO_ROOT}/lib/toolmaster-usb.sh"

USB_LOG_FILE="usb_dist_sync.log"
USB_LOG_TAG="tool-dist-sync"

LOCAL_MASTER_DIR="${LOCAL_MASTER_DIR:-/opt/toolmaster/master}"
LOCAL_DOC_DIR="${LOCAL_DOC_DIR:-/opt/toolmaster/docviewer}"

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

if [[ ${DRY_RUN} -eq 0 ]]; then
  usb_log "info" "dist sync completed source=${USB_MOUNT}"
else
  usb_log "info" "dist sync dry-run complete source=${USB_MOUNT}"
fi
