#!/usr/bin/env bash
set -euo pipefail

REMOTE_URL="https://github.com/denkoushi/RaspberryPiSystem_001.git"
TARGET_DIR="$HOME/RaspberryPiSystem_001"
LEGACY_DIR="$HOME/OnSiteLogistics"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${LEGACY_DIR}_legacy_${TIMESTAMP}"

if [ -d "$TARGET_DIR" ]; then
  echo "[INFO] $TARGET_DIR already exists. Aborting so you can inspect manually." >&2
  exit 1
fi

if [ -d "$LEGACY_DIR" ]; then
  echo "[INFO] Moving existing $LEGACY_DIR to $BACKUP_DIR"
  mv "$LEGACY_DIR" "$BACKUP_DIR"
else
  echo "[INFO] No $LEGACY_DIR found; skipping backup move."
  BACKUP_DIR=""
fi

echo "[INFO] Cloning $REMOTE_URL into $TARGET_DIR"
git clone "$REMOTE_URL" "$TARGET_DIR"

if [ -n "$BACKUP_DIR" ]; then
  cat <<EONOTE
[INFO] Backup located at: $BACKUP_DIR
Please copy any environment files or device-specific configs from the backup into:
  $TARGET_DIR/handheld
before restarting services.
EONOTE
else
  echo "[INFO] Fresh clone completed. Configure handheld settings under $TARGET_DIR/handheld."
fi
