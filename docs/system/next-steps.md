# 開発ロードマップ（ドラフト）

モジュールごとの今後の作業を整理する。進捗に応じて更新すること。

## 状況ダッシュボード（2025-11-10 午前時点）

| 区分 | ステータス | タスク概要 | 対応ファイル/備考 |
| --- | --- | --- | --- |
| コード実装 | 完了 | `/api/v1/scans` の DB upsert（`scan_ingest_backlog`→`part_locations`）の実装とテスト拡充 | server/src/raspberrypiserver/services/backlog.py, tests/test_backlog_service.py, tests/test_repositories.py（pytest + 実DB検証済み） |
| コード実装 | 完了 | BacklogDrainService のロギング強化・異常系テスト整備 | server/src/raspberrypiserver/services/backlog.py, tests/test_backlog_service.py |
| コード実装 | 進行中 | Socket.IO 運用仕様（設定・ログ・再接続テスト）の確定 | server/src/raspberrypiserver/app.py, server/tests/test_api_scans.py, server/config/default.toml, docs/system/documentviewer-integration.md |
| 実機検証 | 進行中 | Pi Zero mirrorctl 連携：`mirrorctl@tools01.service` を常駐させ、バーコード A/B → Pi5 → Window A の e2e を再確認する。電子ペーパー表示や drain-only、HEADLESS モードなど旧システム要件を `docs/system/window-a-toolmgmt.md` に反映。 | docs/system/pi-zero-integration.md, docs/test-notes/2025-11/pi-zero-test-plan.md, docs/system/window-a-toolmgmt.md |
| コード実装 | 完了 | 手動スモーク用 `scripts/smoke_scan.sh` 作成とテスト追加 | server/scripts/smoke_scan.sh, tests/test_broadcast_service.py |
| 実機検証 | 進行中 | Pi Zero → Pi5 → Window A 統合テスト（2025-11-14 10:36 Pi Zero 実機＋Window A ブラウザ常時起動で `client.log` に Socket.IO イベントが記録されることを確認。今後はブラウザ起動手順を忘れず実施） | docs/test-notes/2025-11/pi-zero-test-plan.md, docs/system/pi-zero-integration.md, docs/test-notes/2025-11/window-a-demo.md |
| 実機検証 | 解消 | Pi4 ↔ Pi5 の PostgreSQL 接続は `docs/system/window-a-toolmgmt.md` 12章のチェックリストで復旧済み。`window_a/config/window-a.env` 更新＋ `toolmgmt.service` 再起動手順を `docs/test-notes/2025-11/window-a-demo.md` へ記録し、今後は LAN 切替え時に /etc/hosts または `DATABASE_URL` を更新する。 | docs/test-notes/2025-11/window-a-demo.md, window_a/scripts/check_db_connection.py, docs/system/postgresql-setup.md |
| 実機検証 | 進行中 | Window A Dashboard の DocumentViewer/Socket 表示を定常化する。`DOCUMENT_VIEWER_URL=http://127.0.0.1:5000` を設定し、USB バーコードで PDF 切替が動作するか `docs/test-notes/2025-11/window-a-demo.md` にログを残す（2025-11-14 14:25 から監視開始、2025-11-15 16:40 確認済み）。 | window_a/config/window-a.env, document_viewer/README.md, docs/test-notes/2025-11/window-a-demo.md |
| コード実装 | 進行中 | Window A Dashboard の工具管理ペインを Pi5 REST API ベースに刷新。TM-DIST → importer → Dashboard → Pi5 `/api/v1/loans` 連携に加え、NFC からの貸出登録（利用者→工具）も実装済み。今後は本番 CSV／DocumentViewer USB／Pi4 NFC／tools01 ハンディ実装を本番データで検証し、UI 文言（成功時表示など）を整える。 | window_a/app_flask.py, window_a/templates/index.html, docs/system/window-a-toolmgmt.md, server/src/raspberrypiserver/api/tool_management.py |
| コード実装 | 進行中 | Pi5 `/api/v1/part-locations` / `/api/logistics/jobs` のデータ源を DB 化し、Window A Dashboard に実データを表示させる。`SCAN_REPOSITORY_BACKEND="db"` + `AUTO_DRAIN_ON_INGEST=1` の流れは確認済み。`server/config/logistics-jobs.sample.json` / `production-plan.sample.json` を `docs/system/window-a-toolmgmt.md` 13章の手順で TM-DIST と併用すればサンプル表示は可能なので、次は実運用データ（PostgreSQL 連携など）へ置き換える。 | server/config/local.toml, server/src/raspberrypiserver/**, docs/system/postgresql-setup.md |
| コード実装 | 進行中 | Pi5 `/api/v1/production-plan` / `/api/v1/standard-times` のモック実装を追加済み（JSON ファイル or DB テーブル `production_plan_entries` / `standard_time_entries` を選択可）。`server/scripts/seed_plan_tables.py` で DB を初期化できる。今後は実データ API へ接続し、Window A Dashboard に本番値を表示させる。 | server/src/raspberrypiserver/api/production.py, server/config/production-plan.sample.json, server/config/standard-times.sample.json, server/config/schema.sql |
| 体制整備 | 進行中 | すべてのデバイスで `~/RaspberryPiSystem_001` のワークツリーを使用する（tools01 側は移行済み。Pi5 = `/srv/RaspberryPiSystem_001` へ統一済み。Pi4/Zero は legacy ディレクトリが残り、systemd 側が旧パスのまま） | docs/system/repo-structure-plan.md:1-41, AGENTS.md:21-35 |
| 実機検証 | 進行中 | DocumentViewer / Window A Socket.IO 実機テスト (Pi5 `send_scan.py` および Pi Zero `send_scan_headless.py` で e2e 確認済み。次は Pi Zero 実機 UI/GPIO 版で最終確認) | docs/test-notes/2025-11/window-a-socket-plan.md, docs/test-notes/2025-11/window-a-demo.md, window_a/** |
| 体制整備 | 進行中 | Pi4 (Window A) を `~/RaspberryPiSystem_001` ベースに刷新し、旧 `~/tool-management-system02` は `*_legacy_` へ退避する（systemd 停止→clone→venv 再構築→toolmgmt.service 差し替え。USB/station_config/api_token_store/raspi_client のスタブと `config/window-a.env` を旧リポジトリから移管。2025-11-14 に `window_a/README.md` を作成済みで、tools02 での clone/venv/systemd 手順を統一済み） | docs/system/repo-structure-plan.md:30-72, window_a/README.md, docs/test-notes/2025-11/window-a-demo.md |
| 体制整備 | 進行中 | Pi5/Pi4/Pi Zero のホスト名・systemd・ログ出力をすべて `RaspberryPiSystem_001` へ名寄せ（hostname + `/etc/hosts` + PS1、WorkingDirectory/ExecStart、`/srv|~/RaspberryPiSystem_001/**/logs`。Pi5 は `server/src/raspberrypiserver/app.py` フォールバック＋ `/srv/.../logs/app.log` 出力を 2025-11-11 に確認済み） | docs/system/repo-structure-plan.md:42-66, server/config/default.toml:1-22 |
| 実機検証 | 完了 | ローカル Docker + PostgreSQL での drain → `part_locations` 反映 | docs/test-notes/2025-11/window-a-demo.md |
| ドキュメント更新 | 進行中 | 方針・進捗トラッカー（本ファイル＋ Pi Zero 手順の更新） | 本ファイル, docs/system/pi-zero-integration.md |
| ドキュメント更新 | 新規 | Window A psycopg3 移行手順と既知課題の記録 | docs/test-notes/2025-11/window-a-demo.md |
| ドキュメント更新 | 完了 | スモーク手順・イベントペイロードの整備 | server/README.md, docs/system/documentviewer-integration.md |
| 体制整備 | 完了 | DocumentViewer ログディレクトリ（`/var/log/document-viewer`）の自動整備手順を `scripts/setup_docviewer_env.sh` 解説付きで追記し、環境構築時に権限不足でログが書けなくなる再発を防ぐ | docs/system/documentviewer-integration.md, docs/test-notes/2025-11/window-a-demo.md |
| 体制整備 | 完了 | DocumentViewer のコードを本リポジトリ（`document_viewer/` ディレクトリ）へ移設し、Pi4 の systemd も `~/RaspberryPiSystem_001` を参照するように切り替える（2025-11-12 Pi4 実機反映済） | docs/system/documentviewer-integration.md, docs/system/repo-structure-plan.md, docs/test-notes/2025-11/window-a-demo.md |
| コード実装 | 完了 | Pi5 側 USB 処理 (`tool-ingest-sync.sh`, `tool-dist-export.sh`, `tool-backup-export.sh`) と共通ライブラリ `lib/toolmaster-usb.sh` を `~/RaspberryPiSystem_001/scripts/server/` へ移植し、`/srv/RaspberryPiSystem_001/toolmaster` を標準データルートとするよう更新（systemd/udev + `/usr/local/bin` 配置 + `/usr/local/scripts/update_plan_cache.py` スキップ対応まで実機で確認済み）。 | /Users/tsudatakashi/RaspberryPiServer/docs/usb-operations.md, /Users/tsudatakashi/RaspberryPiServer/scripts/** |
| コード実装 | 完了 | 端末側 `tool-dist-sync.sh` と DocumentViewer `document-importer.service` を連携させ、Pi4(Window A) でも USB を挿すだけで `master/` / `docviewer/` 同期→DocumentViewer 反映まで自動化（`install_usb_services.sh --mode client-dist`＋ `RUN_IMPORTER_AFTER_SYNC` で importer を直接呼び出す） | scripts/server/toolmaster/install_usb_services.sh, scripts/server/toolmaster/tool-dist-sync.sh, docs/test-notes/2025-11/window-a-demo.md |
| 体制整備 | 進行中 | Shell script lint を標準化し、`scripts/dev/run_shellcheck.sh`（Docker fallback 付き）で `toolmaster` 系スクリプトを常時検証できるようにする（Pi5/mac の双方で lint 済み。今後もリポジトリ更新後に実行する）。 | scripts/dev/run_shellcheck.sh |

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
| Pi5 サーバー | 統一済み | `/srv/RaspberryPiSystem_001` で venv ＋ systemd 運用に移行済み（/healthz 応答 OK）。`server/README.md` に clone/venv/systemd/`git pull` の手順を追記済み。旧 `/srv/rpi-server` は参照専用。 | - | `docs/system/repo-structure-plan.md` Milestone3 完了, server/README.md |
| DocumentViewer / Window A | 旧リポジトリを参照のみで維持 | 新リポジトリへ統合するか、境界をどこに置くか未決。 | 要検討 | AGENTS.md で「参照のみ可」を明確化する |

### Window A 工具管理ペイン再構築タスク
- **データソースの棚卸し**  
  - TM-DIST USB から Pi4 へ同期された `~/RaspberryPiSystem_001/window_a/master/` の CSV 群（ユーザー・工具定義・貸出履歴など）を確認し、旧 OnSiteLogistics（`/Users/tsudatakashi/OnSiteLogistics/docs/handheld-reader.md` 等）と突き合わせてカラム仕様を文書化する。  
  - 仕様書は `docs/system/window-a-toolmgmt.md` に集約し、`tool-dist-sync.sh` が参照するローカルディレクトリとファイル名を一覧化する。  
- **インポートサービスの整備**  
  - `window_a/app_flask.py` には `tool_master`/`tools`/`users`/`loans` テーブルを初期化するロジックが存在する。`window_a/scripts/import_tool_master.py` を `tool-dist-sync.sh` に統合したので、`install_usb_services.sh --mode client-dist` を適用すると TM-DIST 同期後に自動で PostgreSQL が更新される。  
  - インポート処理では CSV の更新時刻を保持し、UI 側でも「同期日時」や不整合を表示できるように `api_actions.log` と同様に記録する。  
- **UI/表示要件**  
  - Dashboard の「工具管理」セクションで以下を表示する: (1) 同期済み CSV の更新日時と件数サマリ、(2) 貸出中リスト（工具名・借用者・貸出日時）、(3) 直近の貸出/返却履歴、(4) 手動操作（貸出記録の強制完了・削除）ボタン。  
  - Pi5 側に `/api/v1/loans`（互換 `/api/loans`）と手動返却・削除 API を実装済み。Window A の工具管理ビューも REST に切り替え済みで、`docs/system/window-a-toolmgmt.md` に仕様とルーティングを整理した。  
  - UI 側では Socket.IO を使って貸出状況を push する必要はないが、API 認証 (`API_TOKEN_ENFORCE`) を通じて操作ログを `api_actions.log` に残す。  
- **Pi5 / Pi4 実機確認タスク**  
  - Pi5: `config/local.toml` の `[tool_management]` を `enabled=true` + DSN 指定で有効化し、`sudo systemctl restart raspi-server.service` → `curl http://<Pi5>:8501/api/v1/loans` でレスポンスを確認する。  
  - Pi4(Window A): `scripts/server/toolmaster/install_usb_services.sh --mode client-dist` で USB サービスを再適用し、TM-DIST USB → `tool-dist-sync.sh` → `window_a/scripts/import_tool_master.py` の自動実行と `toolmgmt.service` の再起動を確認。Dashboard の工具管理カードと `docs/test-notes/2025-11/window-a-demo.md` に結果を追記する。  
- **運用導線**  
  - `window_a/README.md` に追記した `git pull` / `.venv` 手順に続き、工具管理ペインを更新するときのチェックリスト（CSV の場所確認、DB マイグレーション、`toolmgmt.service` 再起動、ブラウザでの確認）を `docs/test-notes/2025-11/window-a-demo.md` へテンプレート化する。  
  - Pi Zero スキャン結果から Pi5 `/api/v1/scans` → part_locations → Window A 表示までの導線も合わせて記録し、工具貸出 UI と所在 UI の両方を同じダッシュボードから確認できるようにする。

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
