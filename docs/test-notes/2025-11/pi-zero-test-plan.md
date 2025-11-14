# Pi Zero 実機統合テスト計画 / 実施ログ（2025-11-05〜）

- 目的: Pi Zero → Pi5 → Window A / DocumentViewer のフローを実機で検証する際の詳細手順を事前に固める。
- 参照ドキュメント: `docs/system/pi-zero-integration.md`, `docs/test-notes/templates/pi-zero-integration.md`

## 1. 前提条件
- Pi5 側のバックエンドが `SCAN_REPOSITORY_BACKEND = "db"` で稼働し、`BacklogDrainService` の drain / status が正常に動作する。
- Window A / DocumentViewer の Socket.IO 設定が `SOCKET_IO_URL=http://pi5.local:8501`, `SOCKET_IO_PATH=/socket.io` に更新済み。
- 共通トークンを各端末に配布し、Pi Zero の `/etc/onsitelogistics/config.json` が最新値を指している。

## 2. 実施手順と 2025-11-10 ログ
1. **Pi Zero 側の事前チェック**
   - `sudo mirrorctl status`、`sudo systemctl status handheld@tools01.service`、`./scripts/pi_zero_pull_logs.sh …` を実行。
   - ログ採取は root 権限で `sudo journalctl -u handheld@tools01.service -n 80 --since "YYYY-MM-DD HH:MM"` を使う（tools01 だけでは閲覧不可）。  
   - ログ取得結果を `docs/test-notes/YYYY-MM/pi-zero-*.md` に貼り付け。
2. **テスト用バーコードのスキャン**
   - 既存テンプレートに従い注文バーコード→棚バーコードのペアを読み取る。
   - 実施時刻と使用したバーコード番号を記録。
3. **Pi5 受信確認**
   - `/srv/rpi-server/logs/api_actions.log`, `/srv/rpi-server/logs/socket.log` を確認。
   - `BacklogDrainService.drain_once()` を実行して pending 件数が 0 になることを確認し、出力を記録。
   - 2025-11-10 08:26 JST のログ抜粋  
     ```
     2025-11-10 08:26:05,428 INFO Posting to http://192.168.10.230:8501/api/v1/scans: None
     2025-11-10 08:26:05,737 WARNING Failed to post payload ... (None): 400 Client Error
     2025-11-10 08:26:05,761 INFO Posting to ...: a6f316a6-8f82-4d6f-8de1-b870023b8327
     2025-11-10 08:26:05,815 INFO Server accepted payload ...
     2025-11-10 08:26:05,828 INFO Posting to ...: 8a6a52d3-50b5-4942-9d41-323295377ffb
     2025-11-10 08:26:05,861 INFO Server accepted payload ...
     2025-11-10 08:26:05,871 INFO Posting to ...: 08d45478-3644-4ab9-984b-9548c45d4c77
     2025-11-10 08:26:05,903 INFO Server accepted payload ...
     ```
   - `scan_queue.db` を確認するとエントリは空で、`scan_id=None` の旧データは削除済み。
4. **UI 反映確認**
   - Window A の所在一覧、DocumentViewer の PDF 表示が更新されるかを目視し、必要ならスクリーンショットを取得。
   - 2025-11-10: Window A / DocumentViewer 側は未確認（Pi5 API 復旧優先のため）。後日 Socket.IO 実機テストで補完する。
5. **結果の整理**
   - テンプレートに従って判定・差異・フォローアップを記述。
   - 2025-11-10 実施メモ  
     - Pi Zero: `[SERIAL] forcing /dev/minjcode0 @ 115200bps` → `[SERIAL] scanner ready` → A/B (`4989999058963`, `https://e.bambulab.com/...`) で電子ペーパー更新完了。  
     - Pi5: API 受信は成功。旧キューで `scan_id=None` だった行は削除済み。`sqlite3 ~/.onsitelogistics/scan_queue.db 'SELECT COUNT(*) FROM scan_queue;'` の結果は 0。  
     - drain-only を headless で実行する場合は `HANDHELD_HEADLESS=1 python handheld/scripts/handheld_scan_display.py --drain-only` を使用し、GPIO 初期化エラーを避ける。  
     - 今後は PR 用に上記ログを添付し、Phase-1 ブランチへまとめる。
    - 2025-11-14 実施メモ  
      - Pi Zero: `sudo -E PYTHONPATH=... handheld_scan_display.py` を通常モードで実行し、A/B (`4989999058963`, `https://e.bambulab.com/t/?c=ga8XCc2Q6l1idFKP`) をスキャン。電子ペーパーは A/B 表示ともに `[OK]` となり `Status: DONE` を表示。  
      - CLI ログ抜粋:  
        ```
        2025-11-14 09:17:56,245 INFO [SERIAL] forcing /dev/minjcode0 @ 115200bps
        2025-11-14 09:17:56,290 INFO [SERIAL] scanner ready: /dev/minjcode0 (serial 115200bps)
        [DEBUG] Read code: 4989999058963
        [DEBUG] Read code: https://e.bambulab.com/t/?c=ga8XCc2Q6l1idFKP
        2025-11-14 09:18:24,659 INFO Posting to http://192.168.10.230:8501/api/v1/scans: None
        2025-11-14 09:18:24,867 INFO Server accepted payload (target=http://192.168.10.230:8501/api/v1/scans)
        ```
      - Pi5: `Server accepted payload` が確認でき、scan_queue は drain-only 後に Pending 0。GPIO Busy は `/dev/gpiochip0` を占有していた旧 `tools01` プロセス (PID 960) を停止することで解消できることを再確認。  
      - 次回以降は headless drain と通常モードテストの双方を記録し、`docs/system/pi-zero-integration.md` のトラブルシュート節を参照すること。

## 3. 想定リスクと対処
- **トークン不一致**: API 応答が 401/403 になる。`manage_api_token.py` で再発行して各端末へ再配布。
- **ネットワーク断**: Pi Zero から `ping`/`curl` が失敗する場合は Wi-Fi 状態と Pi5 の Firewall を確認。
- **Socket.IO 切断**: DocumentViewer の `client.log` と Pi5 の `socket.log` を突き合わせ、再接続設定を確認。

## 4. フォローアップ
- 実施後、`docs/system/next-steps.md` に結果を反映し、残タスク（再送キュー、RUNBOOK 追記など）を更新する。
