# UI 側実装メモ

- `SocketListener` をビュー層から利用し、`scan.ingested` 受信で所在一覧を更新する。
- REST フォールバックは `fetchPartLocations` 関数（今後実装）で行い、Socket と並列運用する。
- 旧リポジトリから React コンポーネントを移植する際の注意点をリスト化予定。
