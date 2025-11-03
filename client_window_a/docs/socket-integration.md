# Socket.IO 連携メモ（ドラフト）

## 1. イベント設定
- 既定のイベント名は `scan.ingested`。`SOCKET_BROADCAST_EVENT` を変更した場合は Window A 側も合わせる。
- base URL は Pi5 側の `/socket.io`。環境変数で指定する想定。

## 2. 実装概要
- `ScanSocket` クラス（`src/socket.ts`）で接続を管理する。
- イベント受信で所在一覧を更新し、必要に応じて REST フォールバックをトリガーする。

## 3. テスト
- 手動テストはハンドブックに準拠 (`scan.ingested` イベントが UI に反映されるか)。
- 自動テストはモック Socket.IO を使ったユニットテストを追加予定。
