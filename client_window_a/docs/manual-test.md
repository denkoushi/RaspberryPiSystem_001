# Window A 手動テスト手順

Window A クライアントの REST / Socket.IO 連携をローカルで検証するための手順。

## 0. 準備
- Docker Desktop を起動し、PostgreSQL コンテナを立ち上げる。
  ```bash
  cd ~/RaspberryPiSystem_001/server
  docker compose up -d
  ./scripts/init_db.sh "postgresql://app:app@localhost:15432/sensordb"
  python scripts/seed_backlog.py --dsn "postgresql://app:app@localhost:15432/sensordb" --order TEST-005 --location RACK-E1
  python scripts/seed_backlog.py --dsn "postgresql://app:app@localhost:15432/sensordb" --order TEST-004 --location RACK-D1
  python scripts/seed_backlog.py --dsn "postgresql://app:app@localhost:15432/sensordb" --order TEST-003 --location RACK-C1
  python scripts/seed_backlog.py --dsn "postgresql://app:app@localhost:15432/sensordb" --order TEST-002 --location RACK-B1
  python scripts/seed_backlog.py --dsn "postgresql://app:app@localhost:15432/sensordb" --order TEST-001 --location RACK-A1
  python scripts/drain_backlog.py --dsn "postgresql://app:app@localhost:15432/sensordb" --limit 50
  ```
- `server/config/local.toml` を用意し、`SCAN_REPOSITORY_BACKEND = "db"`・`database.dsn` を設定する。
- `AUTO_DRAIN_ON_INGEST` を設定すると、スキャン受付後に指定件数のドレインが自動実行される（例: `AUTO_DRAIN_ON_INGEST = 50`）。

## 1. Flask サーバーの起動
```bash
cd ~/RaspberryPiSystem_001/server
source .venv/bin/activate
RPI_SERVER_CONFIG=~/RaspberryPiSystem_001/server/config/local.toml python -m raspberrypiserver.app
```
- 別ターミナルで以下の検証を進める。終了時は `Ctrl+C` で停止する。
- 最短確認は自動スモーク (`server/scripts/smoke_scan.sh`) を利用できる。
  ```bash
  cd ~/RaspberryPiSystem_001/server
  ./scripts/smoke_scan.sh
  ```
  - サーバー起動 → スキャン送信 → 停止まで自動実行し、ログの尻尾も出力される。
  - 詳細確認や複数イベント検証が必要な場合は以下の手順を続行する。

## 2. REST `/api/v1/part-locations` の確認
```bash
cd ~/RaspberryPiSystem_001
source server/.venv/bin/activate
python client_window_a/scripts/check_part_locations.py
```
- 期待結果: `entries` に `TEST-001`〜`TEST-005` の所在が表示される。

## 3. Socket.IO イベントの確認
1. リスナーを起動してイベントを待ち受ける（ローカルでは IPv6 ループバックに接続できないため `127.0.0.1` を指定する）。
   ```bash
   cd ~/RaspberryPiSystem_001/client_window_a
   npx ts-node scripts/listen_for_scans.ts --api http://127.0.0.1:8501
   ```
   - `API_BASE` や `SOCKET_BASE` を変更したい場合は `--api`／`--socket` または環境変数で指定する。
2. 別ターミナルからテスト用のスキャンを送信する。
   - 新しいヘルパースクリプト（`send_scan.py`）を利用する場合:
     ```bash
     cd ~/RaspberryPiSystem_001
     source server/.venv/bin/activate
     python client_window_a/scripts/send_scan.py \
       --order TEST-900 --location RACK-Z9 --device HANDHELD-99
     ```
     - `--order` / `--location` を省略するとタイムスタンプ由来の値が自動生成される。
   - `curl` を直接叩く場合:
     ```bash
     curl -X POST http://127.0.0.1:8501/api/v1/scans \
       -H "Content-Type: application/json" \
       -d '{"order_code":"TEST-900","location_code":"RACK-Z9","device_id":"HANDHELD-99"}'
     ```
   - リスナー画面に `scan.ingested` イベントのペイロードが表示されること、`order_code` / `location_code` 未設定時に `HTTP 400` が返ることを確認する。
3. 必要に応じてバックログをドレインし、REST 応答が更新されることを再確認する。
   ```bash
   cd ~/RaspberryPiSystem_001/server
   source .venv/bin/activate
   python scripts/drain_backlog.py --dsn "postgresql://app:app@localhost:15432/sensordb" --limit 50
   cd ~/RaspberryPiSystem_001
   source server/.venv/bin/activate
   python client_window_a/scripts/check_part_locations.py
   ```
   - `TEST-900` の所在がリストに加わっていることを期待する。
   - スクリプトの代わりに管理 API を呼び出すこともできる。
     ```bash
     curl -X POST http://localhost:8501/api/v1/admin/drain-backlog -d '{"limit": 50}' -H "Content-Type: application/json"
     ```
   - 滞留件数を確認したい場合は以下を実行する。
     ```bash
     curl http://localhost:8501/api/v1/admin/backlog-status
     ```
     - `pending` が 0（ドレイン済み）または想定件数になっているか確認する。

## 4. 片付け
- Socket リスナーと Flask サーバーを `Ctrl+C` で停止する。
- コンテナを停止する場合:
  ```bash
  cd ~/RaspberryPiSystem_001/server
  docker compose down
  ```

検証結果は `/docs/test-notes/2025-11/window-a-demo.md` に追記する。
