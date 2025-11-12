# Raspberry Pi Setup Guide

このドキュメントでは RaspberryPiServer（Pi5）上で DocumentViewer を常駐させ、Window A (Pi4) から `/viewer` を参照できるようにする手順をまとめる。Pi5 以外の端末で再構築する場合も同じ手順を使う。ドキュメント種別ごとの役割は `docs/documentation-guidelines.md` を参照。

> 以降は `DOCVIEWER_HOME=~/RaspberryPiSystem_001/document_viewer` を前提とします（例: `export DOCVIEWER_HOME=~/RaspberryPiSystem_001/document_viewer`）。

## 1. OS 更新
```bash
sudo apt update
sudo apt upgrade -y
```

## 2. 必要パッケージのインストール
```bash
sudo apt install -y python3-venv python3-pip inotify-tools chromium-browser git jq rsync zstd
```

## 3. リポジトリ取得
```bash
cd ~
git clone https://github.com/denkoushi/RaspberryPiSystem_001.git
cd RaspberryPiSystem_001/document_viewer
```
すでに `RaspberryPiSystem_001` を取得済みの場合は `cd ~/RaspberryPiSystem_001 && git pull --ff-only` で最新化する。

## 4. 仮想環境と依存インストール
```bash
cd "$DOCVIEWER_HOME"/app
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
```

## 5. テスト起動
```bash
cd "$DOCVIEWER_HOME"/app
source ../.venv/bin/activate
FLASK_APP=viewer.py flask run --host 0.0.0.0 --port 5000
```
ブラウザで `http://<raspberrypiのIP>:5000` を開き、待機画面が表示されることを確認する。Ctrl+C で停止。

## 6. ドキュメントフォルダと PDF 配置
```bash
cd "$DOCVIEWER_HOME"
mkdir -p documents imports/failed
cp <元PDF> documents/TEST-001.pdf  # サンプル
```

## 7. Flask アプリの systemd サービス化
`/etc/systemd/system/document-viewer.service` を作成し、以下を記述する。
```
[Unit]
Description=Document Viewer Flask App
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/tools02/RaspberryPiSystem_001/document_viewer/app
ExecStart=/home/tools02/RaspberryPiSystem_001/document_viewer/.venv/bin/flask run --host 0.0.0.0 --port 5000
Environment=FLASK_APP=viewer.py
Environment=PYTHONPATH=/home/tools02/RaspberryPiSystem_001/document_viewer/app
Restart=on-failure
User=tools02

[Install]
WantedBy=multi-user.target
```
その後、次を実行。
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now document-viewer.service
sudo systemctl status document-viewer.service
```
`Active: active (running)` になっていることを確認。

## 8. Chromium の自動起動 (LXDE-pi-labwc 環境)
`~/.config/autostart/document-viewer.desktop` を作成し、以下を記述。
```
[Desktop Entry]
Type=Application
Name=Document Viewer Kiosk
Exec=chromium-browser --kiosk --incognito --disable-restore-session-state http://localhost:5000
X-GNOME-Autostart-enabled=true
```

## 9. 動作確認
1. `sudo reboot` で再起動。
2. ログイン完了後、Chromium が kiosk モードで起動し Document Viewer が表示されることを確認。
3. `documents/<部品番号>.pdf` を更新すると、ブラウザ内で閲覧できる。

> メモ: Pi5 のホスト名は Avahi により `raspi-server-*.local` に変わる場合があります。Window A から参照する際は実際に `hostnamectl` や `avahi-browse -rt _workstation._tcp` で確認したホスト名を `VIEWER_API_BASE` / `VIEWER_SOCKET_BASE` に設定し、疎通は `ping <ホスト名>` で確認してください。

## 10. ミラー検証期間中の日次チェック
- RaspberryPiServer 側の日次チェックリスト（`docs/test-notes/mirror-check-template.md`）に合わせ、DocumentViewer では以下を確認・記録する。
  - 工具管理 UI と同じオーダーが一覧に反映されていること（必要に応じてスクリーンショットを取得）。
  - `~/RaspberryPiSystem_001/document_viewer/documents/` 配下の PDF が最新タイムスタンプに更新されていること。
  - `journalctl -u document-viewer.service -n 50` でエラーがないこと。
- チェック結果はチェックシートの DocumentViewer 欄へ○/×とメモを記入。異常時は `sudo systemctl restart document-viewer.service` などで復旧後、再度確認する。

## 備考
- iframe の sandbox 属性を外さないと Chromium が PDF 読み込みをブロックするため、`app/templates/index.html` の iframe は以下のように設定している。
  ```html
  <iframe id="pdf-frame" title="PDF Viewer" allow="clipboard-write"></iframe>
  ```
- USB 自動インポートの systemd サービスは別途 `document-importer.service` を導入予定。


## 運用時の安全な更新手順
1. ターミナルまたは SSH で Raspberry Pi に接続し、`tools01` ユーザーでログインする。
2. Document Viewer を停止: `sudo systemctl stop document-viewer.service`
3. リポジトリを更新: `cd ~/RaspberryPiSystem_001 && git fetch && git pull`
4. 依存パッケージを更新: `source "$DOCVIEWER_HOME"/.venv/bin/activate && pip install -r "$DOCVIEWER_HOME"/app/requirements.txt`
5. サービスを再起動: `sudo systemctl daemon-reload` (必要に応じて) および `sudo systemctl restart document-viewer.service`
6. 状態確認: `sudo systemctl status document-viewer.service` が `active (running)` であることを確認。
7. Chromium が自動で再接続しない場合は `Ctrl+R` または再起動 (`sudo reboot`) で画面を更新する。

> 注意: 仮想環境は `$DOCVIEWER_HOME/.venv` に配置している。誤ってリポジトリ直下に `.venv` を作成すると `git pull` で競合するので、常にこちらの環境を利用する。

## USB インポートの手動実行
USB メモリのルートに以下の構成でファイルを配置する。

```
TOOLMASTER/
├── master/          # 工具管理システム用（既存）
└── docviewer/       # ドキュメントビューア用
    ├── meta.json    # {"updated_at": <UNIX 時刻>}
    └── *.pdf        # 表示したい PDF ファイル
```

手動で最新 PDF を取り込む場合は次のコマンドを利用する。

```bash
cd "$DOCVIEWER_HOME"
sudo bash scripts/usb-import.sh /dev/sda1
```

- コピー結果は `/var/log/document-viewer/import.log` に追記される。
- `docviewer/` 配下は PDF と `meta.json` のみ受け付ける。許可外ファイルや MIME タイプの不一致を検出すると取り込みを中断し、ログへ警告を残す。
  - 警告が出た場合は `tail -n 20 /var/log/document-viewer/import.log` を確認し、記録されたファイルを USB から削除または正しい形式に修正してから再度挿し直す。
- `docviewer/meta.json` の `updated_at` がローカルより新しいときのみ取り込みを行う。初回はファイルがなくても自動作成される。
- 取り込み後は `~/RaspberryPiSystem_001/document_viewer/documents/meta.json` に最新タイムスタンプが記録され、ブラウザを更新すると PDF が表示される。

> 今後 systemd 常駐化する場合は、上記スクリプトをラップする Unit を作成し、tools01 ユーザーが `/media` を監視する構成へ更新する。

## DocumentViewer を常駐サービス化する

### 10.1 API / Socket.IO 接続設定 (任意)
- REST / Socket.IO の接続先を RaspberryPiServer へ切り替える場合は `/etc/default/docviewer` に以下を定義してからサービスを再起動します。
  ```bash
  sudo install -m 640 config/docviewer.env.sample /etc/default/docviewer
  sudo nano /etc/default/docviewer
  sudo systemctl restart document-viewer.service
  ```
- `VIEWER_API_TOKEN` が不要な場合は行を削除してください。既存の `.service` テンプレートで `EnvironmentFile=-/etc/default/docviewer` を読み込むため、ファイルがない場合でもエラーになりません。
- `VIEWER_SOCKET_BASE` を省略すると `VIEWER_API_BASE` が利用されます。`VIEWER_SOCKET_AUTO_OPEN=0` を指定すると Socket.IO 接続を無効化できます。
- `VIEWER_ACCEPT_DEVICE_IDS` / `VIEWER_ACCEPT_LOCATION_CODES` はカンマ区切りで複数指定可能です。指定がある場合は一致したイベントのみで自動表示が発火します。
- `VIEWER_LOG_PATH` を設定するとドキュメント検索や表示リクエストがローテーション付きで記録されます。ログが生成されない場合はディレクトリのパーミッションとパスを確認してください。
- ログ出力と 14 日チェックの詳細は `docs/test-notes/2025-10-26-docviewer-env.md` を参照してください。
工場現場では電源投入のみで利用できることが求められます。以下のスクリプトで DocumentViewer を systemd サービスとして登録すると、ラズパイ起動時に自動で Viewer が開始されます。

```bash
cd ~/RaspberryPiSystem_001/document_viewer
sudo DOCUMENT_VIEWER_USER=tools01 ./scripts/install_docviewer_service.sh
```

- `DOCUMENT_VIEWER_USER` を省略すると `tools01` が利用されます。別ユーザーの場合は環境に合わせて指定してください。
- スクリプトが `/etc/systemd/system/document-viewer.service` を作成し、`systemctl enable --now document-viewer.service` まで実行します。
- サービス設定では `$DOCVIEWER_HOME/.venv/bin/python $DOCVIEWER_HOME/app/viewer.py` を常時起動します。仮想環境が無い場合は先に `python3 -m venv "$DOCVIEWER_HOME/.venv"` などで作成してください。
- 状態確認: `sudo systemctl status document-viewer.service`
- ログ確認: `sudo journalctl -u document-viewer.service -n 50`
- 停止/再起動: `sudo systemctl stop document-viewer.service` / `sudo systemctl restart document-viewer.service`

> 既に手動で `python app/viewer.py` を動かしている場合は、サービス導入後にそのプロセスを停止してください。

### 10.2 USB インポートサービスを導入する
DocumentViewer で USB メモリから PDF を自動同期させる場合は、以下の手順で importer スクリプトと systemd サービスをセットアップする。

```bash
cd ~/RaspberryPiSystem_001/document_viewer
sudo install -m 755 scripts/document-importer.sh /usr/local/bin/document-importer.sh
sudo install -m 755 scripts/document-importer-daemon.sh /usr/local/bin/document-importer-daemon.sh
sudo sed "s/{{USER}}/tools02/g" systemd/document-importer.service | sudo tee /etc/systemd/system/document-importer.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now document-importer.service
```

- `{{USER}}` の部分は実際に importer を動かすユーザー（Pi4 では `tools02`）へ置き換える。
- importer はデフォルトで `/media/<user>` を監視し、USB に `docviewer/` フォルダがあると `document-importer.sh` を起動して `~/RaspberryPiSystem_001/document_viewer/documents` へコピーする。ログは `/var/log/document-viewer/import.log` と `/var/log/document-viewer/import-daemon.log` に出力される。
- PDF や `meta.json` を手動で取り込む場合も、同スクリプトを直接実行すれば同じロジックで検証される。
