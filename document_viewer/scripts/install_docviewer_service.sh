#!/usr/bin/env bash
# install_docviewer_service.sh : Install systemd service for Document Viewer

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "このスクリプトは sudo/root で実行してください" >&2
  exit 1
fi

SERVICE_USER="${DOCUMENT_VIEWER_USER:-tools01}"
SERVICE_USER_HOME="$(eval echo ~${SERVICE_USER})"
PROJECT_DIR="${DOCUMENT_VIEWER_HOME:-${SERVICE_USER_HOME}/RaspberryPiSystem_001/document_viewer}"
VENVSCRIPT="${PROJECT_DIR}/.venv/bin/python"
SERVICE_PATH="/etc/systemd/system/document-viewer.service"
TEMPLATE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_FILE="${TEMPLATE_DIR}/systemd/document-viewer.service"

if [[ ! -d "${PROJECT_DIR}" ]]; then
  echo "プロジェクトディレクトリが見つかりません: ${PROJECT_DIR}" >&2
  exit 1
fi

if [[ ! -x "${VENVSCRIPT}" ]]; then
  echo "仮想環境の Python が見つかりません: ${VENVSCRIPT}" >&2
  echo "先に \"cd ${PROJECT_DIR}/app && python3 -m venv ../.venv && source ../.venv/bin/activate && pip install -r requirements.txt\" を実行してください" >&2
  exit 1
fi

sed "s/{{USER}}/${SERVICE_USER}/g" "${TEMPLATE_FILE}" > "${SERVICE_PATH}"

systemctl daemon-reload
systemctl enable --now document-viewer.service

cat <<MSG
---
document-viewer.service をインストールしました。
ステータス確認: sudo systemctl status document-viewer.service
ログ確認: sudo journalctl -u document-viewer.service -n 50
MSG
