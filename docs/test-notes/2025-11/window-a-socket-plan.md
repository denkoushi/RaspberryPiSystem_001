# Window A / DocumentViewer Socket.IO 実機テスト計画（2025-11-05）

- 目的: Pi Zero からのイベントが Socket.IO 経由で Window A / DocumentViewer に到達し、UI が期待通り更新されることを確認する。
- 参照: `docs/system/documentviewer-integration.md`, `client_window_a/docs/manual-test.md`

## 1. 事前準備
- Pi5 側で Flask サーバー（`python -m raspberrypiserver.app`）を起動し、`SOCKETIO_PATH` がドキュメント通り `/socket.io` になっているか確認。
- Window A にて `npx ts-node scripts/listen_for_scans.ts --api http://pi5.local:8501` を待機させ、DocumentViewer の `client.log` を tail する。
- 共通トークンと API ベース URL が Window A / DocumentViewer の環境ファイルに設定されていることを再確認。

## 2. テストシナリオ
1. **通常スキャン**
   - Pi Zero（または curl）から `/api/v1/scans` へテストデータを投入。
   - Window A のリスナーが `scan.ingested` を受信し、UI のハイライトが変わることを確認。DocumentViewer は該当 PDF に切り替わる。
2. **Socket.IO 切断 → 再接続**
   - DocumentViewer でネットワークを切断／再接続し、再接続ログが出るか確認。
   - 切断中にスキャンを送信し、再接続後に backlog 返済で UI が追いつくかを確認。
3. **エラーケース**
   - イベント名やパスを誤設定した状態を一時的に再現し、ログ（`socket.log`, `client.log`）の警告内容を把握。試験後は正しい設定へ戻す。

## 3. 記録テンプレート
- 実行日時・使用したコマンド・観察結果を `docs/test-notes/2025-11/window-a-demo.md` へ追記。
- Window A / DocumentViewer のログ抜粋、スクリーンショット、UI 動作の動画リンク（必要に応じ）を記録。

## 4. 判定条件
- Socket.IO 受信イベントが到達し、UI が遅延なく更新されること。
- 切断時には再接続が自動で試行され、復旧後に backlog との差が解消されること。
- エラー時のログが運用ドキュメントに記載した内容と一致すること。
