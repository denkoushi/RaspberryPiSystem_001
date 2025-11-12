# DocumentViewer Socket.IO / REST 統合メモ（ドラフト）

Pi5 側の Socket.IO ブロードキャストに合わせて DocumentViewer を切り替える際の準備事項を整理する。

## 1. 接続設定の確認
- `~/RaspberryPiSystem_001/document_viewer/config/docviewer.env`（または `/etc/systemd/system/document-viewer.service.d/env.conf`）で以下を揃える。
```env
VIEWER_API_BASE=http://127.0.0.1:8500
VIEWER_API_TOKEN=<shared-token>
VIEWER_SOCKET_BASE=http://192.168.10.230:8501
VIEWER_SOCKET_PATH=/socket.io
VIEWER_SOCKET_EVENTS=scan.ingested,part_location_updated,scan_update
VIEWER_SOCKET_CLIENT_SRC=https://cdn.socket.io/4.7.5/socket.io.min.js
VIEWER_LOG_PATH=/var/log/document-viewer/client.log
# VIEWER_SOCKET_EVENT=scan.ingested  # 旧システム互換の単一指定
```
- `/var/log/document-viewer` が存在しない場合は `sudo mkdir -p /var/log/document-viewer && sudo chown tools02:tools02 /var/log/document-viewer` を実行してから起動する（権限不足だとログ出力が失敗する）。
- 旧リポジトリのハードコードを参照する場合でも、`VIEWER_SOCKET_EVENTS` を `scan.ingested` に必ず含め、Window A / Pi5 と同じイベント名で受信する。
- systemd を経由する場合は `sudo systemctl daemon-reload && sudo systemctl restart document-viewer.service` で反映する。

## 2. 動作確認手順（ローカル）
1. `scripts/listen_for_scans.ts --api http://127.0.0.1:8501` で受信確認。
2. `curl -X POST /api/v1/scans` や `server/scripts/smoke_scan.sh` でテストデータを投入する。スモークスクリプトは一時的に Flask サーバーを起動し、`SMOKE-<timestamp>` 形式の注文コードで `/api/v1/scans` を呼び出し、完了後は自動で停止する。
   - ブロードキャストされる `scan.ingested` のペイロードは以下のキーを含む。
     ```json
     {
       "order_code": "TEST-900",
       "location_code": "RACK-Z9",
       "device_id": "HANDHELD-99"
     }
     ```
   - DocumentViewer 側では JSON の `order_code` を基準に PDF 表示を切り替える。欠損時はログ警告を出すよう実装しておく。
3. DocumentViewer のログ（`/var/log/document-viewer/client.log`）に以下が出るか確認。
   - `Socket.IO connected` / `scan.ingested received`
   - `Document lookup success` などのレンダリング成功ログ
4. 表示中の PDF が注文番号に合わせて切り替わるか目視し、必要ならブラウザのデベロッパーツールで Console/Network を確認。
5. 再接続・障害対応
- DocumentViewer の Socket.IO クライアントでは `reconnection: true`（デフォルト）を維持し、`reconnectionDelay=5000`, `reconnectionAttempts=0`（無制限）とする。
- Pi5 側では `/srv/RaspberryPiSystem_001/server/logs/socket.log`（旧 `/srv/rpi-server/logs/socket.log`。参照: `/Users/tsudatakashi/RaspberryPiServer/docs/usb-operations.md:1-130`）に `Broadcast emit request` / `Socket.IO emit succeeded` / `Socket.IO emit failed` が出力される。切断時は Pi5 のログと DocumentViewer 側ログを突き合わせて原因を追う。
- 永続的に失敗する場合は `AUTO_DRAIN_ON_INGEST` の設定値と DB 反映状況（`part_locations` の `updated_at`）を確認し、イベントと REST の整合を取る。必要に応じて `GET /api/v1/admin/backlog-status` で backlog 件数を確認する。

## 3. systemd サービス整備
Pi4 を含む全端末で `~/RaspberryPiSystem_001/document_viewer` を正とする。旧 `~/DocumentViewer` は順次 `_legacy_YYYYMMDD` へ退避し、systemd も新パスを参照させる。以下は `/etc/systemd/system/document-viewer.service` の最新テンプレートである。

```ini
[Unit]
Description=Document Viewer (Flask)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=tools02
Group=tools02
WorkingDirectory=/home/tools02/RaspberryPiSystem_001/document_viewer/app
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/home/tools02/RaspberryPiSystem_001/document_viewer/config/docviewer.env
ExecStart=/home/tools02/RaspberryPiSystem_001/document_viewer/.venv/bin/python /home/tools02/RaspberryPiSystem_001/document_viewer/app/viewer.py
Restart=always
RestartSec=5

[Install]
wantedBy=multi-user.target
```

初回セットアップ手順:

```bash
cd ~/RaspberryPiSystem_001/document_viewer/app
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
sudo mkdir -p /var/log/document-viewer
sudo chown tools02:tools02 /var/log/document-viewer
sudo systemctl daemon-reload
sudo systemctl enable --now document-viewer.service
```

以降は `config/docviewer.env` を更新したら `sudo systemctl restart document-viewer.service` で反映する。

### 3.1 旧リポジトリからの PDF 移行
- 旧 `~/DocumentViewer/documents/` を参照していた実機は、以下のスクリプトで新ディレクトリへ一括コピーする。`--dry-run` で差分だけ確認可能。
  ```bash
  cd ~/RaspberryPiSystem_001/document_viewer
  ./scripts/migrate_legacy_documents.sh \
    --legacy ~/DocumentViewer/documents \
    --target ~/RaspberryPiSystem_001/document_viewer/documents
  ```
- コピー後は `sudo systemctl restart document-viewer.service` → `tail -n 5 /var/log/document-viewer/client.log` で最新 PDF が表示されることを確認する。

### 3.2 USB importer サービス
- importer / daemon スクリプトを `/usr/local/bin` へ配置する。
  ```bash
  cd ~/RaspberryPiSystem_001/document_viewer
  sudo install -m 755 scripts/document-importer.sh /usr/local/bin/document-importer.sh
  sudo install -m 755 scripts/document-importer-daemon.sh /usr/local/bin/document-importer-daemon.sh
  ```
- systemd ユニットをユーザー名に合わせて配置する。
  ```bash
  sudo sed "s/{{USER}}/tools02/g" systemd/document-importer.service | sudo tee /etc/systemd/system/document-importer.service >/dev/null
  sudo systemctl daemon-reload
  sudo systemctl enable --now document-importer.service
  ```
- importer は `WATCH_ROOT=/media/<user>` を監視し、USB の `docviewer/` フォルダを検出すると `document-importer.sh` で PDF を検証しつつ `~/RaspberryPiSystem_001/document_viewer/documents` へコピーする。完了後に `document-viewer.service` を自動で再起動するため、Window A/DocumentViewer 側で最新 PDF が利用できる。
- `document-viewer.service` をパスワードなしで再起動できるよう、sudoers に以下を追加しておく。
  ```bash
  sudo tee /etc/sudoers.d/document-viewer <<'EOF'
  tools02 ALL=(root) NOPASSWD:/usr/bin/systemctl restart document-viewer.service
  EOF
  sudo chmod 440 /etc/sudoers.d/document-viewer
  ```

### 3.3 USB メモリの役割とディレクトリ構成
- 旧 DocumentViewer リポジトリのセットアップガイド（`/Users/tsudatakashi/DocumentViewer/docs/setup-raspberrypi.md:119-134`）では、USB ルート直下に `TOOLMASTER/master/`（工具管理 CSV）と `TOOLMASTER/docviewer/`（PDF と `meta.json`）を置くことが前提になっている。新システムでも同じレイアウトを維持し、`docviewer/` には PDF と `meta.json` 以外のファイルを配置しない。
- 旧 RaspberryPiServer リポジトリの USB 手順書（`/Users/tsudatakashi/RaspberryPiServer/docs/usb-operations.md:1-130`）では、USB ラベルと役割を以下のように定義している。新しい Pi でも ext4 ラベルと `/.toolmaster/role` による識別を踏襲する。
  | ラベル | `.toolmaster/role` | 主な用途 | 挿入先 |
  | --- | --- | --- | --- |
  | `TM-INGEST` | `INGEST` | 外部で更新した `master/` CSV や `docviewer/` PDF を Pi5 へ持ち込む。`tool-ingest-sync.sh` が比較してサーバー側を更新し、USB 側も最新化する。 | Pi5（書き込みあり） |
  | `TM-DIST` | `DIST` | Pi5 で確定した `master/` と `docviewer/` を各端末（Window A / DocumentViewer）へ配布。端末側では `tool-dist-sync.sh` が USB → 端末の一方向コピーを行い、USB へは書き戻さない。 | Pi5（エクスポート）、Pi4/他端末（配布） |
  | `TM-BACKUP` | `BACKUP` | Pi5 のスナップショットを `tar+zstd` で退避。DocumentViewer 直接は使わないが、USB 3 本の一貫した運用として管理する。 | Pi5（書き込みあり） |
- Pi5 側のデータルートは `/srv/RaspberryPiSystem_001/toolmaster/{master,docviewer,snapshots}` に統一し、旧 `/srv/rpi-server/**` と同じ役割を持たせる。`tool-ingest-sync.sh` / `tool-dist-export.sh` / `tool-backup-export.sh` で同パスを既定値にしている（参照: `/Users/tsudatakashi/RaspberryPiServer/scripts/tool-*.sh`）。
- `document-importer.sh` で扱うのは `docviewer/` 配下だけだが、`TM-INGEST` / `TM-DIST` の USB には工具管理 CSV など他モジュールのデータも含まれる。将来的に Window A / 工具管理の同期スクリプト（`tool-dist-sync.sh`, `tool-ingest-sync.sh` 等）を `~/RaspberryPiSystem_001` へ移植する際は、同じ USB 内構成を前提に実装すること。
- テスト時は `/.toolmaster/role` の内容と ext4 ラベルが一致しているかを必ず確認し、`udev` ルールまたは手動コマンドで誤った USB を処理しないようにする。

## 4. 未整備タスク
- DocumentViewer の既存 Socket.IO クライアントコードを TypeScript 化し、テスト可能な形に整理。
- API トークン更新時、DocumentViewer の環境ファイルを同期する手順を RUNBOOK に追記。
- リスナーが切断された場合の再接続ログを標準化し、Pi5 側 `socket.log` と突き合わせて監視できるようにする。
