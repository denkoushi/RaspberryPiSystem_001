# 2025-11-03 drain_scan_backlog 手動検証メモ

- DSN: `postgresql://app:app@localhost:15432/sensordb`
- 1件だけ `scan_ingest_backlog` に投入し、`scripts/drain_backlog.py --limit 10` を実行。
- `part_locations` に `TEST-001` が upsert されたことを確認。
