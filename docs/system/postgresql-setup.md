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
