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
3. **Pi5 再構築（着手予定）**
   - 現在 `/srv/rpi-server` に残っている旧 `RaspberryPiServer` 配置を棚卸しし、必要な設定ファイル（`config/`, `.env`, systemd drop-in）をバックアップ。
   - `/srv/RaspberryPiSystem_001` を新規作成し、GitHub の `RaspberryPiSystem_001` を clone（`git clone https://github.com/denkoushi/RaspberryPiSystem_001.git /srv/RaspberryPiSystem_001`）。
   - `sudo systemctl edit raspberrypiserver.service` で `WorkingDirectory=/srv/RaspberryPiSystem_001/server`、`ExecStart=/usr/bin/python3 /srv/RaspberryPiSystem_001/server/src/raspberrypiserver/app.py` へ書き換え、`sudo systemctl daemon-reload && sudo systemctl restart raspberrypiserver.service`。
   - 切り替え後は旧 `/srv/rpi-server` を `rpi-server_legacy_<date>` にリネームし、参照専用にする。
4. **運用切り替え**
   - Mac からの変更は feature ブランチ→PR→main マージのみ
   - Pi 側で作業する場合も `~/RaspberryPiSystem_001` で `git checkout <branch>` を使用し、旧ディレクトリは参照専用にする。

## ToDo
- [x] Pi Zero 移行スクリプトと手順書の作成 (`scripts/pi_zero_migrate_repo.sh`, `docs/system/pi-zero-integration.md`)
- [ ] Pi5 向けドキュメント追記 (`docs/system/postgresql-setup.md`, `docs/system/repo-structure-plan.md` に Pi5 移行手順を詳細化)
- [x] AGENTS.md へ「各デバイスのディレクトリ名統一」ポリシーを明記
- [ ] 旧ディレクトリ削除の前にバックアップ保管先を決定
