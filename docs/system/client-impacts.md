# クライアント影響メモ

## Window A / DocumentViewer
- Socket.IO イベント名 `scan.ingested` を受信して所在更新を反映する。
- REST フォールバックが `part_locations` テーブルと整合するよう API 仕様を確認する。
- バックログ処理（drain）後に UI へ反映される時間を考慮し、リロード/通知戦略を整理する。

## ハンディ端末
- 送信結果がバックログに残る場合の再送・再取得方針を準備する。
- `mirrorctl` 日次チェックで backlog 件数が異常に増加していないか確認ポイントを追加する。
