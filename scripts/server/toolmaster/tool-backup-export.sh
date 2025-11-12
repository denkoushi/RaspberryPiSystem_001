#!/usr/bin/env bash

# Migrated from /Users/tsudatakashi/RaspberryPiServer/scripts/tool-backup-export.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

source "${REPO_ROOT}/lib/toolmaster-usb.sh"

USB_LOG_FILE="usb_backup.log"
USB_LOG_TAG="tool-backup-export"

DEFAULT_SERVER_ROOT="/srv/RaspberryPiSystem_001/toolmaster"
SNAPSHOT_DIR="${SNAPSHOT_DIR:-${DEFAULT_SERVER_ROOT}/snapshots}"
RETENTION_COUNT="${BACKUP_RETENTION:-4}"

DEVICE=""
DRY_RUN=0

usage() {
  cat <<EOF
Usage: $(basename "$0") --device /dev/sdX1 [--dry-run] [--snapshot-dir PATH] [--retention N]

Options:
  --device PATH       Block device to mount (required)
  --snapshot-dir PATH Source snapshot root (default: ${SNAPSHOT_DIR})
  --retention N       Number of archives to keep on USB (default: ${RETENTION_COUNT})
  --dry-run           Show planned operations without writing
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --device)
      DEVICE="$2"
      shift 2
      ;;
    --snapshot-dir)
      SNAPSHOT_DIR="$2"
      shift 2
      ;;
    --retention)
      RETENTION_COUNT="$2"
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

if [[ -z "${DEVICE}" ]]; then
  echo "Error: --device is required" >&2
  usage
  exit 64
fi

if [[ ! -d "${SNAPSHOT_DIR}" ]]; then
  usb_log "err" "snapshot directory not found: ${SNAPSHOT_DIR}"
  exit 2
fi

latest_snapshot="$(find "${SNAPSHOT_DIR}" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' \
  | sort -nr | head -n1 | cut -d' ' -f2-)"

if [[ -z "${latest_snapshot}" ]]; then
  usb_log "err" "no snapshots available in ${SNAPSHOT_DIR}"
  exit 3
fi

snapshot_name="$(basename "${latest_snapshot}")"
archive_name="${snapshot_name}_full.tar.zst"

USB_MOUNT=""
cleanup() {
  if [[ -n "${USB_MOUNT}" ]]; then
    usb_unmount "${USB_MOUNT}" || true
  fi
}
trap cleanup EXIT

USB_MOUNT="$(usb_mount_device "${DEVICE}")" || exit 1

USB_BACKUP_LABEL="${USB_BACKUP_LABEL:-TM-BACKUP}"

if ! usb_validate_role "${USB_MOUNT}" "BACKUP" "${USB_BACKUP_LABEL}"; then
  usb_log "err" "validation failed for ${DEVICE}"
  exit 2
fi

dest_path="${USB_MOUNT}/${archive_name}"
start_ns=0

if [[ ${DRY_RUN} -eq 1 ]]; then
  usb_log "notice" "would archive ${latest_snapshot} -> ${dest_path}"
else
  usb_log "info" "creating archive ${archive_name} from ${latest_snapshot}"
  start_ns=$(date +%s%N 2>/dev/null || echo 0)
  tar --zstd -cf "${dest_path}" -C "${latest_snapshot}" .
fi

if [[ ${RETENTION_COUNT} -gt 0 ]]; then
  old_archives=$(find "${USB_MOUNT}" -maxdepth 1 -type f -name '*_full.tar.zst' -printf '%T@ %p\n' | sort -n)
  count=$(printf '%s\n' "${old_archives}" | wc -l | tr -d ' ')
  if [[ ${count:-0} -gt ${RETENTION_COUNT} ]]; then
    remove_count=$((count - RETENTION_COUNT))
    if [[ ${remove_count} -gt 0 ]]; then
      printf '%s\n' "${old_archives}" | head -n "${remove_count}" | cut -d' ' -f2- | while read -r file; do
        if [[ ${DRY_RUN} -eq 1 ]]; then
          usb_log "notice" "would remove old archive ${file}"
        else
          usb_log "info" "removing old archive ${file}"
          rm -f "${file}"
        fi
      done
    fi
  fi
fi

if [[ ${DRY_RUN} -eq 0 ]]; then
  size_bytes=$(stat -c %s "${dest_path}")
  if [[ ${start_ns} -gt 0 ]]; then
    end_ns=$(date +%s%N 2>/dev/null || echo 0)
    if [[ ${end_ns} -gt ${start_ns} ]]; then
      duration_ms=$(((end_ns - start_ns) / 1000000))
    else
      duration_ms=0
    fi
  else
    duration_ms=0
  fi
else
  size_bytes=0
  duration_ms=0
fi

usb_log "info" "backup export completed archive=${archive_name} size=${size_bytes} dry_run=${DRY_RUN}"
