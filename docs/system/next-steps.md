# 開発ロードマップ（ドラフト）

モジュールごとの今後の作業を整理する。進捗に応じて更新すること。

## 状況ダッシュボード（2025-11-05 時点）

| 区分 | ステータス | タスク概要 | 対応ファイル/備考 |
| --- | --- | --- | --- |
| コード実装 | 完了 | `/api/v1/scans` の DB upsert（`scan_ingest_backlog`→`part_locations`）の実装とテスト拡充 | server/src/raspberrypiserver/services/backlog.py, tests/test_backlog_service.py, tests/test_repositories.py（pytest + 実DB検証済み） |
| コード実装 | 完了 | BacklogDrainService のロギング強化・異常系テスト整備 | server/src/raspberrypiserver/services/backlog.py, tests/test_backlog_service.py |
| コード実装 | 進行中 | Socket.IO 運用仕様（設定・ログ・再接続テスト）の確定 | server/src/raspberrypiserver/app.py, server/tests/test_api_scans.py, server/config/default.toml, docs/system/documentviewer-integration.md |
| コード実装 | 未着手 | Pi Zero mirrorctl 連携スクリプト移行（再送キュー、14 日監視） | docs/system/pi-zero-integration.md, handheld リポジトリ参照 |
| コード実装 | 完了 | 手動スモーク用 `scripts/smoke_scan.sh` 作成とテスト追加 | server/scripts/smoke_scan.sh, tests/test_broadcast_service.py |
| 実機検証 | 未着手 | Pi Zero → Pi5 → Window A 統合テスト（非ローカル環境） | docs/system/pi-zero-integration.md のチェックリストを使用 |
| 実機検証 | 未着手 | DocumentViewer 実機での Socket.IO 受信確認 | docs/system/documentviewer-integration.md |
| 実機検証 | 完了 | ローカル Docker + PostgreSQL での drain → `part_locations` 反映 | docs/test-notes/2025-11/window-a-demo.md |
| ドキュメント更新 | 進行中 | 方針・進捗トラッカー（本ファイル） | 本ファイル |
| ドキュメント更新 | 完了 | スモーク手順・イベントペイロードの整備 | server/README.md, docs/system/documentviewer-integration.md |

## 次に着手する優先タスク
1. **Pi Zero 実機検証準備**  
   - `docs/system/pi-zero-integration.md` のチェックリストを最終化し、API トークン配布〜ログ収集のサンプル記録を `docs/test-notes/2025-11/window-a-demo.md` に追加。  
   - `scripts/pi_zero_pull_logs.sh` の実行手順と出力例をテンプレートへ反映し、実機での再現性を確保する。
2. **Socket.IO 運用仕様の仕上げ**  
   - Window A / DocumentViewer の再接続・イベント設定を確認し、必要な設定値を `server/config/default.toml` や関連ドキュメントに統合。  
   - テストケース（再接続・失敗ログなど）を補強し、設定変更が回帰しないようにする。
3. **差分整理とコミット準備**  
   - 現在のコード／ドキュメント変更を整え、不要ファイルを削除したうえでまとまったコミットに備える。

## メモ
- 進捗・課題は本ファイルで集約管理し、別ドキュメントへの分散を避ける。  
- 実機検証が完了したら、その結果と残課題を `docs/test-notes/` へ記録し、本ファイルにもステータスを反映させる。
