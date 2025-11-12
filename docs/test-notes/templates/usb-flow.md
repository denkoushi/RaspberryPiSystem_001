# USB 配布テストログ

- 日付: `YYYY-MM-DD`
- 実施者:
- 対象端末: Pi5 / Window A / DocumentViewer

## 手順
1. Pi5 側で `tool-dist-export.sh` を実行し、`TOOLMASTER/master/` と `TOOLMASTER/docviewer/` が書き出されることを確認する（参照: `/Users/tsudatakashi/RaspberryPiServer/docs/usb-operations.md`）。
   ```bash
   sudo /usr/local/bin/tool-dist-export.sh --target /media/TM-DIST
   tree -L 2 /media/TM-DIST/TOOLMASTER
   ```
2. 端末（Window A / DocumentViewer）に `TM-DIST` を接続し、同期スクリプトと DocumentViewer importer を実行。
   ```bash
   sudo /usr/local/bin/tool-dist-sync.sh --device /dev/sdX
   sudo journalctl -u document-importer.service --since "1 minute ago" --no-pager
   sudo tail -n 10 /var/log/document-viewer/import.log
   ```
3. 同期後のデータ更新を確認。
   - `master/*.csv` と `docviewer/*.pdf` のタイムスタンプ
   - Window A UI 表示、DocumentViewer で対象 PDF が自動表示されるか（参照: `/Users/tsudatakashi/DocumentViewer/docs/setup-raspberrypi.md:119-134`）

## 結果
- 判定: (OK / NG)
- ログ抜粋:
- 差分メモ:
