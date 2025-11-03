# 2025-11-05 drain パイプライン検証計画

- psql 未導入につき、実検証は PostgreSQL があるテスト環境で実施予定。
- `scripts/seed_backlog.py` でサンプル投入後、`scripts/drain_backlog.py` を実行し、Socket.IO イベントも確認する。
- Docker Desktop 起動後、`docker compose up -d` で PostgreSQL を起動。
- `./scripts/init_db.sh` → `seed_backlog.py` → `drain_backlog.py` を実行し、`part_locations` に TEST-001 が反映されたことを確認。
