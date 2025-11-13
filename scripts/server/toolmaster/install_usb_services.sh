#!/usr/bin/env bash

# Installs Toolmaster USB systemd units / udev rules.
#   server      : Pi5 用 (export/ingest/backup)
#   client-dist : Pi4(Window A) 用 dist sync

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root (use sudo)." >&2
  exit 1
fi

MODE="server"
CLIENT_HOME="/home/tools02"

usage() {
  cat <<'EOF'
Usage: install_usb_services.sh [--mode server|client-dist] [--client-home PATH]

Options:
  --mode         server      : (default) install Pi5-style export/ingest/backup units
                 client-dist : install Pi4(Window A) TM-DIST sync unit/udev rule
  --client-home  Window A user home (only used when --mode client-dist)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
    --client-home)
      CLIENT_HOME="$2"
      shift 2
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

case "$MODE" in
  server|client-dist)
    ;;
  *)
    echo "Invalid --mode '${MODE}' (expected server or client-dist)" >&2
    exit 64
    ;;
esac

CLIENT_HOME="$(python3 -c 'import os, sys; print(os.path.abspath(os.path.expanduser(sys.argv[1])))' "${CLIENT_HOME}")"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_SRC_DIR="${SCRIPT_DIR}/systemd"
UDEV_RULE_SRC="${SCRIPT_DIR}/udev/90-toolmaster.rules"
SYSTEMD_DST_DIR="/etc/systemd/system"
UDEV_RULE_DST="/etc/udev/rules.d/90-toolmaster.rules"
DATA_ROOT="/srv/RaspberryPiSystem_001/toolmaster"
BIN_DST_DIR="/usr/local/bin"
LIB_DST_DIR="${BIN_DST_DIR}/lib"
PY_DST_DIR="/usr/local/scripts"

BIN_SCRIPTS=(
  "tool-ingest-sync.sh"
  "tool-dist-export.sh"
  "tool-dist-sync.sh"
  "tool-backup-export.sh"
)

install_unit() {
  local src="$1"
  local dst_name
  dst_name="$(basename "$src")"
  local dst="${SYSTEMD_DST_DIR}/${dst_name}"
  install -m 644 "$src" "$dst"
}

render_client_unit() {
  local template="$1"
  local dst="$2"
  sed -e "s|{{CLIENT_HOME}}|${CLIENT_HOME}|g" "$template" >"$dst"
  chmod 644 "$dst"
}

echo "Installing toolmaster binaries under ${BIN_DST_DIR}"
mkdir -p "${LIB_DST_DIR}"
install -m 755 "${SCRIPT_DIR}/lib/toolmaster-usb.sh" "${LIB_DST_DIR}/toolmaster-usb.sh"
for script in "${BIN_SCRIPTS[@]}"; do
  install -m 755 "${SCRIPT_DIR}/${script}" "${BIN_DST_DIR}/${script}"
done

UPDATER_SRC="${SCRIPT_DIR}/../../scripts/update_plan_cache.py"
if [[ -f "${UPDATER_SRC}" ]]; then
  echo "Installing helper script to ${PY_DST_DIR}"
  mkdir -p "${PY_DST_DIR}"
  install -m 755 "${UPDATER_SRC}" "${PY_DST_DIR}/update_plan_cache.py"
fi

if [[ "${MODE}" == "server" ]]; then
  echo "Creating data directories under ${DATA_ROOT}"
  mkdir -p \
    "${DATA_ROOT}/master" \
    "${DATA_ROOT}/docviewer" \
    "${DATA_ROOT}/snapshots"

  echo "Installing Pi5 systemd units"
  install_unit "${SYSTEMD_SRC_DIR}/usb-ingest@.service"
  install_unit "${SYSTEMD_SRC_DIR}/usb-dist-export@.service"
  install_unit "${SYSTEMD_SRC_DIR}/usb-backup@.service"

  echo "Installing udev rule to ${UDEV_RULE_DST}"
  install -m 644 "${UDEV_RULE_SRC}" "${UDEV_RULE_DST}"
else
  echo "Installing Pi4 Window-A dist sync unit"
  CLIENT_UNIT_DST="${SYSTEMD_DST_DIR}/usb-dist-sync@.service"
  render_client_unit "${SYSTEMD_SRC_DIR}/usb-dist-sync@.service" "${CLIENT_UNIT_DST}"

  echo "Installing Pi4 udev rule to ${UDEV_RULE_DST}"
  cat <<'RULE' >"${UDEV_RULE_DST}"
ACTION=="add", SUBSYSTEM=="block", ENV{ID_FS_LABEL}=="TM-DIST", \
    ENV{SYSTEMD_WANTS}="usb-dist-sync@%k.service"
RULE
fi

echo "Reloading systemd/udev"
systemctl daemon-reload
udevadm control --reload

cat <<EOF

Install complete (mode=${MODE}).
If udev is already monitoring devices, run:
  sudo udevadm trigger --subsystem-match=block --action=add
to re-evaluate connected USB drives.
EOF
