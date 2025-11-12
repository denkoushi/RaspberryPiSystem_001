#!/usr/bin/env bash
# Watches for newly mounted USB volumes and triggers the document importer.
set -euo pipefail

WATCH_ROOT="${WATCH_ROOT:-/media/pi}"
IMPORTER_SCRIPT="${IMPORTER_SCRIPT:-/usr/local/bin/document-importer.sh}"
LOG_FILE="${IMPORT_DAEMON_LOG:-/var/log/document-viewer/import-daemon.log}"

log() {
  local timestamp message
  timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
  message="$*"
  mkdir -p "$(dirname "$LOG_FILE")"
  printf '%s %s\n' "$timestamp" "$message" | tee -a "$LOG_FILE"
}

require_tools() {
  local missing=0
  for tool in inotifywait mountpoint; do
    if ! command -v "$tool" >/dev/null 2>&1; then
      log "ERROR required command '$tool' not found"
      missing=1
    fi
  done
  if [[ $missing -eq 1 ]]; then
    exit 1
  fi
}

main() {
  if [[ ! -d "$WATCH_ROOT" ]]; then
    log "ERROR watch root '$WATCH_ROOT' does not exist"
    exit 1
  fi

  if [[ ! -x "$IMPORTER_SCRIPT" ]]; then
    log "ERROR importer script '$IMPORTER_SCRIPT' not executable"
    exit 1
  fi

  require_tools

  log "INFO watching $WATCH_ROOT for new mount points"

  while read -r directory; do
    [[ -d "$directory" ]] || continue

    # Give the OS a moment to finish mounting before we read.
    sleep 2

    if mountpoint -q "$directory"; then
      log "INFO detected mount at $directory"
      if "$IMPORTER_SCRIPT" "$directory"; then
        log "INFO import from $directory finished"
      else
        log "ERROR import from $directory failed"
      fi
    else
      log "WARN $directory is no longer a mount point"
    fi
  done < <(inotifywait -m -e create -e moved_to --format '%w%f' "$WATCH_ROOT")
}

main "$@"
