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
| 実機検証 | 停滞 | Pi Zero → Pi5 → Window A 統合テスト（HID が `/dev/input/event0` を掴み電子ペーパーが更新されない） | docs/test-notes/2025-11/pi-zero-test-plan.md, docs/system/pi-zero-integration.md |
| 体制整備 | 未着手 | すべてのデバイスを RaspberryPiSystem_001 リポジトリに統一 | docs/system/repo-structure-plan.md, AGENTS.md |
| 実機検証 | 準備中 | DocumentViewer / Window A Socket.IO 実機テスト | docs/test-notes/2025-11/window-a-socket-plan.md |
| 実機検証 | 完了 | ローカル Docker + PostgreSQL での drain → `part_locations` 反映 | docs/test-notes/2025-11/window-a-demo.md |
| ドキュメント更新 | 進行中 | 方針・進捗トラッカー（本ファイル） | 本ファイル |
| ドキュメント更新 | 完了 | スモーク手順・イベントペイロードの整備 | server/README.md, docs/system/documentviewer-integration.md |

## 次に着手する優先タスク
1. **リポジトリ統一プランの実行**  
   - `docs/system/repo-structure-plan.md` をもとに Mac / Pi Zero / Pi5 のフォルダ構成を洗い出し、Pi Zero の `~/OnSiteLogistics` を `~/RaspberryPiSystem_001` へ移行する手順をスクリプト化する。  
   - AGENTS.md と `docs/system/pi-zero-integration.md` に「各デバイスは RaspberryPiSystem_001 1 本で運用する」という方針を明記する。  
2. **Pi Zero 実機検証復旧**  
   - `handheld/scripts/handheld_scan_display.py` を旧ロジック準拠（by-id 固定）に戻し、`HANDHELD_INPUT_DEVICE` でデバイスを明示できるようにする。  
   - `docs/system/pi-zero-integration.md` に HID 設定手順とトラブルシュート（`/dev/input/by-id/*MINJCODE*event-kbd` を確認する手順）を追記し、`docs/test-notes/2025-11/pi-zero-test-plan.md` へ症状とログを残す。
3. **Socket.IO 運用仕様の仕上げ**  
   - Window A / DocumentViewer の再接続・イベント設定を確認し、必要な設定値を `server/config/default.toml` や関連ドキュメントに統合。  
   - テストケース（再接続・失敗ログなど）を補強し、設定変更が回帰しないようにする。

## メモ
- 進捗・課題は本ファイルで集約管理し、別ドキュメントへの分散を避ける。  
- 実機検証が完了したら、その結果と残課題を `docs/test-notes/` へ記録し、本ファイルにもステータスを反映させる。
