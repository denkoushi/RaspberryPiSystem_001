#!/usr/bin/env bash
# setup_docviewer_env.sh : Deploy /etc/default/docviewer and prepare log directory.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd "${SCRIPT_DIR}/.." && pwd)
DEFAULT_SOURCE="${PROJECT_ROOT}/config/docviewer.env.sample"
DEFAULT_TARGET="/etc/default/docviewer"
DEFAULT_USER="tools01"

usage() {
  cat <<'USAGE'
Usage: setup_docviewer_env.sh [options]
  --source PATH          Source template (default: config/docviewer.env.sample)
  --target PATH          Destination file (default: /etc/default/docviewer)
  --user NAME            Owner of log directory/files (default: tools01)
  --log-dir PATH         Override log directory (otherwise read from env file)
  --force                Overwrite existing target file
  --skip-root-check      Allow running without sudo/root (for testing)
  --help                 Show this help

Example:
  sudo ./scripts/setup_docviewer_env.sh \
    --user tools01 \
    --log-dir /var/log/document-viewer
USAGE
}

SOURCE="${DEFAULT_SOURCE}"
TARGET="${DEFAULT_TARGET}"
OWNER="${DEFAULT_USER}"
LOG_DIR=""
FORCE=false
SKIP_ROOT=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      [[ $# -lt 2 ]] && usage && exit 1
      SOURCE="$2"
      shift 2
      ;;
    --target)
      [[ $# -lt 2 ]] && usage && exit 1
      TARGET="$2"
      shift 2
      ;;
    --user)
      [[ $# -lt 2 ]] && usage && exit 1
      OWNER="$2"
      shift 2
      ;;
    --log-dir)
      [[ $# -lt 2 ]] && usage && exit 1
      LOG_DIR="$2"
      shift 2
      ;;
    --force)
      FORCE=true
      shift
      ;;
    --skip-root-check)
      SKIP_ROOT=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ "${SKIP_ROOT}" != true && "${EUID}" -ne 0 ]]; then
  echo "このスクリプトは sudo/root で実行してください" >&2
  exit 1
fi

if [[ ! -f "${SOURCE}" ]]; then
  echo "テンプレートが見つかりません: ${SOURCE}" >&2
  exit 1
fi

if [[ -f "${TARGET}" && "${FORCE}" != true ]]; then
  echo "既にファイルが存在します: ${TARGET}" >&2
  echo "--force を指定すると上書きできます" >&2
  exit 1
fi

install -m 640 "${SOURCE}" "${TARGET}"

# Determine log directory if not provided explicitly.
if [[ -z "${LOG_DIR}" ]]; then
  LOG_DIR=$(grep -E '^VIEWER_LOG_PATH=' "${TARGET}" | tail -n 1 | cut -d'=' -f2- || true)
  LOG_DIR=${LOG_DIR//$'"'/}
  LOG_DIR=${LOG_DIR//$'\''/}
fi

if [[ -n "${LOG_DIR}" ]]; then
  LOG_DIR=$(eval echo "${LOG_DIR}")
  DIR_ARGS=(-m 750)
  FILE_ARGS=(-m 640 /dev/null)
  if [[ "${SKIP_ROOT}" != true && "${EUID}" -eq 0 ]]; then
    DIR_ARGS+=(-o "${OWNER}" -g "${OWNER}")
    FILE_ARGS=(-m 640 -o "${OWNER}" -g "${OWNER}" /dev/null)
  fi
  install -d "${DIR_ARGS[@]}" "${LOG_DIR}"
  LOG_FILE="${LOG_DIR%/}/client.log"
  if [[ ! -f "${LOG_FILE}" ]]; then
    install "${FILE_ARGS[@]}" "${LOG_FILE}"
  fi
  echo "ログディレクトリを準備しました: ${LOG_DIR}"
fi

cat <<INFO
DocumentViewer 環境ファイルを配置しました: ${TARGET}
必要に応じて内容を編集し、完了後に以下を実行してください:
  sudo systemctl restart docviewer.service
  sudo journalctl -u docviewer.service -n 20
INFO
