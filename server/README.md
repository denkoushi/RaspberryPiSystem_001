# RaspberryPiServer モジュール

このディレクトリは Pi5 上で稼働するサーバー機能をまとめる。REST / Socket.IO / PostgreSQL などの中枢機能をモジュール化し、既存リポジトリで安定していたコードを移設しやすい構成を目指す。

## ディレクトリ構成（初期案）
- `src/raspberrypiserver/` — Flask ベースのアプリケーション本体とモジュール群
- `tests/` — サーバーモジュール向けのテストコード（将来的な自動テスト復帰用に保持）
- `config/` — `default.toml` など設定テンプレートを保管
- `scripts/`（未作成） — USB やメンテナンス用スクリプト

## 現状の内容
- `app.py` が Flask アプリの雛形と設定読込処理を提供する。
- `api/` 配下に `/api/v1/scans` のプレースホルダー Blueprint を用意（POST 受信の疎通確認用）。
- `api/` 配下に `/api/v1/part-locations` を追加し、最新所在情報を返せるようにした。
- `config/default.toml` に基本設定（API prefix、ログ出力先など）を記述。
- `config/schema.sql` に `scan_ingest_backlog` / `part_locations` テーブルと `drain_scan_backlog` 関数の雛形を含め、バックログ→本番テーブル移行の入口を用意。
- `tests/test_healthz.py` がヘルスチェックと設定上書きのユニットテストを実装。
- `tests/test_api_scans.py` がスキャン受信エンドポイントのエコーバックを検証。
- `tests/test_repositories.py` がメモリ/DB プレースホルダーリポジトリの挙動と切替を検証。
- `services/` に Socket.IO ブロードキャストのプレースホルダーを追加し、スキャン受信時に `scan.ingested` イベントを発火（設定で変更可）。

## 次のステップ
1. 旧 `RaspberryPiServer` リポジトリから API ハンドラや設定ファイルを段階的に移設。
2. `SCAN_REPOSITORY_BACKEND = "db"` を有効化できるよう PostgreSQL 向け実装を用意し、Socket.IO など周辺ロジックを統合する。
3. USB / mirrorctl 連携や Socket.IO など、高難度ロジックを独立モジュールとして整理する。

## バックログのドレイン（手動）
PostgreSQL が稼働している環境では、以下のスクリプトで `scan_ingest_backlog` から本番テーブルへ移送できます。

```bash
cd ~/RaspberryPiSystem_001/server
source .venv/bin/activate
python scripts/drain_backlog.py --dsn "postgresql://app:app@localhost:15432/sensordb" --limit 200
```

> 注意: 上記コマンドはローカルで PostgreSQL が起動していない場合エラーになります。実際に実行するときは DB が利用可能な環境で行ってください。

アプリケーション内でも `BACKLOG_DRAIN_SERVICE` を通じて同様の処理を呼び出せるため、今後 systemd timer や管理 API から利用できる設計を想定しています。

### バックログへのサンプル投入
検証用にサンプルデータを投入したい場合は以下を利用できます。

```bash
python scripts/seed_backlog.py --dsn "postgresql://app:app@localhost:15432/sensordb" \
  --order TEST-123 --location RACK-A1
```

## ローカル PostgreSQL の起動（docker-compose）

```bash
cd ~/RaspberryPiSystem_001/server
docker compose up -d
./scripts/init_db.sh "postgresql://app:app@localhost:15432/sensordb"
```

> `psql` コマンドが必要です。macOS では `brew install postgresql` などで導入してください。
