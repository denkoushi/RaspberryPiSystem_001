#!/usr/bin/env bash
#
# Install or update /etc/default/docviewer from the repository sample,
# optionally overriding common variables and preparing log/doc directories.
#
# Example:
#   sudo ./scripts/install_docviewer_env.sh \
#     --owner tools01:tools01 \
#     --api-base http://raspi-server.local:8501 \
#     --docs-dir /home/tools01/DocumentViewer/documents \
#     --log-path /var/log/document-viewer/client.log
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SAMPLE_FILE="${REPO_ROOT}/config/docviewer.env.sample"

ENV_FILE="/etc/default/docviewer"
API_BASE=""
SOCKET_BASE=""
DOCS_DIR=""
LOG_PATH=""
OWNER_SPEC=""
FORCE=0
DRY_RUN=0
SKIP_LOG=0

usage() {
  cat <<'USAGE'
DocumentViewer environment installer

Usage:
  sudo ./scripts/install_docviewer_env.sh [options]

Options:
  --env-file PATH          出力先環境ファイル（既定: /etc/default/docviewer）
  --sample PATH            基にするサンプルファイル（既定: config/docviewer.env.sample）
  --api-base URL           VIEWER_API_BASE を上書き
  --socket-base URL        VIEWER_SOCKET_BASE を上書き
  --docs-dir PATH          VIEWER_LOCAL_DOCS_DIR を上書きし、ディレクトリを作成
  --log-path PATH          VIEWER_LOG_PATH を上書きし、親ディレクトリとログファイルを作成
  --owner USER[:GROUP]     docs-dir / log-path を chown する所有者（未指定時は SUDO_USER を推奨）
  --force                  既存ファイルをバックアップのうえ上書き（.bak を作成）
  --dry-run                実際にはファイルを変更せず、処理内容のみ表示
  --skip-log-setup         --log-path 指定時のログディレクトリ作成と権限設定をスキップ
  -h, --help               このヘルプを表示

例:
  sudo ./scripts/install_docviewer_env.sh \
    --owner tools01:tools01 \
    --api-base http://raspi-server.local:8501 \
    --docs-dir /home/tools01/DocumentViewer/documents \
    --log-path /var/log/document-viewer/client.log
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      ENV_FILE="$2"; shift 2;;
    --sample)
      SAMPLE_FILE="$2"; shift 2;;
    --api-base)
      API_BASE="$2"; shift 2;;
    --socket-base)
      SOCKET_BASE="$2"; shift 2;;
    --docs-dir)
      DOCS_DIR="$2"; shift 2;;
    --log-path)
      LOG_PATH="$2"; shift 2;;
    --owner)
      OWNER_SPEC="$2"; shift 2;;
    --force)
      FORCE=1; shift;;
    --dry-run)
      DRY_RUN=1; shift;;
    --skip-log-setup)
      SKIP_LOG=1; shift;;
    -h|--help)
      usage; exit 0;;
    *)
      echo "未知の引数: $1" >&2
      usage
      exit 1;;
  esac
done

if [[ ! -f "${SAMPLE_FILE}" ]]; then
  echo "サンプルファイルが見つかりません: ${SAMPLE_FILE}" >&2
  exit 1
fi

if [[ "${DRY_RUN}" -eq 0 && $EUID -ne 0 ]]; then
  echo "このスクリプトは root 権限での実行を推奨します（例: sudo ...）。" >&2
  exit 1
fi

backup_env_file() {
  local target="$1"
  if [[ -f "${target}" ]]; then
    if [[ "${FORCE}" -eq 0 ]]; then
      echo "ERROR: ${target} は既に存在します。--force を指定するか、手動で削除してください。" >&2
      exit 1
    fi
    local backup="${target}.$(date +%Y%m%d%H%M%S).bak"
    echo "既存ファイルをバックアップ: ${backup}"
    if [[ "${DRY_RUN}" -eq 0 ]]; then
      cp -p "${target}" "${backup}"
    else
      echo "[dry-run] cp -p ${target} ${backup}"
    fi
  fi
}

set_env_value() {
  local file="$1"
  local key="$2"
  local value="$3"
  if [[ -z "${value}" ]]; then
    return
  fi
  local escaped
  escaped="$(printf '%s\n' "${value}" | sed 's/[&/\\]/\\&/g')"
  if grep -q "^${key}=" "${file}"; then
    if [[ "${DRY_RUN}" -eq 0 ]]; then
      sed -i "" "s|^${key}=.*|${key}=${escaped}|" "${file}"
    else
      echo "[dry-run] set ${key}=${value}"
    fi
  else
    if [[ "${DRY_RUN}" -eq 0 ]]; then
      printf '%s=%s\n' "${key}" "${value}" >> "${file}"
    else
      echo "[dry-run] append ${key}=${value}"
    fi
  fi
}

create_dirs_if_needed() {
  local path="$1"
  local type="$2"
  if [[ -z "${path}" ]]; then
    return
  fi
  local dir_path
  if [[ "${type}" == "file" ]]; then
    dir_path="$(dirname "${path}")"
  else
    dir_path="${path}"
  fi
  if [[ "${DRY_RUN}" -eq 0 ]]; then
    install -d -m 750 "${dir_path}"
  else
    echo "[dry-run] install -d -m 750 ${dir_path}"
  fi
  if [[ "${type}" == "file" && "${DRY_RUN}" -eq 0 && ${SKIP_LOG} -eq 0 ]]; then
    if [[ ! -f "${path}" ]]; then
      touch "${path}"
    fi
  elif [[ "${type}" == "file" && ${SKIP_LOG} -eq 0 ]]; then
    echo "[dry-run] touch ${path}"
  fi
}

apply_owner() {
  local path="$1"
  local owner="$2"
  if [[ -z "${owner}" ]]; then
    return
  fi
  if [[ "${DRY_RUN}" -eq 0 ]]; then
    chown "${owner}" "${path}"
  else
    echo "[dry-run] chown ${owner} ${path}"
  fi
}

default_owner() {
  local spec="$1"
  if [[ -n "${spec}" ]]; then
    printf '%s\n' "${spec}"
    return
  fi
  if [[ -n "${SUDO_USER:-}" ]]; then
    local group
    group="$(id -gn "${SUDO_USER}")"
    printf '%s:%s\n' "${SUDO_USER}" "${group}"
  else
    printf '%s:%s\n' "$(id -un)" "$(id -gn)"
  fi
}

OWNER_SPEC="$(default_owner "${OWNER_SPEC}")"

printf 'Environment file : %s\n' "${ENV_FILE}"
printf 'Sample file      : %s\n' "${SAMPLE_FILE}"
printf 'API base override: %s\n' "${API_BASE:-<unchanged>}"
printf 'Socket base      : %s\n' "${SOCKET_BASE:-<unchanged>}"
printf 'Docs directory   : %s\n' "${DOCS_DIR:-<unchanged>}"
printf 'Log path         : %s\n' "${LOG_PATH:-<unchanged>}"
printf 'Owner            : %s\n' "${OWNER_SPEC}"
printf 'Force overwrite  : %s\n' "${FORCE}"
printf 'Dry-run          : %s\n' "${DRY_RUN}"

if [[ "${DRY_RUN}" -eq 0 ]]; then
  backup_env_file "${ENV_FILE}"
  install -m 640 "${SAMPLE_FILE}" "${ENV_FILE}"
else
  echo "[dry-run] install -m 640 ${SAMPLE_FILE} ${ENV_FILE}"
fi

set_env_value "${ENV_FILE}" "VIEWER_API_BASE" "${API_BASE}"
set_env_value "${ENV_FILE}" "VIEWER_SOCKET_BASE" "${SOCKET_BASE}"
set_env_value "${ENV_FILE}" "VIEWER_LOCAL_DOCS_DIR" "${DOCS_DIR}"
set_env_value "${ENV_FILE}" "VIEWER_LOG_PATH" "${LOG_PATH}"

if [[ -n "${DOCS_DIR}" ]]; then
  echo "Creating documents directory: ${DOCS_DIR}"
  create_dirs_if_needed "${DOCS_DIR}" "dir"
  apply_owner "${DOCS_DIR}" "${OWNER_SPEC}"
fi

if [[ -n "${LOG_PATH}" ]]; then
  echo "Preparing log path: ${LOG_PATH}"
  create_dirs_if_needed "${LOG_PATH}" "file"
  if [[ ${SKIP_LOG} -eq 0 ]]; then
    apply_owner "$(dirname "${LOG_PATH}")" "${OWNER_SPEC}"
    apply_owner "${LOG_PATH}" "${OWNER_SPEC}"
    if [[ "${DRY_RUN}" -eq 0 ]]; then
      chmod 640 "${LOG_PATH}"
    else
      echo "[dry-run] chmod 640 ${LOG_PATH}"
    fi
  fi
fi

echo "完了しました。必要に応じて systemctl restart docviewer.service を実行してください。"
