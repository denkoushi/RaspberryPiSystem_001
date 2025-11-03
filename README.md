# RaspberryPiSystem_001

## プロジェクト概要
RaspberryPiServer（Pi5）を中核に据え、Window A（Pi4）や Pi Zero 2 W との役割分担を整理し直した新構成をこのリポジトリで再構築する。既存リポジトリで試作した成果物は参照材料としつつ、本リポジトリで白紙状態から設計・実装をやり直す。

## ゴール
- Window A（tool-management-system02）は DocumentViewer や工具管理 UI などクライアント機能に専念する。
- RaspberryPiServer（Pi5）は REST / Socket.IO / PostgreSQL / USB 配布・バックアップを統合し、Pi Zero 2 W（ハンディ）からのスキャンを唯一の受信点とする。
- Pi Zero 2 W は mirrorctl／mirror_compare による 14 日連続健全性チェックを完了した状態で本番切り替えを行う。
- RUNBOOK・systemd・USB 運用を整備し、旧 Window A サーバーを安全に退役できる状態にする。

## 現在のディレクトリ構成（進行中）
- `server/` — Pi5 向けサーバーモジュール（Flask 雛形を実装済み）
- `client_window_a/` — Pi4 クライアント UI 再構築領域
- `handheld/` — Pi Zero 2 W（ハンディ端末）向けモジュール
- `docs/` — アーキテクチャ・テストハンドブック・手動テストログ
- `docs/system/` — 今後のロードマップやタスク整理

## 構成と責務
| コンポーネント | 主な責務 | 参照ドキュメント |
| --- | --- | --- |
| RaspberryPiServer (Pi5) | API / Socket.IO / DB / USB 運用のハブ | `RUNBOOK.md`, `docs/implementation-plan.md`, `docs/mirror-verification.md` |
| Window A (Pi4) | クライアント表示（DocumentViewer iframe、所在一覧、構内物流 UI 等） / 周辺機器（NFC・USB ハンディ）の集約点 | Window A リポジトリ `docs/right-pane-plan.md`, `docs/docs-index.md` |
| Pi Zero 2 W | ハンディ送信専用端末、mirrorctl 管理対象 | OnSiteLogistics `docs/handheld-reader.md`, RaspberryPiServer `docs/mirrorctl-spec.md` |

各コンポーネントの詳細な説明は `docs/architecture.md` を参照。

## 作業ガイド
- このリポジトリは白紙スタートで再構成する。過去リポジトリ（Window A, DocumentViewer, RaspberryPizero2W_withDropbox, OnSiteLogistics, RaspberryPiServer）の中間成果は参照のみとし、必要部分をここに再設計する。
- エージェントや自動化タスクは `AGENTS.md` の手順に従う。
- 一次情報（最新決定事項）は本リポジトリで管理し、詳細手順や履歴は各参照ドキュメント側を確認する。
- 既存リポジトリで正常動作していたコードはモジュール単位で流用し、再利用しやすい構造へ作り直す。拡張性・保守性を最優先し、機能ごとに独立性を高める。
- 直近の自動テストは 1 回目が成功、2 回目テスト準備時に環境が破損して再開発に至った。再構築ではテスト環境の復旧手順と再現性を確保する。
- 手動テスト資産は `docs/test-handbook.md` に整備し、保守や構造理解に役立つ形で常設する。
- モジュール別ディレクトリ整備（例: `server/`, `client_window_a/`, `handheld/`）と既存コード移設のロードマップ策定

## サーバーモジュール（server/）の動作確認
mac / Raspberry Pi のどちらでも以下のコマンドブロックをコピー＆ペーストして利用できます。

### 依存パッケージのインストール（venv 利用例）
```bash
cd ~/RaspberryPiSystem_001/server
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

### 開発サーバーの起動
```bash
cd ~/RaspberryPiSystem_001/server
source .venv/bin/activate
raspberrypiserver
```
> Flask の開発サーバーは前面で実行されるため、処理が完了するまで次のコマンドが入力できません。動作確認が済んだら `Ctrl+C` で必ず終了してください。

### ヘルスチェック
```bash
curl -i http://127.0.0.1:8501/healthz
```

### テスト実行（pytest）
```bash
cd ~/RaspberryPiSystem_001/server
source .venv/bin/activate
python -m pytest
```

### 設定ファイルのカスタマイズ（任意）
```bash
cd ~/RaspberryPiSystem_001/server
cp config/default.toml config/local.toml
# 任意の内容に編集した後で
python -m raspberrypiserver.app  # または raspberrypiserver
```
`config/local.toml` を作成した場合は環境変数 `RPI_SERVER_CONFIG` でパスを指定できます。

```bash
export RPI_SERVER_CONFIG=~/RaspberryPiSystem_001/server/config/local.toml
```

#### リポジトリバックエンドの切り替え
`config/*.toml` の `SCAN_REPOSITORY_BACKEND` を `memory`（既定）または `db` に設定できます。

- `memory`: `InMemoryScanRepository` が指定容量だけペイロードを保持（開発・テスト向け）
- `db`: PostgreSQL 用のプレースホルダー `DatabaseScanRepository` を初期化。現状は実際の upsert を実装していないため、後続タスクで差し替える想定です。

```toml
SCAN_REPOSITORY_BACKEND = "db"
SCAN_REPOSITORY_BUFFER = 500
[database]
dsn = "postgresql://app:app@localhost:15432/sensordb"
```
`db` バックエンドを利用する際は、サーバー側で `scan_ingest_backlog` など受け皿テーブルを作成しておきます（現状は挿入のみ行い、今後 upsert ロジックへ差し替える予定です）。

### Pi 側でリポジトリを最新化する例
```bash
cd ~/RaspberryPiSystem_001
git pull
```

## 今後のタスク（ドラフト）
- RaspberryPiServer の API / Socket.IO / DB インターフェース再設計
- Pi Zero 2 W ハンディ端末の mirrorctl 監視フロー整備
- RUNBOOK・systemd・USB 運用手順書の整理
- Window A クライアントから Pi5 API への移行シナリオ策定

## 確認したい事項
1. Pi5 上で予定している REST API のエンドポイント一覧や入出力仕様は最新が別ドキュメントに存在するか。
2. Pi Zero 2 W の mirrorctl 設定値や運用条件（例: 通信要件、アラート閾値）の詳細がどこに記録されているか。
3. Window A クライアント側で現時点までに既存リポジトリへ実装された UI/機能の中で、この再開発で引き継ぐべき要素は何か。
4. RUNBOOK / USB 運用に関する既存手順書の最新ファイルパスや参照先。

上記の不明点について情報をいただければ、本リポジトリへの整理を継続できる。
