# DocumentViewer

Raspberry Pi 上で部品ごとの PDF 手順書を表示するためのビューアです。バーコード付き移動票を読み取ると、対応する PDF を即座に全画面表示します。

## はじめに
- Raspberry Pi への導入手順: `docs/setup-raspberrypi.md`
- 機能要件・ロードマップ: `docs/requirements.md`
- ドキュメント運用ルール: `docs/documentation-guidelines.md`
- エージェント向け指針: `docs/AGENTS.md`
- 適用済み変更: `CHANGELOG.md`
- テスト実行手順: `pytest`（詳細は以下参照）
- サービス環境ファイルのサンプル: `config/docviewer.env.sample`

## リポジトリ構成
```
app/        Flask ベースのビューア本体
scripts/    USB 取り込み等の補助スクリプト
systemd/    常駐化用ユニットファイル（例）
ui/         プロトタイプやスタイル関連のリソース
docs/test-notes/ 実機検証ログ・チェックリスト
```

## 開発メモ
- 開発時は `app/` ディレクトリで仮想環境を作成し、`FLASK_APP=viewer.py flask run --port 5000` などで起動できます。
- Raspberry Pi 上で常時運用する場合は、`docs/setup-raspberrypi.md` の手順に従って systemd サービス登録と kiosk 起動を設定してください。
- `VIEWER_API_BASE` / `VIEWER_SOCKET_BASE` などの環境変数で RaspberryPiServer 連携先を切り替えられます（下表参照）。
- `VIEWER_LOCAL_DOCS_DIR` を指定すると PDF の配置ディレクトリを任意パスへ変更できます。未指定時はリポジトリ直下の `documents/` を自動作成します（USB 取り込みを使う場合は `imports/failed/` も合わせて作成しておきます）。
- `raspi-server.local` が解決できない場合は、Pi5 側のホスト名が `raspi-server` になっているか、クライアント側の Avahi (mDNS) が起動しているかを確認してください。
- `VIEWER_LOG_PATH` を指定するとドキュメント検索・配信イベントがローテーション付きログ（最大 3 MB × 3 世代）として出力されます。未指定時は標準ログのみ利用します。
- 実機設定・検証ログは `docs/test-notes/` 配下（例: `2025-10-26-docviewer-env.md`）に記録しています。
  - `/var/log/document-viewer/import.log` を確認したい場合は `scripts/show_import_log.sh` を使うと便利です（`FILTER=ERROR` や `LINES=100` などの環境変数で絞り込み可）。
  - 環境ファイルの展開は `sudo ./scripts/install_docviewer_env.sh` を利用すると、自動で `/etc/default/docviewer` とログディレクトリを整備できます。
    ```bash
    sudo ./scripts/install_docviewer_env.sh \
      --owner tools01:tools01 \
      --api-base http://raspi-server.local:8501 \
      --docs-dir /home/tools01/DocumentViewer/documents \
      --log-path /var/log/document-viewer/client.log
    ```
  - RaspberryPiServer 側の 14 日チェック（`RaspberryPiServer/docs/mirror-verification.md`）と併せて運用状況を確認します。

### 主要な環境変数

| 変数名 | 役割 | 省略時の既定値 |
| --- | --- | --- |
| `VIEWER_API_BASE` | REST API の接続先ベース URL | `http://raspi-server.local:8501` |
| `VIEWER_API_TOKEN` | REST API 呼び出し時の Bearer トークン | 未設定（認証無し） |
| `VIEWER_SOCKET_BASE` | Socket.IO の接続先ベース URL | `VIEWER_API_BASE` |
| `VIEWER_SOCKET_PATH` | Socket.IO のパス | `/socket.io` |
| `VIEWER_SOCKET_AUTO_OPEN` | Socket.IO を自動で開くか (`0`/`1`) | `1` |
| `VIEWER_SOCKET_CLIENT_SRC` | Socket.IO クライアント JS の取得元 | `https://cdn.socket.io/4.7.5/socket.io.min.js` |
| `VIEWER_SOCKET_EVENTS` | 購読する Socket.IO イベント名（カンマ区切り） | `scan.ingested,part_location_updated,scan_update` |
| `VIEWER_SOCKET_EVENT` | 上記と同等の単一イベント指定（互換用） | 未設定 |
| `VIEWER_ACCEPT_DEVICE_IDS` | 受信対象の `device_id` をカンマ区切りで指定 | 未指定で全受信 |
| `VIEWER_ACCEPT_LOCATION_CODES` | 受信対象の `location_code` をカンマ区切りで指定 | 未指定で全受信 |
| `VIEWER_LOCAL_DOCS_DIR` | PDF を格納するディレクトリ | `~/DocumentViewer/documents` |
| `VIEWER_IMPORT_FAILED_DIR` | 取り込み失敗時に退避するフォルダ | `~/DocumentViewer/imports/failed` |
| `VIEWER_LOG_PATH` | ローテーション付きログの出力先 | 未出力 |

Pi5・Window A と同じ Bearer トークンを利用するため、ローテーション時は RaspberryPiServer RUNBOOK（4章）に従って `VIEWER_API_TOKEN` と Pi5 側の `API_TOKEN` / `VIEWER_API_TOKEN`、Window A 側 `RASPI_SERVER_API_TOKEN` を同時に更新してください。

### テスト

`pytest` を使って Flask ビューアの設定や API 応答を検証できます。
加えて `scripts/docviewer_check.py` で `/api/documents/<part>` の疎通確認とローカル PDF の存在チェックを実行できます。

```bash
cd ~/DocumentViewer
python -m venv venv
source venv/bin/activate
pip install -r app/requirements.txt pytest
pytest

# 単発で DocumentViewer API を確認する例
./scripts/docviewer_check.py --part TESTPART \
  --api-base http://raspi-server.local:8501 \
  --token "${VIEWER_API_TOKEN:-}" \
  --docs-dir ~/DocumentViewer/documents
```

USB importer を利用する場合は、上記ディレクトリに加えて `mkdir -p ~/DocumentViewer/imports/failed`
を実行し、取り込み失敗時の退避先を用意してください。

## 連携するシステム
- **tool-management-system02（Window A）**: 右ペインの所在ビューと連動し、OnSiteLogistics から送られた `part_locations` を Socket.IO 経由で参照します。DocumentViewer は `VIEWER_SOCKET_EVENTS`（既定: `scan.ingested,part_location_updated,scan_update`）で指定したイベントを購読し、該当 PDF を自動表示します。USB 同期スクリプト（`scripts/usb-import.sh`）は Window A の `usb_master_sync.sh` から呼び出され、要領書 PDF を共通運用します。
- **OnSiteLogistics（ハンディリーダ）**: 製造オーダーと棚位置を `feature/scan-intake` API で登録し、DocumentViewer と同じ Raspberry Pi 上の右ペインにリアルタイム反映されます（詳細は Window A の RUNBOOK 3.4 を参照）。
- **RaspberryPizero2W_withDropbox（Window C）**: 将来的に Window A と協調して所在/作業情報をサイネージへ配信する計画です。Dropbox ベースの JSON を活用する場合は、Window A 側でデータ提供方法を定義してから本ビューアと整合させます。

## ライセンス
このプロジェクトのライセンスについては別途定義されている場合があります。必要に応じて管理者へ確認してください。
