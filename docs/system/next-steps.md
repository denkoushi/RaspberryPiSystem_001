# 開発ロードマップ（ドラフト）

モジュールごとの今後の作業を整理する。進捗に応じて更新すること。

## 状況ダッシュボード（2025-11-10 午前時点）

| 区分 | ステータス | タスク概要 | 対応ファイル/備考 |
| --- | --- | --- | --- |
| コード実装 | 完了 | `/api/v1/scans` の DB upsert（`scan_ingest_backlog`→`part_locations`）の実装とテスト拡充 | server/src/raspberrypiserver/services/backlog.py, tests/test_backlog_service.py, tests/test_repositories.py（pytest + 実DB検証済み） |
| コード実装 | 完了 | BacklogDrainService のロギング強化・異常系テスト整備 | server/src/raspberrypiserver/services/backlog.py, tests/test_backlog_service.py |
| コード実装 | 進行中 | Socket.IO 運用仕様（設定・ログ・再接続テスト）の確定 | server/src/raspberrypiserver/app.py, server/tests/test_api_scans.py, server/config/default.toml, docs/system/documentviewer-integration.md |
| コード実装 | 停滞 | Pi Zero mirrorctl 連携スクリプト移行（再送キュー、14 日監視） | docs/system/pi-zero-integration.md, handheld/scripts/** |
| コード実装 | 完了 | 手動スモーク用 `scripts/smoke_scan.sh` 作成とテスト追加 | server/scripts/smoke_scan.sh, tests/test_broadcast_service.py |
| 実機検証 | 進行中 | Pi Zero → Pi5 → Window A 統合テスト（Pi Zero シリアル復旧済み、Pi5 API 応答あり。旧キューに `scan_id=None` が残存） | docs/test-notes/2025-11/pi-zero-test-plan.md, docs/system/pi-zero-integration.md |
| 体制整備 | 進行中 | すべてのデバイスで `~/RaspberryPiSystem_001` のワークツリーを使用する（tools01 側は移行済み。Pi5 = `/srv/RaspberryPiSystem_001` へ統一済み。Pi4/Zero は legacy ディレクトリが残り、systemd 側が旧パスのまま） | docs/system/repo-structure-plan.md:1-41, AGENTS.md:21-35 |
| 実機検証 | 進行中 | DocumentViewer / Window A Socket.IO 実機テスト (Window A psycopg3 反映と Pi4 venv 再構築を完了してから実施) | docs/test-notes/2025-11/window-a-socket-plan.md, docs/test-notes/2025-11/window-a-demo.md, window_a/** |
| 体制整備 | 進行中 | Pi4 (Window A) を `~/RaspberryPiSystem_001` ベースに刷新し、旧 `~/tool-management-system02` は `*_legacy_` へ退避する（systemd 停止→clone→venv 再構築→toolmgmt.service 差し替え。USB/station_config/api_token_store/raspi_client のスタブと `config/window-a.env` を旧リポジトリから移管） | docs/system/repo-structure-plan.md:30-72, docs/test-notes/2025-11/window-a-demo.md |
| 体制整備 | 進行中 | Pi5/Pi4/Pi Zero のホスト名・systemd・ログ出力をすべて `RaspberryPiSystem_001` へ名寄せ（hostname + `/etc/hosts` + PS1、WorkingDirectory/ExecStart、`/srv|~/RaspberryPiSystem_001/**/logs`。Pi5 は `server/src/raspberrypiserver/app.py` フォールバック＋ `/srv/.../logs/app.log` 出力を 2025-11-11 に確認済み） | docs/system/repo-structure-plan.md:42-66, server/config/default.toml:1-22 |
| 実機検証 | 完了 | ローカル Docker + PostgreSQL での drain → `part_locations` 反映 | docs/test-notes/2025-11/window-a-demo.md |
| ドキュメント更新 | 進行中 | 方針・進捗トラッカー（本ファイル＋ Pi Zero 手順の更新） | 本ファイル, docs/system/pi-zero-integration.md |
| ドキュメント更新 | 新規 | Window A psycopg3 移行手順と既知課題の記録 | docs/test-notes/2025-11/window-a-demo.md |
| ドキュメント更新 | 完了 | スモーク手順・イベントペイロードの整備 | server/README.md, docs/system/documentviewer-integration.md |
| 体制整備 | 新規 | DocumentViewer ログディレクトリ（`/var/log/document-viewer`）の自動整備手順を追加し、環境構築時に権限不足でログが書けなくなる再発を防ぐ | docs/system/documentviewer-integration.md, docs/test-notes/2025-11/window-a-demo.md |
| 体制整備 | 完了 | DocumentViewer のコードを本リポジトリ（`document_viewer/` ディレクトリ）へ移設し、Pi4 の systemd も `~/RaspberryPiSystem_001` を参照するように切り替える（2025-11-12 Pi4 実機反映済） | docs/system/documentviewer-integration.md, docs/system/repo-structure-plan.md, docs/test-notes/2025-11/window-a-demo.md |

## 直近マイルストーンとサブブランチ方針

| マイルストーン | 目的 | 推奨ブランチ | ゴール | 備考 |
| --- | --- | --- | --- | --- |
| Handheld Migration Phase-1 | 旧ハンディの Serial/HID 切替と電子ペーパーの完全復旧 | `feature/handheld-migration-p1`（現 `feature/repo-structure-plan` から派生） | Pi Zero で `[SERIAL] scanner ready` を安定表示し、Pi5 復旧後すぐに API 通信が通る状態 | PR には `handheld.log` と `journalctl` の最新ログを添付 |
| Handheld Migration Phase-2 | mirrorctl / 14 日監視、LED/ボタン I/O を移植 | `feature/handheld-migration-p2` | `mirrorctl` 連携スクリプトを新リポジトリで再実装し、旧 OnSiteLogistics リポジトリへの依存を解消 | Phase-1 完了後に開始 |
| Repo Unification Pi5 | Pi5 側のディレクトリ／systemd を刷新 | `feature/pi5-repo-sync` | `/srv/RaspberryPiSystem_001` 配下で一元化し、`raspberrypiserver.service` の WorkingDirectory を更新 | Pi5 停止時間の調整が必要 |

各マイルストーンでブランチを分け、main へマージ→Pi へデプロイの流れを固定する。必要に応じて PR テンプレートに「対象マイルストーン」「必要ログ」を明記する。

### Handheld Migration Phase-1 ブランチ準備チェックリスト
1. `feature/repo-structure-plan` 上の差分を棚卸しし、`handheld/scripts/**`・`docs/system/**`・`docs/test-notes/2025-11/pi-zero-test-plan.md` が Phase-1 の対象であることを明確にする。  
2. Pi Zero 実機ログを収集し、以下の 2 点を PR 添付用に保管する。  
   - `sudo journalctl -u handheld@tools01.service -n 80 --since "2025-11-10 08:20"`（A/B スキャン完了と `[SERIAL] scanner ready` を含む）  
   - `/home/tools01/.onsitelogistics/logs/handheld.log` の 2025-11-10 08:26 JST 付近の抜粋（`Server accepted payload` 連続記録）  
3. `sqlite3 ~/.onsitelogistics/scan_queue.db 'SELECT COUNT(*) FROM scan_queue;'` の結果が 0 であるスクリーンショット／ログを添付し、旧データが残っていないことを証明する。  
   - 2025-11-10 09:02 JST に ID 4/5 を削除し 0 件を確認済み。今後も `SELECT id, payload FROM scan_queue;` → `DELETE ...` → `SELECT COUNT(*)` の流れを残し、Pending=0 の証跡を添付する。  
4. `docs/system/pi-zero-integration.md` と `docs/test-notes/2025-11/pi-zero-test-plan.md` に本日の結果を反映したうえで、`git switch -c feature/handheld-migration-p1` を実行し、Phase-1 ブランチで PR を作成する。  
5. PR 説明欄には「Mac → GitHub → tools01 同期フロー」「Pi Zero 実機確認ログ」「scan_queue 空確認」の 3 点を添付し、レビュー時の確認工数を下げる。

#### 推奨ログ取得コマンド
```bash
# Pi Zero (tools01) のサービスログ 80 行
sudo journalctl -u handheld@tools01.service -n 80 --since "2025-11-10 08:20"

# Pi Zero handheld.log (末尾 100 行)
sudo -u tools01 -H bash -lc '
  tail -n 100 /home/tools01/.onsitelogistics/logs/handheld.log
'

# queue の件数確認
sudo -u tools01 -H sqlite3 /home/tools01/.onsitelogistics/scan_queue.db \
  "SELECT COUNT(*) FROM scan_queue;"

# queue ゼロ化後に drain-only で再送（UI 初期化不要な場合は HANDHELD_HEADLESS=1）
sudo -u tools01 -H bash -lc '
  source ~/.venv-handheld/bin/activate
  HANDHELD_HEADLESS=1 python /home/tools01/RaspberryPiSystem_001/handheld/scripts/handheld_scan_display.py --drain-only
'
```

## 旧 OnSiteLogistics → 新リポジトリ移植状況

| 領域 | 現状 | 取りこぼし / リスク | 推定対応時間 | 備考 |
| --- | --- | --- | --- | --- |
| ハンディ本体（handheld_scan_display.py） | シリアル検出・再送キューは移植済み。Pi Zero では 2025-11-09 21:08 JST に A/B 完走を確認。 | Pi5 API が落ちているため end-to-end 送信確認が未完。`mirrorctl` 連携や LED/ボタン GPIO は未移植。 | 0.5 日（Pi5 復旧＋drain-only＋ログ採取）、+1 日（mirrorctl/GPIO 移植） | `docs/test-notes/2025-11/pi-zero-test-plan.md` にログ追記予定 |
| Pi Zero デプロイ経路 | `update_handheld_override.sh` に tools01 同期を実装し、VS Code → GitHub → tools01 で整合が取れる状態 | `tools01` ディレクトリに手入力した設定ファイルは `reset --hard` で消えるため、除外リスト/別管理場所を整理する必要あり。 | 0.5 日 | `docs/system/pi-zero-integration.md` へ保護すべきファイル一覧を追加する |
| Pi5 サーバー | 統一済み | `/srv/RaspberryPiSystem_001` で venv ＋ systemd 運用に移行済み（/healthz 応答 OK）。旧 `/srv/rpi-server` は参照専用。 | - | `docs/system/repo-structure-plan.md` Milestone3 完了 |
| DocumentViewer / Window A | 旧リポジトリを参照のみで維持 | 新リポジトリへ統合するか、境界をどこに置くか未決。 | 要検討 | AGENTS.md で「参照のみ可」を明確化する |

## ここまでの状況サマリ（2025-11-10 午前）
- Pi Zero: 08:25 JST の再起動後も `[SERIAL] forcing /dev/minjcode0 @ 115200bps` → `[SERIAL] scanner ready` が安定。A/B スキャン（4989999058963, https://e.bambulab...）で電子ペーパー更新を確認。  
- Pi5: 08:26 JST に `Server accepted payload` が連続で出力され、API が復旧。旧バージョンで生成した `scan_id=None` のキューのみ 400 で残っている。  
- 体制: tools01 リポジトリ強制同期は動作中。残課題は (1) キュー残骸の処理、(2) Handheld Migration Phase-1 ブランチの確立、(3) mirrorctl / Pi5 再統一の段取り決め。

## 今後 1 週間の優先タスク（提案）
1. **scan_queue 残骸の整理**  
   - Pi Zero で `sqlite3 ~/.onsitelogistics/scan_queue.db 'SELECT id,payload FROM scan_queue;'` を実行し、`scan_id` が `None` の行を確認。  
   - 対象行を削除もしくは JSON を補正したうえで `sudo -u tools01 -H bash -lc "source ~/.venv-handheld/bin/activate && python handheld/scripts/handheld_scan_display.py --drain-only"` を実行し、キューを空にする。
2. **Handheld Migration Phase-1 ブランチの確立**  
   - 現在の `feature/repo-structure-plan` の差分を棚卸しし、マイルストーン専用ブランチへ整理。PR にはシリアル検出ログと API 送信ログを添付。  
3. **Pi5 統合後の確認タスク**  
   - `/srv/RaspberryPiSystem_001` で `.venv/bin/python` の稼働を継続監視し、`curl http://localhost:8501/healthz` の結果と `raspi-server.service` ログをテストノートへ記録。  
4. **Window A 依存更新 → Soket.IO 実機テスト**  
   - Pi4 のワークツリーを `~/RaspberryPiSystem_001` へ移設し、`window_a/` サブディレクトリを本リポジトリの内容で構築する（旧 `~/tool-management-system02` は `*_legacy_` へ退避）。  
   - `window_a/requirements.txt` / `app_flask.py` / `tests/test_load_plan.py` をコミット→push したあと、Pi4 で `git pull` → venv 再構築 (`python3 -m venv .venv && source .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt && pytest`) を実施し、`pip show psycopg` と pytest 成功ログを `docs/test-notes/2025-11/window-a-demo.md` へ追記。  
   - Pi5 / Pi Zero でも同様に `pip show psycopg` と `pytest`（handheld は `pytest handheld/tests`）を実行し、3 台とも 3.2.x 系で揃っているログを収集。  
   - 3 台の整合を確認したら `docs/test-notes/2025-11/window-a-socket-plan.md` の手順で Pi Zero → Pi5 → Window A → DocumentViewer の Socket.IO e2e を実施する。  
5. **mirrorctl / 14 日監視の仕様洗い出し**  
   - 旧 OnSiteLogistics の `docs/handheld-reader.md` / `docs/mirrorctl.md` 等をレビューし、移植対象と工数を一覧化。  
   - 結果を本ファイルおよび `docs/system/pi-zero-integration.md` に反映し、Phase-2 の TODO を固める。

## メモ
- 進捗・課題は本ファイルで集約管理し、別ドキュメントへの分散を避ける。  
- 実機検証が完了したら、その結果と残課題を `docs/test-notes/` へ記録し、本ファイルにもステータスを反映させる。
