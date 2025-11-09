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
3. **tools01 ワーキングツリーの同期**  
   - Pi Zero には「作業用ユーザー（例: `denkonzero`）の clone」と「systemd サービスが参照する `/home/tools01/RaspberryPiSystem_001`」の2系統が存在する。  
   - `scripts/update_handheld_override.sh` は実行時に以下を自動実施する:  
     1. Mac 側 VS Code で checkout しているブランチ名とコミット ID を取得  
     2. `sudo -u tools01 -H bash -lc 'cd ~/RaspberryPiSystem_001 && git fetch --all --tags --prune && git checkout <branch> && git reset --hard <commit>'` を実行  
   - これにより、サービスが必ず最新コミットを参照する。`git pull` を忘れて `tools01` 側だけ古くなる事故を防げる。  
   - **注意**: `tools01` リポジトリに手作業の差分を残さないこと（上記 `reset --hard` で破棄される）。Pi 固有の設定ファイルは `/etc/onsitelogistics` や `/home/tools01/.onsitelogistics` 側で管理する。
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
   - **HID モードのフォールバック**: どうしてもシリアルへ切り替えられない場合でも、`handheld_scan_display.py` が `/dev/input/by-id/*MINJCODE*event-kbd` や `evtest` で検出した MINJCODE の event デバイスを自動選択して動作する。`sudo evtest` で MINJCODE の番号（例: `/dev/input/event2`）を確認し、`journalctl -fu handheld@tools01.service` に `[INFO] Scanner device: /dev/input/event2 (MINJCODE...)` が出れば HID モードでも運用可能。Pi のコンソールにキー入力が流れないよう、サービスを停止した状態でスキャンしない。
   - `HANDHELD_INPUT_DEVICE` という環境変数を systemd 環境に追加すると、HID デバイスを強制的に指定できる。例: `Environment=HANDHELD_INPUT_DEVICE=/dev/input/by-id/usb-MINJCODE_MINJCODE_MJ2818A_00000000011C-event-kbd`。
   - シリアルを強制したい場合は `Environment=HANDHELD_SERIAL_PATHS=/dev/minjcode0,/dev/ttyACM0` を systemd 環境に追加する。該当デバイスに 115200bps で接続を試み、失敗すれば HID へフォールバックする。

Pi Zero でコードを反映→動作確認する定型コマンドは下記。毎回これを実行し、ログでシリアル検出を確認する。  
```bash
cd ~/RaspberryPiSystem_001
git pull
./scripts/update_handheld_override.sh
sudo systemctl restart handheld@tools01.service
sudo journalctl -fu handheld@tools01.service
```

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
ExecStartPre=/bin/sh -c "for i in $(seq 1 15); do for dev in /dev/minjcode0 /dev/ttyACM0 /dev/input/by-id/*MINJCODE*event-kbd /dev/input/by-path/*MINJCODE*event-kbd; do if [ -e \"$dev\" ]; then exit 0; fi; done; sleep 2; done; echo 'no scanner device'; exit 1"
ExecStart=
ExecStart=/home/%i/.venv-handheld/bin/python /home/%i/RaspberryPiSystem_001/handheld/scripts/handheld_scan_display.py
Restart=on-failure
RestartSec=2
```
Pi Zero 側でコードを反映する際は、必ず次のコードブロックを一括で実行する。個別の貼り付けは行わない。  
```bash
cd ~/RaspberryPiSystem_001
git pull
./scripts/update_handheld_override.sh
sudo systemctl restart handheld@tools01.service
sudo journalctl -fu handheld@tools01.service
```
`sudo systemctl daemon-reload && sudo systemctl enable --now handheld@tools01.service`

### 0.3 ハンディ更新で陥りやすい不具合と対策
- **tools01 ワーキングツリー未更新**  
  - 症状: `journalctl -fu handheld@tools01.service` に `[INFO] Scanner device: /dev/input/event0 (vc4-hdmi)` しか出ず、電子ペーパー表示も `A/B: WAIT` のまま。CLI で `python handheld_scan_display.py` を実行しても HID モードで動作する。  
  - 原因: systemd サービスが参照する `/home/tools01/RaspberryPiSystem_001` が古いまま放置され、シリアル対応版 `handheld_scan_display.py` が配置されていない。作業ユーザー（例: `denkonzero`）側の clone だけ更新しても、サービス側は古いコミットを実行し続ける。  
  - 対策:  
    1. VS Code で差分をステージ → ユーザーが commit/push。  
    2. Pi Zero で以下のコマンドブロックを実行し、`update_handheld_override.sh` が `git fetch && checkout && reset --hard` を自動実行するようにする。  
    3. `journalctl` に `[SERIAL] forcing /dev/minjcode0 @ 115200bps` が出るまで確認し、出ない場合はブランチ・コミット ID を再確認してやり直す。  
- **API (Pi5) への接続失敗**  
  - 症状: `[SERIAL] scanner ready` の後に `Posting to http://192.168.10.230:8501/api/v1/scans` → `Max retries exceeded` → `Queueing payload` が繰り返される。電子ペーパーは完了表示になるが、サーバー側には反映されない。  
  - 原因: Pi Zero から Pi5 (`http://192.168.10.230:8501`) へのネットワーク疎通ができていない、または Pi5 の `raspberrypiserver.service` が停止している。  
  - 対策: `curl -I http://192.168.10.230:8501` や `ping` で疎通を確認し、必要に応じて Pi5 側サービスを再起動する。タイムアウト中に受け付けたスキャンは SQLite キューに残っているため、復旧後に `sudo -u tools01 -H bash -lc "source ~/.venv-handheld/bin/activate && python handheld/scripts/handheld_scan_display.py --drain-only"` を実行して一気に再送する。

### 0.4 ペイロード仕様と Pi5 側との整合
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

### 0.5 直近の検証結果ログ（2025-11-09 21:08 JST）
- 21:08:07 `journalctl -fu handheld@tools01.service`  
  ```
  [SERIAL] forcing /dev/minjcode0 @ 115200bps
  [SERIAL] scanner ready: /dev/minjcode0 (serial 115200bps)
  ```
  → シリアル優先ロジックが新リポジトリのコードで動作していることを確認。  
- 21:08:17〜21:08:18  
  ```
  [DEBUG] Read code: 1920095030005
  [STATE] transition -> WAIT_B ...
  [DEBUG] Read code: 9784305710628
  [UI] update -> ... Status: DONE
  ```
  → 電子ペーパーが A/B 完了表示まで更新される状態に復旧。  
- 21:08:23 以降  
  ```
  Posting to http://192.168.10.230:8501/api/v1/scans ...
  WARNING ... Max retries exceeded ...
  Queueing payload for retry ...
  ```
  → Pi Zero から Pi5 への HTTP POST がタイムアウト。Pi5 側サービス復旧とネットワーク疎通確認後、`handheld_scan_display.py --drain-only` でキューを空にすること。  
- 上記ログは `docs/test-notes/2025-11/pi-zero-test-plan.md` に貼り付け、再テスト時の比較基準とする。

### 0.6 scan_queue の点検と残骸掃除
- Pi Zero で旧バージョンが生成したキューが残っていると、`scan_id` が `None` のまま送信され 400 エラーになる。以下のコマンドで中身を確認する。  
  ```bash
  sudo -u tools01 -H sqlite3 /home/tools01/.onsitelogistics/scan_queue.db \
    "SELECT id, target, payload FROM scan_queue ORDER BY id;"
  ```
- `scan_id` や `order_code` が欠けているレコードは、以下のいずれかで処理する。  
  1. **削除**: `DELETE FROM scan_queue WHERE id=<ID>;` を実行して破棄。  
  2. **補正**: `UPDATE scan_queue SET payload='<修正後JSON>' WHERE id=<ID>;` で整合を取った後、`--drain-only` で再送。  
- キューが空になったかは `SELECT COUNT(*) FROM scan_queue;` で確認する。ゼロであれば `handheld_scan_display.py --drain-only` の実行結果も「Pending queue size: 0」となる。

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
