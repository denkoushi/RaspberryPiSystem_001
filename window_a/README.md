# Window A モジュール

Pi4（Window A）で稼働する Flask ベースのダッシュボードと補助スクリプトをまとめたディレクトリ。Pi Zero から Pi5 へ送信された所在情報や DocumentViewer の状態を表示し、将来的には工具貸出 UI も再構築する。

## ディレクトリ構成
- `app_flask.py` — Flask アプリ本体。Socket.IO クライアントや API 呼び出しを統合する予定。
- `config/window-a.env` — Pi5 API、DocumentViewer、DB などの接続情報を定義する `.env`。`window_a/config/window-a.env.sample` を基に作成する。
- `requirements.txt` — Window A 専用の Python 依存。
- `scripts/` — DB 接続チェックなどの補助スクリプト。
- `templates/` — Flask/Bootstrap テンプレート。工具管理ペインや DocumentViewer 埋め込みをここで構築する。
- `tests/` — `pytest` ベースのユニットテスト。
- `master/` — TM-DIST USB から同期される CSV（`users.csv` / `tools.csv` / `tool_master.csv` など）の置き場。`tool-dist-sync.sh` がここへ展開する。

## Pi4 実機デプロイ（標準手順）
- **実行ユーザー / ディレクトリ**  
  - Pi4 では `tools02` ユーザーを標準とし、`/home/tools02/RaspberryPiSystem_001` を Git ワークツリーとする。  
  - systemd サービス `toolmgmt.service` もこのユーザーの `.venv` と `window_a/` ディレクトリを前提にしているため、別ユーザーで clone しても本番サービスでは使用しない。  
- **初期セットアップ**
  ```bash
  sudo systemctl stop toolmgmt.service
  sudo -u tools02 -H bash -lc '
    cd ~
    git clone https://github.com/denkoushi/RaspberryPiSystem_001.git RaspberryPiSystem_001
    cd RaspberryPiSystem_001/window_a
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
  '
  sudo systemctl daemon-reload
  sudo systemctl enable --now toolmgmt.service
  ```
  - 旧 `~/tool-management-system02` は `*_legacy_YYYYMMDD` へ退避し、参照専用にする。
- **定期更新フロー（Pi4 での `git pull`）**
  ```bash
  cd ~/RaspberryPiSystem_001
  git pull
  cd window_a
  source .venv/bin/activate
  pip install -r requirements.txt   # 依存追加があった場合のみ
  pytest
  deactivate
  sudo systemctl restart toolmgmt.service
  sudo journalctl -u toolmgmt.service -n 60 --no-pager
  ```
  - Chromium ベースのクライアント（`client_window_a/`）を併用する場合も同じワークツリーで `npm install && npm run build` を実行する。
- **工具マスタ CSV → PostgreSQL 取り込み**
  - `install_usb_services.sh --mode client-dist --client-home /home/tools02` を適用すると、TM-DIST USB の挿入→`tool-dist-sync.sh` 実行→`import_tool_master.py`→`document-importer.sh` の順で自動処理される。手動確認が必要な場合は以下の手順で実行する。  
  1. TM-DIST USB を挿入し、`scripts/server/toolmaster/tool-dist-sync.sh` で `window_a/master/` 以下に CSV を同期する。  
  2. `window_a/scripts/import_tool_master.py` を使って CSV を PostgreSQL に流し込む。  
     ```bash
     cd ~/RaspberryPiSystem_001/window_a
     source .venv/bin/activate
     python scripts/import_tool_master.py \
       --env-file config/window-a.env \
       --master-dir master
     deactivate
     ```
  3. 取り込み件数が `users/tool_master/tools` それぞれで表示される。必要に応じて `--truncate` で既存テーブルをクリアしてから再取り込みできる。
  4. 取り込み結果は Dashboard の「工具管理」カードに表示する予定のため、同期日時や件数は `docs/test-notes/2025-11/window-a-demo.md` に記録しておく。
- **設定ファイル**
- `window_a/config/window-a.env` の主要項目（`window_a/config/window-a.env.sample` をコピーして作成）:  
  ```
  RASPI_SERVER_BASE=http://raspi-server.local:8501
  RASPI_SERVER_API_TOKEN=raspi-token-XXXX
  DOCUMENT_VIEWER_URL=http://127.0.0.1:5000
  DATABASE_URL=postgresql://app:app@raspi-server.local:15432/sensordb
  ```
  - systemd の override (`/etc/systemd/system/toolmgmt.service.d/window-a.conf`) で  
    `EnvironmentFile=/home/tools02/RaspberryPiSystem_001/window_a/config/window-a.env` を読み込む。
- **systemd サービス例**
  ```
  [Service]
  User=tools02
  WorkingDirectory=/home/tools02/RaspberryPiSystem_001/window_a
  Environment=PATH=/home/tools02/RaspberryPiSystem_001/window_a/.venv/bin:/usr/bin:/bin
  Environment=PYTHONUNBUFFERED=1
  ExecStart=/home/tools02/RaspberryPiSystem_001/window_a/.venv/bin/python app_flask.py
  Restart=on-failure
  ```
  - 変更後は `sudo systemctl daemon-reload && sudo systemctl restart toolmgmt.service` を忘れずに実行する。

### API トークン管理
- 工具管理カードや REST API（`/api/tokens`, `/api/plan/refresh` など）は `X-API-Token` ヘッダーによる簡易認証を利用する。Pi4 では `window_a/config/api_tokens.json` にトークンを保存し、`window_a/config/window-a.env` から `WINDOW_A_API_TOKEN_HEADER` / `WINDOW_A_API_TOKEN_FILE` を参照する。
- CLI で発行・一覧を行う場合は次のスクリプトを使用する。  
  ```bash
  cd ~/RaspberryPiSystem_001/window_a
  source .venv/bin/activate
  python scripts/manage_api_tokens.py issue window-a-01 --note "初期発行"
  python scripts/manage_api_tokens.py list
  deactivate
  ```
  `list --reveal` を指定すると完全なトークン値を表示できる。既存トークンを残したまま新規発行したい場合は `--keep-existing` を付与する。
  `toolmgmt.service` を再起動すると Dashboard にトークンのマスク値・ステーション ID が表示され、貸出操作ボタンが有効になる。

### NFC スキャン（Pi4）
- Dashboard の「NFC でスキャン」ボタンを押すと `scan_tag()` が PC/SC リーダーから UID を取得し、利用者タグ→工具タグの順で読み取った後に Pi5 `/api/v1/loans` へ貸出登録を行う。  
- 前提: `sudo systemctl enable --now pcscd` で PC/SC サービスを有効化し、`config/window-a.env` で `ENABLE_LOCAL_SCAN=1` に設定。  
- テスト方法: Pi4 で `pcsc_scan` を実行してタグを読み取れることを確認 → Dashboard を開き、利用者タグ・工具タグの順でスキャン。Pi5 `/api/v1/loans` に貸出が追加される。  
- ログ確認: `journalctl -u toolmgmt.service -n 40 | grep NFC` や `window_a/api_actions.log` で UID と操作結果を確認する。

### DocumentViewer + USB バーコード
- DocumentViewer (`document_viewer/README.md`) に USB 接続のバーコードリーダーを常時挿し、右ペイン iframe の入力欄へフォーカスを固定する。  
- TM-DIST から配布された PDF は `document-importer.sh`（`/usr/local/bin`）経由で `/srv/RaspberryPiSystem_001/document_viewer/docviewer/` に配置される。  
- バーコード読み取り → DocumentViewer が該当 PDF を全画面表示 → Dashboard の DocumentViewer パネルで `ONLINE` が表示されることを確認。  
- ログ: `/var/log/document-viewer/importer.log` や `docs/test-handbook.md` の手順に従って定期的に記録する。

## Pi5 連携（工具管理 API）
- Pi5 側で `server/config/local.toml` の `[tool_management] enabled = true` に設定し、Pi4 と同じ PostgreSQL を参照させる。  
- Window A は `RASPI_SERVER_BASE`／`RASPI_SERVER_API_TOKEN` を用いて `/api/v1/loans`（互換 `/api/loans`）および手動返却・削除 API を呼び出す。`manual_return`／`delete_open_loan` エンドポイントはすべて Pi5 REST を経由し、ローカル DB には直接触れない。  
- `docs/system/window-a-toolmgmt.md` に Pi5 API を含めた同期フローを記載しているため、Pi4 で新機能を有効化するときは必ず参照する。

## Mac / Git フロー
1. Mac (VS Code) で開発 → `git add/commit/push`。
2. Pi4 (tools02) では上記「定期更新フロー」のコマンドブロックを実行して `git pull`。  
3. 追加の設定やログは `docs/test-notes/2025-11/window-a-demo.md` に記録し、`docs/system/next-steps.md` のステータスを更新する。

このルールを守ることで、Window A も他デバイス同様に `~/RaspberryPiSystem_001` だけで構成管理できる。
