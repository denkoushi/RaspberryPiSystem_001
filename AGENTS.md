# エージェント実行ガイド

このリポジトリでエージェントや自動化タスクを起動する際の前提と手順をまとめる。新しいスレッドやフローを開始するときは必ず本ファイルを参照する。

## プロジェクト構成
- Window A: `/Users/tsudatakashi/tool-management-system02`
- Window B: `/Users/tsudatakashi/DocumentViewer`
- Window C: `/Users/tsudatakashi/RaspberryPizero2W_withDropbox`
- Window D: `/Users/tsudatakashi/OnSiteLogistics`
- Window E: `/Users/tsudatakashi/RaspberryPiServer`

各ウィンドウ（リポジトリ）のコンテキストは独立して扱う。別ウィンドウの情報を参照する場合でも、都度ユーザー確認は不要。

## 方針
1. 一次情報（要件・決定事項）は本リポジトリ内で管理する。詳細手順や過去履歴は参照先ドキュメントにまとめる。
2. 既存の各リポジトリは途中までの試作が残っているが、本リポジトリでは白紙から再開発する。必要に応じて参照のみ行う。
3. エージェントは作業内容と参照元を明記し、進捗や未解決事項を README などに反映させる。
