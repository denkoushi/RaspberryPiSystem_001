# DocumentViewer Socket.IO / REST 統合メモ（ドラフト）

Pi5 側の Socket.IO ブロードキャストに合わせて DocumentViewer を切り替える際の準備事項を整理する。

## 1. 接続設定の確認
- `config/viewer.env`（または `/etc/systemd/system/document-viewer.service.d/env.conf`）で以下を揃える。
```env
API_BASE_URL=http://pi5.local:8501
SOCKET_IO_URL=http://pi5.local:8501
SOCKET_IO_NAMESPACE=/
SOCKET_IO_EVENT=scan.ingested
SOCKET_IO_PATH=/socket.io
API_TOKEN=<SHARED_TOKEN>
```
- 旧リポジトリ `DocumentViewer` の `static/js/socket.js` を移植する場合は、`io("http://127.0.0.1:8501", { path: "/socket.io" })` のように IPv4 ループバックを利用する形へ更新する。
- systemd を経由する場合は `sudo systemctl daemon-reload && sudo systemctl restart document-viewer.service` で反映する。

## 2. 動作確認手順（ローカル）
1. `scripts/listen_for_scans.ts --api http://127.0.0.1:8501` で受信確認。
2. `curl -X POST /api/v1/scans` や `server/scripts/smoke_scan.sh` でテストデータを投入する。スモークスクリプトは一時的に Flask サーバーを起動し、`SMOKE-<timestamp>` 形式の注文コードで `/api/v1/scans` を呼び出し、完了後は自動で停止する。
   - ブロードキャストされる `scan.ingested` のペイロードは以下のキーを含む。
     ```json
     {
       "order_code": "TEST-900",
       "location_code": "RACK-Z9",
       "device_id": "HANDHELD-99"
     }
     ```
   - DocumentViewer 側では JSON の `order_code` を基準に PDF 表示を切り替える。欠損時はログ警告を出すよう実装しておく。
3. DocumentViewer のログ（`/var/log/document-viewer/client.log`）に以下が出るか確認。
   - `Socket.IO connected` / `scan.ingested received`
   - `Document lookup success` などのレンダリング成功ログ
4. 表示中の PDF が注文番号に合わせて切り替わるか目視し、必要ならブラウザのデベロッパーツールで Console/Network を確認。
5. 再接続・障害対応
- DocumentViewer の Socket.IO クライアントでは `reconnection: true`（デフォルト）を維持し、`reconnectionDelay=5000`, `reconnectionAttempts=0`（無制限）とする。
- Pi5 側では `/srv/rpi-server/logs/socket.log` に `Broadcast emit request` / `Socket.IO emit succeeded` / `Socket.IO emit failed` が出力される。切断時は Pi5 のログと DocumentViewer 側ログを突き合わせて原因を追う。
- 永続的に失敗する場合は `AUTO_DRAIN_ON_INGEST` の設定値と DB 反映状況（`part_locations` の `updated_at`）を確認し、イベントと REST の整合を取る。必要に応じて `GET /api/v1/admin/backlog-status` で backlog 件数を確認する。

## 3. 未整備タスク
- DocumentViewer の既存 Socket.IO クライアントコードを TypeScript 化し、テスト可能な形に整理。
- API トークン更新時、DocumentViewer の環境ファイルを同期する手順を RUNBOOK に追記。
- リスナーが切断された場合の再接続ログを標準化し、Pi5 側 `socket.log` と突き合わせて監視できるようにする。
