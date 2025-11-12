#!/usr/bin/env bash

# Migrated from /Users/tsudatakashi/RaspberryPiServer/scripts/tool-dist-export.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/server/toolmaster/lib/toolmaster-usb.sh
source "${SCRIPT_DIR}/lib/toolmaster-usb.sh"

# shellcheck disable=SC2034
USB_LOG_FILE="usb_dist_export.log"
# shellcheck disable=SC2034
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

Options:
  --device PATH   Block device to mount (required)
  --dry-run       Show planned operations without modifying data
  --skip-master   Omit master/ directory from export
  --skip-doc      Omit docviewer/ directory from export
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --device)
      DEVICE="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --skip-master)
      INCLUDE_MASTER=0
      shift
      ;;
    --skip-doc)
      INCLUDE_DOC=0
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

if [[ -z "${DEVICE}" ]]; then
  echo "Error: --device is required" >&2
  usage
  exit 64
fi

if [[ ${INCLUDE_MASTER} -eq 0 && ${INCLUDE_DOC} -eq 0 ]]; then
  echo "Error: nothing to export (both master and doc skipped)" >&2
  exit 64
fi

rsync_flags=(-a --delete --human-readable)
if [[ ${DRY_RUN} -eq 1 ]]; then
  rsync_flags+=(--dry-run --itemize-changes)
fi

USB_MOUNT=""
cleanup() {
  if [[ -n "${USB_MOUNT}" ]]; then
    usb_unmount "${USB_MOUNT}" || true
  fi
}
trap cleanup EXIT

USB_MOUNT="$(usb_mount_device "${DEVICE}")" || exit 1

USB_DIST_LABEL="${USB_DIST_LABEL:-TM-DIST}"

if ! usb_validate_role "${USB_MOUNT}" "DIST" "${USB_DIST_LABEL}"; then
  usb_log "err" "validation failed for ${DEVICE}"
  exit 2
fi

if [[ ! -d "${SERVER_MASTER_DIR}" && ${INCLUDE_MASTER} -eq 1 ]]; then
  usb_log "err" "server master directory missing: ${SERVER_MASTER_DIR}"
  exit 3
fi
if [[ ! -d "${SERVER_DOC_DIR}" && ${INCLUDE_DOC} -eq 1 ]]; then
  usb_log "err" "server docviewer directory missing: ${SERVER_DOC_DIR}"
  exit 3
fi

copy_to_usb() {
  local src="$1"
  local dest="$2"
  mkdir -p "${dest}"
  rsync "${rsync_flags[@]}" "${src}/" "${dest}/"
}

if [[ ${INCLUDE_MASTER} -eq 1 ]]; then
  usb_log "info" "exporting master data to USB"
  copy_to_usb "${SERVER_MASTER_DIR}" "${USB_MOUNT}/master"
fi

if [[ ${INCLUDE_DOC} -eq 1 ]]; then
  usb_log "info" "exporting docviewer data to USB"
  copy_to_usb "${SERVER_DOC_DIR}" "${USB_MOUNT}/docviewer"
fi

update_meta() {
  local file="$1"
  local ts
  ts="$(date +%s)"
  if [[ ${DRY_RUN} -eq 1 ]]; then
    usb_log "notice" "would update meta ${file}"
    return 0
  fi
  mkdir -p "$(dirname "${file}")"
  printf '{"updated_at": %s}\n' "${ts}" > "${file}"
}

if [[ ${INCLUDE_MASTER} -eq 1 ]]; then
  update_meta "${USB_MOUNT}/master/meta.json"
fi
if [[ ${INCLUDE_DOC} -eq 1 ]]; then
  update_meta "${USB_MOUNT}/docviewer/meta.json"
fi

usb_log "info" "dist export completed (dry_run=${DRY_RUN})"
