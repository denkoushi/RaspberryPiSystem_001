#!/usr/bin/env bash

# Shared helper functions for Toolmaster USB operations.
# Migrated from /Users/tsudatakashi/RaspberryPiServer/lib/toolmaster-usb.sh

set -o pipefail

: "${USB_LOG_DIR:=/srv/rpi-server/logs}"
: "${USB_LOG_FILE:=usb_generic.log}"
: "${USB_LOG_TAG:=toolmaster-usb}"
: "${USB_MAX_RETRY:=3}"

usb__ensure_log_dir() {
  if [[ ! -d "${USB_LOG_DIR}" ]]; then
    mkdir -p "${USB_LOG_DIR}" || return 1
  fi
}

usb_log() {
  local level="$1"
  shift
  local message="$*"
  local timestamp
  timestamp="$(date --iso-8601=seconds)"
  local line="${timestamp} [${level}] ${message}"

  usb__ensure_log_dir || return 1
  printf '%s\n'
