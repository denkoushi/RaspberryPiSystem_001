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

## 1. ハンディ送信フロー（Pi Zero → Pi5 → クライアント）

### 目的
- Pi Zero で読み取ったスキャンが RaspberryPiServer（Pi5）に到達し、Window A と DocumentViewer の UI に反映されることを確認する。

### 前提条件
- Pi Zero の `onsitelogistics` サービスが起動し、`mirror_mode=true` で設定済み。
- Pi5 の REST API が `/api/v1/scans` を受け付ける状態で稼働している。
- Window A クライアントおよび DocumentViewer が Pi5 の Socket.IO / REST を参照する設定になっている。
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
   sudo tail -n 10 /srv/rpi-server/logs/mirror_requests.log
   sudo tail -n 10 /srv/rpi-server/logs/api_actions.log
   ```  
   - 同一 `scan_id` と `HTTP 200` が記録されているか確認。  
   - `journalctl -u raspi-server.service -n 50` でエラーがないか確認。
4. **データベース反映確認**  
   ```bash
   PGPASSWORD=app psql -h 127.0.0.1 -p 15432 -U app -d sensordb \
     -c "SELECT order_code, location_code, updated_at FROM part_locations ORDER BY updated_at DESC LIMIT 5;"
   ```  
   - 最新レコードが期待通りの `order_code` / `location_code` で更新されているかを見る。
5. **Window A UI 確認**  
   - 所在一覧で該当オーダーを検索し、リアルタイム更新または REST フォールバック（20 秒以内）で反映されるか目視する。  
   - 必要に応じ `journalctl -u toolmgmt.service -n 50` を確認。
6. **DocumentViewer 表示確認**  
   - DocumentViewer で該当オーダーが自動表示される／検索で即時表示されるか確認。  
   - `/var/log/document-viewer/client.log` に `Document lookup success` が残ることを確認。
7. **証跡保存**  
   - ログ断片や UI スクリーンショットをまとめ、`docs/test-notes/<YYYY-MM-DD>-handheld-flow.md` に貼り付ける。

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

## 今後の拡張タスク
- 上記手順を具体的なコマンド、入力データ例、期待ログ出力まで詳細化する。
- DocumentViewer 単体テスト（PDF 検索・表示）、Window A ステータスバー操作、Pi5 API 直接確認などのシナリオを順次追加。
- チェックリスト形式（○/×）と差分メモ欄をテンプレート化し、運用時に流用できるよう整備する。
