# 開発ロードマップ（ドラフト）

モジュールごとの今後の作業を整理する。進捗に応じて更新すること。

## server（Pi5）
- `/api/v1/scans` を含む既存エンドポイントをモジュール化して移設（現在はエコー用プレースホルダー）。
- `SCAN_REPOSITORY_BACKEND = "db"` を有効活用できるよう、PostgreSQL upsert 実装と接続プールを実装（`config/schema.sql` で基礎テーブルを管理）。
- `scan_ingest_backlog` → 本番テーブル（例: `part_locations`）への移送バッチ／ストリーム処理を設計し、旧 Window A 連携と整合させる。
- バックログ処理状況を監視するためのメトリクス（件数、滞留時間）とアラート条件を定義し、`docs/system/migrations.md` に検証結果を記録する。
- `drain_scan_backlog`（schema.sql）をジョブ化し、処理失敗時のリトライ・アラートを決める（`scripts/drain_backlog.py` や `BacklogDrainService` を systemd timer/管理 API から呼び出す）。`docs/system/postgresql-setup.md` に psql 導入メモを集約。
- docker-compose によるローカル検証手順を `server/README.md` に追記済み。実 DB での drain 検証を実行したら結果を `docs/test-notes/` に記録する。
- 実テーブル構成（例: `part_locations` のカラム整合）を確認し、マイグレーション手順とテストデータ適用方法を `docs/system/migrations.md` にまとめる。
- Socket.IO ブロードキャストのイベント構造を整理し、テストダブルを用意。
- クライアント（Window A / DocumentViewer）向けに `scan.ingested` イベントの取り扱い仕様を決め、受信テストを追加。
- `/api/v1/part-locations` エンドポイントを実装済み。Window A デモの実機テストを実施予定。
- `client_window_a/tests/location-state.test.ts` で REST + Socket 更新の単体テストを整備済み。サーバー側は `tests/test_backlog_service.py` を追加し、DB バックログ処理の動作をモックで検証。
- `client_window_a/docs/manual-test.md` に REST/Socket の手動テスト手順を整理済み。近日中に実施。
- `POST /api/v1/admin/drain-backlog` を追加し、バックログドレインをリモート操作できるようにした。`tests/test_api_maintenance.py` で動作確認済み。
- `/api/v1/scans` で必須フィールドをバリデーションし、DB バックエンド時には `scan_ingest_backlog` へ保存する。`AUTO_DRAIN_ON_INGEST` 設定で自動ドレインを行えるよう拡張済み。
- Socket.IO ブロードキャストは現状プレースホルダーのため、実イベント配信（Flask-SocketIO など）への置き換えと Window A での受信確認を実装する。
- Flask-SocketIO を `async_mode="gevent"` で導入し、Window A リスナー（IPv4 で接続）までイベント受信を確認済み。
- Pi Zero → Pi5 → Window A / DocumentViewer の統合テストに向けて、`docs/system/pi-zero-integration.md` のチェックリストに沿って実機準備（mirrorctl 状態、共通トークン、DocumentViewer の Socket.IO 設定）を進める。
- USB 運用スクリプト（INGEST/DIST/BACKUP）の新構成への対応。
- `mirrorctl` 連携スクリプトの移行と設定テンプレートの整備。

### 現状まとめ（2025-11-05）
- ローカル Docker + PostgreSQL で drain → `part_locations` 反映を確認済み。
- Window A クライアントは API 未実装のためデモ実行は保留；テストテンプレートを準備済み。
- ハンディ再送キューは mirrorctl hook を実装し、Pi Zero 実機テスト計画を更新。

## client_window_a（Pi4）
- 右ペイン UI コンポーネントの移設とテスト容易性の改善。
- Socket.IO クライアントの再構築と REST フォールバックのテスト記録。
- systemd ドロップインと環境ファイルのテンプレート化。

## handheld（Pi Zero 2 W）
- 送信キュー処理（再送・ログ記録）のモジュール化。
- `mirrorctl` 設定テンプレートと 14 日ログの保持方針を文書化。
- テストメニューに沿ったログ確認手順のスクリプト化。

## ドキュメント・テスト
- `docs/test-handbook.md` に USB フローや DocumentViewer シナリオを追加。
- `docs/test-notes/templates/` に追加テンプレート（USB、Viewer）を整備。
- 既存リポジトリから引き継ぐ要件を `docs/system/next-steps.md` に順次追記。
2025-11-05 07:51:12 JST: Reviewed AGENTS.md before continuing.
