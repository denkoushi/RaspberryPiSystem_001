# DocumentViewer CHANGELOG

本プロジェクトで適用済みの主要な変更を時系列で記録します。開発中の計画や未実装事項は `docs/requirements.md` や `docs/test-notes/` を参照してください。

## 2025-10-26

- DocumentViewer Flask アプリに `VIEWER_LOCAL_DOCS_DIR` を追加し、PDF 保存先を環境変数で切り替え可能にした。
- `VIEWER_LOG_PATH` を新設し、ドキュメント検索/配信/拒否イベントをローテーション付きファイルへ記録。
- `tests/test_viewer_app.py` を追加し、環境変数適用・API 応答・ログ出力を含む 5 ケースの `pytest` を整備。
- `README.md` を更新し、主要な環境変数一覧と `pytest` 実行手順を追記。
- `docs/test-notes/2025-10-26-viewer-check.md` にログ対応状況を反映。
- `/etc/default/docviewer` テンプレート (`config/docviewer.env.sample`) とログ手順ノート (`docs/test-notes/2025-10-26-docviewer-env.md`) を追加。
- API 疎通確認用スクリプト `scripts/docviewer_check.py` を追加し、テスト (`tests/test_docviewer_check.py`) を整備。

## 2025-10-31

- DocumentViewer の要件 (`docs/requirements.md`) を Pi5 サーバー集約後の構成に合わせて再整備。
- README / setup ガイドに Pi5 ホスト名 (`raspi-server-*.local`) や追加依存パッケージを反映。
- ドキュメント索引 (`docs/docs-index.md`) とテストノート索引を棚卸しし、✅ を記録。
