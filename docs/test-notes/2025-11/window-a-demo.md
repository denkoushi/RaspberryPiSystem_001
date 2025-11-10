# Window A デモテストメモ (2025-11-05)

## REST 応答確認
- `docker compose up -d` で PostgreSQL 起動 → `./scripts/init_db.sh`, `seed_backlog.py`, `drain_backlog.py` で `TEST-001`〜`TEST-005` を投入。
- `server/config/local.toml` を作成し、`SCAN_REPOSITORY_BACKEND = "db"`／`database.dsn = "postgresql://app:app@localhost:15432/sensordb"` を指定。
- Flask サーバー (`RPI_SERVER_CONFIG=~/RaspberryPiSystem_001/server/config/local.toml`) を起動し、以下のコマンドで確認。
  ```bash
  cd ~/RaspberryPiSystem_001
  source server/.venv/bin/activate
  python client_window_a/scripts/check_part_locations.py
  ```
- 出力例:
  ```python
  {'entries': [
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-E1', 'order_code': 'TEST-005', 'updated_at': '2025-11-04 00:40:56.155083+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-D1', 'order_code': 'TEST-004', 'updated_at': '2025-11-04 00:34:42.575703+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-C1', 'order_code': 'TEST-003', 'updated_at': '2025-11-04 00:29:08.875170+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-B1', 'order_code': 'TEST-002', 'updated_at': '2025-11-03 22:58:31.110353+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-A1', 'order_code': 'TEST-001', 'updated_at': '2025-11-03 22:55:58.506797+00:00'}
  ]}
  ```
- 2025-11-04 07:49 (JST) 実施結果:
  ```python
  {'entries': [
      {'device_id': 'HANDHELD-42', 'location_code': 'RACK-Y0', 'order_code': 'TEST-910', 'updated_at': '2025-11-04 01:58:03.541858+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-Z1', 'order_code': 'TEST-901', 'updated_at': '2025-11-04 01:57:55.945996+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-Z3', 'order_code': 'TEST-903', 'updated_at': '2025-11-04 01:57:55.945996+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-Z2', 'order_code': 'TEST-902', 'updated_at': '2025-11-04 01:57:55.945996+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-E1', 'order_code': 'TEST-005', 'updated_at': '2025-11-04 00:40:56.155083+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-D1', 'order_code': 'TEST-004', 'updated_at': '2025-11-04 00:34:42.575703+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-C1', 'order_code': 'TEST-003', 'updated_at': '2025-11-04 00:29:08.875170+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-B1', 'order_code': 'TEST-002', 'updated_at': '2025-11-03 22:58:31.110353+00:00'},
      {'device_id': 'HANDHELD-01', 'location_code': 'RACK-A1', 'order_code': 'TEST-001', 'updated_at': '2025-11-03 22:55:58.506797+00:00'}
  ]}
  ```

## 次のステップ
- `client_window_a/docs/manual-test.md` の手順に沿って、Socket.IO を含むデモ UI の手動テストを実施予定。
- バックログドレインはスクリプトに加えて `POST /api/v1/admin/drain-backlog` でトリガー可能（`{"limit": 50}` など）。
- `AUTO_DRAIN_ON_INGEST` を設定すると、スキャン受付時に自動ドレインが走りレスポンスに `backlog_drained` が含まれる。
- 2025-11-05 07:36 (JST): `curl POST /api/v1/scans` で `TEST-965` を送信 → サーバーログに Socket.IO emit 成功が記録され、Window A リスナー(`scripts/listen_for_scans.ts --api http://127.0.0.1:8501`) で `scan.ingested` イベントを受信できることを確認。
- 2025-11-05 10:00 (JST): `server/scripts/smoke_scan.sh` 実行。`SMOKE-1762304404` を送信し HTTP 202 / Socket.IO emit 成功をログで確認。テスト後にポートは自動解放済み。
- 2025-11-05 10:40 (JST): Docker/PostgreSQL を起動し `BacklogDrainService('postgresql://app:app@localhost:15432/sensordb').drain_once()` を実行。`drained 18` / `pending 0` を確認し、`part_locations` に upsert されたレコードを `psql` で検証。
- 2025-11-05 10:42 (JST): `./scripts/pi_zero_pull_logs.sh pi-zero.local --service handheld@tools01.service --output ./pi-zero-logs` を試行。以下のファイルが生成され、journal・mirrorctl・systemctl のログを取得できることを確認。  
  ```
  pi-zero-logs/pi-zero.local-20251105-104200/mirrorctl-status.txt
  pi-zero-logs/pi-zero.local-20251105-104200/journalctl-handheld@tools01.service.log
  pi-zero-logs/pi-zero.local-20251105-104200/systemctl-status.txt
  pi-zero-logs/pi-zero.local-20251105-104200/system-info.txt
  ```
- 2025-11-05 10:45 (JST): 事前チェックログを `docs/test-notes/2025-11/pi-zero-precheck.md` にまとめ、実機検証開始前の状態を記録。
# Window A / DocumentViewer Socket.IO デモ記録（2025-11）

| 日時 | シナリオ | Pi5 ログ確認 | Window A ログ | DocumentViewer ログ | 結果 | 備考 |
| --- | --- | --- | --- | --- | --- | --- |
| 2025-11-11 13:00 (準備中) | Pi Zero → Pi5 → Window A Socket.IO e2e | `journalctl -u raspi-server.service -n 120` / `tail -n 200 /srv/RaspberryPiSystem_001/server/logs/socket.log` | `npx ts-node scripts/listen_for_scans.ts --api http://192.168.10.230:8501 --socket-path /socket.io --token $SOCKET_API_TOKEN` | `sudo tail -f /var/log/document-viewer/client.log` | 未実施 | Window A 依存更新を反映後に実施。Pi Zero 側は `handheld_scan_display.py --drain-only` でトリガー予定。 |
| 2025-11-10 11:30 (予定) | Pi Zero から通常スキャン (A/B) | `journalctl -u raspi-server.service -n 80` / `tail -n 120 /srv/RaspberryPiSystem_001/server/logs/socket.log` | `npx ts-node scripts/listen_for_scans.ts --api http://192.168.10.230:8501 --socket-path /socket.io` | `tail -f /var/log/document-viewer/client.log` | 未実施 | Pi5 統合後初の Socket.IO 実機テスト |
| 2025-11-10 11:13 | Pi5 新 systemd 反映 / healthz 確認 | `sudo journalctl -u raspi-server.service --since "2025-11-10 11:13"` | - | - | PASS | `/srv/RaspberryPiSystem_001/server/.venv/bin/python ...` で稼働、`curl -I http://localhost:8501/healthz` が 200 OK。旧 `/srv/rpi-server` は `*_legacy_20251110` に退避済み。 |

## 2025-11-10 Window A 依存更新メモ
- Debian trixie (Python 3.13) では `psycopg2-binary==2.9.9` がビルド不可のため、tool-management-system02 を `psycopg[binary]==3.2.3` へ移行。  
- `app_flask.py` の接続コードを `psycopg.connect(**DB)` に変更し、`tests/test_load_plan.py` のスタブも `psycopg` に合わせた。  
- 以後は `python3 -m venv venv` → `pip install -r requirements.txt` で trixie 環境でもセットアップが通る。Pi Zero / Pi5 も同依存に揃えることで将来の Python 3.13 対応が確実になる。
- 本リポジトリの `window_a/` ディレクトリに、上記変更を反映した `requirements.txt` / `app_flask.py` / `tests/test_load_plan.py` を配置した。VS Code から Window A リポジトリへコピーする際はここを最新版のソース・オブ・トゥルースとして利用する。

## 2025-11-11 Python 3.13 / psycopg2 ビルド失敗への対処

### 状況整理
- Raspberry Pi OS (Debian trixie, Python 3.13) 上で `psycopg2-binary==2.9.9` をビルドすると `_PyInterpreterState_Get` が見つからず `error: implicit declaration of function '_PyInterpreterState_Get'` → `undefined symbol` で失敗する。  
- これは公式 Issue [psycopg/psycopg2#1692](https://github.com/psycopg/psycopg2/issues/1692) で追跡されており、Python 3.13 で `_PyInterpreterState_Get` が `PyInterpreterState_Get` に公開/改名されたことが原因と明記されている。Linux (aarch64) でも同じビルドエラーが再現する。  
- Pi4 でのみ顕在化したのは、Window A (tool-management-system02) だけがまだ `psycopg2` を固定しており、Pi Zero / Pi5 はすでに `RaspberryPiSystem_001/server` と同様に `psycopg[binary]>=3.2` へ移行済みだったため。

### ラズパイ別の影響
- **Pi Zero / Pi5**: `server/pyproject.toml` で `psycopg[binary]>=3.2.0` を採用済み。Python 3.13 / Debian trixie でもインストール可能であり、`server/.venv` 上で `pytest` が 31 件 PASS することを確認 (2025-11-11)。  
- **Pi4 (Window A)**: 旧 `tool-management-system02` のままなので `requirements.txt` に `psycopg2-binary==2.9.9` が残っており、venv 再構築のたびにビルド失敗 → 作業が止まっていた。

### 対処ポリシー
1. **依存関係を `psycopg[binary]==3.2.12` に固定**  
   ```text
   Flask==2.3.3
   Flask-SocketIO==5.3.6
   psycopg[binary]==3.2.12
   pyscard==2.0.7
   requests==2.31.0
   ```
2. **DB 接続コードを psycopg3 API に揃える**  
   ```python
   import psycopg

   def get_connection():
       return psycopg.connect(
           host=DB["host"],
           port=DB["port"],
           dbname=DB["dbname"],
           user=DB["user"],
           password=DB["password"],
           connect_timeout=5,
       )
   ```
3. **テストダブルの更新**  
   - `tests/test_load_plan.py` などで `psycopg2.connect` をモックしていた箇所を `psycopg.connect` に変更。  
   - Flask サーバー起動スクリプト (`app_flask.py`) も psycopg3 へ統一する。

### ラズパイセットアップ手順 (再掲)
```bash
cd ~/tool-management-system02
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pytest
```
- Debian trixie では PEP 668 によりシステム Python への `pip install` がブロックされるため、**必ず venv を作成**する。`--break-system-packages` の乱用は避け、どうしても必要なら一時的な検証に限定する。参考: [PEP 668 – Marking Python base environments as “externally managed”](https://peps.python.org/pep-0668/).

### 公式情報との整合
- psycopg2 Issue [#1692](https://github.com/psycopg/psycopg2/issues/1692) で Python 3.13 との非互換が議論され、「3.13 向けの公式ビルドは 2.9.10 以降で提供予定」とメンテナが回答済み。  
- 我々の対応 (psycopg3 への移行) は、同 issue で案内されている「Python 3.13 では新 API を用いる」方針と一致する。  
- Pi Zero / Pi5 側も同じ psycopg3 を採用することで、新 OS へ切り替わっても追加作業は不要になる。

## Raspberry Pi 3 台の Python 3.13 / psycopg3 反映状況（2025-11-11）

| デバイス | 実体 | リポジトリ/ディレクトリ | 依存状況 | 確認・実施すべき手順 |
| --- | --- | --- | --- | --- |
| Pi5 (tools02) | `/srv/RaspberryPiSystem_001` | `server/pyproject.toml` に `psycopg[binary]>=3.2.0` を記載済み。`server/.venv` では `pip install -e ".[dev]"` と `pytest` (31 件) が 2025-11-11 に PASS。 | 反映済み | `sudo -u pi5 -H bash -lc 'cd /srv/RaspberryPiSystem_001/server && source .venv/bin/activate && pip show psycopg && pytest'` を定期実行してログを `docs/test-notes/2025-11/pi5-verification.md` 等に記録する。 |
| Pi Zero (tools01) | `/home/tools01/RaspberryPiSystem_001` | handheld モジュールで psycopg3 を利用中（`handheld/src/retry_loop.py` など）。`scripts/update_handheld_override.sh` で main ブランチと同期。 | 反映済み (コード側) | `sudo -u tools01 -H bash -lc 'cd ~/RaspberryPiSystem_001 && git status -sb && source ~/.venv-handheld/bin/activate && pip show psycopg'` で 3.2.x か確認。再送キュー drain も合わせてログ化。 |
| Pi4 (Window A / tools02) | `~/RaspberryPiSystem_001/window_a` | 2025-11-11 に `~/tool-management-system02` を `*_legacy_` へ退避し、新リポジトリを clone。`pip show psycopg` で 3.2.12、`pytest` で 4 件 PASS を確認済み。 | 反映済み (2025-11-11) | 以後は `~/RaspberryPiSystem_001/window_a` で `git pull` → `.venv/bin/pytest` を実行し、systemd `toolmgmt.service` の WorkingDirectory も同パスに統一する。 |

### Pi4 実施コマンド（例）
```bash
cd ~/tool-management-system02
git pull
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pytest
```
> Pi4 は PEP 668 によりシステム Python が「外部管理」扱いなので、`--break-system-packages` を避け、必ず venv 内で完結させる。pytest ログと `pip show psycopg` の出力を `docs/test-notes/2025-11/window-a-demo.md` に追記する。

## Pi4 (Window A) ディレクトリ統一メモ

現在 Pi4 は旧リポジトリ `~/tool-management-system02` をそのまま運用しているため、`git pull` しても `psycopg[binary]` の変更が届かない。`docs/system/repo-structure-plan.md` に従い、以下の段取りで `~/RaspberryPiSystem_001` へ統一する。

1. **サービス停止 & 旧ディレクトリ退避**
   ```bash
   sudo systemctl stop toolmgmt.service
   mv ~/tool-management-system02 ~/tool-management-system02_legacy_$(date +%Y%m%d)
   ```
2. **新リポジトリ clone**
   ```bash
   git clone https://github.com/denkoushi/RaspberryPiSystem_001.git ~/RaspberryPiSystem_001
   cd ~/RaspberryPiSystem_001
   git checkout feature/repo-structure-plan   # 進行中ブランチ
   ```
3. **Window A サブディレクトリのセットアップ**  
   - `window_a/requirements.txt` を使って venv を作成。  
   - `client_window_a/` も同じワークツリーで管理し、`npm install` などのセットアップをやり直す。  
```bash
cd ~/RaspberryPiSystem_001/window_a
python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   pip show psycopg
   pytest
```
4. **systemd 更新**  
   - `setup_auto_start.sh` や `/etc/systemd/system/toolmgmt.service` の `WorkingDirectory` と `ExecStart` を `/home/tools02/RaspberryPiSystem_001/window_a` に変更。  
   - `sudo systemctl daemon-reload && sudo systemctl start toolmgmt.service` で再起動。
5. **ログ記録**  
   - 上記コマンドの出力を本ファイルに貼り付け、`docs/system/next-steps.md` のダッシュボードを更新する。

### Pi4 セットアップ実績（2025-11-11 17:20 JST）
```
(.venv) tools02@raspberrypi:~/RaspberryPiSystem_001/window_a $ pip show psycopg
Name: psycopg
Version: 3.2.12
Location: /home/tools02/RaspberryPiSystem_001/window_a/.venv/lib/python3.13/site-packages

(.venv) tools02@raspberrypi:~/RaspberryPiSystem_001/window_a $ pytest
============================= test session starts ==============================
platform linux -- Python 3.13.5, pytest-9.0.0, pluggy-1.6.0
rootdir: /home/tools02/RaspberryPiSystem_001/window_a
collected 4 items

tests/test_load_plan.py ....                                             [100%]
======================== 4 passed, 2 warnings in 1.14s =========================
```
※ warnings は旧 smartcard SWIG 由来で既知。テスト本体は PASS。

### Pi5 / Pi Zero セットアップログ
- Pi5 (2025-11-11 18:05 JST)
  ```
  cd /srv/RaspberryPiSystem_001/server
  source .venv/bin/activate
  pip show psycopg
  # psycopg 3.2.12, pytest 31 passed
  ```
- Pi Zero (2025-11-11 18:20 JST)
  ```
  cd ~/RaspberryPiSystem_001/handheld
  source ~/.venv-handheld/bin/activate
  pip show psycopg
  PYTHONPATH=.. pytest tests
  # 5 passed, DeprecationWarning(datetime.utcnow)
  ```

### Pi5 ログパス検証（2025-11-11 08:15 JST）
`docs/system/repo-structure-plan.md:42-54` に従って Pi5 側のログディレクトリ作成と systemd 再起動を実施。`journalctl` では正常に停止→起動が確認できたものの、`app.log` が生成されていないため `tail` が失敗している。
```
denkon5ssd@raspi-server:~ $ sudo mkdir -p /srv/RaspberryPiSystem_001/server/logs
denkon5ssd@raspi-server:~ $ sudo chown -R denkon5ssd:denkon5ssd /srv/RaspberryPiSystem_001/server/logs
denkon5ssd@raspi-server:~ $ sudo systemctl daemon-reload
denkon5ssd@raspi-server:~ $ sudo systemctl restart raspi-server.service
denkon5ssd@raspi-server:~ $ sudo journalctl -u raspi-server.service -n 120 --no-pager
Nov 10 17:22:57 raspi-server systemd[1]: Started raspi-server.service - RaspberryPiSystem_001 server.
Nov 11 08:14:12 raspi-server systemd[1]: Stopping raspi-server.service - RaspberryPiSystem_001 server...
Nov 11 08:14:12 raspi-server systemd[1]: raspi-server.service: Deactivated successfully.
Nov 11 08:14:12 raspi-server systemd[1]: Stopped raspi-server.service - RaspberryPiSystem_001 server.
Nov 11 08:14:12 raspi-server systemd[1]: Started raspi-server.service - RaspberryPiSystem_001 server.
denkon5ssd@raspi-server:~ $ tail -n 50 /srv/RaspberryPiSystem_001/server/logs/app.log
tail: /srv/RaspberryPiSystem_001/server/logs/app.log: そのようなファイルやディレクトリはありません
```
→ server 側で `logging.path` を読んでファイルハンドラを初期化する処理が未実装。`server/src/raspberrypiserver/app.py` へ `logging.basicConfig` などを追加し、`app.logger` がファイルへ出力するよう修正する。

### Pi5 ログファイル出力実装（ローカル確認 2025-11-11 10:05 JST）
Mac 上で `server/src/raspberrypiserver/app.py` にファイルロギング設定を追加し、`server/tests/test_logging_config.py` を新設して検証。`pytest` 全件 PASS。
```
% cd server && pytest
============================= test session starts ==============================
collected 32 items
...
tests/test_logging_config.py .                                           [ 90%]
...
============================== 32 passed in 6.51s ==============================
```
→ `APP_NAME` に応じたログ行が `tmp/logs/app.log` に書き込まれることを確認済み。Pi5 実機に反映すると `/srv/RaspberryPiSystem_001/server/logs/app.log` が自動生成される見込み。

### Pi5 ログファイル標準パスのフォールバック追加（2025-11-11 18:40 JST）
- `server/src/raspberrypiserver/app.py` に `DEFAULT_LOG_PATH=<repo_root>/logs/app.log` を定義し、`.toml` に `[logging]` 設定が無くても `<リポジトリ>/logs/app.log` が作成されるように変更。
- Pi5 実機では `/srv/RaspberryPiSystem_001/server/logs/app.log` が自動生成される想定。既存の `server/config/default.toml` でパス指定済みのため、Pi5 側では `git pull` → `.venv` 再インストール後に `sudo systemctl restart raspi-server.service && tail -n 50 /srv/RaspberryPiSystem_001/server/logs/app.log` を再実行して生成を確認する。

### Pi5 ログ出力確認（2025-11-11 08:30 JST）
```
denkon5ssd@raspi-server:/srv/RaspberryPiSystem_001/server $ sudo systemctl daemon-reload
denkon5ssd@raspi-server:/srv/RaspberryPiSystem_001/server $ sudo systemctl restart raspi-server.service
denkon5ssd@raspi-server:/srv/RaspberryPiSystem_001/server $ sudo journalctl -u raspi-server.service -n 120 --no-pager
... Started raspi-server.service ...
denkon5ssd@raspi-server:/srv/RaspberryPiSystem_001/server $ tail -n 50 /srv/RaspberryPiSystem_001/server/logs/app.log
2025-11-11 08:28:04,839 WARNING [raspberrypiserver.services.backlog] Skipping backlog row id=2 due to missing order/location (order=None, location=LOC-MISSING)
2025-11-11 08:28:04,840 INFO [raspberrypiserver.services.backlog] Backlog drain succeeded: processed=1 limit=10 table=scan_ingest_backlog
...
2025-11-11 08:28:04,952 INFO [raspberrypiserver.services.backlog] Backlog drain succeeded: processed=1 limit=5 table=scan_ingest_backlog
```
→ `/srv/RaspberryPiSystem_001/server/logs/app.log` に backlog / Socket.IO の詳細ログが出力されることを確認。既存の backlog テストデータにより WARNING が複数出ているが、ログファイル生成自体は成功している。

### Pi4 Window A 名寄せ途中経過（2025-11-11 08:31 JST）
```
cd ~/RaspberryPiSystem_001 && git pull
cd window_a && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pytest  # 4 passed

sudo systemctl stop toolmgmt.service
sudo systemctl daemon-reload
sudo systemctl start toolmgmt.service
sudo journalctl -u toolmgmt.service -n 120 --no-pager
```
`toolmgmt.service` は `ModuleNotFoundError: usb_sync` のため 5 秒間隔でリスタートを繰り返す状態。Window A API `/api/usb_sync` が未移植の `usb_sync` モジュールを import していることが原因。

### usb_sync スタブの追加（2025-11-11 09:00 JST）
- `window_a/usb_sync.py` を新規作成し、以下の挙動を提供:
  - `WINDOW_A_USB_SYNC_CMD` 環境変数または `window_a/scripts/usb_sync.(sh|py)` が存在すればそのコマンドを呼び出す。
  - 上記が存在しない場合は WARNING を記録しつつ returncode=1 の結果を返す（API が 500 を返すのは維持）。
- これにより `app_flask` import 時の `ModuleNotFoundError` が解消され、Window A systemd サービスは起動可能となる。実運用の USB 同期ロジックは後続タスクで `scripts/usb_sync.sh` を移植する。

### Pi4 systemd 切り替えログ
```
# PATH/ExecStart の .venv 化と旧 EnvironmentFile の除去
sudo sed -i 's#/window_a/venv/#/window_a/.venv/#g' /etc/systemd/system/toolmgmt.service
sudo sed -i 's#^EnvironmentFile=/home/tools02/tool-management-system02/config/window-a-client.env#;EnvironmentFile removed#g' /etc/systemd/system/toolmgmt.service.d/window-a.conf

sudo systemctl daemon-reload
sudo systemctl start toolmgmt.service
sudo systemctl status toolmgmt.service -n 20 --no-pager

# 出力
● toolmgmt.service - Tool Management System (Flask + SocketIO)
     Loaded: loaded (/etc/systemd/system/toolmgmt.service; enabled)
    Drop-In: /etc/systemd/system/toolmgmt.service.d
             └─window-a.conf
     Active: active (running) since 2025-11-10 15:21:29 JST
   Main PID: 5417 (/home/tools02/RaspberryPiSystem_001/window_a/.venv/bin/python)
```
旧 `EnvironmentFile` をコメントアウトしたため、必要な環境変数は `window_a/config/window-a-client.env` など新パスへ移す予定。現状は `.env` を読み込まずとも起動・Socket.IO 接続が完了している。

### Pi5 / Pi Zero で取得する確認ログ
1. **Pi5 (tools02)**  
   ```bash
   cd /srv/RaspberryPiSystem_001/server
   source .venv/bin/activate
   pip install pytest  # 初回のみ
   pip show psycopg
   pytest
   ```
   - 出力を本ファイルに貼り付け、Pi4 と同じく psycopg 3.2.x / pytest PASS を証跡として残す。
2. **Pi Zero (tools01)**  
   - まず `handheld/requirements.txt` を this repo から `scp` するか `git pull` で取得し、以下を実行。  
     ```bash
     cd ~/RaspberryPiSystem_001/handheld
     python3 -m venv ~/.venv-handheld
     source ~/.venv-handheld/bin/activate
     pip install --upgrade pip
     pip install -r requirements.txt
     pip show psycopg
     pytest handheld/tests
     ```
   - 必要に応じて `HANDHELD_HEADLESS=1 python handheld/scripts/handheld_scan_display.py --drain-only` のログも取得し、再送キューが空であることを示す。  
3. 3 台分のログが揃ったら `docs/test-notes/2025-11/window-a-socket-plan.md` のシナリオに従って Socket.IO 実機テストへ進む。


### Pi5 / Pi Zero セットアップログ
- **Pi5** (2025-11-11 18:05 JST)
  ```
  Name: psycopg
  Version: 3.2.12
  Location: /srv/RaspberryPiSystem_001/server/.venv/lib/python3.13/site-packages
  pytest ... 31 passed
  ```
- **Pi Zero** (2025-11-11 18:20 JST)
  ```
  Name: psycopg
  Version: 3.2.12
  Location: /home/denkonzero/.venv-handheld/lib/python3.13/site-packages
  PYTHONPATH=.. pytest tests  # 5 passed (warnings due to datetime.utcnow)
  ```

## 記録テンプレート（追記用）
- **日時 / スキャン内容**: YYYY-MM-DD HH:MM, A=xxxx, B=xxxx  
- **Pi5 ログ抜粋**: `api_actions.log`, `socket.log` の抜粋  
- **Window A ログ**: `scripts/listen_for_scans.ts` 出力  
- **DocumentViewer ログ**: `/var/log/document-viewer/client.log` から抜粋  
- **UI スクリーンショット**: Window A / DocumentViewer の更新結果  
- **判定 / フォローアップ**: PASS/FAIL と追加アクション
