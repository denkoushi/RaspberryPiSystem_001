# Window A 手動テストログ

- 日付: `YYYY-MM-DD`
- 実施者:
- API_BASE:

## シナリオ
1. `LocationState` で REST 取得 → 初期表示を確認。
2. `scan.ingested` イベントを送信し、UI が更新されることを確認。
3. REST フォールバックを手動実行し、最新データが取得できることを確認。

## 観察
- Socket イベント
- REST レスポンス
- UI スクリーンショット

## 判定
- 結果: OK / NG
- メモ:
