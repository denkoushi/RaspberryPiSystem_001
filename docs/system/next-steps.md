# 開発ロードマップ（ドラフト）

モジュールごとの今後の作業を整理する。進捗に応じて更新すること。

## server（Pi5）
- `/api/v1/scans` を含む既存エンドポイントをモジュール化して移設（現在はエコー用プレースホルダー）。
- `SCAN_REPOSITORY_BACKEND = "db"` を有効活用できるよう、PostgreSQL upsert 実装と接続プールを実装（`config/schema.sql` で基礎テーブルを管理）。
- `scan_ingest_backlog` → 本番テーブル（例: `part_locations`）への移送バッチ／ストリーム処理を設計し、旧 Window A 連携と整合させる。
- Socket.IO ブロードキャストのイベント構造を整理し、テストダブルを用意。
- クライアント（Window A / DocumentViewer）向けに `scan.ingested` イベントの取り扱い仕様を決め、受信テストを追加。
- USB 運用スクリプト（INGEST/DIST/BACKUP）の新構成への対応。
- `mirrorctl` 連携スクリプトの移行と設定テンプレートの整備。

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
