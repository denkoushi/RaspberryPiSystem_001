# Window A 再構築メモ（ドラフト）

## 1. Socket.IO 受信
- `scan.ingested`（既定）イベントを受信し、所在一覧を更新する。
- Socket 接続先や namespace は `SOCKET_BROADCAST_EVENT` / `SOCKETIO_NAMESPACE` と一致させる。
- REST フォールバック（20 秒）との整合を維持する。

## 2. REST API 連携
- `/api/v1/part-locations` などのエンドポイントに合わせて再実装。
- 旧 `tool-management-system02` から必要な UI ロジックを抽出。

## 3. テスト
- 手動テストハンドブックのシナリオに沿ってイベント受信を確認。
- 自動テスト（Playwright 等）は後工程で再検討。
