# Pi Zero 統合事前チェックログ（2025-11-05）

- 実施者: Codex (AI)
- 目的: Pi Zero 実機検証に入る前の準備状況を確認する
- 参照テンプレート: `docs/test-notes/templates/pi-zero-integration.md`

## 1. 事前チェック
- [x] API トークン一致（Pi Zero, Pi5, Window A, DocumentViewer）  
  - メモ: `server/scripts/manage_api_token.py` で発行したトークンを各端末で確認済み。
- [x] mirrorctl 状態確認 (`sudo mirrorctl status`)  
  - 出力要約: `mirror_mode=true`, `Last success` 正常、`Next run` が未来時刻。
- [x] Pi Zero ネットワーク疎通  
  - `ping pi5.local` 3 回成功。  
  - `curl -I http://pi5.local:8501/healthz` → `HTTP/1.0 200 OK`。
- [x] Pi5 サービス状態  
  - `sudo systemctl status raspberrypiserver.service` → `active (running)`。
- [x] Window A / DocumentViewer サービス状態  
  - `window-a.service` / `document-viewer.service` ともに `active (running)`。

## 2. ログ収集
```bash
cd ~/RaspberryPiSystem_001
./scripts/pi_zero_pull_logs.sh pi-zero.local --service handheld@tools01.service --output ./pi-zero-logs
```
- 取得ファイル:
  - `mirrorctl-status.txt` — 状態 OK / エラーなし
  - `journalctl-handheld@tools01.service.log` — `status=delivered` を確認
  - `systemctl-status.txt` — `loaded` / `active (running)`
  - `system-info.txt` — `hostname`, `uptime`, `ip addr` を記録
- 保存先: `pi-zero-logs/pi-zero.local-20251105-104200/`

## 3. サーバーログ確認
```bash
sudo tail -n 20 /srv/rpi-server/logs/api_actions.log
sudo tail -n 20 /srv/rpi-server/logs/socket.log
```
- `api_actions.log`: `SMOKE-1762306813` など最近のスキャンが 202 応答になっている。  
- `socket.log`: `Socket.IO emit succeeded` ログあり。エラーなし。

## 4. PostgreSQL 反映確認
```bash
PGPASSWORD=app psql -h 127.0.0.1 -p 15432 -U app -d sensordb \
  -c "SELECT order_code, location_code, updated_at FROM part_locations ORDER BY updated_at DESC LIMIT 5;"
```
- 確認結果: 直近のテストデータ（`SMOKE-1762306813`, `TEST-965` 等）が更新済み。  
- `BacklogDrainService.drain_once()` 実行結果: `drained 0`（バックログ残なし）。

## 5. UI 確認
- Window A: 所在一覧にデモデータが表示されている（Socket.IO イベント待受 OK）。  
- DocumentViewer: `scan.ingested received` ログを確認。該当 PDF が切り替わることを手動確認。

## 6. 判定
- 判定: OK  
- 次のアクション: 実機検証本番（Pi Zero からのリアルスキャン）に進む。`docs/system/pi-zero-integration.md` の手順を基にテストログを残す。
