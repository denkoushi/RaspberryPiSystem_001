# リポジトリ構成再統一プラン

## 現状
- **Mac**: `~/RaspberryPiSystem_001` が単一の Git リポジトリとして存在。VS Code のソース管理はここに紐づく。
- **Pi Zero**: 旧システム時代の `~/OnSiteLogistics` をそのまま使用。Git リモートは `OnSiteLogistics` のままで、新リポジトリとの差分が直接貼り付けで反映されている。
- **Pi5**: `/srv/RaspberryPiSystem_001/server` など複数ディレクトリが混在し、旧 `RaspberryPiServer` リポジトリ名が残っている。

## 目的
- すべてのデバイスで **RaspberryPiSystem_001** リポジトリのみを使用し、`git pull` で同一コードを展開できる状態にする。
- VS Code → GitHub → Pi (git pull) の一方向フローを崩さない。

## マイルストーン
1. **ドキュメント整備** (本ファイル, `docs/system/pi-zero-integration.md`, `docs/system/postgresql-setup.md` に反映)
2. **Pi Zero 再構築**
   - `~/OnSiteLogistics` をバックアップ (`mv ~/OnSiteLogistics ~/OnSiteLogistics_legacy_$(date +%Y%m%d)`)
   - `git clone https://github.com/denkoushi/RaspberryPiSystem_001.git ~/RaspberryPiSystem_001`
   - `cd ~/RaspberryPiSystem_001 && git checkout main && git pull`
   - 既存の `.env`, トークン, systemd など必要ファイルを `legacy` からマージ
   - `sudo systemctl edit handheld@tools01.service` の WorkingDirectory を `/home/tools01/RaspberryPiSystem_001/handheld` 等へ更新
3. **Pi5 再構築（完了: 2025-11-10）**
   - Docker Compose で稼働していた `/srv/rpi-server` を停止（`sudo docker compose down`）し、`/srv/rpi-server_legacy_20251110` として退避。
   - GitHub の `RaspberryPiSystem_001` を `/srv/RaspberryPiSystem_001` に clone し、`server/.venv` を作成 → `pip install -e .` で依存をインストール。
   - 新しい `raspi-server.service` を `/etc/systemd/system/raspi-server.service` に配置（`ExecStart=/srv/RaspberryPiSystem_001/server/.venv/bin/python ...`、`Environment=PATH=...`、`RPI_SERVER_CONFIG=/srv/RaspberryPiSystem_001/server/config/local.toml`）。
   - `/srv/RaspberryPiSystem_001/server/config/local.toml` に旧 `/etc/default/raspi-server` の値（API_TOKEN, DocumentViewer 設定等）を反映。
   - `sudo systemctl daemon-reload && sudo systemctl enable --now raspi-server.service` の後、`curl -I http://localhost:8501/healthz` で 200 OK を確認。旧 `/srv/rpi-server` は参照専用に維持。
4. **運用切り替え**
   - Mac からの変更は feature ブランチ→PR→main マージのみ
   - Pi 側で作業する場合も `~/RaspberryPiSystem_001` で `git checkout <branch>` を使用し、旧ディレクトリは参照専用にする。

## 標準ユーザーと clone パス
| デバイス | 役割 | 実行ユーザー | Git clone / 作業ディレクトリ | 補足 |
| --- | --- | --- | --- | --- |
| Pi Zero | ハンディ（scanner + mirrorctl） | `tools01`（systemd サービス実行用に固定） | `/home/tools01/RaspberryPiSystem_001` | `~/.venv-handheld` に `handheld/requirements.txt` を導入し、`handheld@tools01.service`／`mirrorctl@tools01.service` から使用する。作業アカウント（例: `denkonzero`）の clone は検証専用であり、本番サービスは必ず `tools01` 側を参照する。 |
| Pi4 (Window A) | Dashboard / DocumentViewer クライアント | `tools02`（Window A 用アカウント） | `/home/tools02/RaspberryPiSystem_001` | `window_a/.venv` をここで構築し、`toolmgmt.service`／`client_window_a` ビルドも同ディレクトリを前提とする。旧 `~/tool-management-system02` は `_legacy_` フォルダへ退避。 |
| Pi5 (Server) | Flask + Socket.IO + PostgreSQL API | `root`（systemd） / 管理ユーザー `denkon5ssd` | `/srv/RaspberryPiSystem_001` | `raspi-server.service` が `/srv/RaspberryPiSystem_001/server/.venv/bin/python` を起動する。手動操作は `cd /srv/RaspberryPiSystem_001 && git pull` を基本とし、`server/logs` も同配下に作成。 |

> いずれのデバイスでも、Mac での作業 → GitHub → 各 Pi で `git pull` という一方向フローを徹底する。Pi 上で直接編集が必要な場合は必ず `~/RaspberryPiSystem_001` でコミット差分として残し、他ユーザーの clone と食い違わないよう `update_handheld_override.sh` などの同期スクリプトを活用する。

5. **Pi4 (Window A) 再構築**  
   - 旧リポジトリ名 `tool-management-system02` を廃止し、`~/RaspberryPiSystem_001` へ統一する。  
   - Mac 側で作成した `window_a/requirements.txt`、`window_a/app_flask.py`、`window_a/tests/test_load_plan.py` をリポジトリ直下（`window_a/` サブディレクトリ）で管理し、Pi4 も同じソースを pull できるようにする。  
   - Pi4 側での作業手順:  
     ```bash
     sudo systemctl stop toolmgmt.service  # Window A サービス名に合わせる
     mv ~/tool-management-system02 ~/tool-management-system02_legacy_$(date +%Y%m%d)
     git clone https://github.com/denkoushi/RaspberryPiSystem_001.git ~/RaspberryPiSystem_001
     cd ~/RaspberryPiSystem_001
     git checkout feature/repo-structure-plan   # 進行中ブランチ
     ```
   - Window A アプリは `client_window_a/`＋`window_a/` の構成で動作するため、systemd サービスや `setup_auto_start.sh` で参照しているパスを `/home/tools02/RaspberryPiSystem_001/window_a` / `/home/tools02/RaspberryPiSystem_001/client_window_a` に更新する。  
   - 依存インストールも `cd ~/RaspberryPiSystem_001/window_a && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` のように統一。旧 `~/tool-management-system02` は参照専用の `*_legacy_` ディレクトリとして保持する。
7. **DocumentViewer 統合**
   - 現状は Pi4 上の旧リポジトリ（`~/DocumentViewer`）で稼働しているが、最終的には `~/RaspberryPiSystem_001/document_viewer` へ移設し、GitHub の新リポジトリに統合する。
   - 短期対応: 旧リポジトリを参照しつつ Socket.IO 連携などの修正を反映し、Pi4 では `git pull` で運用継続する。
   - 中期対応: DocumentViewer のソース／docs／systemd を新リポジトリへコピーし、Mac 側で VS Code 管理下に置く。Pi4 の systemd/EnvironmentFile も新パスへ切り替える。
   - 長期対応: 旧 `~/DocumentViewer` を `~/DocumentViewer_legacy_YYYYMMDD` へ退避し、旧 GitHub リポジトリは参照専用にする。以後は `RaspberryPiSystem_001` 上でのみ開発・運用する。
6. **ホスト名・systemd・ログパスの名寄せ**  
   - **共通ルール**: 3 台すべてのホスト名をリポジトリ名と同じ `RaspberryPiSystem_001` に揃える。`/etc/hostname` と `/etc/hosts` を同時に編集し、`sudo hostnamectl set-hostname RaspberryPiSystem_001` を実行後に SSH を再接続する。PS1／MOTD も同名を表示させ、利用者がどのマシンでも同じプロンプトを目視できる状態を維持する。  
   - **Pi5（server）**  
     1. `sudo mkdir -p /srv/RaspberryPiSystem_001/server/logs && sudo chown -R denkon5ssd:denkon5ssd /srv/RaspberryPiSystem_001/server/logs` でログディレクトリを用意する。  
     2. `/etc/systemd/system/raspi-server.service` の `WorkingDirectory` と `ExecStart` が `/srv/RaspberryPiSystem_001/server` 配下を向いているか確認し、`.venv` は `.venv` というディレクトリ名で統一する。  
     3. `server/config/default.toml:19-22` と `server/config/local.toml` の `[logging].path` を `/srv/RaspberryPiSystem_001/server/logs/app.log` に揃える（未指定でも `server/src/raspberrypiserver/app.py` が `<repo>/logs/app.log` をフォールバックで生成する）。  
     4. 下記コマンドで反映し、`journalctl -u raspi-server.service -n 120` と `tail -n 50 /srv/RaspberryPiSystem_001/server/logs/app.log` の結果をテストノートへ転記する。  
        ```bash
        sudo systemctl daemon-reload
        sudo systemctl restart raspi-server.service
        ```  
   - **Pi4（Window A/B）**  
     1. ホスト名変更後に `sudo systemctl stop toolmgmt.service` を実行し、停止した状態で設定を入れ替える。  
     2. `/etc/systemd/system/toolmgmt.service` と `toolmgmt.service.d/window-a.conf` から旧 `~/tool-management-system02` パスを削除し、`WorkingDirectory=/home/tools02/RaspberryPiSystem_001/window_a`、`ExecStart=/home/tools02/RaspberryPiSystem_001/window_a/.venv/bin/python .../app_flask.py` に統一する。  
     3. `Environment=PATH=/home/tools02/RaspberryPiSystem_001/window_a/.venv/bin:...` のように `.venv` への PATH を明示し、`.env` 類も `window_a/config` に集約する。  
     4. `config/window-a.env` を旧リポジトリ（`~/tool-management-system02/config/window-a-client.env.sample`）を参照して作成し、`RASPI_SERVER_BASE`・`RASPI_SERVER_API_TOKEN`・`DATABASE_URL=postgresql://app:app@raspi-server.local:15432/sensordb` などを移植。`/etc/systemd/system/toolmgmt.service.d/window-a-env.conf` で `EnvironmentFile=/home/tools02/RaspberryPiSystem_001/window_a/config/window-a.env` を読み込む。  
     5. USB 同期 API 用のスタブ (`window_a/usb_sync.py`) を配置し、旧リポジトリ依存が無くても `app_flask` import が成功するようにした。実機で USB 同期を行う際は `WINDOW_A_USB_SYNC_CMD` か `window_a/scripts/usb_sync.sh` を配置し、スタブ経由で呼び出す。  
     6. ステーション設定 API 用のスタブ (`window_a/station_config.py`) を配置し、`window_a/config/station_config.json` へ JSON 保存する。実運用で別パスを使う場合は `WINDOW_A_STATION_CONFIG` を設定する。  
     7. API トークン管理 (`window_a/api_token_store.py`) と Pi5 REST クライアント (`window_a/raspi_client.py`) を本リポジトリに移植し、`pytest` で 12 件 PASS を確認。  
     8. `window_a/logs` を作成し、アプリ内の `LOG_DIR` なども新パスへ変更したうえで `sudo systemctl daemon-reload && sudo systemctl restart toolmgmt.service` を実施。`journalctl -u toolmgmt.service -n 80` を記録して完了とする。  
   - **Pi Zero（handheld）**  
     1. ホスト名を統一後、`~/RaspberryPiSystem_001/handheld` と `~/.venv-handheld` を標準作業ディレクトリ／仮想環境とする。  
     2. `handheld@tools01.service` の `WorkingDirectory` と `ExecStart=/home/tools01/.venv-handheld/bin/python /home/tools01/RaspberryPiSystem_001/handheld/src/main.py` を確認し、`Environment=PYTHONPATH=/home/tools01/RaspberryPiSystem_001` を追加してテスト時の `PYTHONPATH=..` を不要にする。  
     3. `handheld/logs` を作り、`retry_queue.py` や再送キュー設定がそのディレクトリを参照するように更新する。`sudo systemctl daemon-reload && sudo systemctl restart handheld@tools01.service` の後に `journalctl -u handheld@tools01.service -n 80` を取得し、結果をテストノートへ貼る。  
   - **検証ログの扱い**: すべての再起動結果と `tail` 出力は `docs/test-notes/2025-11/window-a-demo.md` など各デバイスのテストノートに貼り付け、本ファイルおよび `docs/system/next-steps.md` の該当行に完了日時を反映する。

## ToDo
- [x] Pi Zero 移行スクリプトと手順書の作成 (`scripts/pi_zero_migrate_repo.sh`, `docs/system/pi-zero-integration.md`)
- [ ] Pi5 向けドキュメント追記 (`docs/system/postgresql-setup.md`, `docs/system/repo-structure-plan.md` に Pi5 移行手順を詳細化)
- [x] AGENTS.md へ「各デバイスのディレクトリ名統一」ポリシーを明記
- [ ] Pi4（Window A）再構築手順を `docs/test-notes/2025-11/window-a-demo.md` / `docs/system/next-steps.md` に反映し、`tool-management-system02` 廃止タイムラインを決定
- [ ] 旧ディレクトリ削除の前にバックアップ保管先を決定
- [ ] Pi5/Pi4/Pi Zero のホスト名・systemd ユニット名・ログパス名寄せを実施し、本ドキュメントに進捗を記録
- [x] RaspberryPiServer (Pi5) で `logging.path` を読むファイルハンドラを実装し、`/srv/RaspberryPiSystem_001/server/logs/app.log` に出力させる（`server/tests/test_logging_config.py` で検証済み）
- [ ] Window A の USB 同期スクリプトを移植し、`window_a/usb_sync.py` から実行できるようにする
- [ ] Window A の station_config 永続化を本番仕様（PostgreSQL or Pi5 API）へ移行する
- [ ] Window A の `api_token_store` と `raspi_client` を実運用仕様へ拡張する（現在は JSON + requests ベースの暫定実装）
