# Window A デモテストメモ (2025-11-05)

## REST 応答確認
- `docker compose up -d` で PostgreSQL 起動 → `./scripts/init_db.sh`, `seed_backlog.py`, `drain_backlog.py` で `TEST-001`〜`TEST-005` を投入。
- `server/config/local.toml` を作成し、`SCAN_REPOSITORY_BACKEND = "db"`／`database.dsn = "postgresql://app:app@localhost:15432/sensordb"` を指定。
- Flask サーバー (`RPI_SERVER_CONFIG=~/RaspberryPiSystem_001/server/config/local.toml`) を起動し、以下のコマンドで確認。
  ```bash
  cd ~/RaspberryPiSystem_001
  source server/.venv/bin/activate
  python client_window_a/scripts/check_part_locations.py
  ```
- 出力例:
  ```python
  {'entries': [
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-E1', 'order_code': 'TEST-005', 'updated_at': '2025-11-04 00:40:56.155083+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-D1', 'order_code': 'TEST-004', 'updated_at': '2025-11-04 00:34:42.575703+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-C1', 'order_code': 'TEST-003', 'updated_at': '2025-11-04 00:29:08.875170+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-B1', 'order_code': 'TEST-002', 'updated_at': '2025-11-03 22:58:31.110353+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-A1', 'order_code': 'TEST-001', 'updated_at': '2025-11-03 22:55:58.506797+00:00'}
  ]}
  ```
- 2025-11-04 07:49 (JST) 実施結果:
  ```python
  {'entries': [
      {'device_id': 'HANDHELD-42', 'location_code': 'RACK-Y0', 'order_code': 'TEST-910', 'updated_at': '2025-11-04 01:58:03.541858+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-Z1', 'order_code': 'TEST-901', 'updated_at': '2025-11-04 01:57:55.945996+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-Z3', 'order_code': 'TEST-903', 'updated_at': '2025-11-04 01:57:55.945996+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-Z2', 'order_code': 'TEST-902', 'updated_at': '2025-11-04 01:57:55.945996+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-E1', 'order_code': 'TEST-005', 'updated_at': '2025-11-04 00:40:56.155083+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-D1', 'order_code': 'TEST-004', 'updated_at': '2025-11-04 00:34:42.575703+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-C1', 'order_code': 'TEST-003', 'updated_at': '2025-11-04 00:29:08.875170+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-B1', 'order_code': 'TEST-002', 'updated_at': '2025-11-03 22:58:31.110353+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-A1', 'order_code': 'TEST-001', 'updated_at': '2025-11-03 22:55:58.506797+00:00'}
  ]}
  ```

## 次のステップ
- `client_window_a/docs/manual-test.md` の手順に沿って、Socket.IO を含むデモ UI の手動テストを実施予定。
- バックログドレインはスクリプトに加えて `POST /api/v1/admin/drain-backlog` でトリガー可能（`{"limit": 50}` など）。
- `AUTO_DRAIN_ON_INGEST` を設定すると、スキャン受付時に自動ドレインが走りレスポンスに `backlog_drained` が含まれる。
- 2025-11-05 07:36 (JST): `curl POST /api/v1/scans` で `TEST-965` を送信 → サーバーログに Socket.IO emit 成功が記録され、Window A リスナー(`scripts/listen_for_scans.ts --api http://127.0.0.1:8501`) で `scan.ingested` イベントを受信できることを確認。
- 2025-11-05 10:00 (JST): `server/scripts/smoke_scan.sh` 実行。`SMOKE-1762304404` を送信し HTTP 202 / Socket.IO emit 成功をログで確認。テスト後にポートは自動解放済み。
