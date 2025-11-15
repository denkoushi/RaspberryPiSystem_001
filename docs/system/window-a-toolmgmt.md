# Window A 工具管理データ取り込みメモ

Pi4（Window A）で運用する工具管理 UI のデータ源と同期手順をまとめる。TM-DIST USB → `window_a/master/*.csv` → PostgreSQL（`users` / `tool_master` / `tools` / `loans`）という流れを一本化し、Dashboard から一目で状況を確認できるようにする。

## 1. CSV 配置
- TM-DIST USB には `TOOLMASTER/master/` 以下に CSV を配置する（旧 OnSiteLogistics と同じ構造）。
- Pi4 側では `tool-dist-sync.sh` が `/home/tools02/RaspberryPiSystem_001/window_a/master/` へ同期する。想定ファイル:
  | ファイル名 | 役割 | 必須カラム |
  | --- | --- | --- |
  | `users.csv` | 社員 ID / フルネーム | `uid`, `full_name` |
  | `tool_master.csv` | 工具マスタ一覧 | `name` |
  | `tools.csv` | 工具タグ UID と工具名の対応表 | `uid`, `name` |
  | （将来）`loans.csv` | 旧システムの貸出履歴を移行する際に使用する。現在は DB 管理のため空で可。 |

> 旧システムと同じ UTF-8 (BOM 可) の CSV を想定。ヘッダー行が必須。

## 2. 取り込みフロー
1. `scripts/server/toolmaster/install_usb_services.sh --mode client-dist --client-home /home/tools02` を実行して Pi4 側の systemd/udev をセットアップする。
2. TM-DIST USB を挿入すると `usb-dist-sync@.service` が起動し、`tool-dist-sync.sh` が以下を実施する。  
   - `/usr/local/bin/tool-dist-sync.sh --device /dev/sdXn`
   - `/home/tools02/RaspberryPiSystem_001/window_a/master/` へ rsync
   - `RUN_IMPORTER_AFTER_SYNC=1` の場合は `/usr/local/bin/document-importer.sh` を実行（DocumentViewer 用）
   - `RUN_TOOL_MASTER_IMPORT=1`（デフォルト）なので `sudo -u tools02 -H /home/tools02/RaspberryPiSystem_001/window_a/.venv/bin/python window_a/scripts/import_tool_master.py --env-file window_a/config/window-a.env --master-dir window_a/master` を自動実行
3. 取り込み結果は PostgreSQL の `users` / `tool_master` / `tools` テーブルに反映され、Window A Dashboard の「工具管理」セクションにも同期日時・件数として表示される。

### 手動実行コマンド（確認用）
```bash
cd ~/RaspberryPiSystem_001/window_a
source .venv/bin/activate
python scripts/import_tool_master.py \
  --env-file config/window-a.env \
  --master-dir master \
  --truncate       # 必要に応じてテーブル初期化
deactivate
```

## 3. PostgreSQL テーブル
`window_a/app_flask.py` の `ensure_tables()` に定義。キー情報のみ抜粋。

| テーブル | カラム | 備考 |
| --- | --- | --- |
| `users` | `uid` (PK), `full_name` | 旧 `users.csv` の内容を保持。 |
| `tool_master` | `id` (serial PK), `name` (UNIQUE) | 工具名称マスタ。CSV の `name` を一意化。 |
| `tools` | `uid` (PK), `name` (FK → `tool_master.name`) | 工具タグ UID と紐付く表示名。 |
| `loans` | `id`, `tool_uid`, `borrower_uid`, `loaned_at`, `returned_at`, `return_user_uid` | Pi Zero の貸出スキャンで更新される。CSV 取り込みでは直接触らない。 |

## 4. Dashboard 表示
- Flask テンプレート `window_a/templates/index.html` では工具管理カードに次の要素を常設。
  - 同期ファイルの更新状況 (`master_files`)
  - Pi5 REST `/api/v1/loans` を呼び出した結果（貸出中リスト／直近履歴）
  - API トークン状態（マスク済み）と、未設定時の警告表示
  - 操作ログ欄（Pi5 へ送信した結果を時刻付きで追記）
  - 最終取得時刻（Pi5 側から受信した `fetched_at` を表示）
- Pi5 で `[tool_management] enabled = true` にすると `/api/v1/loans`（互換 `/api/loans`）と手動返却/削除 API を利用できる。Window A は `_create_raspi_client()` を介してこれらの REST API と通信し、ローカル DB へ直接アクセスしない。
- 手動返却 (`/api/v1/loans/<id>/manual_return`) や貸出削除 (`/api/v1/loans/<id>`) も Pi5 側で実行され、Window A の `api_actions.log` に操作ログが記録される。
- Dashboard 上のボタン操作は AJAX (`fetch`) で Pi5 API を呼び出し、応答後に `/api/toolmgmt/overview` を再取得して表を差し替えるため、ページを更新しなくても最新状態へ即時追従できる。
- Pi5 の `/api/logistics/jobs` は `LOGISTICS_PROVIDER` を通じて提供される。既定では `LOGISTICS_JOBS_FILE=config/logistics-jobs.sample.json` を参照し、JSON ファイルを `FileLogisticsProvider` で読み込む。`config/local.toml` で `LOGISTICS_JOBS_FILE` を実データのパスに差し替えるか、`LOGISTICS_JOBS` に直接 JSON を埋め込むと Window A の「物流依頼」カードへ反映される。

## 5. 運用チェックリスト（Pi4）
1. USB 挿入後に `journalctl -u usb-dist-sync@<device>.service -n 20` を確認し、`tool master importer completed` のログが出ているか検証。
2. `sudo -u tools02 -H psql -d sensordb -c "SELECT COUNT(*) FROM tool_master;"` で件数を確認。
3. Window A Dashboard の「同期ファイル」セクションで件数と更新日時が一致しているか確認。
4. `docs/test-notes/2025-11/window-a-demo.md` にログとスクリーンショットを残す。

## 6. 今後の TODO
- Window A UI からの貸出/返却操作を Pi5 `/api/v1/loans` へ完全移行し、ローカル DB 直接更新コードを縮小する。  
- 旧工具管理 UI の操作（手動返却、貸出削除など）を Flask API と連動させ、`api_actions.log` に監査証跡を残す。

## 7. Pi5 側設定と API 動作確認
Pi5（`/srv/RaspberryPiSystem_001/server`）で工具管理 API を有効化し、Window A から呼び出せる状態にする。

1. `server/config/local.toml` に `[tool_management]` ブロックを追加/更新して有効化する。  
   ```toml
   [tool_management]
   enabled = true
   dsn = "postgresql://app:app@localhost:15432/sensordb"  # 既定の [database].dsn を流用する場合は省略可
   ```
2. 最新コードを反映し、pytest を確認した上で systemd を再起動する。  
   ```bash
   cd /srv/RaspberryPiSystem_001
   git pull
   cd server
   source .venv/bin/activate
   python -m pytest                 # 必須ではないが失敗時は修正してから進める
   deactivate
   sudo systemctl restart raspi-server.service
   sudo journalctl -u raspi-server.service -n 40 --no-pager
   ```
3. REST エンドポイントのヘルスチェック。  
   ```bash
   curl http://localhost:8501/api/v1/loans
   curl -X POST http://localhost:8501/api/v1/loans/1/manual_return
   curl -X DELETE http://localhost:8501/api/v1/loans/1
   ```
   - `tool_management.enabled=false` の場合は HTTP 503 / `{"error":"tool_management_unavailable"}` が返る。
   - 応答内容とログ（`server/logs/app.log` 等）を `docs/test-notes/2025-11/window-a-demo.md` に記録しておくと、Window A 側の障害切り分けに使える。

## 8. Pi4 (Window A) の再同期と Dashboard 検証
Pi4 側では USB 同期→PostgreSQL 取り込み→Dashboard 表示を 1 セットで確認する。Pi5 で API が起動済みであることが前提。

1. Window A コードを更新し、必要に応じて依存を再インストールする。  
   ```bash
   cd ~/RaspberryPiSystem_001
   git pull
   cd window_a
   source .venv/bin/activate
   pip install -r requirements.txt   # requirements が変わった場合のみ
   pytest
   deactivate
   ```
2. TM-DIST USB サービスを再適用（初回のみ）。  
   ```bash
   cd ~/RaspberryPiSystem_001
   sudo scripts/server/toolmaster/install_usb_services.sh --mode client-dist --client-home /home/tools02
   ```
3. USB を挿入し、`journalctl -u usb-dist-sync@<device>.service -n 40` で `tool master importer completed` が出ることを確認する。自動実行された `import_tool_master.py` のログは `/var/log/toolmgmt.log` と `api_actions.log` に出力される。
4. Dashboard を開き、  
   - 「同期ファイル」カードに CSV の更新日時と件数が表示されること  
   - 「工具貸出状況」カードが Pi5 `api/v1/loans` の内容（貸出中・履歴）を表示していること  
   を確認する。必要に応じてスクリーンショットを `docs/test-notes/2025-11/window-a-demo.md` に追加する。
5. 画面に表示される「手動返却」「削除」ボタンを押して Pi5 側 API で処理されるか（HTTP 200 ＋ `api_actions.log` への記録）を確認する。ブラウザの結果欄と Pi5 の `server/logs/app.log` / `curl` の結果も併記しておくと復旧手順が明確になる。API トークンが未設定の場合はボタンが自動的に無効化されるため、Pi4 の `window_a/config/window-a.env` で token を発行してから再表示する。操作が成功すると `/api/toolmgmt/overview` から最新情報を取得してテーブルが自動更新されるため、F5 に頼らず貸出状況を追跡できる。

> Pi4 のブラウザを再起動したり DocumentViewer 埋め込みを更新した際も、必ず `git pull` → `toolmgmt.service` 再起動 → Dashboard 目視 → テストノート更新の流れを維持する。Window A 側で直接 DB を触る調査は一時的に留め、最終的な状態は常に Pi5 REST API を通過させる。

## 9. Pi5 物流ジョブのデータ差し替え手順
Window A の「物流依頼」カードは Pi5 `/api/logistics/jobs` の結果を表示する。実装データへ切り替える場合は以下を実施する。

1. `server/config/logistics-jobs.sample.json` をコピーして実運用データを作成する。  
   ```bash
   cd /srv/RaspberryPiSystem_001/server/config
   cp logistics-jobs.sample.json logistics-jobs.json
   $EDITOR logistics-jobs.json   # 実データを JSON 配列で記述
   ```
2. Pi5 の `config/local.toml` に `LOGISTICS_JOBS_FILE` を設定する（相対パスの場合は `/srv/.../server/` からの相対）。  
   ```toml
   LOGISTICS_JOBS_FILE = "/srv/RaspberryPiSystem_001/server/config/logistics-jobs.json"
   ```
   または `LOGISTICS_JOBS = [{...}]` と JSON 配列を直接記述すると `JSONLogisticsProvider` が使われる。
3. 設定変更後は従来どおり `git pull` → `python -m pytest` → `sudo systemctl restart raspi-server.service` を実行して反映する。
4. Pi4 側 Dashboard の「物流依頼」カードに新しいジョブが表示されることを確認し、`docs/test-notes/2025-11/window-a-demo.md` にスクリーンショットと確認手順を記録する。

## 10. TM-DIST USB を新規整備する手順
まっさらな USB メモリを TM-DIST 用に整備するときは以下を実施する。

1. Pi4 に USB を挿し、デバイス名を確認する。  
   ```bash
   lsblk -o NAME,FSTYPE,SIZE,LABEL,MOUNTPOINT
   ```
2. ext4 フォーマットとラベル設定（例: デバイスが `/dev/sda1` の場合）。  
   ```bash
   sudo mkfs.ext4 -F -L TM-DIST /dev/sda1
   sudo tune2fs -m 0 /dev/sda1          # 予約領域をゼロに（任意）
   ```
3. `.toolmaster/role` を作成し、役割を `DIST` に固定する。  
   ```bash
   sudo mkdir -p /mnt/tm_dist
   sudo mount /dev/sda1 /mnt/tm_dist
   sudo mkdir -p /mnt/tm_dist/.toolmaster
   echo "DIST" | sudo tee /mnt/tm_dist/.toolmaster/role
   ```
4. `master/`・`docviewer/` ディレクトリを作成し、必要な CSV や文書を入れる。最低限の空ファイルでも可。  
   ```bash
   sudo mkdir -p /mnt/tm_dist/master
   sudo tee /mnt/tm_dist/master/users.csv >/dev/null <<'EOF'
   uid,full_name
   EOF
   sudo tee /mnt/tm_dist/master/tool_master.csv >/dev/null <<'EOF'
   name
   EOF
   sudo tee /mnt/tm_dist/master/tools.csv >/dev/null <<'EOF'
   uid,name
   EOF
   sudo mkdir -p /mnt/tm_dist/docviewer
   sudo umount /mnt/tm_dist
   ```
5. これ以降は `tool-dist-sync.sh --device /dev/sda1` で同期・インポートできる。ログは `/srv/RaspberryPiSystem_001/server/logs/usb_dist_sync.log` に出力される。

## 11. Pi5 生産計画 / 標準工数データの準備
「生産計画 / 標準工数」カードは `/api/v1/production-plan` / `/api/v1/standard-times` のレスポンスを表示している。Pi5 では JSON ファイルまたは PostgreSQL テーブルをデータソースとして選べる。

1. **JSON ファイル運用**  
   - `server/config/production-plan.sample.json` / `standard-times.sample.json` を複製し、実データを記入する。  
   - `config/local.toml` に以下のように設定する。  
     ```toml
     PRODUCTION_PLAN_FILE = "/srv/RaspberryPiSystem_001/server/config/production-plan.json"
     STANDARD_TIMES_FILE = "/srv/RaspberryPiSystem_001/server/config/standard-times.json"
     ```
2. **PostgreSQL テーブル運用**  
   - `config/local.toml` に `PRODUCTION_PLAN_TABLE = "production_plan_entries"`、`STANDARD_TIMES_TABLE = "standard_time_entries"` を指定し、`[database].dsn` を Pi5 の sensordb に向ける。  
   - 初期データ投入は `server/scripts/seed_plan_tables.py` を使用する。  
     ```bash
     cd /srv/RaspberryPiSystem_001/server
     source .venv/bin/activate
     python scripts/seed_plan_tables.py \
       --dsn postgresql://app:app@localhost:15432/sensordb \
       --truncate
     deactivate
   ```
3. 設定変更後は `git pull` → `python -m pytest` → `sudo systemctl restart raspi-server.service` の順で Pi5 を再起動し、Window A のカードで最新データが表示されることを確認する。

## 12. Pi4 ↔ Pi5 ネットワーク / DB チェックリスト
LAN を切り替えた直後など、Pi4 から Pi5 の PostgreSQL へ接続できない場合は次の順に切り分ける。

1. **Pi5 側の PostgreSQL コンテナを確認**  
   ```bash
   cd /srv/RaspberryPiSystem_001/server
   docker compose up -d postgres
   docker compose ps postgres
   PGPASSWORD=app psql -h 127.0.0.1 -p 15432 -U app -d sensordb -c '\dt'
   ```
   テーブル一覧が表示されれば DB 自体は稼働している。
2. **Pi4 から Pi5 への疎通確認**  
   ```bash
   ping -c 3 192.168.xxx.xxx            # Pi5 の現在の IP
   PGPASSWORD=app psql -h 192.168.xxx.xxx -p 15432 -U app -d sensordb -c '\dt'
   ```
   ここで成功すればネットワークと認証は問題ない。
3. **ホスト名解決と `DATABASE_URL` の整合性**  
   - `/etc/hosts` で `raspi-server.local` を Pi5 の現行 IP に向ける。  
     LAN が変わると IP も変わるため、更新を忘れると Pi4 だけ古い IP を参照し続ける。  
   - もしくは `window_a/config/window-a.env` の `DATABASE_URL` を直接 IP ベースに書き換える（例: `postgresql://app:app@192.168.128.128:15432/sensordb`）。  
     編集後は `sudo systemctl restart toolmgmt.service` を実行し `sudo journalctl -u toolmgmt.service -n 40 --no-pager` でエラーが出ていないかを確認する。
4. **再発防止**  
   - Pi5 の IP が変わる運用が続く場合は、Pi4 の `/etc/hosts` を更新する手順または上記 `DATABASE_URL` の書き換え手順を `docs/test-notes/2025-11/window-a-demo.md` に都度記録し、LAN 切替え後は必ず実施するようチェックリスト化する。

このチェックリストに従うことで、今回発生したような「Pi4 から psql は通るのに systemd 経由では接続できない」トラブルを短時間で再現・修正できる。
