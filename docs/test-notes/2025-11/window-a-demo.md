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
# Pi4 DocumentViewer USB インポーター検証（2025-11-13）

- **目的**: `document_viewer/scripts/document-importer.sh` の新しいデフォルト（`DOCVIEWER_HOME` 未指定でも実行ユーザーの `~/RaspberryPiSystem_001/document_viewer` を優先）と権限自動補正が Pi4（tools02）で機能するか確認する。
- **前提**: `feature/repo-structure-plan` を最新化し、`sudo install -m 755 document_viewer/scripts/document-importer*.sh /usr/local/bin` を実施済み。`~/RaspberryPiSystem_001/document_viewer/{documents,imports}` は `tools02:tools02` に変更済み。
- **手順**
  1. `sudo mount /dev/sda1 /media/tools02/TM-DIST && sleep 5`
  2. `sudo /usr/local/bin/document-importer.sh /media/tools02/TM-DIST`
  3. `sudo tail -n 30 /var/log/document-viewer/import.log`
  4. `sudo tail -n 20 /var/log/document-viewer/client.log`
- **結果 (2025-11-13 11:15 JST)**  
  - `import.log` に `INFO USB payload validation passed` → `INFO local PDFs are up to date (usb_ts=1762995277, local_ts=1762995277)` → `INFO importer finished with code 0` が追記され、`DOCVIEWER_HOME` の明示設定なしでも `/home/tools02/.../documents` を参照。  
  - `client.log` は変化なし（TEST-001 の過去ログのみ）。  
  - 自動 inotify は「新規マウントディレクトリ」作成時のみ発火するため、手動 `mount` ではログは動かず。物理的な USB 抜き差し、もしくは udev/systemd (`scripts/server/toolmaster/install_usb_services.sh`) を導入して `/media/tools02/TM-DIST1` などが生成されるパスで検証する必要がある。  
- **今後の TODO**  
  - USB 抜き差し時に `/media/tools02/TM-DIST1` などの生成を確認し、`journalctl -u document-importer.service --since "1 minute ago"` へ自動イベントが記録されることを撮影。  
  - `docs/system/next-steps.md` の DocumentViewer セクションに「Pi4 importer 権限修正済み／自動検知検証 pending」と追記。  
  - Pi4 でも `scripts/server/toolmaster/install_usb_services.sh --mode client-dist --client-home /home/tools02` を適用し、`usb-dist-sync@.service` で `tool-dist-sync.sh`→`document-importer.sh` を自動実行する。  

## Pi4 USB 自動同期リグレッション（2025-11-13）

- **目的**: Pi5→TM-DIST→Pi4 DocumentViewer の配布フローを、USB 挿抜だけで“同期→importer→viewer”まで自動完結させる。  
- **手順**  
  1. Pi5 (`/srv/RaspberryPiSystem_001`) で `sudo /usr/local/bin/tool-dist-export.sh --device /dev/sda1` を実行し、`12:26:48` の `dist export completed` を確認。  
  2. Pi4 (`~/RaspberryPiSystem_001`) で `sudo ./scripts/server/toolmaster/install_usb_services.sh --mode client-dist --client-home /home/tools02` を再適用し、`sudo udevadm trigger --subsystem-match=block --action=add` を実行。  
  3. USB を挿し直して待機。`journalctl -u usb-dist-sync@sda1.service --since "1 minute ago"` に `running importer /usr/local/bin/document-importer.sh /run/toolmaster/sda1` → `importer completed for /run/toolmaster/sda1` が記録されることを確認。  
  4. `sudo tail -n 20 /var/log/document-viewer/import.log` の最新行に `INFO USB payload validation passed` → `INFO local PDFs are up to date (usb_ts=..., local_ts=...)` → `INFO importer finished with code 0` が記録されていることを確認。  
- **結果 (PASS)**  
  - Pi4 は USB 挿抜だけで `tool-dist-sync.sh` → `document-importer.sh` が自動実行され、`DOCVIEWER_HOME=/home/tools02/RaspberryPiSystem_001/document_viewer` を参照して PDF を同期。  
  - `tool-dist-sync.sh` の `RUN_IMPORTER_AFTER_SYNC=1` ルートで importer が呼び出され、`/run/toolmaster/sda1` から直接読み取り→アンマウントまで行うため、DocumentViewer サービス側の inotify 依存は不要になった。  
  - DocumentViewer UI (`http://127.0.0.1:5000/`) で `TEST-001` を検索し、2025-11-13 13:09 JST に PDF が即時表示された。`/var/log/document-viewer/client.log` に `Document lookup success: TEST-001 -> TEST-001.pdf` と `Document served` が追記されている。  

# Window A / DocumentViewer Socket.IO デモ記録（2025-11）

| 日時 | シナリオ | Pi5 ログ確認 | Window A ログ | DocumentViewer ログ | 結果 | 備考 |
| --- | --- | --- | --- | --- | --- | --- |
| 2025-11-13 13:29 | Pi5 → Window A Socket.IO e2e（`send_scan.py` + DocumentViewer 表示） | `/srv/RaspberryPiSystem_001/server/logs/app.log` に `Socket.IO emit succeeded` を確認 | `npx ts-node scripts/listen_for_scans.ts --api http://192.168.10.230:8501 --socket-path /socket.io --token raspi-token-20251026` | `/var/log/document-viewer/client.log` に `Document lookup success: TEST-HELLO -> TEST-HELLO.pdf` | PASS | Pi5 から `send_scan.py --order TEST-HELLO` を実行 → Pi4 DocumentViewer で即時表示。Pi Zero からの実機スキャンは次フェーズで実施。 |
| 2025-11-13 16:33 | Pi Zero → Pi5 → Window A Socket.IO e2e（`send_scan_headless.py`） | `/srv/RaspberryPiSystem_001/server/logs/app.log` に `Received scan payload: {'order_code': 'TEST-ZERO', ...}` → `Socket.IO emit succeeded` を確認 | `npx ts-node scripts/listen_for_scans.ts ...` に `scan.ingested` が表示 | `/var/log/document-viewer/client.log` に `Document lookup success: TEST-ZERO -> TEST-ZERO.pdf` | PASS | Pi Zero (tools01) をヘッドレス送信で実行 → Pi5/Window A/DocumentViewer まで `TEST-ZERO` が反映。 |
| 2025-11-14 09:18 | Pi Zero 実機 UI スキャン（A=4989999058963, B=https://e.bambulab.com/t/?c=ga8XCc2Q6l1idFKP） | `/srv/RaspberryPiSystem_001/server/logs/app.log` に受信ログと `Socket.IO emit succeeded` が残り、HTTP 202 応答を確認（PostgreSQL 未起動のため persist は WARNING） | -（Window A Socket.IO リスナー未起動につきログ未取得） | `/var/log/document-viewer/client.log` は 11/13 までで STOP；11/14 分は要再取得 | 部分完了 | Pi Zero 電子ペーパーは DONE 表示まで動作。Window A/DocumentViewer のログは次回スキャン時にリスナーを起動して採取する。 |
| 2025-11-14 09:45 | Pi Zero 実機 UI スキャン（A=6975337037026, B=URL:orange-book） | `/srv/RaspberryPiSystem_001/server/logs/app.log` に `Received scan payload …` と `Socket.IO emit succeeded` が記録。HTTP 202 で応答、DB 永続化は PostgreSQL 未起動のため WARNING | `client_window_a/scripts/listen_for_scans.ts` で `scan.ingested` を受信（payload に order/location/device_id/metadata を確認） | `/var/log/document-viewer/client.log` は依然 11/13 で停止（document-viewer.service がログ出力していない or inotify 未反応）。次回テスト前に `sudo systemctl restart document-viewer.service && sudo truncate -s0 /var/log/document-viewer/client.log` でログを再生成してから実施する。 | 部分完了 | Pi Zero→Pi5→Window A の流れは確認済み。DocumentViewer 側のログ未取得が残課題。 |
| 2025-11-14 10:36 | Pi Zero 実機 UI スキャン（A=6975337037026, B=6975337037026 等） | `/srv/RaspberryPiSystem_001/server/logs/app.log` に 10:25/10:33/10:36 の受信ログを追記。HTTP 202、Socket.IO emit 成功。 | Pi4 Chromium を常時起動（Socket: LIVE）させた状態で実施。 | `/var/log/document-viewer/client.log` に `2025-11-14 10:36:57,094 INFO Socket.IO event: scan.ingested payload=...` が出力され、ブラウザ起動中は従来方式でログ取得できることを確認。 | PASS | DocumentViewer ログを取得したい場合はブラウザを常時起動すれば OK。バックグラウンド listener の導入は必須ではない。 |
| 2025-11-10 11:30 (予定) | Pi Zero から通常スキャン (A/B) | `journalctl -u raspi-server.service -n 80` / `tail -n 120 /srv/RaspberryPiSystem_001/server/logs/socket.log` | `npx ts-node scripts/listen_for_scans.ts --api http://192.168.10.230:8501 --socket-path /socket.io` | `tail -f /var/log/document-viewer/client.log` | 未実施 | Pi5 統合後初の Socket.IO 実機テスト |
| 2025-11-10 11:13 | Pi5 新 systemd 反映 / healthz 確認 | `sudo journalctl -u raspi-server.service --since "2025-11-10 11:13"` | - | - | PASS | `/srv/RaspberryPiSystem_001/server/.venv/bin/python ...` で稼働、`curl -I http://localhost:8501/healthz` が 200 OK。旧 `/srv/rpi-server` は `*_legacy_20251110` に退避済み。 |
| 2025-11-13 10:30 | TM-DIST → DocumentViewer USB 同期（Pi5 export + Pi4 importer） | `/srv/RaspberryPiSystem_001/server/logs/usb_dist_export.log`（09:54 `dist export completed`） | `sudo /usr/local/bin/tool-dist-sync.sh --device /dev/sda1`, `sudo /usr/local/bin/document-importer.sh /media/tools02/TM-DIST` | `/var/log/document-viewer/import.log` と `client.log` に `Document lookup success: TEST-001` を確認 | PASS | `document-importer.sh` が `~/RaspberryPiSystem_001/document_viewer` を自動参照するよう修正済み。Pi4 の自動 importer でも同ディレクトリを扱えることを次回確認する。 |

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

### station_config スタブの追加（2025-11-11 09:20 JST）
- `window_a/station_config.py` を新設。`window_a/config/station_config.json` を読み書きする軽量実装を提供し、環境変数 `WINDOW_A_STATION_CONFIG` で保存場所を切り替えられる。
- `tests/test_station_config.py` を追加して `load_station_config` / `save_station_config` の正常動作を保証 (`pytest` 6 件 PASS)。
- 今後、旧リポジトリにあったステーション設定ロジックを段階的に移植するまではこの JSON ストレージを参照する。

### Pi4 → Pi5 DB 接続復旧ログ（2025-11-11 09:20 JST）
- `window_a/config/window-a.env` を旧 `tool-management-system02/config/window-a-client.env.sample` を参照し、`RASPI_SERVER_BASE`・`RASPI_SERVER_API_TOKEN`・`DATABASE_URL=postgresql://app:app@raspi-server.local:15432/sensordb` などを移植。`/etc/systemd/system/toolmgmt.service.d/window-a-env.conf` で `EnvironmentFile` を読み込むよう設定。
- Pi5 で Docker PostgreSQL (`docker compose up -d postgres`) を起動し、`sudo docker compose exec postgres psql -U app -d sensordb -c "ALTER USER app WITH PASSWORD 'app';"` で旧システムと同じ資格情報に揃える。
- Pi4 側で `sudo systemctl restart toolmgmt.service` を実行すると、過去ログに `password authentication failed` が残るものの、09:20 JST 以降は安定稼働し Flask 起動ログのみが出力されている。
  ```
  Nov 11 09:20:07 raspberrypi systemd[1]: Started toolmgmt.service - Tool Management System (Flask + SocketIO).
  Nov 11 09:20:09 raspberrypi python[5288]: 📡 NFCスキャン監視スレッド開始
  Nov 11 09:20:09 raspberrypi python[5288]: 🚀 Flask 工具管理システムを開始します...
  Nov 11 09:20:09 raspberrypi python[5288]: 🌐 http://0.0.0.0:8501 でアクセス可能
  Nov 11 09:20:09 raspberrypi python[5288]: 💡 タイムアウトエラーは正常動作（タグ待機中）なので無視して良い
  Nov 11 09:20:09 raspberrypi python[5288]:  * Serving Flask app 'app_flask'
  Nov 11 09:20:09 raspberrypi python[5288]:  * Running on http://127.0.0.1:8501 / http://192.168.10.223:8501
  ```

### api_token_store / raspi_client の暫定実装（2025-11-11 09:45 JST）
- `window_a/api_token_store.py`: `window_a/config/api_tokens.json` を用いたトークン管理を実装。`list_tokens`, `issue_token`, `revoke_token`, `get_active_tokens`, `get_token_info` を提供。テスト (`tests/test_api_token_store.py`) で file I/O を検証。
- `window_a/raspi_client.py`: `requests` ベースの最小 HTTP クライアントを実装し、`RaspiServerClient.from_env()` で `RASPI_SERVER_BASE` / `RASPI_SERVER_API_TOKEN` を読み込む。`tests/test_raspi_client.py` で例外分岐と JSON パースを確認。
- Pi4 で `git pull` → `pytest`（12 件）→ `sudo systemctl restart toolmgmt.service` を実施済み。次回の `journalctl` では `api_token_store` の import エラーが解消され、残る依存関係を順次移設予定。

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

### Window A / DocumentViewer Socket 切り分けメモ（2025-11-11 21:45 JST）
- Pi5 `logs/app.log` では `Socket.IO emit succeeded` が継続しており、POST `/api/v1/scans` → `scan.ingested` ブロードキャストまでは正常に動いていることを確認。
- Pi4 側で `VIEWER_API_BASE` / `VIEWER_SOCKET_BASE` を `http://192.168.10.230:8501` に統一し、Flask を再起動。`tail -f ~/DocumentViewer/logs/client.log` はイベント未着のため空。
- Window A 手動リスナー (`scripts/listen_for_scans.ts`) を `TS_NODE_TRANSPILE_ONLY=1` で起動し、`curl -X POST ...TEST-001...` を複数回発行してもイベントが出力されない事象を再現。
- 切り分けのため `client_window_a/src/socket.ts` を更新し、`path`（`/socket.io` 既定）・namespace 正規化・debug ログ（connect/disconnect/onAny）を追加。CLI から `SOCKET_DEBUG=1` で詳細ログを取得できるようにした。`npm test -- tests/socket.test.ts` で回 regresion PASS。
- 次ステップ: Pi4 で新バージョンを `git pull` → `npm install` → `scripts/listen_for_scans.ts` 再実行し、デバッグログ (`[scan-socket] event scan.ingested ...`) が出力されるか確認。DocumentViewer 側の JavaScript も同様の namespace/path を参照しているか要確認。

### DocumentViewer Socket イベント更新（2025-11-11 22:30 JST）
- `~/DocumentViewer/app/viewer.py` に `VIEWER_SOCKET_EVENTS` / `VIEWER_SOCKET_EVENT` の解決ロジックを追加し、デフォルトで `scan.ingested,part_location_updated,scan_update` を購読。`DOCVIEWER_CONFIG.socketEvents` 経由でフロントへ渡すよう更新。
- `~/DocumentViewer/app/static/app.js` で `config.socketEvents` を正規化し、指定されたイベントそれぞれに `handleSocketPayload` を紐付けるよう実装。console.debug で受信イベントを出力。
- `config/docviewer.env.sample` / `README.md` を更新し、新環境変数の使い方を明記。`docs/system/documentviewer-integration.md` の接続設定表も Pi5 実機の値に合わせて刷新。
- `~/DocumentViewer/tests/test_viewer_app.py` を調整し、新しい環境変数が HTML と内部定数へ反映されることを検証。`cd ~/DocumentViewer && pytest` で 10件 PASS（2025-11-11 22:31 JST）。

### DocumentViewer Socket ログ連携（2025-11-11 22:50 JST）
- DocumentViewer に `/api/socket-events` を追加し、フロントエンドで受信した Socket.IO イベントを POST すると `VIEWER_LOG_PATH` へ `Socket.IO event: <name> payload=...` が記録されるようにした。`app/static/app.js` は `navigator.sendBeacon` → `fetch(keepalive)` でサーバーへ通知。
- `tests/test_viewer_app.py` に API の 201 応答 / ログ書き込み / 非 JSON 400 応答のテストを追加。`pytest` は 12 件 PASS。
- 次の検証時は Pi4 で DocumentViewer を再起動し、Window A から `curl` 送信 → `tail -f ~/DocumentViewer/logs/client.log` で `Socket.IO event: scan.ingested` を確認する。

### 2025-11-11 15:28 JST SocketIO 受信テスト（Pi4）
- `cd ~/DocumentViewer && git pull && mv config/docviewer.env.local config/docviewer.env` で最新化し、`FLASK_APP=viewer.py flask run --host 0.0.0.0 --port 8500` を再起動。`curl -X POST http://127.0.0.1:8500/api/socket-events ...` で 201 応答を確認し、`~/DocumentViewer/logs/client.log` へ `Socket.IO event: connect.test payload={'note': 'manual test'}` が記録されることを確認。
- Window A 手動リスナー（`TS_NODE_TRANSPILE_ONLY=1 ... scripts/listen_for_scans.ts`）で `[scan-socket] event scan.ingested {...}` が出力され、並行して `tail -f ~/DocumentViewer/logs/client.log` は `2025-11-11 15:17:03,082 INFO Socket.IO event: connect.test payload={'note': 'manual test'}` のみ記録（`scan.ingested` は今回まだ未記録のため、後続でイベント送信フローを継続監視する）。
- 追加で `VIEWER_SOCKET_EVENTS=scan.ingested,part_location_updated,scan_update` を `config/docviewer.env` に追記し再テストしたが、現時点ではログは `connect.test` のみで `scan.ingested` は未記録。DocumentViewer フロントの `/api/socket-events` 呼び出しを継続調査中。

### 2025-11-12 10:30 JST /var/log/document-viewer 整備
- Pi4 で `VIEWER_API_BASE=http://127.0.0.1:8500`, `VIEWER_SOCKET_BASE=http://192.168.10.230:8501`, `VIEWER_SOCKET_CLIENT_SRC=https://cdn.socket.io/4.7.5/socket.io.min.js` へ設定を戻し、`sudo mkdir -p /var/log/document-viewer && sudo chown tools02:tools02 /var/log/document-viewer` を実行。
- DocumentViewer を再起動し、Window A から `curl` で `TEST-001` を送信したところ `/var/log/document-viewer/client.log` に以下が記録されることを確認。
  ```
  2025-11-12 10:10:52,956 INFO Socket.IO event: scan.ingested payload={'order_code': 'TEST-001', 'location_code': 'RACK-A1', 'device_id': 'HANDHELD-01'}
  2025-11-12 10:10:52,986 INFO Document not found: TEST-001
  ```
- これにより Socket.IO 受信ログが正常化したため、今後の環境構築手順に `/var/log/document-viewer` の作成と権限設定を必須作業として追加する。

### 2025-11-12 10:45 JST systemd テンプレート追記
- `docs/system/documentviewer-integration.md` に DocumentViewer の systemd ユニット例とセットアップ手順（`.venv` 作成、`pip install -r requirements.txt`、`/var/log/document-viewer` 作成、`systemctl enable --now`）を追記。
- これにより Pi4 での再起動手順が明文化され、新規 Pi 展開時も同じ設定で自動起動できる。

## 記録テンプレート（追記用）
- **日時 / スキャン内容**: YYYY-MM-DD HH:MM, A=xxxx, B=xxxx  
- **Pi5 ログ抜粋**: `api_actions.log`, `socket.log` の抜粋  
- **Window A ログ**: `scripts/listen_for_scans.ts` 出力  
- **DocumentViewer ログ**: `/var/log/document-viewer/client.log` から抜粋  
- **UI スクリーンショット**: Window A / DocumentViewer の更新結果  

### Pi4 DocumentViewer 本リポジトリ移行（2025-11-12 13:40 JST）
- Pi4 で `~/RaspberryPiSystem_001` を `git pull`。DocumentViewer 一式が `document_viewer/` として取り込まれていることを確認。
- 旧 `document-viewer.service` を停止し、新ディレクトリで仮想環境を作成:  
  `cd ~/RaspberryPiSystem_001/document_viewer/app && python3 -m venv ../.venv && source ../.venv/bin/activate && pip install -r requirements.txt`
- `/etc/systemd/system/document-viewer.service` を `WorkingDirectory=/home/tools02/RaspberryPiSystem_001/document_viewer/app` 等に書き換え、`sudo systemctl daemon-reload && sudo systemctl enable --now document-viewer.service` で再登録。`status` は `active (running)` を確認。
- `config/docviewer.env` の `VIEWER_API_BASE` を `http://127.0.0.1:5000` へ戻し（CORS 解消）、`VIEWER_SOCKET_BASE` は Pi5 (`http://192.168.10.230:8501`) を維持。`sudo systemctl restart document-viewer.service` で反映。
- 旧リポジトリの `~/DocumentViewer/documents/TEST-001.pdf` を新ディレクトリの `documents/` へコピー。将来的には importer を新パスに合わせる必要あり。
- 既存 PDF の大量移行用に `document_viewer/scripts/migrate_legacy_documents.sh` を追加。`./scripts/migrate_legacy_documents.sh --legacy ~/DocumentViewer/documents --target "$DOCVIEWER_HOME/documents"` で一括コピー可能（`--dry-run` 対応）。
- Chromium で `http://127.0.0.1:5000` を再表示し、Window A から `curl -X POST /api/v1/scans`（order_code=TEST-001）を実行。  
  `/var/log/document-viewer/client.log` に  
  ```
  2025-11-12 13:39:18,721 INFO Socket.IO event: scan.ingested payload={'order_code': 'TEST-001', ...}
  2025-11-12 13:39:18,730 INFO Document lookup success: TEST-001 -> TEST-001.pdf
  2025-11-12 13:39:18,798 INFO Document served: TEST-001.pdf
  ```  
  が記録され、ブラウザ側でも PDF が自動表示された。

### Pi4 DocumentViewer 旧ドキュメント移行（2025-11-12 14:20 JST）
- `cd ~/RaspberryPiSystem_001/document_viewer && ./scripts/migrate_legacy_documents.sh --legacy ~/DocumentViewer/documents --target ~/RaspberryPiSystem_001/document_viewer/documents --dry-run` で差分を確認（`TEST-001.pdf`, `testpart.pdf` のみ検出）。
- 同コマンドから `--dry-run` を外して本実行し、旧 `~/DocumentViewer/documents` から新 `document_viewer/documents` へコピー。rsync 出力をログへ記録。
- `sudo systemctl restart document-viewer.service` 実行後、Window A から `curl -X POST /api/v1/scans ... TEST-001` を送信。  
  `/var/log/document-viewer/client.log` に  
  ```
  2025-11-12 14:18:23,596 INFO Socket.IO event: scan.ingested payload={'order_code': 'TEST-001', 'location_code': 'RACK-A1', 'device_id': 'HANDHELD-01'}
  2025-11-12 14:18:23,626 INFO Document lookup success: TEST-001 -> TEST-001.pdf
  ```  
  が追記され、ブラウザでも PDF が自動表示されたことを確認。
- 今後は importer/systemd が新パスを前提としているため、追加 PDF も同スクリプトで同期後に `document-viewer.service` を再起動する。
- **判定 / フォローアップ**: PASS/FAIL と追加アクション

### Pi4 USB インポートデーモン整備（2025-11-12 15:40 JST）
- `scripts/document-importer.sh` / `systemd/document-importer.service` を `DOCVIEWER_HOME=~/RaspberryPiSystem_001/document_viewer` 対応へ更新し、Pi4 でも `git pull` 後に `/usr/local/bin` へ再配置。
- `sudo tee /etc/sudoers.d/document-viewer <<'EOF' ... EOF` を追加し、`tools02` が `sudo -n systemctl restart document-viewer.service` を実行できるようにした。
- `/tmp/USB_TEST/docviewer` に `TEST-001.pdf` と `meta.json` を配置して `sudo mount --bind /tmp/USB_TEST /media/tools02/TMP-USB` を実施。  
  `journalctl -u document-importer.service --since "1 minute ago"` には
  ```
  INFO detected mount at /media/tools02/TMP-USB
  INFO USB payload validation passed
  INFO found 1 pdf file(s) in /media/tools02/TMP-USB/docviewer
  INFO copied TEST-001.pdf to /home/tools02/RaspberryPiSystem_001/document_viewer/documents
  INFO restarted document-viewer.service
  ```
  が記録され、自動的に PDF がコピーされることを確認。
- `/var/log/document-viewer/import.log` にも成功ログが追記され、Importer 手動実行時と同じログが残る。以降は sudoers 設定済みのため WARNING は解消。

### 2025-11-14 13:40 JST Window A DB 接続調査
- `toolmgmt.service` を RaspberryPiSystem_001 ベースのユニットへ切り替えたが、起動直後から `[DB] connect retry N/30: connection failed ... port 5432 refused` が継続。`/var/log/document-viewer/client.log` は Pi Zero からの `scan.ingested` を受信しているため、Socket.IO 連携は正常。
- 原因切り分けのため、Pi4 側で DSN 可視化＋疎通確認スクリプト `window_a/scripts/check_db_connection.py` を追加。環境ファイルを引き渡した実行例:
  ```bash
  cd ~/RaspberryPiSystem_001
  source window_a/.venv/bin/activate  # 既存 venv があれば
  python window_a/scripts/check_db_connection.py \
    --env-file window_a/config/window-a.env \
    --timeout 3
  deactivate
  ```
- 現時点では `raspi-server.local:15432` への接続で `status=error ... connection refused` となるため、Pi5 側 PostgreSQL (`sensordb`) を起動し、外部ホストからアクセス可能な状態にする必要あり。  
  - Pi5 で `docker compose up -d postgres` または `sudo systemctl start postgresql@14-main` (採用方式に合わせて選択) を実施。
  - `PGPASSWORD=app psql -h 0.0.0.0 -p 15432 -U app -d sensordb -c '\l'` が Pi5 で成功したら、Pi4 からも上記スクリプトで再チェックしてログを更新する。
  - 成功後は `window_a/logs/api_actions.log` と `part_locations` テーブルを確認し、Window A UI で貸出ステータスが更新されるか追跡する。

### 2025-11-14 14:02 JST Pi Zero 実機スキャン & DocumentViewer ログ
- Pi5 で Docker Postgres (`server/docker-compose.yaml`) を起動後、Pi4 `window_a/scripts/check_db_connection.py --env-file config/window-a.env` が `status=ok target=raspi-server.local:15432` を返すことを確認。
- Pi Zero (`denkonzero`) で `sudo systemctl stop handheld@tools01.service` → `HANDHELD_HEADLESS=1 python handheld/scripts/handheld_scan_display.py --drain-only` でキュー空を確認後、通常モードで A/B (`4989999058963`, `https://e.bambulab.com/t/?c=ga8XCc2Q6l1idFKP`) をスキャン。CLI には `Server accepted payload` が表示。
- Pi5 `/srv/RaspberryPiSystem_001/server/logs/app.log` 抜粋:
  ```
  2025-11-14 14:01:59,939 INFO [raspberrypiserver.api.scans] Received scan payload: {...}
  2025-11-14 14:01:59,941 WARNING [raspberrypiserver.repositories.scans] Scan payload persistence failed: connection failed: connection to server at "127.0.0.1", port 5432 failed: Connection refused
  2025-11-14 14:01:59,941 WARNING [app] Socket.IO emit succeeded: event=scan.ingested ...
  ```
- Pi4 `/var/log/document-viewer/client.log` 抜粋:
  ```
  2025-11-14 14:01:59,938 INFO Socket.IO event: scan.ingested payload={'order_code': '4989999058963', 'location_code': 'https://e.bambulab.com/t/?c=ga8XCc2Q6l1idFKP', ...}
  ```
- 判定: Socket.IO 連携は Pi Zero → Pi5 → Pi4 まで動作。DB 永続化はまだ無効（Pi5 の `SCAN_REPOSITORY_BACKEND` が memory のため）だが、Window A / DocumentViewer の再接続検証は完了。

### 2025-11-14 14:15 JST Window A UI 500 対応
- Chromium で `http://192.168.10.223:8501` 表示時に `500 Internal Server Error` が発生し、`journalctl -u toolmgmt.service` には `jinja2.exceptions.TemplateNotFound: index.html` が記録されていた。
- 原因: 新リポジトリへ移植した際に Flask テンプレート (`window_a/templates/index.html`) が未配置だった。
- 対応: `window_a/templates/index.html` を追加し、DocumentViewer iframe / part_locations / logistics_jobs / production plan / station_config をシンプルなテーブルで表示するダッシュボードを実装。`socket_client_config` もブラウザ側で確認できる。
- 以後 `git pull` → `sudo systemctl restart toolmgmt.service` 後に再読み込みすれば 500 は解消される。DocumentViewer 側の `/api/documents/...` が 404 の場合でも UI 自体は表示できる。

### 2025-11-14 14:25 JST DocumentViewer ステータス更新
- `window_a/config/window-a.env` の `DOCUMENT_VIEWER_URL` を `http://127.0.0.1:5000` に設定し、`sudo systemctl restart toolmgmt.service` を実行。Dashboard のヘッダーが `DocumentViewer: ONLINE`（緑）になり、iframe 内にローカル 130.0.0.1 の DocumentViewer が表示されるようになった。
- Dashboard の運用手順: Pi4 ブラウザで `http://192.168.10.223:8501` を開いたら、ヘッダーの DocumentViewer/Socket ステータスが `ONLINE/LIVE` になっていることを確認。DocumentViewer タブ（`http://127.0.0.1:5000`）も並行で開いておく。
- `part_locations` と `logistics jobs` セクションは現状空欄。Pi5 の `/api/v1/part-locations` は `SCAN_REPOSITORY_BACKEND="memory"` のため再起動で消えるので、PostgreSQL 起動後に `db` backend へ切り替える必要がある。`/api/logistics/jobs` はファイルプロバイダ（`LOGISTICS_JOBS_FILE`）でプレースホルダーデータを表示できるようになったが、実データ運用は今後のタスク。
- **常時運用チェック（2025-11-14 時点）**  
  1. DocumentViewer (`http://127.0.0.1:5000`) をブラウザで開き、PDF が参照できる状態にする。  
  2. Window A Dashboard (`http://192.168.10.223:8501`) を開き、ヘッダーの `DocumentViewer: ONLINE` と `Socket: LIVE` を確認。  
  3. Pi Zero からスキャンすると `/var/log/document-viewer/client.log` に `scan.ingested` が追記されることを確認。  
  4. Pi5 の PostgreSQL を `docker compose up -d postgres` で起動している場合、`window_a/scripts/check_db_connection.py --env-file config/window-a.env` で疎通を確認。  
- 2025-11-14 16:56 JST: Pi Zero 実機で `4909411096557` → `4969887821220` をスキャン。Pi5 `/srv/RaspberryPiSystem_001/server/logs/app.log` には `Received scan payload` → `Backlog drain succeeded: processed=1` が出力され、`part_locations` に `order_code=4909411096557 / location_code=4969887821220` が記録された。Window A Dashboard の “最新の所在情報” も即座に更新されたためスクリーンショットで保存。

### 2025-11-14 14:40 JST Logistics API プレースホルダー
- Pi5 サーバーに `/api/logistics/jobs` を追加し、未実装時でも 404 ではなく `{"items": []}` を返すようにした（`server/src/raspberrypiserver/api/logistics.py`）。Dashboard は空リストをそのまま表示する。
- `LOGISTICS_PROVIDER` を Flask アプリの config に設定すれば `.list_jobs(limit)` を通じて結果を差し替え可能。将来的に PostgreSQL や別システムと連携する場合は Provider を実装する。
- `LOGISTICS_JOBS_FILE=/srv/RaspberryPiSystem_001/server/config/logistics-jobs.json` のように設定すると、`server/config/logistics-jobs.sample.json` を参考に静的 JSON を表示できる。Pi5 再起動時もこのファイルを編集すれば即座に Dashboard に反映される。
- 当面はファイルベースで運用し、実データ連携を行う際は Pi5 側で Provider を差し込むこと。
- Pi5 側設定例（`server/config/local.toml`）  
  ```toml
  LOGISTICS_JOBS_FILE = "/srv/RaspberryPiSystem_001/server/config/logistics-jobs.sample.json"
  PRODUCTION_PLAN_FILE = "/srv/RaspberryPiSystem_001/server/config/production-plan.sample.json"
  STANDARD_TIMES_FILE = "/srv/RaspberryPiSystem_001/server/config/standard-times.sample.json"
  ```
  `RPI_SERVER_CONFIG=/srv/RaspberryPiSystem_001/server/config/local.toml` を指定し `sudo systemctl restart raspberrypiserver` すれば適用される。Window A Dashboard の “物流依頼” や “生産計画 / 標準工数” セクションでサンプルが表示されることを確認する。
- 工具管理カード: Dashboard に「工具管理 (Tool Management)」セクションを追加し、現在は再構築中である旨をユーザーに明示。`window_a/app_flask.py` の `TOOLMGMT_STATUS_MESSAGE` で文言を変更できる。旧 UI の貸出/返却ロジックを移植するまでは、ここに進捗や注意事項だけを掲載する運用とする。

### 2025-11-14 16:00 JST 生産計画/標準工数モック
- `/api/v1/production-plan` / `/api/v1/standard-times` を追加し、`PRODUCTION_PLAN_FILE` / `STANDARD_TIMES_FILE` が指定されている場合は JSON ファイルから entries を返す。未設定時は空配列。
- サンプルデータは `server/config/production-plan.sample.json` / `server/config/standard-times.sample.json`。Pi5 でファイルを書き換えればそのまま Dashboard に反映される。
- PostgreSQL を利用する場合は `server/config/schema.sql` の `production_plan_entries` / `standard_time_entries` を追加（`./scripts/init_db.sh` 経由）し、`PRODUCTION_PLAN_TABLE` / `STANDARD_TIMES_TABLE` を `local.toml` に設定すると new DatabaseJSONProvider が参照する。JSON 形式で `payload` 列へ保管すれば UI 側もそのまま表示できる。
- DB へサンプルを投入するには `server/scripts/seed_plan_tables.py --dsn postgresql://app:app@localhost:15432/sensordb --truncate` を実行すると `production_plan_entries` / `standard_time_entries` に JSON をまとめて挿入できる。
- Pi4 Dashboard では「品名／担当／数量／納期／製番」が列として表示される。より詳細な表示を行う場合は JSON のキーを増やしてもそのまま table に出力される。

### 2025-11-15 13:20 JST Pi4 Dashboard 復旧とネットワーク手順整理
- 会社 ⇔ 自宅間で LAN が切り替わった際に `raspi-server.local` の IP が変わり、Pi4 systemd サービスだけが古い IP を参照していたため、`toolmgmt.service` が PostgreSQL へ接続できなくなった（`OperationalError: server closed the connection unexpectedly`）。コンソールから `psql -h 192.168.128.128` を実行すると成功するのに、サービスは失敗する状態だった。
- Pi5 で `docker compose up -d postgres` → `PGPASSWORD=app psql -h 127.0.0.1 -p 15432 -U app -d sensordb -c '\dt'` を実施し、DB が正常稼働していることを確認。合わせて `server/scripts/init_db.sh postgresql://app:app@localhost:15432/sensordb` を流して `users/tool_master/tools/...` テーブルを作成。
- Pi4 では `ping -c3 192.168.128.128` → `PGPASSWORD=app psql -h 192.168.128.128 ... '\dt'` の順で疎通を確認し、ネットワークと認証に問題が無いことを確認。原因を `window_a/config/window-a.env` の `DATABASE_URL` が `raspi-server.local` 参照のままだった点と特定し、IP ベース (`postgresql://app:app@192.168.128.128:15432/sensordb`) へ書き換えて `sudo systemctl restart toolmgmt.service` → `sudo journalctl -u toolmgmt.service -n 40 --no-pager` でエラーが消えたことを確認。  
  - 併せて `/etc/hosts` を新 LAN の IP に更新し、以後も IP が変わるたびに更新する運用をチェックリスト化。
- Dashboard は `http://192.168.128.102:8501` で再表示され、DocumentViewer/物流/生産計画カードも正常。Tool Management カードは CSV が空のため件数 0 表示だが、API トークン未設定で意図どおりの文言になっている。
- 上記の切り分け手順と再発防止策を `docs/system/window-a-toolmgmt.md` の「12. Pi4 ↔ Pi5 ネットワーク / DB チェックリスト」に反映済み。LAN 切替え時は必ず同節の手順に従うこと。

### 2025-11-15 13:30 JST Tool Master サンプル CSV インポート
- Pi5 `/srv/RaspberryPiSystem_001/TOOLMASTER/master/` にテスト用 CSV（users/tool_master/tools 各 2 行）を配置し、TM-DIST USB（`/dev/sdb1`）へ `rsync -a …/master/ /mnt/tm_dist/master/` でコピー → Pi4 へ持参。
- Pi4 で `sudo ./tool-dist-sync.sh --device /dev/sda1` を実行して `window_a/master/` に展開。
- `python scripts/import_tool_master.py --env-file config/window-a.env --master-dir master --truncate` を再実行したところ `[DONE] users=2 tool_master=2 tools=2` で完了し、Dashboard の工具管理カードに同期日時と件数が表示された。

### 2025-11-15 13:45 JST API トークン CLI 追加
- `window_a/scripts/manage_api_tokens.py` を追加し、`issue/list/revoke` サブコマンドで `config/api_tokens.json` を直接操作できるようにした。`python scripts/manage_api_tokens.py issue window-a-01 --note "初期発行"` → `list --reveal` で実値確認。
- `window_a/config/window-a.env` に `WINDOW_A_API_TOKEN_HEADER` / `WINDOW_A_API_TOKEN_FILE` / `API_TOKEN_ENFORCE=1` を追記し、`toolmgmt.service` 再起動後に Dashboard の工具管理カードで API トークンがマスク表示され、貸出操作が有効化された。
- `docs/system/window-a-toolmgmt.md` へ日次運用チェックリスト（TM-DIST 同期→ importer → Dashboard 確認 → トークン管理）を追加して手順化。

### 2025-11-15 14:45 JST Pi4 でのトークン発行・サービス再起動
- Pi4 (`tools02`) で `git pull` → `window_a/scripts/manage_api_tokens.py issue window-a-01 --note "initial"` を実行し、`/home/tools02/RaspberryPiSystem_001/window_a/config/api_tokens.json` にトークン `2z-R9t11hIB1in7XtkiI7kDpEmiHAB3s1oWN58gdjSw` を発行。`PYTHONPATH=.` を指定してスクリプトを呼び出した（`api_token_store` を正しく import するため）。  
- `sudo systemctl restart toolmgmt.service` 後、Dashboard (`http://192.168.128.102:8501`) の工具管理カードに `APIトークン: 2z-R***Sw (Station: window-a-01)` と表示され、同期ファイル欄も `[users/tool_master/tools = 2件]` を維持していることを確認。`tool_management_unavailable` は Pi5 REST が未接続のため赤字で残っており、次の作業は Pi5 `/api/v1/loans` を実データ化して UI 操作を有効化すること。

### 2025-11-15 15:41 JST Pi5 Loan API 確認
- Pi5 で `docker compose exec -T postgres psql -U app -d sensordb` を開き、`INSERT INTO loans (tool_uid, borrower_uid, loaned_at) VALUES ('t001','u001', now());` を実行しテスト貸出レコードを投入。
- Pi4 から `curl -H "Authorization: Bearer 2z-R9t11hIB1in7XtkiI7kDpEmiHAB3s1oWN58gdjSw" http://raspi-server.local:8501/api/v1/loans` を呼び出したところ、`open_loans` / `history` に `tool_name: "ドライバーA" / borrower: "山田太郎"` が表示され 200 応答となった。
- Dashboard の工具管理カードでも貸出中 1 件・履歴 1 件が表示され、`tool_management_unavailable` が解消。

### 2025-11-15 16:02 JST 手動返却ボタン確認
- Dashboard から貸出 ID=1 の「手動返却」を押下すると Pi5 `/api/v1/loans/1/manual_return` が 200 を返し、`return_user_uid` が `u001` で記録された。Pi5 ログにも `POST ... manual_return HTTP/1.1" 200` が出力された。
- UI の操作ログには REST 応答をそのまま表示しているため文言が "エラー" になっているが、レスポンス内容は `{"status":"ok" ...}` であり処理は成功。今後は表示文言を調整予定。


### 2025-11-15 16:08 JST 削除ボタン確認
- 新たに挿入した貸出 ID=2 (`t002`/`u002`) を Dashboard の「削除」から操作すると、Pi5 `/api/v1/loans/2` DELETE が 200 を返し、ログには `{"loan_id":2,"status":"deleted","tool_name":"ドライバーB"...}` が記録された。
- UI の操作ログは成功時も "エラー:" 表記だが、レスポンス内容は 200 のため表示文言を後日調整する予定。

