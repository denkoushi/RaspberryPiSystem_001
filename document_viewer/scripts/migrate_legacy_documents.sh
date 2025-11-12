#!/usr/bin/env bash
# Copy legacy DocumentViewer PDFs into the new document_viewer/documents directory.

set -euo pipefail

SERVICE_USER_HOME="$(eval echo ~${SUDO_USER:-$USER})"
DEFAULT_LEGACY="${LEGACY_DOCS_DIR:-${SERVICE_USER_HOME}/DocumentViewer/documents}"
DEFAULT_TARGET="${TARGET_DOCS_DIR:-${SERVICE_USER_HOME}/RaspberryPiSystem_001/document_viewer/documents}"

LEGACY_DIR="$DEFAULT_LEGACY"
TARGET_DIR="$DEFAULT_TARGET"
DRY_RUN=0
RSYNC_OPTS=()

usage() {
  cat <<'USAGE'
migrate_legacy_documents.sh

旧 `~/DocumentViewer/documents` から新しい `~/RaspberryPiSystem_001/document_viewer/documents`
へ PDF / meta.json をコピーする補助スクリプトです。必要に応じて --legacy / --target
でパスを上書きできます。

Usage:
  ./scripts/migrate_legacy_documents.sh [options]

Options:
  --legacy PATH   旧 DocumentViewer の documents パス（既定: ~/DocumentViewer/documents）
  --target PATH   新 DocumentViewer の documents パス（既定: ~/RaspberryPiSystem_001/document_viewer/documents）
  --dry-run       実際にはコピーせず、rsync の計画のみ表示
  -h, --help      このヘルプを表示

環境変数:
  LEGACY_DOCS_DIR, TARGET_DOCS_DIR を指定すると既定値を上書きできます。
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --legacy)
      LEGACY_DIR="$2"; shift 2;;
    --target)
      TARGET_DIR="$2"; shift 2;;
    --dry-run)
      DRY_RUN=1; shift;;
    -h|--help)
      usage; exit 0;;
    *)
      echo "unknown option: $1" >&2
      usage; exit 1;;
  esac
done

if [[ ! -d "$LEGACY_DIR" ]]; then
  echo "legacy documents directory not found: $LEGACY_DIR" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"

RSYNC_OPTS=(-av --human-readable --info=stats1)
if (( DRY_RUN )); then
  RSYNC_OPTS+=(--dry-run)
fi

echo "Copying PDFs from: $LEGACY_DIR"
echo "                 to: $TARGET_DIR"
if (( DRY_RUN )); then
  echo "[dry-run] no files will be modified"
fi

rsync "${RSYNC_OPTS[@]}" \
  --include='*.pdf' \
  --include='meta.json' \
  --exclude='*' \
  "${LEGACY_DIR}/" \
  "${TARGET_DIR}/"

echo "Done."
