# Pi Zero → Pi5 統合テストログ（テンプレート）

- 日付: 2025-11-05
- 実施者: Codex (AI)
- 対象システム: Pi Zero / RaspberryPiServer / Window A / DocumentViewer

## 1. 事前チェック
- [ ] API トークン一致（Pi Zero, Pi5, Window A, DocumentViewer）
- [ ] Pi Zero `mirrorctl status`
  ```bash
  sudo mirrorctl status
  ```
  - 出力メモ: _実機接続後に記録_
- [ ] Pi Zero ネットワーク疎通（Pi5 への ping / curl）
  ```bash
  ping -c 3 <pi5-host>
  curl -I http://<pi5-host>:8501/healthz
  ```
  - メモ: _実機接続後に記録_
- [ ] Pi5 サービス状態
  ```bash
  sudo systemctl status raspberrypiserver.service
  ```
  - メモ: `active (running)` を確認済み（開発環境）。
- [ ] Window A / DocumentViewer サービス状態
  ```bash
  sudo systemctl status window-a.service
  sudo systemctl status document-viewer.service
  ```
  - メモ: _実機で要確認_

## 2. 操作手順と観測
1. Pi Zero ハンディスキャン
   - 実施時刻:
   - バーコード / 注文番号:
   - 観察メモ:
2. Pi Zero 送信ログ
   ```bash
   sudo journalctl -u handheld@tools01.service -n 40 --no-pager
   ```
   - 抜粋:
3. Pi5 受信ログ
   ```bash
   sudo tail -n 20 /srv/rpi-server/logs/api_actions.log
   sudo tail -n 20 /srv/rpi-server/logs/socket.log
   ```
   - 抜粋:
4. PostgreSQL 反映
   ```bash
   PGPASSWORD=app psql -h 127.0.0.1 -p 15432 -U app -d sensordb \\
     -c "SELECT order_code, location_code, updated_at FROM part_locations ORDER BY updated_at DESC LIMIT 5;"
   ```
   - 抜粋:
5. Window A UI / DocumentViewer 確認
   - リアルタイム更新状況:
   - DocumentViewer ログ (`/var/log/document-viewer/client.log`) 抜粋:

## 3. 片付け
- [ ] リスナー停止（`Ctrl+C` / `lsof -i :8501`）
- [ ] Flask サーバー停止（`Ctrl+C` / PID Kill）
- [ ] Pi Zero `onsitelogistics` サービス状態確認
  ```bash
  sudo systemctl status handheld@tools01.service
  ```

## 4. 判定・メモ
- 判定（OK / NG）:
- 想定との差異:
- 次回への改善点:
