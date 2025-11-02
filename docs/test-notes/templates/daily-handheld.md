# 日次テストログ（ハンディ送信フロー）

- 日付: `YYYY-MM-DD`
- 実施者:
- 対象システム: Pi Zero / RaspberryPiServer / Window A / DocumentViewer

## 1. 事前状態
- Pi Zero `mirrorctl status`:
  ```bash
  sudo mirrorctl status
  ```
  - 出力メモ:
- Pi5 健康チェック:
  ```bash
  curl -I http://127.0.0.1:8501/healthz
  ```
  - 結果メモ:
- Window A 状態:
- DocumentViewer 状態:

## 2. 操作手順と結果
1. ハンディスキャン:
   - 実施時刻:
   - 観察メモ:
2. Pi Zero 送信ログ:
   ```bash
   sudo journalctl -u handheld@tools01.service -n 30 --no-pager
   ```
   - 抜粋:
3. Pi5 受信ログ:
   ```bash
   sudo tail -n 10 /srv/rpi-server/logs/mirror_requests.log
   sudo tail -n 10 /srv/rpi-server/logs/api_actions.log
   ```
   - 抜粋:
4. DB 確認:
   ```bash
   PGPASSWORD=app psql -h 127.0.0.1 -p 15432 -U app -d sensordb \
     -c "SELECT order_code, location_code, updated_at FROM part_locations ORDER BY updated_at DESC LIMIT 5;"
   ```
   - 抜粋:
5. Window A UI 確認:
   - 観察メモ:
6. DocumentViewer 確認:
   ```bash
   sudo tail -n 20 /var/log/document-viewer/client.log
   ```
   - 抜粋:

## 3. 判定
- 結果: （OK / NG）
- 想定との差異:
- 再現手順（必要な場合）:

## 4. 次回へのメモ
- 改善点:
- 未解決事項:
- 追加対応:
