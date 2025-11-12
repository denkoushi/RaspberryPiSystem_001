# 手動テストハンドブック（ドラフト）

本ドキュメントは RaspberryPiSystem_001 の手動テスト資産として、機能間の連携や高難度フローを検証する際のガイドラインとチェックリストをまとめる。自動テスト環境は再構築しない方針のため、ここで定義したシナリオが品質確認の基盤となる。

## テスト設計の原則
- Pi Zero → Pi5 → Window A / DocumentViewer へ至るフローなど、開発難易度の高い機能から優先的に手順化する。
- テストはモジュール単位に切り分け、再利用可能な前提条件・入力データ・期待結果を明記する。
- 実施ログ（日時・担当者・結果）は今後の保守と調査に役立つよう、`docs/test-notes/` 配下へ記録する。

## 連携ドキュメント
- アーキテクチャ概要: `docs/architecture.md`
- Pi5 API/運用詳細（参照元）: 旧 RaspberryPiServer リポジトリ `docs/api-plan.md`, `docs/mirror-verification.md`, `docs/usb-operations.md`
- Window A クライアント運用: 旧 tool-management-system02 リポジトリ `RUNBOOK.md`
- DocumentViewer 運用: 旧 DocumentViewer リポジトリ `docs/setup-raspberrypi.md`
- ハンディ端末運用: 旧 OnSiteLogistics リポジトリ `docs/handheld-reader.md`
- テスト記録テンプレート: `docs/test-notes/`（`README.md` と `templates/` を参照）

## 2. USB メモリ運用チェック（INGEST / DIST / BACKUP）
- 参照元
  - `/Users/tsudatakashi/RaspberryPiServer/docs/usb-operations.md:1-130`（USB ラベル・役割・`/.toolmaster/role`）
  - `/Users/tsudatakashi/DocumentViewer/docs/setup-raspberrypi.md:119-134`（`TOOLMASTER/master` / `docviewer` のディレクトリ構成）

### 目的
- USB 3 本（`TM-INGEST`, `TM-DIST`, `TM-BACKUP`）が正しいラベルとシグネチャファイルを持ち、想定されたフォルダ構成（`master/*.csv`, `docviewer/*.pdf + meta.json` など）が維持されていることを確認する。
- DocumentViewer / Window A / Pi5 のスクリプト（`tool-ingest-sync.sh`, `tool-dist-sync.sh`, `document-importer.sh` 等）が同じ USB 構成を前提に正しく動作することを担保する。

### 事前条件
- Pi5 には旧仕様と同等の USB スクリプトが配置されている（例: `/usr/local/bin/tool-dist-export.sh`）。
- Pi4 (Window A / DocumentViewer) には `tool-dist-sync.sh`, `document-importer.sh` が `/usr/local/bin` に配置され、`document-importer.service` が稼働している。
- `/etc/sudoers.d/document-viewer` が設定されており、DocumentViewer の再起動がパスワード無しで実行できる。

### 手順
1. **USB ラベルとシグネチャの確認**
   ```bash
   sudo blkid | grep TM-
   sudo cat /media/TM-INGEST/.toolmaster/role
   sudo cat /media/TM-DIST/.toolmaster/role
   sudo cat /media/TM-BACKUP/.toolmaster/role
   ```
   - `TM-INGEST` → `INGEST`、`TM-DIST` → `DIST`、`TM-BACKUP` → `BACKUP` であることを確認。異なる場合は処理を中断する。
2. **ディレクトリ構成の検証**
   ```bash
   tree -L 2 /media/TM-INGEST/TOOLMASTER
   tree -L 2 /media/TM-DIST/TOOLMASTER
   ```
   - `master/*.csv` と `docviewer/meta.json` `docviewer/*.pdf` 以外のファイルが無いか確認する。DocumentViewer 取り込みは `docviewer/` のみを対象にする。
3. **Pi5 での INGEST / DIST エクスポート**
   ```bash
   sudo /usr/local/bin/tool-ingest-sync.sh --refresh
   sudo /usr/local/bin/tool-dist-export.sh --target /media/TM-DIST
   sudo /usr/local/bin/tool-backup-export.sh --target /media/TM-BACKUP
   ```
   - ログ: `/srv/RaspberryPiSystem_001/server/logs/usb_ingest.log`, `/srv/RaspberryPiSystem_001/server/logs/usb_dist_export.log`, `/srv/RaspberryPiSystem_001/server/logs/backup.log`（旧 `/srv/rpi-server/logs/*`。参照: `/Users/tsudatakashi/RaspberryPiServer/docs/usb-operations.md:1-160`）を確認し、エラーが無いことを記録する。
4. **Pi4 での DIST 受信と DocumentViewer 反映**
   ```bash
   sudo /usr/local/bin/tool-dist-sync.sh --device /dev/sdX
   sudo mount --bind /media/tools02/TMP-USB /media/tool-dist-test  # ループバック試験時
   sudo journalctl -u document-importer.service --since "1 minute ago" --no-pager
   sudo tail -n 10 /var/log/document-viewer/import.log
   ```
   - `INFO copied …` と `INFO restarted document-viewer.service` が出力されることを確認。必要に応じて Window A 側のログ (`/var/log/tool-dist-sync.log`) も併せて記録する。
5. **テストログへの記録**
   - `docs/test-notes/templates/usb-flow.md` をコピーし、実施日・USB ラベル・結果（○/×）を記録する。異常があった場合は該当 USB を隔離し、マニュアル（旧 RaspberryPiServer RUNBOOK）に従って再作成する。

### 成功判定
- 3 本すべてでラベル・シグネチャ・フォルダ構成が一致し、Pi5 側スクリプトと Pi4 側 importer がエラーなく完了すること。
- DocumentViewer で `docviewer/` に入れた PDF が表示されること、Window A の工具管理 UI が `master/` CSV を取り込めることを確認し、ログをスクリーンショットや `docs/test-notes/YYYY-MM-DD-*.md` へ添付する。

### フォローアップ
- ラベルや構成が異なる USB が見つかった場合は 旧 RaspberryPiServer リポジトリの `/Users/tsudatakashi/RaspberryPiServer/scripts/setup_usb_tests.sh` を参考に再フォーマットし、再発防止として RUNBOOK へ記録する。
- Window A / DocumentViewer の importer が対応していないデータ種別（標準工数や生産日程 CSV）については、対応する同期スクリプトを `~/RaspberryPiSystem_001` へ移植し、それぞれのテストケースを本ハンドブックへ追記する。

## 1. ハンディ送信フロー（Pi Zero → Pi5 → クライアント）

### 目的
- Pi Zero で読み取ったスキャンが RaspberryPiServer（Pi5）に到達し、Window A と DocumentViewer の UI に反映されることを確認する。

### 前提条件
- Pi Zero の `onsitelogistics` サービスが起動し、`mirror_mode=true` で設定済み。
- Pi5 の REST API が `/api/v1/scans` を受け付ける状態で稼働している（`order_code` / `location_code` が必須、空文字は 400）。
- `/api/v1/part-locations` が動作し、Window A の REST フォールバックで利用できる。
- Window A クライアントおよび DocumentViewer が Pi5 の Socket.IO / REST を参照する設定になっている。
- macOS などでローカル動作を確認する際は、クライアント（`scripts/listen_for_scans.ts` 等）の接続先を `http://127.0.0.1:8501` に指定する（`localhost` は IPv6(::1) を指すため接続に失敗する場合がある）。
- `/api/v1/scans` の疎通チェックは `client_window_a/scripts/send_scan.py` を利用すると CLI から実行しやすい。`--order` / `--location` / `--device` を指定でき、省略時はタイムスタンプ由来の値が自動生成される。`--dry-run` で送信せず確認のみも可能。
- 簡易スモークについては `server/scripts/smoke_scan.sh` を実行すると、サーバー起動・送信・停止まで自動化できる（詳細検証が必要な場合は手順を個別に実行する）。
- 共通 Bearer トークンが Pi Zero / Pi5 / Window A / DocumentViewer で一致している。
- テスト用移動票（例: `ORDER-CODE=TEST-001`, `LOCATION=RACK-A1`）が準備され、DocumentViewer で該当 PDF を表示できる。
- Pi5・Window A・DocumentViewer のログ参照コマンドが実行できる権限を持つ。

### 事前確認
- Pi Zero: `sudo mirrorctl status` → `mirror_mode=true`、`Next run` が未来時刻。
  - Pi5: `curl -I http://127.0.0.1:8501/healthz` が `200 OK`。
- Window A: ステータスバー等で接続状態が「LIVE」であること。
- DocumentViewer: `/viewer` を開きロードエラーが無いこと、環境変数が Pi5 を指すこと。

### 手順
1. **ハンディでスキャン実行**  
   - 移動票バーコード → 棚バーコードの順に読み取る。成功表示・音を確認しメモする。
2. **Pi Zero 送信ログ確認**  
   ```bash
   sudo journalctl -u handheld@tools01.service -n 30 --no-pager
   ```  
   - `status=delivered` 等が出力され、`scan_id` / `order_code` / `location_code` を記録。
   - 併せて `sudo ./scripts/check_connection.sh --last` で直近送信結果を取得しても良い。
3. **Pi5 受信ログ確認**  
   ```bash
  sudo tail -n 10 /srv/RaspberryPiSystem_001/server/logs/mirror_requests.log
  sudo tail -n 10 /srv/RaspberryPiSystem_001/server/logs/api_actions.log
   ```  
   - 同一 `scan_id` と `HTTP 200` が記録されているか確認。  
   - `journalctl -u raspi-server.service -n 50` でエラーがないか確認。
4. **データベース反映確認**  
   - `SCAN_REPOSITORY_BACKEND` が `memory` の場合は `scan_ingest_backlog` ではなくアプリの内部バッファで確認する。  
- `db` を利用する場合は以下のように PostgreSQL テーブル（例: `scan_ingest_backlog`）を参照し、JSON ペイロードが登録されていることを確認する。  
  ```bash
  PGPASSWORD=app psql -h 127.0.0.1 -p 15432 -U app -d sensordb \
    -c "SELECT payload->>'order_code', payload->>'location_code', received_at FROM scan_ingest_backlog ORDER BY received_at DESC LIMIT 5;"
  ```
- バックログ処理後に `part_locations` へ反映される場合は、下記クエリで upsert 結果を確認する。  
   ```bash
   PGPASSWORD=app psql -h 127.0.0.1 -p 15432 -U app -d sensordb \
     -c "SELECT order_code, location_code, updated_at FROM part_locations ORDER BY updated_at DESC LIMIT 5;"
   ```
- バックログの滞留件数だけ確認したい場合は `GET /api/v1/admin/backlog-status` を利用できる（`pending` フィールドで件数を返す）。
5. **Window A UI 確認**  
   - 所在一覧で該当オーダーを検索し、リアルタイム更新または REST フォールバック（20 秒以内）で反映されるか目視する。  
   - 必要に応じ `journalctl -u toolmgmt.service -n 50` を確認。
6. **Socket.IO ブロードキャスト確認（任意）**  
   - Window A または別のクライアントで `scan.ingested`（既定）イベントを受信できるか確認。ローカル検証では IPv4 ループバックを利用し、下記のように接続する。  
     ```bash
     cd ~/RaspberryPiSystem_001/client_window_a
     npx ts-node scripts/listen_for_scans.ts --api http://127.0.0.1:8501
     ```
   - 同一ターミナルまたは別ターミナルで送信を試す場合は以下を利用する。  
     ```bash
     cd ~/RaspberryPiSystem_001
     source server/.venv/bin/activate
     python client_window_a/scripts/send_scan.py --order TEST-901 --location RACK-AZ --device HANDHELD-NOTE
     ```
     - 手動 `curl` 送信と同様に `order_code` / `location_code` が必須であることを確認する。
   - クライアントが別イベント名を期待する場合は `SOCKET_BROADCAST_EVENT` を合わせる。  
   - DocumentViewer で該当オーダーが自動表示される／検索で即時表示されるか確認。  
   - `/var/log/document-viewer/client.log` に `Document lookup success` が残ることを確認。
7. **証跡保存**  
   - ログ断片や UI スクリーンショットをまとめ、`docs/test-notes/<YYYY-MM-DD>-handheld-flow.md` に貼り付ける。
   - `drain_scan_backlog` を実行した場合は処理件数と対象時間帯をログに残す。

### 後片付け（備忘）
- Window A リスナー: `Ctrl+C` で停止（バックグラウンド起動した場合は `lsof -i :8501` で PID を確認して kill する）。
- Flask サーバー: フォアグラウンドなら `Ctrl+C`、バックグラウンド時は `lsof -i :8501` で PID を確認し `kill <PID>`。

### 期待結果
- 各ステップでエラーなしに進む。UI が最新状態を表示する。
- Pi Zero・Pi5・Window A・DocumentViewer のログと DB で同一 `scan_id` が確認できる。

### トラブルシュートメモ
- `status=queued` が続く場合 → ネットワーク / API トークン / `config.json` を確認。
- Pi5 で 401/403 → Bearer トークン不一致。`scripts/manage_api_token.py` で再発行。
- Window A が更新しない → Socket.IO 接続状態と REST フォールバック処理を確認。
- DocumentViewer が表示しない → `documents/` のファイル有無、USB 同期、ログを確認。
- 発生した事象は `docs/test-notes/` に追記し、次回再実施に備える。

## 2. USB 配布フロー（Pi5 → 端末）

### 目的
- Pi5 から `TM-DIST` USB を経由して Window A / DocumentViewer へ最新マスターデータ・PDF を配布できることを確認する。

### 前提条件
- `TM-DIST` USB が正しいシグネチャファイルを持ち、Pi5 で最新化されている。
- 端末側の `tool-dist-sync.sh` や DocumentViewer の USB 取り込みスクリプトが配置されている。

### 手順（概要）
1. Pi5 で `tool-dist-export.sh` を実行し、USB へ最新データを書き出す。
2. Window A や DocumentViewer 端末に USB を接続し、同期スクリプトが成功するかログを確認。
3. 同期後の端末でデータが更新されていることを確認する（UI 表示、ファイルタイムスタンプ等）。

### 期待結果
- USB 経由で必要なファイルが最新化され、端末側で新しい内容が反映される。

## 実機検証を開始する目安
- `/api/v1/scans` のサーバー側ロジックがテスト環境で DB 反映・イベント発火まで確認できたタイミング。
- Window A クライアントの Socket.IO 受信と REST フォールバックが新構成へ切り替わったタイミング。
- ハンディ送信モジュールが新 API に向けた送信テストをローカルで完了し、ログ上で 200 応答が取得できたタイミング。
- `docs/test-notes/templates/window-a-manual.md` を用いた手動テストが一巡し、想定どおり動作したタイミング。

上記のいずれかを満たした段階で、Pi Zero → Pi5 → Window A/DocumentViewer の統合テストを実機で実施する。

## 今後の拡張タスク
- 上記手順を具体的なコマンド、入力データ例、期待ログ出力まで詳細化する。
- DocumentViewer 単体テスト（PDF 検索・表示）、Window A ステータスバー操作、Pi5 API 直接確認などのシナリオを順次追加。
- チェックリスト形式（○/×）と差分メモ欄をテンプレート化し、運用時に流用できるよう整備する。
