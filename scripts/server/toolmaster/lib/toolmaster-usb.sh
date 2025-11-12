#!/usr/bin/env bash

# Shared helper functions for Toolmaster USB operations.
# 旧 RaspberryPiServer リポジトリ (/Users/tsudatakashi/RaspberryPiServer/lib/toolmaster-usb.sh)
# から移植し、Pi5 統一方針に合わせてログパスのみ更新している。

set -o pipefail

: "${USB_LOG_DIR:=/srv/RaspberryPiSystem_001/server/logs}"
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
  printf '%s\n' "${line}" >> "${USB_LOG_DIR}/${USB_LOG_FILE}"

  if command -v logger >/dev/null 2>&1; then
    local priority="user.info"
    case "${level,,}" in
      err|error) priority="user.err" ;;
      warning|warn) priority="user.warning" ;;
      notice) priority="user.notice" ;;
      debug) priority="user.debug" ;;
      info) priority="user.info" ;;
    esac
    logger -t "${USB_LOG_TAG}" -p "${priority}" -- "${message}"
  fi
}

usb_mount_device() {
  local device="$1"
  local base="/run/toolmaster"
  local mp="${base}/${device##*/}"

  if [[ -z "${device}" || ! -b "${device}" ]]; then
    usb_log "err" "invalid device: ${device}"
    return 1
  fi

  mkdir -p "${base}" || return 1
  mkdir -p "${mp}" || return 1

  if findmnt -n "${mp}" >/dev/null 2>&1; then
    echo "${mp}"
    return 0
  fi

  if ! mount "${device}" "${mp}"; then
    usb_log "err" "failed to mount ${device} on ${mp}"
    rmdir "${mp}" 2>/dev/null || true
    return 1
  fi

  echo "${mp}"
}

usb_unmount() {
  local mountpoint="$1"
  local attempt=0

  if [[ -z "${mountpoint}" ]]; then
    usb_log "err" "unmount called without mountpoint"
    return 1
  fi

  while [[ ${attempt} -lt ${USB_MAX_RETRY} ]]; do
    if umount "${mountpoint}" >/dev/null 2>&1; then
      rmdir "${mountpoint}" 2>/dev/null || true
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done

  usb_log "err" "failed to unmount ${mountpoint}"
  return 1
}

usb_validate_role() {
  local mountpoint="$1"
  local expected_role="$2"
  local expected_label="$3"

  if [[ -z "${mountpoint}" || -z "${expected_role}" ]]; then
    usb_log "err" "usb_validate_role missing arguments"
    return 2
  fi

  local device
  device="$(findmnt -n -o SOURCE "${mountpoint}" 2>/dev/null)" || {
    usb_log "err" "unable to resolve device for ${mountpoint}"
    return 2
  }

  if [[ -n "${expected_label}" ]]; then
    local label
    label="$(blkid -s LABEL -o value "${device}" 2>/dev/null)"
    if [[ "${label}" != "${expected_label}" ]]; then
      usb_log "warning" "label mismatch for ${device}: expected=${expected_label} actual=${label}"
      return 3
    fi
  fi

  local role_file="${mountpoint}/.toolmaster/role"
  if [[ ! -f "${role_file}" ]]; then
    usb_log "warning" "role file missing on ${mountpoint}"
    return 3
  fi

  local role
  role="$(tr -d '\r\n\t ' < "${role_file}")"
  if [[ "${role}" != "${expected_role}" ]]; then
    usb_log "warning" "role mismatch on ${mountpoint}: expected=${expected_role} actual=${role}"
    return 3
  fi

  return 0
}
