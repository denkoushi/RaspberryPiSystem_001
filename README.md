# RaspberryPiSystem_001

## プロジェクト概要

RaspberryPiServer（Pi5）を中核に据え、Window A（Pi4）や Pi Zero 2 W の役割分担を整理し直した新構成を、このリポジトリで再構築する。  
既存リポジトリで試作した成果物は参照材料としつつ、本リポジトリでは白紙状態から設計・実装をやり直す。

## ゴール

- Window A（`tool-management-system02`）は DocumentViewer や工具管理 UI などクライアント機能に専念させる。  
- RaspberryPiServer（Pi5）は REST / Socket.IO / PostgreSQL / USB 配布・バックアップを統合し、Pi Zero 2 W（ハンディ端末）からのスキャンを唯一の受信点とする。  
- Pi Zero 2 W は `mirrorctl`／`mirror_compare` による 14 日連続健全性チェックを完了した状態で本番切り替えを行う。  
- RUNBOOK・systemd・USB 運用を整備し、旧 Window A サーバーを安全に退役できる状態にする。

## 構成と責務

| コンポーネント | 主な責務 | 参照ドキュメント |
| --- | --- | --- |
| RaspberryPiServer (Pi5) | API / Socket.IO / DB / USB 運用のハブ | `RUNBOOK.md`, `docs/implementation-plan.md`, `docs/mirror-verification.md` |
| Window A (Pi4) | クライアント表示（DocumentViewer iframe、所在一覧、構内物流 UI 等）および NFC・USB ハンディなど周辺機器の集約点 | Window A リポジトリ `docs/right-pane-plan.md`, `docs/docs-index.md` |
| Pi Zero 2 W | ハンディ送信専用端末、`mirrorctl` 管理対象 | OnSiteLogistics `docs/handheld-reader.md`, RaspberryPiServer `docs/mirrorctl-spec.md` |

各コンポーネントの詳細な説明は `docs/architecture.md` を参照する。

## ディレクトリ構成（進行中）

- `server/` — Pi5 向けサーバーモジュール。Flask ベースの雛形を実装済みであり、今後の API / Socket.IO / DB 機能をここに統合する。  
- `client_window_a/` — Pi4 クライアント UI 再構築領域。DocumentViewer や構内物流 UI など Window A 側のフロントエンドを収容する。  
- `handheld/` — Pi Zero 2 W（ハンディ端末）向けモジュール。スキャン送信や `mirrorctl` 連携をここで扱う。  
- `docs/` — アーキテクチャ・テストハンドブック・手動テストログなどのドキュメント全般。  
- `docs/system/` — 今後のロードマップやタスク整理用のシステムドキュメント。`next-steps.md` と `repo-structure-plan.md` をタスク管理の入口とする。  

## 作業ガイド

- エージェント向けの詳細な行動ルールは `AGENTS.md` に集約し、この README はプロジェクト全体像と具体的なコマンドの正本とする。  
- このリポジトリは白紙スタートで再構成する。過去リポジトリ（Window A, DocumentViewer, RaspberryPizero2W_withDropbox, OnSiteLogistics, RaspberryPiServer）の中間成果は参照のみとし、必要部分をここで再設計する。  
- 一次情報（最新決定事項）は本リポジトリで管理し、詳細手順や履歴は各参照ドキュメント側に整理する。  
- 既存リポジトリで正常動作していたコードはモジュール単位で流用し、再利用しやすい構造へ作り直す。拡張性・保守性を最優先し、機能ごとに独立性を高める。  
- 手動テスト資産は `docs/test-handbook.md` に整備し、保守や構造理解に役立つ形で常設する。  
- モジュール別ディレクトリ整備（例: `server/`, `client_window_a/`, `handheld/`）と既存コード移設のロードマップを `docs/system/next-steps.md` と連動させる。  

## サーバーモジュール（server/）のセットアップと動作確認

このセクションは、Pi5 および開発用 Mac 上で `server/` を動かすための最小手順をまとめる。  
ここで定義したコマンドは AGENTS.md からも参照される。

### 1. 依存パッケージのインストール（venv 利用例）

    cd ~/RaspberryPiSystem_001/server
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e '.[dev]'

### 2. 開発サーバーの起動

    cd ~/RaspberryPiSystem_001/server
    source .venv/bin/activate
    raspberrypiserver

Flask の開発サーバーは前面で実行される。  
動作確認が済んだら `Ctrl+C` で必ず終了する。

### 3. ヘルスチェック

    curl -i http://127.0.0.1:8501/healthz

ステータスコード 200 が返れば、基本的な起動は成功している。

### 4. テスト実行（pytest）

    cd ~/RaspberryPiSystem_001/server
    source .venv/bin/activate
    python -m pytest

新しい機能や修正を加えた場合は、このコマンドを最低 1 回実行してからコミットする。

### 5. 設定ファイルのカスタマイズ（任意）

    cd ~/RaspberryPiSystem_001/server
    cp config/default.toml config/local.toml
    # 任意の内容に編集した後で
    python -m raspberrypiserver.app  # または raspberrypiserver

`config/local.toml` を利用する場合は、環境変数 `RPI_SERVER_CONFIG` を次のように設定する。

    export RPI_SERVER_CONFIG=~/RaspberryPiSystem_001/server/config/local.toml

### 6. リポジトリバックエンドの切り替え

`config/*.toml` の `SCAN_REPOSITORY_BACKEND` を `memory`（既定）または `db` に設定できる。

- `memory`: `InMemoryScanRepository` が指定容量だけペイロードを保持する（開発・テスト向け）。  
- `db`: PostgreSQL 用のプレースホルダー `DatabaseScanRepository` を初期化する。現状は実際の upsert を実装していないため、後続タスクで差し替える想定である。  

    SCAN_REPOSITORY_BACKEND = "db"
    SCAN_REPOSITORY_BUFFER = 500
    [database]
    dsn = "postgresql://app:app@localhost:15432/sensordb"

`db` バックエンドを利用する際は、サーバー側で `scan_ingest_backlog` など受け皿テーブルを作成しておく。  
現状は挿入のみ行い、今後 upsert ロジックへ差し替える予定である。

    cd ~/RaspberryPiSystem_001/server
    source .venv/bin/activate
    psql "postgresql://app:app@localhost:15432/sensordb" -f config/schema.sql

### 7. Pi 側でリポジトリを最新化する例

    cd ~/RaspberryPiSystem_001
    git pull

Pi 側のコード更新は、常に Git リポジトリの `git pull` を通して行い、手作業でのファイル編集は避ける。

## ドキュメントとタスク管理

- ロードマップと優先度付きタスクは `docs/system/next-steps.md` に集約する。  
- リポジトリ構造や systemd／ログパス整理といった構造系タスクの詳細は `docs/system/repo-structure-plan.md` に記録する。  
- 個々のテスト実行ログや観察結果は `docs/test-notes/**` に記録し、対応するタスクを `next-steps.md` から参照できるようにする。  

README にはタスク一覧を残さず、常に `docs/system/next-steps.md` を単一の「タスクの入り口」として扱う。  
