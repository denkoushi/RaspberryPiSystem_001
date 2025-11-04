# Pi Zero → Pi5 → Window A / DocumentViewer 統合チェックリスト（ドラフト）

Pi Zero のハンディ送信フローを再構築する際に必要な設定・検証ポイントを整理する。実機検証に入る前の準備タスクとして活用する。

## 1. トークン / 設定ファイルの整合
- 共通 API トークン
  - Pi Zero (`onsitelogistics`)、Pi5 (`server/config/local.toml` または `/etc/systemd/system/raspberrypiserver.service.d/env.conf`)、Window A、DocumentViewer の Bearer トークンを統一する。
  - `server/scripts/manage_api_token.py --rotate` などで再発行した場合は即時に全端末へ配布し、必要に応じて `sudo systemctl restart ...` で反映を確認する。
- Pi Zero 側設定
  - `/etc/onsitelogistics/config.json` 例:
    ```json
    {
      "api_base": "http://pi5.local:8501",
      "api_token": "<SHARED_TOKEN>",
      "device_id": "HANDHELD-01"
    }
    ```
  - `mirrorctl status` が `mirror_mode=true` で 14 日監視に入れる状態かチェック。
    ```bash
    sudo mirrorctl status
    sudo systemctl status handheld@tools01.service
    sudo journalctl -u handheld@tools01.service -n 40 --no-pager
    ```
    `Last success`/`Next run` の時刻、journal に `status=delivered` が並んでいるか確認し、異常があれば `sudo systemctl restart handheld@tools01.service`。
- Pi5 側設定
  - `server/config/local.toml` 例:
    ```toml
    APP_NAME = "RaspberryPiServer"
    SCAN_REPOSITORY_BACKEND = "db"
    SOCKET_BROADCAST_EVENT = "scan.ingested"

    [database]
    dsn = "postgresql://app:app@localhost:15432/sensordb"
    ```
  - systemd 環境ファイルで `Environment="RPI_SERVER_CONFIG=/srv/rpi-server/config/local.toml"` を指定し `sudo systemctl daemon-reload` → `sudo systemctl restart raspberrypiserver.service`。
- Window A / DocumentViewer
  - `.env` / systemd 環境ファイルに API/Socket.IO のホスト名（IPv4）とトークンを設定。
  - 例: `SOCKET_IO_URL=http://pi5.local:8501`、`SOCKET_IO_NAMESPACE=/`、`SOCKET_IO_EVENT=scan.ingested`。

## 2. ネットワーク疎通・サービス監視
- Pi Zero → Pi5 REST 疎通
  - `curl -I http://<pi5-host>:8501/healthz`
  - Pi Zero から Pi5 への `ping`, `curl /api/v1/ping` を確認（必要なら `tcpdump` で追跡）。
- Pi5 サービス監視
  ```bash
  sudo journalctl -u raspberrypiserver.service -n 50
  sudo tail -n 50 /srv/rpi-server/logs/api_actions.log
  sudo tail -n 20 /srv/rpi-server/logs/socket.log
  ```
- Window A クライアント
  - `systemctl status window-a.service` を確認し、デプロイ先の `.env` が最新トークン/URL を参照しているか確認。
  - `scripts/listen_for_scans.ts --api http://127.0.0.1:8501` で Socket.IO 疎通テスト。
- DocumentViewer
  - `systemctl status document-viewer.service`
  - `/var/log/document-viewer/client.log` に接続ログ、イベント受信ログが出ているか確認。

## 3. テスト手順（実施時チェックリスト）
1. Pi Zero でテスト用バーコード（注文番号）をスキャン。
2. Pi Zero 送信ログ (`journalctl -u handheld@tools01.service -n 50`) に 200 応答が記録されているか確認。
3. Pi5 サーバーログ
   - REST 受信ログ (`api_actions.log`)
   - Socket.IO emit ログ (`Broadcast emit request`, `Socket.IO emit succeeded`)
4. PostgreSQL への反映確認
   ```bash
   PGPASSWORD=app psql -h 127.0.0.1 -p 15432 -U app -d sensordb \
     -c "SELECT order_code, location_code, updated_at FROM part_locations ORDER BY updated_at DESC LIMIT 5;"
   ```
5. Window A UI / DocumentViewer の更新を目視（注文番号に合わせてハイライト/表示が変わるか）。
6. 必要に応じて `POST /api/v1/admin/drain-backlog` でバックログを処理。
7. 記録テンプレート作成と保存。
   ```bash
   cp docs/test-notes/templates/pi-zero-integration.md \
      docs/test-notes/$(date +%F)-pi-zero-integration.md
   ```
   - 上記ファイルに各ログ抜粋・観察結果を貼り付ける。

## 4. 片付け / ロールバック
- Window A の Socket.IO リスナーや開発用スクリプトは `Ctrl+C` で停止。
- RaspberryPiServer (Pi5) は `sudo systemctl stop raspberrypiserver.service`（開発時はターミナル上で `Ctrl+C`）。
- Pi Zero の `onsitelogistics` サービスを停止／再起動する場合は `sudo systemctl restart handheld@tools01.service` を使用。
- DocumentViewer のデバッグリスナーを停止した場合は `sudo systemctl restart document-viewer.service` で通常運用に戻す。

## 5. 未完タスク / メモ
- DocumentViewer 側の Socket.IO 設定が新構成に追従しているか確認。
- Pi Zero からの再送キュー（mirrorctl hook）をモジュール化し、ログ出力フォーマットを統一する。
- 実機テスト結果は `docs/test-notes/YYYY-MM/pi-zero-*.md` に記録し、差分比較できるようテンプレート化する。
