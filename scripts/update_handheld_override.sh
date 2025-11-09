#!/usr/bin/env bash
set -euo pipefail
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
ExecStartPre=/bin/sh -c "for i in $(seq 1 15); do for dev in /dev/minjcode* /dev/ttyACM* /dev/input/by-id/*MINJCODE*event-kbd /dev/input/by-path/*MINJCODE*event-kbd; do if [ -e \"${dev}\" ]; then exit 0; fi; done; sleep 2; done; echo 'no scanner device'; exit 1"
ExecStart=
ExecStart=/home/%i/.venv-handheld/bin/python /home/%i/RaspberryPiSystem_001/handheld/scripts/handheld_scan_display.py
Restart=on-failure
RestartSec=2
UNIT

echo "[INFO] override.conf updated"
sudo systemctl daemon-reload
sudo systemctl restart handheld@tools01.service
sudo systemctl status handheld@tools01.service --no-pager
