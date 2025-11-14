# PostgreSQL セットアップメモ

- 2回目の `psql --version` 実行で `command not found` が発生。
- ローカル macOS には psql が未インストール。
- drain や seed スクリプトを動かす際は、必要に応じて `brew install postgresql` などで psql を導入する。

## 備考（2025-11-03）
- `psql --version` を再度実行したところ、`command not found` のまま。macOS 側に psql が入っていない状態。
- drain / seed スクリプトをローカルで動かす場合は `brew install postgresql` 等でインストールが必要。
- 2025-11-03: `psql --version` は引き続き未導入。DB 検証は PostgreSQL のある環境で実施する。
- `server/docker-compose.yml` を用意した。`docker compose up -d` でローカルに PostgreSQL を立ち上げ、`scripts/init_db.sh` で `schema.sql` を適用する。
- Docker Desktop などで Docker デーモンを起動しておく必要がある。未起動の場合は `Cannot connect to the Docker daemon` エラーになる。
- 2025-11-03: psql 未導入のまま。Docker デーモンも停止中のため、先に Docker Desktop を起動し、必要なら `brew install postgresql` で psql を導入する。

## 備考（2025-11-04）
- `brew install postgresql@14` で psql を導入し、`/opt/homebrew/opt/postgresql@14/bin/psql` が利用可能になった。
- `brew services start postgresql@14` は不要（Docker Compose の PostgreSQL を利用）。必要に応じてサービスを停止する。
- インストール後に `./scripts/init_db.sh "postgresql://app:app@localhost:15432/sensordb"` を実行し、`schema.sql` が正常に適用された（`CREATE TABLE` などのログを確認）。

## 備考（2025-11-05）
- `drain_scan_backlog` を CTE + `FOR UPDATE SKIP LOCKED` に刷新。まとめて upsert / delete を行うため、従来の 1 件ずつ削除より高速かつ並列動作に強くなった。
- テスト時は `AUTO_DRAIN_ON_INGEST` を設定すると API 側から自動で `drain_scan_backlog(limit)` が呼ばれる。負荷を掛けないよう小さめの値で試す。

## 備考（2025-11-14）
- Pi4 (Window A) は `.env` で `DATABASE_URL=postgresql://app:app@raspi-server.local:15432/sensordb` を参照しているが、Pi5 側 PostgreSQL が停止していると `connection refused` で 30 秒リトライ後に失敗する。DocumentViewer や Socket.IO は動作しているので、DB だけ独立して起動させる必要がある。
- Pi5 での起動候補:
  ```bash
  cd /srv/RaspberryPiSystem_001/server
  docker compose up -d postgres              # Docker 運用の場合
  # または
  sudo systemctl start postgresql@14-main    # OS サービスで管理している場合
  ```
- 起動後は Pi5 から以下を実行し、`sensordb` に `part_locations` などがあることを確認する。
  ```bash
  PGPASSWORD=app psql -h 127.0.0.1 -p 15432 -U app -d sensordb -c '\dt'
  ```
- Pi4 からの疎通確認には `window_a/scripts/check_db_connection.py` を使用する。`git pull` 後に
  ```bash
  cd ~/RaspberryPiSystem_001/window_a
  source .venv/bin/activate
  python scripts/check_db_connection.py --env-file config/window-a.env
  deactivate
  ```
  を実行し、`status=ok target=raspi-server.local:15432 ...` が出力されれば完了。失敗した場合は `raspi-server.local` の `/etc/hosts` とファイアウォール設定を再確認する。
