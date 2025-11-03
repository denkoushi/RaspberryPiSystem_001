# PostgreSQL マイグレーションメモ（ドラフト）

## 1. ベーステーブル確認
- `part_locations` の既存カラムと制約を調査し、`schema.sql` の定義と差異を洗い出す。
- バックアップ方法（pg_dump 等）を決めてからマイグレーションを適用する。

## 2. マイグレーション手順案
1. `scan_ingest_backlog` テーブルと `drain_scan_backlog` 関数を作成。
2. 本番 `part_locations` の列構成（`order_code`,`location_code`,`device_id`,`updated_at`）と schema.sql の定義差分を解消し、必要なら alter を追加。
3. テストデータを投入し、`scripts/drain_backlog.py` または `BacklogDrainService` で upsert が期待どおり動くか確認。
4. 本番環境では systemd timer 等で定期実行し、メトリクスを監視する。

## 3. テスト
- 手動テスト: `docs/test-handbook.md` の DB 確認手順を参照。
- 自動テスト: BacklogDrainService のモックテストを維持しつつ、将来的に Integration テストを追加検討。
