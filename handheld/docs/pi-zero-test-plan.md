# Pi Zero 実機テスト計画（ドラフト）

## 前提
- `/etc/onsitelogistics/config.json` が新 API トークンで更新済み。
- 再送キュー (`handheld/src/retry_queue.py`) と mirrorctl 連携がデプロイされている。

## 手順案
1. `mirrorctl status` で初期状態を確認し、キューが空であることを確認。
2. 意図的に送信失敗させ、再送キューに残った後、`retry_loop` を実行。
3. Pi5 で drain → part_locations 更新、Window A でイベント受信を確認。
4. テスト結果を `docs/test-notes/` に記録し、mirrorctl の日次カウントを更新。

## 所要時間目安
- 約 2〜3 日（再送シナリオの再現、Pi Zero 実機操作、ログ取得を含む）。
- mirrorctl hook 実装済み。次回テストでは成功/失敗件数を `mirrorctl status` メモへ記録する。
