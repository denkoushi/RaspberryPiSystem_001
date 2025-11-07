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
3. **Pi5 再構築**
   - 現在の `/srv/RaspberryPiSystem_001/server` を棚卸しし、同リポジトリを `/srv/RaspberryPiSystem_001` 直下で clone
   - `git clone ... /srv/RaspberryPiSystem_001 && cd server && git checkout main && git pull`
   - systemd（`raspberrypiserver.service`）の WorkingDirectory も `/srv/RaspberryPiSystem_001/server` へ統一
4. **運用切り替え**
   - Mac からの変更は feature ブランチ→PR→main マージのみ
   - Pi 側で作業する場合も `~/RaspberryPiSystem_001` で `git checkout <branch>` を使用し、旧ディレクトリは参照専用にする。

## ToDo
- [ ] Pi Zero 移行スクリプトと手順書の作成 (`scripts/pi_zero_migrate_repo.sh`)
- [ ] Pi5 向けドキュメント追記 (`docs/system/postgresql-setup.md` に systemd の WorkingDirectory 更新手順)
- [ ] AGENTS.md へ「各デバイスのディレクトリ名統一」ポリシーを明記
- [ ] 旧ディレクトリ削除の前にバックアップ保管先を決定
