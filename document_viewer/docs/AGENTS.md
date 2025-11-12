# AGENTS.md

DocumentViewer リポジトリで作業するエージェント向けの指針です。新しいスレッドや自動化タスクを開始するときは、最初に確認してください。

## 1. リポジトリ概要
- ルートパス: `/Users/tsudatakashi/RaspberryPiSystem_001/document_viewer`
- 主要ドキュメント:
  - `README.md`: 概要と導入手順への案内
  - `docs/setup-raspberrypi.md`: Raspberry Pi へのセットアップ手順
  - `docs/requirements.md`: 要件・優先順位・決定事項
  - `docs/documentation-guidelines.md`: ドキュメントの役割と更新ルール

## 2. 作業フロー
1. `git status -sb` でブランチとローカル変更を確認する。
2. README / requirements / setup ドキュメントを読み、最新方針と矛盾がないかを把握する。`docs/requirements.md` の機能要件は ✅/☐ で進捗を管理し、変更があれば必ず更新する。
3. 仕様不明点があれば作業前にユーザーへ確認し、回答を `docs/requirements.md` に記録する。
4. 小さな修正は `main` に直接コミットしてよい。大きな変更・後戻りしづらい改修はブランチを切り、検証後にマージする。
5. コードや手順を更新した場合は、関連ドキュメント（setup・requirements 等）を忘れずに反映する。

## 3. コミュニケーションとコマンド提示
- すべて日本語で回答する。
- コードはコードブロックで示す。
- ラズパイ操作コマンドは以下をセットで提示する:
  1. 実行コマンド
  2. 期待される出力や結果の目安
  3. エラー時の診断コマンド
  4. 必要であれば再起動／状態確認／ロールバック手順
- Pi5 / Window A / Pi Zero の API トークンは RaspberryPiServer RUNBOOK（4章）に合わせてワンステップずつ更新する。ユーザーが各ステップを実行し結果を共有したのちに、次の指示を提示する。

## 4. エラー対応
- エラーが発生した場合は原因と復旧手順を提示し、可能なら予防策も提案する。
- ロールバックが必要か判断に迷う場合はユーザーへ確認する。

## 5. 提案スタイル
- 複数案を示し、推奨案と理由・トレードオフを説明する。
- 決定事項は `docs/requirements.md` へ反映し、関連ドキュメントのリンクも更新する。

## 6. 参考リンク
- ドキュメント索引: `docs/docs-index.md`
- ドキュメント運用ガイドライン: `docs/documentation-guidelines.md`
- セットアップ手順: `docs/setup-raspberrypi.md`
- 要件とロードマップ: `docs/requirements.md`
- テストメモ: `docs/test-notes/2025-10-26-viewer-check.md`
