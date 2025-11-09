#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
CURRENT_BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
CURRENT_REV="$(git -C "$REPO_ROOT" rev-parse HEAD)"
TOOLS01_HOME="/home/tools01"
TOOLS01_REPO="$TOOLS01_HOME/RaspberryPiSystem_001"

echo "[INFO] syncing tools01 git working tree"
if sudo test -d "$TOOLS01_REPO/.git"; then
  sudo -u tools01 -H bash -lc "
    set -euo pipefail
    cd '$TOOLS01_REPO'
    git fetch --all --tags --prune
    git checkout '${CURRENT_BRANCH}'
    git reset --hard '${CURRENT_REV}'
  "
  echo "[INFO] tools01 repo now at $CURRENT_REV ($CURRENT_BRANCH)"
else
  echo "[WARN] $TOOLS01_REPO missing (.git not found). Skipping sync."
fi

sudo mkdir -p /etc/systemd/system/handheld@.service.d
cat <<'UNIT' | sudo tee /etc/systemd/system/handheld@.service.d/override.conf >/dev/null
[Unit]
After=dev-ttyACM0.device
Wants=dev-ttyACM0.device

[Service]
SupplementaryGroups=input dialout gpio spi i2c
WorkingDirectory=/home/%i/RaspberryPiSystem_001/handheld
Environment=PYTHONUNBUFFERED=1
Environment=ONSITE_CONFIG=/etc/onsitelogistics/config.json
Environment=PYTHONPATH=/home/%i/e-Paper/RaspberryPi_JetsonNano/python/lib
Environment=GPIOZERO_PIN_FACTORY=lgpio
ExecStartPre=/bin/sh -c "for i in $(seq 1 15); do for dev in /dev/minjcode0 /dev/ttyACM0 /dev/input/by-id/*MINJCODE*event-kbd /dev/input/by-path/*MINJCODE*event-kbd; do if [ -e \"$dev\" ]; then exit 0; fi; done; sleep 2; done; echo 'no scanner device'; exit 1"
ExecStart=
ExecStart=/home/%i/.venv-handheld/bin/python /home/%i/RaspberryPiSystem_001/handheld/scripts/handheld_scan_display.py
Restart=on-failure
RestartSec=2
UNIT

echo "[INFO] override.conf updated"
sudo systemctl daemon-reload
sudo systemctl restart handheld@tools01.service
sudo systemctl status handheld@tools01.service --no-pager
