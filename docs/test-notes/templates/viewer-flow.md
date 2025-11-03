# DocumentViewer テストログ

- 日付: `YYYY-MM-DD`
- 実施者:
- 利用端末: Pi4 / DocumentViewer

## 前提
- `VIEWER_API_BASE` と Token が Pi5 と一致。
- DocumentViewer サービス起動済み。

## 手順
1. テスト用の部品番号を入力／イベント受信で表示させる。
2. Socket.IO イベント `scan.ingested` を受信して自動表示されるか確認。
3. REST フォールバック（再読み込み）で最新 PDF が表示されるか確認。

## ログ／観察
- `/var/log/document-viewer/client.log` 抜粋:
- UI スクリーンショット:

## 判定
- 結果: (OK / NG)
- メモ:
