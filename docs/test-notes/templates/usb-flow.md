# USB 配布テストログ

- 日付: `YYYY-MM-DD`
- 実施者:
- 対象端末: Pi5 / Window A / DocumentViewer

## 手順
1. Pi5 側で `tool-dist-export.sh` を実行。
   ```bash
   sudo /usr/local/bin/tool-dist-export.sh --target /media/TM-DIST
   ```
2. 端末に USB を接続し、同期スクリプトを実行。
   ```bash
   sudo /usr/local/bin/tool-dist-sync.sh
   ```
3. 同期後のデータ更新を確認。
   - ファイルタイムスタンプ
   - UI 表示

## 結果
- 判定: (OK / NG)
- ログ抜粋:
- 差分メモ:
