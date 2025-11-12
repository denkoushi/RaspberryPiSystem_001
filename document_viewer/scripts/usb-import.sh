#!/usr/bin/env bash
# Mount a USB device and import PDF documents for the viewer.
set -euo pipefail

DEVICE="${1:-}"
MOUNT_POINT="${MOUNT_POINT:-/media/docviewer}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMPORTER="$SCRIPT_DIR/document-importer.sh"
LOG_TAG="docviewer-usb"

log(){
  echo "[$LOG_TAG] $*"
}

cleanup(){
  sync || true
  if mountpoint -q "$MOUNT_POINT"; then
    umount "$MOUNT_POINT" || log "WARN: failed to unmount $MOUNT_POINT"
  fi
}
trap cleanup EXIT

if [[ -z "$DEVICE" ]]; then
  log "ERROR: USB device path is required"
  exit 1
fi

if [[ ! -x "$IMPORTER" ]]; then
  log "ERROR: importer script not found at $IMPORTER"
  exit 1
fi

mkdir -p "$MOUNT_POINT"
log "Mounting $DEVICE to $MOUNT_POINT"
mount "$DEVICE" "$MOUNT_POINT"

USB_SUBDIR="docviewer" IMPORT_LOG="${IMPORT_LOG:-/var/log/document-viewer/import.log}" \
  "$IMPORTER" "$MOUNT_POINT"
rc=$?
log "USB import completed (exit=$rc)"
exit $rc
