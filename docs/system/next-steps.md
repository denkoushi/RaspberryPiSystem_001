# 開発ロードマップ（ドラフト）

モジュールごとの今後の作業を整理する。進捗に応じて更新すること。

## 状況ダッシュボード（2025-11-09 時点）

| 区分 | ステータス | タスク概要 | 対応ファイル/備考 |
| --- | --- | --- | --- |
| コード実装 | 完了 | `/api/v1/scans` の DB upsert（`scan_ingest_backlog`→`part_locations`）の実装とテスト拡充 | server/src/raspberrypiserver/services/backlog.py, tests/test_backlog_service.py, tests/test_repositories.py（pytest + 実DB検証済み） |
| コード実装 | 完了 | BacklogDrainService のロギング強化・異常系テスト整備 | server/src/raspberrypiserver/services/backlog.py, tests/test_backlog_service.py |
| コード実装 | 進行中 | Socket.IO 運用仕様（設定・ログ・再接続テスト）の確定 | server/src/raspberrypiserver/app.py, server/tests/test_api_scans.py, server/config/default.toml, docs/system/documentviewer-integration.md |
| コード実装 | 停滞 | Pi Zero mirrorctl 連携スクリプト移行（再送キュー、14 日監視） | docs/system/pi-zero-integration.md, handheld/scripts/** |
| コード実装 | 完了 | 手動スモーク用 `scripts/smoke_scan.sh` 作成とテスト追加 | server/scripts/smoke_scan.sh, tests/test_broadcast_service.py |
| 実機検証 | 復旧中 | Pi Zero → Pi5 → Window A 統合テスト（Pi Zero 側はシリアル復旧済み、Pi5 API がタイムアウト中） | docs/test-notes/2025-11/pi-zero-test-plan.md, docs/system/pi-zero-integration.md |
| 体制整備 | 進行中 | すべてのデバイスを RaspberryPiSystem_001 リポジトリに統一（tools01 ワーキングツリー同期を実装済み） | docs/system/repo-structure-plan.md, AGENTS.md, scripts/update_handheld_override.sh |
| 実機検証 | 準備中 | DocumentViewer / Window A Socket.IO 実機テスト | docs/test-notes/2025-11/window-a-socket-plan.md |
| 実機検証 | 完了 | ローカル Docker + PostgreSQL での drain → `part_locations` 反映 | docs/test-notes/2025-11/window-a-demo.md |
| ドキュメント更新 | 進行中 | 方針・進捗トラッカー（本ファイル＋ Pi Zero 手順の更新） | 本ファイル, docs/system/pi-zero-integration.md |
| ドキュメント更新 | 完了 | スモーク手順・イベントペイロードの整備 | server/README.md, docs/system/documentviewer-integration.md |

## 直近マイルストーンとサブブランチ方針

| マイルストーン | 目的 | 推奨ブランチ | ゴール | 備考 |
| --- | --- | --- | --- | --- |
| Handheld Migration Phase-1 | 旧ハンディの Serial/HID 切替と電子ペーパーの完全復旧 | `feature/handheld-migration-p1`（現 `feature/repo-structure-plan` から派生） | Pi Zero で `[SERIAL] scanner ready` を安定表示し、Pi5 復旧後すぐに API 通信が通る状態 | PR には `handheld.log` と `journalctl` の最新ログを添付 |
| Handheld Migration Phase-2 | mirrorctl / 14 日監視、LED/ボタン I/O を移植 | `feature/handheld-migration-p2` | `mirrorctl` 連携スクリプトを新リポジトリで再実装し、旧 OnSiteLogistics リポジトリへの依存を解消 | Phase-1 完了後に開始 |
| Repo Unification Pi5 | Pi5 側のディレクトリ／systemd を刷新 | `feature/pi5-repo-sync` | `/srv/RaspberryPiSystem_001` 配下で一元化し、`raspberrypiserver.service` の WorkingDirectory を更新 | Pi5 停止時間の調整が必要 |

各マイルストーンでブランチを分け、main へマージ→Pi へデプロイの流れを固定する。必要に応じて PR テンプレートに「対象マイルストーン」「必要ログ」を明記する。

## 旧 OnSiteLogistics → 新リポジトリ移植状況

| 領域 | 現状 | 取りこぼし / リスク | 推定対応時間 | 備考 |
| --- | --- | --- | --- | --- |
| ハンディ本体（handheld_scan_display.py） | シリアル検出・再送キューは移植済み。Pi Zero では 2025-11-09 21:08 JST に A/B 完走を確認。 | Pi5 API が落ちているため end-to-end 送信確認が未完。`mirrorctl` 連携や LED/ボタン GPIO は未移植。 | 0.5 日（Pi5 復旧＋drain-only＋ログ採取）、+1 日（mirrorctl/GPIO 移植） | `docs/test-notes/2025-11/pi-zero-test-plan.md` にログ追記予定 |
| Pi Zero デプロイ経路 | `update_handheld_override.sh` に tools01 同期を実装し、VS Code → GitHub → tools01 で整合が取れる状態 | `tools01` ディレクトリに手入力した設定ファイルは `reset --hard` で消えるため、除外リスト/別管理場所を整理する必要あり。 | 0.5 日 | `docs/system/pi-zero-integration.md` へ保護すべきファイル一覧を追加する |
| Pi5 サーバー | コードは新リポジトリ由来で進行中 | インフラ（systemd, ディレクトリ構成）が旧名称のまま。deploy 時に手順が枝分かれしている。 | 1 日（切替手順 + ダウンタイム調整） | `docs/system/repo-structure-plan.md` の Milestone3 未完 |
| DocumentViewer / Window A | 旧リポジトリを参照のみで維持 | 新リポジトリへ統合するか、境界をどこに置くか未決。 | 要検討 | AGENTS.md で「参照のみ可」を明確化する |

## ここまでの状況サマリ（2025-11-09 夜）
- Pi Zero: `journalctl` で `[SERIAL] forcing /dev/minjcode0 @ 115200bps` → `[SERIAL] scanner ready` が出力され、電子ペーパー UI も A/B → DONE 表示まで復旧。  
- Pi5: `http://192.168.10.230:8501/api/v1/scans` がタイムアウトし、スキャンは SQLite キューに積まれている。Pi5 でサービス復旧後、`handheld_scan_display.py --drain-only` 実行が必要。  
- 体制: tools01 リポジトリを強制同期する仕組みを導入済み。今後は Pi5 側の再構築と mirrorctl 移植が優先。

## 今後 1 週間の優先タスク（提案）
1. **Pi5 API 復旧**  
   - `raspberrypiserver.service` を再起動し、`curl -I http://192.168.10.230:8501` で疎通確認。  
   - 復旧後すぐに Pi Zero で `sudo -u tools01 -H bash -lc "source ~/.venv-handheld/bin/activate && python handheld/scripts/handheld_scan_display.py --drain-only"` を実行してキューを空にする。
2. **Handheld Migration Phase-1 ブランチの確立**  
   - 現在の `feature/repo-structure-plan` の差分を棚卸しし、マイルストーン専用ブランチへ整理。PR にはシリアル検出ログと API 送信ログを添付。  
3. **mirrorctl / 14 日監視の仕様洗い出し**  
   - 旧 OnSiteLogistics の `docs/handheld-reader.md` / `docs/mirrorctl.md` 等をレビューし、移植対象と工数を一覧化。  
   - 結果を本ファイルおよび `docs/system/pi-zero-integration.md` に反映し、Phase-2 の TODO を固める。

## メモ
- 進捗・課題は本ファイルで集約管理し、別ドキュメントへの分散を避ける。  
- 実機検証が完了したら、その結果と残課題を `docs/test-notes/` へ記録し、本ファイルにもステータスを反映させる。
