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
- `config/default.toml` に基本設定（API prefix、ログ出力先など）を記述。
- `tests/test_healthz.py` がヘルスチェックと設定上書きのユニットテストを実装。
- `tests/test_api_scans.py` がスキャン受信エンドポイントのエコーバックを検証。

## 次のステップ
1. 旧 `RaspberryPiServer` リポジトリから API ハンドラや設定ファイルを段階的に移設。
2. USB / mirrorctl 連携や Socket.IO など、高難度ロジックを独立モジュールとして整理する。
