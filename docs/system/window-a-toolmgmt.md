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
- Flask テンプレート `window_a/templates/index.html` で以下を表示:
  - 同期ファイルの更新状況
  - 貸出中リスト／直近履歴（Pi5 REST `/api/v1/loans` から取得）
- Pi5 で `[tool_management] enabled = true` にすると `/api/v1/loans`（互換 `/api/loans`）と手動返却/削除 API を利用できる。Window A は `_create_raspi_client()` を介してこれらの REST API と通信し、ローカル DB へ直接アクセスしない。
- 手動返却 (`/api/v1/loans/<id>/manual_return`) や貸出削除 (`/api/v1/loans/<id>`) も Pi5 側で実行され、Window A の `api_actions.log` に操作ログが記録される。

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
5. 画面に表示される「手動返却」「削除」ボタンを押して Pi5 側 API で処理されるか（HTTP 200 ＋ `api_actions.log` への記録）を確認する。ブラウザの結果欄と Pi5 の `server/logs/app.log` / `curl` の結果も併記しておくと復旧手順が明確になる。API トークンが未設定の場合はボタンが自動的に無効化されるため、Pi4 の `window_a/config/window-a.env` で token を発行してから再表示する。

> Pi4 のブラウザを再起動したり DocumentViewer 埋め込みを更新した際も、必ず `git pull` → `toolmgmt.service` 再起動 → Dashboard 目視 → テストノート更新の流れを維持する。Window A 側で直接 DB を触る調査は一時的に留め、最終的な状態は常に Pi5 REST API を通過させる。
