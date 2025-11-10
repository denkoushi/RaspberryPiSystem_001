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
| Pi4 (Window A / tools02) | `~/tool-management-system02` | 旧 `psycopg2-binary==2.9.9` のまま。本リポジトリ内の `docs/test-notes/2025-11/window-a-demo.md` に対策メモのみ記載。`requirements.txt` / `app_flask.py` / `tests/test_load_plan.py` はローカルで修正済みだが **Git 未反映**。 | 未反映（要コミット & デプロイ） | 1. VS Code で `tool-management-system02` の差分 (`requirements.txt`, `app_flask.py`, `tests/test_load_plan.py`) をコミットし、リモートへ push。<br>2. Pi4 で `git pull && rm -rf venv && python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt && pytest` を実行。<br>3. 成功ログを本ファイルに貼り付け、`docs/system/next-steps.md` のダッシュボードを「完了」に更新する。 |

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

## 記録テンプレート（追記用）
- **日時 / スキャン内容**: YYYY-MM-DD HH:MM, A=xxxx, B=xxxx  
- **Pi5 ログ抜粋**: `api_actions.log`, `socket.log` の抜粋  
- **Window A ログ**: `scripts/listen_for_scans.ts` 出力  
- **DocumentViewer ログ**: `/var/log/document-viewer/client.log` から抜粋  
- **UI スクリーンショット**: Window A / DocumentViewer の更新結果  
- **判定 / フォローアップ**: PASS/FAIL と追加アクション
