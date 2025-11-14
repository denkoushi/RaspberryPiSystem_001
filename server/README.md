# RaspberryPiServer モジュール

このディレクトリは Pi5 上で稼働するサーバー機能をまとめる。REST / Socket.IO / PostgreSQL などの中枢機能をモジュール化し、既存リポジトリで安定していたコードを移設しやすい構成を目指す。

## ディレクトリ構成（初期案）
- `src/raspberrypiserver/` — Flask ベースのアプリケーション本体とモジュール群
- `tests/` — サーバーモジュール向けのテストコード（将来的な自動テスト復帰用に保持）
- `config/` — `default.toml` など設定テンプレートを保管
- `scripts/`（未作成） — USB やメンテナンス用スクリプト

## 現状の内容
- `app.py` が Flask アプリの雛形と設定読込処理を提供する。
- `api/` 配下に `/api/v1/scans` のプレースホルダー Blueprint を用意（POST 受信の疎通確認用）。
- `api/` 配下に `/api/v1/part-locations` を追加し、最新所在情報を返せるようにした。
- `config/default.toml` に基本設定（API prefix、ログ出力先など）を記述。
- `config/schema.sql` に `scan_ingest_backlog` / `part_locations` テーブルと `drain_scan_backlog` 関数の雛形を含め、バックログ→本番テーブル移行の入口を用意。
- `tests/test_healthz.py` がヘルスチェックと設定上書きのユニットテストを実装。
- `tests/test_api_scans.py` がスキャン受信エンドポイントのエコーバックを検証。
- `tests/test_repositories.py` がメモリ/DB プレースホルダーリポジトリの挙動と切替を検証。
- `services/` に Socket.IO ブロードキャストのプレースホルダーを追加し、スキャン受信時に `scan.ingested` イベントを発火（設定で変更可）。
- Flask-SocketIO は `async_mode="gevent"` で動作し、依存として `gevent` / `gevent-websocket` が必要。

## 次のステップ
1. 旧 `RaspberryPiServer` リポジトリから API ハンドラや設定ファイルを段階的に移設。
2. `SCAN_REPOSITORY_BACKEND = "db"` を有効化できるよう PostgreSQL 向け実装を用意し、Socket.IO など周辺ロジックを統合する。
3. USB / mirrorctl 連携や Socket.IO など、高難度ロジックを独立モジュールとして整理する。

## Pi5 実機デプロイ（標準手順）
- **実行ユーザー / ディレクトリ**  
  - Pi5 では `/srv/RaspberryPiSystem_001` が正本。`raspi-server.service` は root 権限で `/srv/RaspberryPiSystem_001/server/.venv/bin/python` を起動する。  
  - CLI でメンテナンスを行うときは管理ユーザー（例: `denkon5ssd`）でログインし、常にこのディレクトリを `git pull` する。  
- **初期セットアップ**  
  ```bash
  sudo mkdir -p /srv/RaspberryPiSystem_001
  sudo chown denkon5ssd:denkon5ssd /srv/RaspberryPiSystem_001
  cd /srv/RaspberryPiSystem_001
  git clone https://github.com/denkoushi/RaspberryPiSystem_001.git .
  cd server
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -e ".[dev]"
  deactivate
  ```
  - `server/scripts/bootstrap_venv.sh` を使う場合もカレントディレクトリは `/srv/RaspberryPiSystem_001/server` に合わせる。
- **定期更新フロー（Pi5 上での `git pull`）**  
  ```bash
  cd /srv/RaspberryPiSystem_001
  git pull
  cd server
  source .venv/bin/activate
  python -m pytest             # 必要に応じて
  deactivate
  sudo systemctl restart raspi-server.service
  sudo journalctl -u raspi-server.service -n 40 --no-pager
  ```
  - `server/logs/app.log` も同じディレクトリ配下に生成されるため、`tail -f logs/app.log` で動作確認できる。  
- **設定ファイルの配置**  
  - `/srv/RaspberryPiSystem_001/server/config/local.toml` に Pi5 固有の DSN、DocumentViewer 連携、`SCAN_REPOSITORY_BACKEND` などを記載する。  
  - systemd ユニットでは `Environment=RPI_SERVER_CONFIG=/srv/RaspberryPiSystem_001/server/config/local.toml` を指定する。  
- **systemd ユニット**  
  - `/etc/systemd/system/raspi-server.service` の例:  
    ```
    [Service]
    WorkingDirectory=/srv/RaspberryPiSystem_001/server
    ExecStart=/srv/RaspberryPiSystem_001/server/.venv/bin/python /srv/RaspberryPiSystem_001/server/src/raspberrypiserver/app.py
    Environment=PATH=/srv/RaspberryPiSystem_001/server/.venv/bin:/usr/bin:/bin
    Environment=RPI_SERVER_CONFIG=/srv/RaspberryPiSystem_001/server/config/local.toml
    Restart=on-failure
    ```
  - 変更後は `sudo systemctl daemon-reload && sudo systemctl restart raspi-server.service` を実行し、`curl -I http://127.0.0.1:8501/healthz` でヘルスチェックを行う。

## 工具管理 API（Window A 連携）
- `config/local.toml` に以下のように設定し、Pi5 上でも工具貸出 API を有効化する。DSN を指定しない場合は `[database].dsn` を利用する。  
  ```toml
  [tool_management]
  enabled = true
  dsn = "postgresql://app:app@localhost:15432/sensordb"
  ```
- Database スキーマ（`server/config/schema.sql`）には `users` / `tool_master` / `tools` / `loans` テーブルが定義済み。Window A と同じ PostgreSQL を参照していれば追加のマイグレーションは不要。  
- エンドポイント一覧:  
  - `GET /api/v1/loans`（互換のため `/api/loans` も可）: 貸出中リストと直近履歴を返す。クエリパラメータ `open_limit` / `history_limit` で件数調整。  
  - `POST /api/v1/loans/<loan_id>/manual_return`: 指定 ID の貸出を強制返却する。  
  - `DELETE /api/v1/loans/<loan_id>`: 返却済みでないレコードを削除する。  
- Window A (`window_a/app_flask.py`) の `/api/loans` エンドポイントは上記 API を呼び出す設計になっているため、Pi5 側で `tool_management.enabled = true` にすると REST 連携へ移行できる。

## バックログのドレイン（手動）
PostgreSQL が稼働している環境では、以下のスクリプトで `scan_ingest_backlog` から本番テーブルへ移送できます。

```bash
cd ~/RaspberryPiSystem_001/server
source .venv/bin/activate
python scripts/drain_backlog.py --dsn "postgresql://app:app@localhost:15432/sensordb" --limit 200
```

> 注意: 上記コマンドはローカルで PostgreSQL が起動していない場合エラーになります。実際に実行するときは DB が利用可能な環境で行ってください。

アプリケーション内でも `BACKLOG_DRAIN_SERVICE` を通じて同様の処理を呼び出せるため、今後 systemd timer や管理 API から利用できる設計を想定しています。

### バックログへのサンプル投入
検証用にサンプルデータを投入したい場合は以下を利用できます。

```bash
python scripts/seed_backlog.py --dsn "postgresql://app:app@localhost:15432/sensordb" \
  --order TEST-123 --location RACK-A1
```

## ローカル PostgreSQL の起動（docker-compose）

```bash
cd ~/RaspberryPiSystem_001/server
docker compose up -d
./scripts/init_db.sh "postgresql://app:app@localhost:15432/sensordb"
```

> `psql` コマンドが必要です。macOS では `brew install postgresql` などで導入してください。
>
> トラブルシュートや Homebrew 導入手順の詳細は `docs/system/postgresql-setup.md` を参照。

## 仮想環境の初期化
- `scripts/bootstrap_venv.sh` で `server/.venv` を作成し、`pip install -e ".[dev]"` まで自動化できる。
- 既存の仮想環境が壊れている場合も再作成してくれる。
  ```bash
  cd ~/RaspberryPiSystem_001/server
  ./scripts/bootstrap_venv.sh
  source .venv/bin/activate
  ```
- 以降、テスト実行などは以下のように実行する。
  ```bash
  pytest
  ```

## ローカル設定ファイル
- `config/local.toml` を作成し、`SCAN_REPOSITORY_BACKEND = "db"` とローカル DSN（例: `postgresql://app:app@localhost:15432/sensordb`）を設定する。
- Flask 起動時は環境変数で設定ファイルを指定する。
  ```bash
  cd ~/RaspberryPiSystem_001/server
  source .venv/bin/activate
  RPI_SERVER_CONFIG=~/RaspberryPiSystem_001/server/config/local.toml python -m raspberrypiserver.app
  ```
- Socket.IO を別パスで提供したい場合は `SOCKETIO_PATH = "/custom.io"` のように指定すると、サーバー側もそのパスで待ち受ける（クライアントも同じパスに合わせる）。
- 起動～送信～停止をまとめて確認したい場合はスモークスクリプトを利用できる。
  ```bash
  cd ~/RaspberryPiSystem_001/server
  ./scripts/smoke_scan.sh
  ```
  - ポート占有を検知した場合は自動で中断する。成功時には `SMOKE-<timestamp>` のオーダーが 202 応答で受理され、ログ末尾に Socket.IO emit の結果が表示される。

## `/api/v1/scans`（スキャン受信 API）
- 必須フィールドは `order_code` と `location_code`（どちらも空文字不可）。`device_id` は任意だが指定する場合は空でない文字列にする。
- 受信したペイロードはサーバー側でトリミング後に保存・ブロードキャストされる。余分なキーは保持されない。
- バリデーションに失敗した場合は `HTTP 400`／`{"status":"error","reason":"missing-order_code"}` のように返す。
- `AUTO_DRAIN_ON_INGEST` を設定すると、受信後に `BacklogDrainService.drain_once(limit=設定値)` を自動実行する。
- 正常時のレスポンス例:
  ```json
  {
    "status": "accepted",
    "received": {
      "order_code": "TEST-001",
      "location_code": "RACK-A1",
      "device_id": "HANDHELD-01"
    },
    "app": "RaspberryPiServer"
  }
  ```

## 管理 API（バックログドレイン）
- `POST /api/v1/admin/drain-backlog` で `BacklogDrainService` を 1 回だけ起動できる（`SCAN_REPOSITORY_BACKEND="db"` かつ DSN 設定済みの場合のみ有効）。
- リクエスト例:
  ```bash
  curl -X POST http://localhost:8501/api/v1/admin/drain-backlog \
    -H "Content-Type: application/json" \
    -d '{"limit": 50}'
  ```
- 応答例:
  ```json
  {"status": "ok", "drained": 5, "limit": 50}
  ```
- `AUTO_DRAIN_ON_INGEST` を設定している場合は `/api/v1/scans` のレスポンスに `"backlog_drained"` が含まれ、同時に backlog-status からも最新件数を取得できる。
- 失敗時（DSN 未設定や SQL エラー）は `HTTP 503` で `{"status":"skipped","reason":"backlog-drain-disabled"}` が返る。PiZero 側からのスキャンは継続するため、ログ（`api_actions.log` / `socket.log`）を確認し再実行する。
- `GET /api/v1/admin/backlog-status` で滞留件数とドレイン設定を確認できる。
  ```bash
  curl http://localhost:8501/api/v1/admin/backlog-status
  ```
  ```json
  {
    "status": "ok",
    "pending": 12,
    "drain_limit": 200,
    "auto_drain_on_ingest": 50
  }
  ```

> Pi Zero 連携や DocumentViewer 連携の手順・チェックリストは `docs/system/pi-zero-integration.md` と `docs/system/documentviewer-integration.md` に整理している。
