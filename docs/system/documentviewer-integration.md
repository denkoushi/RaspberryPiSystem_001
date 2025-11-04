# DocumentViewer Socket.IO / REST 統合メモ（ドラフト）

Pi5 側の Socket.IO ブロードキャストに合わせて DocumentViewer を切り替える際の準備事項を整理する。

## 1. 接続設定の確認
- `config/viewer.env`（または `/etc/systemd/system/document-viewer.service.d/env.conf`）で以下を揃える。
  ```env
  API_BASE_URL=http://pi5.local:8501
  SOCKET_IO_URL=http://pi5.local:8501
  SOCKET_IO_NAMESPACE=/
  SOCKET_IO_EVENT=scan.ingested
  API_TOKEN=<SHARED_TOKEN>
  ```
- 旧リポジトリ `DocumentViewer` の `static/js/socket.js` を移植する場合は、`io("http://127.0.0.1:8501", { path: "/socket.io" })` のように IPv4 ループバックを利用する形へ更新する。
- systemd を経由する場合は `sudo systemctl daemon-reload && sudo systemctl restart document-viewer.service` で反映する。

## 2. 動作確認手順（ローカル）
1. `scripts/listen_for_scans.ts --api http://127.0.0.1:8501` で受信確認。
2. `curl -X POST /api/v1/scans` でテストデータ投入。
3. DocumentViewer のログ（`/var/log/document-viewer/client.log`）に以下が出るか確認。
   - `Socket.IO connected` / `scan.ingested received`
   - `Document lookup success` などのレンダリング成功ログ
4. 表示中の PDF が注文番号に合わせて切り替わるか目視し、必要ならブラウザのデベロッパーツールで Console/Network を確認。

## 3. 未整備タスク
- DocumentViewer の既存 Socket.IO クライアントコードを TypeScript 化し、テスト可能な形に整理。
- API トークン更新時、DocumentViewer の環境ファイルを同期する手順を RUNBOOK に追記。
- リスナーが切断された場合の再接続ログを標準化し、Pi5 側 `socket.log` と突き合わせて監視できるようにする。
