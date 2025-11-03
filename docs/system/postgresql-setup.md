# PostgreSQL セットアップメモ

- 2回目の `psql --version` 実行で `command not found` が発生。
- ローカル macOS には psql が未インストール。
- drain や seed スクリプトを動かす際は、必要に応じて `brew install postgresql` などで psql を導入する。

## 備考（2025-11-03）
- `psql --version` を再度実行したところ、`command not found` のまま。macOS 側に psql が入っていない状態。
- drain / seed スクリプトをローカルで動かす場合は `brew install postgresql` 等でインストールが必要。
- 2025-11-03: `psql --version` は引き続き未導入。DB 検証は PostgreSQL のある環境で実施する。
- `server/docker-compose.yml` を用意した。`docker compose up -d` でローカルに PostgreSQL を立ち上げ、`scripts/init_db.sh` で `schema.sql` を適用する。
