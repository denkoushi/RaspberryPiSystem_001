# Window A クライアントモジュール

Window A（Pi4）で稼働するクライアント UI と周辺機器連携コードをこのディレクトリに集約する。DocumentViewer iframe や所在一覧 UI、Socket.IO クライアントなどを段階的に移設する計画。

## 今後の整理方針
- 旧 `tool-management-system02` リポジトリから UI コンポーネントや設定スクリプトを抽出し、再利用しやすい形に分割する。
- Pi5 と連携するための環境変数・systemd 設定サンプルを `config/`（未作成）にまとめる。
- 手動テストメニュー（`docs/test-handbook.md`）に沿って UI 健全性を確認できるスクリプトやメモを整備する。
