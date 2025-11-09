#!/usr/bin/env bash
#
# Configure Pi Zero handheld environment for serial-mode barcode scanners.
#
# Usage:
#   sudo ./scripts/setup_serial_env.sh tools01
#
# - Installs a udev rule (VID/PID 152a:880f) to expose /dev/minjcode0
# - Reloads udev, then restarts handheld@<user>.service

set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "ERROR: This script must be run with sudo/root." >&2
  exit 1
fi

if [[ "$#" -ne 1 ]]; then
  echo "Usage: sudo $0 <pi-user>" >&2
  exit 1
fi

PI_USER="$1"
SERVICE="handheld@${PI_USER}.service"
UDEV_RULE="/etc/udev/rules.d/60-minjcode.rules"

echo "[INFO] Writing udev rule to ${UDEV_RULE}"
cat <<'RULE' > "${UDEV_RULE}"
SUBSYSTEM=="tty", ATTRS{idVendor}=="152a", ATTRS{idProduct}=="880f", SYMLINK+="minjcode%n", GROUP="dialout", MODE="0660"
RULE

echo "[INFO] Reloading udev rules"
udevadm control --reload-rules
udevadm trigger --attr-match=idVendor=152a --attr-match=idProduct=880f || true

echo "[INFO] Verifying /dev entries (replug the scanner if needed)"
ls -l /dev/minjcode* /dev/ttyACM* 2>/dev/null || true

echo "[INFO] Reloading systemd & restarting ${SERVICE}"
systemctl daemon-reload
systemctl restart "${SERVICE}"
systemctl status "${SERVICE}" --no-pager

echo "[INFO] Done. If the serial device was not present above, unplug/replug the scanner and rerun."
