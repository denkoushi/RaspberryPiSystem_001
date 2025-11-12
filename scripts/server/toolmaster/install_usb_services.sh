#!/usr/bin/env bash

# Installs Toolmaster USB systemd units and udev rules onto Pi5.
# Run as root (or via sudo) on the host where /etc/systemd/system exists.

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root (use sudo)." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_SRC_DIR="${SCRIPT_DIR}/systemd"
UDEV_RULE_SRC="${SCRIPT_DIR}/udev/90-toolmaster.rules"

SYSTEMD_DST_DIR="/etc/systemd/system"
UDEV_RULE_DST="/etc/udev/rules.d/90-toolmaster.rules"
DATA_ROOT="/srv/RaspberryPiSystem_001/toolmaster"

install_unit() {
  local src="$1"
  local dst_name
  dst_name="$(basename "${src}")"
  local dst="${SYSTEMD_DST_DIR}/${dst_name}"
  install -m 644 "${src}" "${dst}"
}

echo "[1/4] Ensuring data directories exist under ${DATA_ROOT}"
mkdir -p \
  "${DATA_ROOT}/master" \
  "${DATA_ROOT}/docviewer" \
  "${DATA_ROOT}/snapshots"

echo "[2/4] Installing systemd units to ${SYSTEMD_DST_DIR}"
install_unit "${SYSTEMD_SRC_DIR}/usb-ingest@.service"
install_unit "${SYSTEMD_SRC_DIR}/usb-dist-export@.service"
install_unit "${SYSTEMD_SRC_DIR}/usb-backup@.service"

echo "[3/4] Installing udev rule to ${UDEV_RULE_DST}"
install -m 644 "${UDEV_RULE_SRC}" "${UDEV_RULE_DST}"

echo "[4/4] Reloading systemd and udev"
systemctl daemon-reload
udevadm control --reload

echo
echo "Install complete."
echo "USB labels TM-INGEST / TM-DIST / TM-BACKUP will now trigger the respective services."
echo "If udev is already watching devices, run 'udevadm trigger --subsystem-match=block --action=add' to re-evaluate."
