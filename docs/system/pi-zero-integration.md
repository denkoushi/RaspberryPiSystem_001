# Pi Zero → Pi5 → Window A / DocumentViewer 実機統合チェックリスト

Pi Zero ハンディの本番切り替え前に「設定 → 疎通 → 反映確認 → 片付け」までを一気通貫で確認するためのチェックリスト。各ステップの結果は `docs/test-notes/templates/pi-zero-integration.md` をベースに記録する。

## 0. Pi Zero (tools01) セットアップ手順メモ
今回のハンディ復旧で踏んだステップをそのまま残す。新しい Pi Zero を用意した場合もこの手順で整備してから Git / Pi5 側のテストに入る。

### 0.1 ベース環境
1. `tools01` ユーザーを作成（`sudo adduser --disabled-password --gecos "" tools01`）し、`input gpio spi i2c dialout` グループに追加。
2. **RaspberryPiSystem_001 の clone**  
   - `scripts/pi_zero_migrate_repo.sh` を実行すると、旧 `~/OnSiteLogistics` を `~/OnSiteLogistics_legacy_<timestamp>` に退避し、新しい `~/RaspberryPiSystem_001` を clone する（git がインストールされている前提）。  
     ```bash
     cd ~/RaspberryPiSystem_001/scripts   # Mac 側で差分を pull した後を想定
     scp pi-zero-mac:~/RaspberryPiSystem_001/scripts/pi_zero_migrate_repo.sh tools01@pi-zero:/home/tools01/
     ssh tools01@pi-zero 'bash ~/pi_zero_migrate_repo.sh'
     ```
   - スクリプト実行後、旧ディレクトリにしかない `.env` や `config.json` などはバックアップから手動でマージする。
3. venv 準備  
   ```bash
   sudo -u tools01 -H python3 -m venv /home/tools01/.venv-handheld
   sudo -u tools01 -H /home/tools01/.venv-handheld/bin/pip install --upgrade pip
   sudo -u tools01 -H /home/tools01/.venv-handheld/bin/pip install evdev pillow requests pyserial gpiozero lgpio
   ```
4. Waveshare ドライバ（2.13" e-Paper HAT V4）  
   - GitHub からの `git clone` は途中で `invalid index-pack output` になることがあるため、公式 Wiki が案内している ZIP を常用する。  
   ```bash
   sudo -u tools01 -H bash -lc '
     set -euo pipefail
     cd /home/tools01
     rm -rf e-Paper E-Paper_code.zip
     wget -O E-Paper_code.zip https://files.waveshare.com/upload/7/71/E-Paper_code.zip
     unzip -q E-Paper_code.zip -d e-Paper
     source /home/tools01/.venv-handheld/bin/activate
     cd /home/tools01/e-Paper/RaspberryPi_JetsonNano/python
     python setup.py install
   '
   ```
   - インストール直後に venv で import を確認する。  
     ```bash
     sudo -u tools01 -H bash -lc "source ~/.venv-handheld/bin/activate && python - <<'PY'
import importlib
import sys
missing = []
for name in ('waveshare_epd', 'waveshare_epaper'):
    try:
        importlib.import_module(name)
    except ModuleNotFoundError:
        missing.append(name)
if missing:
    sys.exit(f'Missing modules: {missing}')
print('waveshare driver OK')
PY"
   ```
   - 参照元: [Waveshare 2.13inch e-Paper HAT Wiki](https://www.waveshare.com/wiki/2.13inch_e-Paper_HAT)
   - `.env` や systemd override で `/home/tools01/e-Paper/RaspberryPi_JetsonNano/python/lib` を `PYTHONPATH` に足しておくと import が安定する。
5. スキャナ（CDC-ACM）環境  
   - 旧システムと同様に MINJCODE をシリアルモードで扱う。`scripts/setup_serial_env.sh` を root で実行すると udev ルール（`/dev/minjcode0`）と systemd の再起動まで自動化できる。  
     ```bash
     cd ~/RaspberryPiSystem_001
     sudo ./scripts/setup_serial_env.sh tools01
     ls -l /dev/minjcode* /dev/ttyACM*      # デバイス確認
     ```
   - ルール適用後にスキャナを再接続し、`dmesg | grep -i ttyACM` で `/dev/ttyACM0` の生成を確認する。`sudo evtest` には出ないので、`handheld_scan_display.py` が自動的に `/dev/minjcode*` → `/dev/ttyACM*` → `/dev/ttyUSB*` の順で探す。
   - 詳細背景は旧リポジトリ `docs/handheld-reader.md`（セクション 4.x）を参照。

### 0.2 systemd テンプレート
`/etc/systemd/system/handheld@.service.d/override.conf`
```ini
[Unit]
After=dev-ttyACM0.device
Wants=dev-ttyACM0.device

[Service]
SupplementaryGroups=input dialout gpio spi i2c
WorkingDirectory=/home/%i/RaspberryPiSystem_001/handheld
Environment=PYTHONUNBUFFERED=1
Environment=ONSITE_CONFIG=/etc/onsitelogistics/config.json
Environment=PYTHONPATH=/home/%i/e-Paper/RaspberryPi_JetsonNano/python/lib
Environment=GPIOZERO_PIN_FACTORY=lgpio
ExecStartPre=/bin/sh -c "for i in $(seq 1 15); do [ -e /dev/ttyACM0 ] && exit 0; sleep 2; done; echo 'no serial device'; exit 1"
ExecStart=
ExecStart=/home/%i/.venv-handheld/bin/python /home/%i/RaspberryPiSystem_001/handheld/scripts/handheld_scan_display.py
Restart=on-failure
RestartSec=2
```
`sudo systemctl daemon-reload && sudo systemctl enable --now handheld@tools01.service`

### 0.3 ペイロード仕様と Pi5 側との整合
- Pi5 `/api/v1/scans` は `order_code` / `location_code` を必須にしているため、A/B を送るハンディスクリプトは以下の JSON を POST する。  
  ```json
  {
    "order_code": "<A code>",
    "location_code": "<B code>",
    "device_id": "pi-zero2w-01",
    "metadata": {
      "scan_id": "<uuid4>",
      "scanned_at": "2025-11-07T05:36:28Z",
      "retries": 0
    }
  }
  ```
- 再送キュー (`~/.onsitelogistics/scan_queue.db`) には上記 JSON がそのまま入る。Pi5 の API を変更した場合は `_normalize_payload` の条件に合わせてクライアント側も必ず更新する。
- 既存 `handheld/scripts/handheld_scan_display.py` を更新する際は、このリポジトリ内のパッチ `handheld/docs/patches/2025-11-07-handheld-payload.patch` を適用する。  
  ```bash
  cd /home/tools01/RaspberryPiSystem_001
  git apply handheld/docs/patches/2025-11-07-handheld-payload.patch
  sudo systemctl restart handheld@tools01.service
  ```

以上を満たした状態で Git にコミットしておくと、VS Code 側で `git pull`→`systemctl restart handheld@tools01.service` を実行するだけで Pi Zero 側の更新が反映される。

## 1. 事前整備
- [ ] **共通トークンの同期**  
  `server/scripts/manage_api_token.py --rotate` 等で再発行した場合は Pi Zero (`/etc/onsitelogistics/config.json`)、Pi5 (`/srv/rpi-server/config/local.toml`)、Window A、DocumentViewer へ同じ Bearer トークンを配布する。
- [ ] **Pi Zero 設定ファイル確認**  
  `/etc/onsitelogistics/config.json` が以下のように最新ホスト/トークンを指していること。  
  ```json
  {
    "api_base": "http://pi5.local:8501",
    "api_token": "<SHARED_TOKEN>",
    "device_id": "HANDHELD-01"
  }
  ```
- [ ] **Pi5 systemd 環境**  
  `/etc/systemd/system/raspberrypiserver.service.d/env.conf` に `RPI_SERVER_CONFIG=/srv/rpi-server/config/local.toml` を設定し、`sudo systemctl daemon-reload && sudo systemctl restart raspberrypiserver.service` で反映。
- [ ] **Window A / DocumentViewer**  
  `.env` もしくは systemd 環境ファイルで `SOCKET_IO_URL=http://pi5.local:8501` 等、IPv4 アドレスと共通トークンを指定。

## 2. サービス状態チェック
- [ ] Pi Zero:  
  ```bash
  sudo mirrorctl status
  sudo systemctl status handheld@tools01.service
  sudo journalctl -u handheld@tools01.service -n 40 --no-pager
  ```
  `mirror_mode=true`、`status=delivered` ログが連続していることを確認。
- [ ] Pi5:  
  ```bash
  sudo journalctl -u raspberrypiserver.service -n 50
  sudo tail -n 50 /srv/rpi-server/logs/api_actions.log
  sudo tail -n 20 /srv/rpi-server/logs/socket.log
  ```
- [ ] Window A: `systemctl status window-a.service`、`scripts/listen_for_scans.ts --api http://127.0.0.1:8501`
- [ ] DocumentViewer: `systemctl status document-viewer.service`、`/var/log/document-viewer/client.log`

## 3. 統合試験フロー
1. **Pi Zero でテストバーコードをスキャン**（注文→棚）。
2. **Pi Zero ログ記録**  
   ```bash
   ./scripts/pi_zero_pull_logs.sh <pi-zero-host> --service handheld@tools01.service
   ```
   取得したログをテストノートへ貼り付ける。
3. **Pi5 受信確認**  
   - REST: `/srv/rpi-server/logs/api_actions.log`
   - Socket.IO: `/srv/rpi-server/logs/socket.log`
4. **PostgreSQL 反映**  
   ```bash
   PGPASSWORD=app psql -h 127.0.0.1 -p 15432 -U app -d sensordb \
     -c "SELECT order_code, location_code, updated_at FROM part_locations ORDER BY updated_at DESC LIMIT 5;"
   ```
   バックログが残る場合は `BacklogDrainService` を直接呼び出す。
   ```bash
   cd ~/RaspberryPiSystem_001/server
   source .venv/bin/activate
   python - <<'PY'
from raspberrypiserver.services.backlog import BacklogDrainService
service = BacklogDrainService('postgresql://app:app@localhost:15432/sensordb', limit=100)
print('drained', service.drain_once())
print('pending', service.count_backlog())
PY
   ```
   `SELECT COUNT(*) FROM scan_ingest_backlog;` で残数を確認。
5. **UI 反映確認**  
   Window A の所在一覧／DocumentViewer の PDF 表示が scancode に追随するかを目視し、必要に応じてスクリーンショットを保存。
6. **管理 API 併用（必要時）**  
   ```bash
   curl -X POST http://pi5.local:8501/api/v1/admin/drain-backlog -H "Content-Type: application/json" -d '{"limit": 100}'
   curl http://pi5.local:8501/api/v1/admin/backlog-status
   ```
7. **記録**  
   ```bash
   cp docs/test-notes/templates/pi-zero-integration.md docs/test-notes/$(date +%F)-pi-zero-integration.md
   ```
   コマンド出力・観察メモ・判定を記入する。
   - `docs/test-notes/2025-11/window-a-demo.md` にログサンプルあり（`SMOKE-1762306813` など）。

## 4. 片付け
- [ ] Window A / DocumentViewer のテスト用リスナーを停止。
- [ ] Pi5 開発サーバー（ターミナル実行中なら `Ctrl+C`）または systemd サービスを停止。
- [ ] Pi Zero `onsitelogistics` を通常運用へ戻す（`sudo systemctl restart handheld@tools01.service`）。
- [ ] 収集したログを所定のテストノートへ保存し、必要なら関係者へ共有。

## 5. 未決課題
- DocumentViewer の Socket.IO 実装を TypeScript 化し、再接続ロジックをテスト可能な形にする。
- mirrorctl hook 経由での再送キュー処理の挙動をログフォーマットごとに統一する。
- 実機テスト完了後、今回のチェックリストの改善点をフィードバックし次回に反映する。
