# Window A クライアントモジュール

Window A（Pi4）で稼働する UI と周辺機器連携を再構築する領域。`docs/plan.md` に初期タスクを整理している。

## 当面のゴール
- Socket.IO で `scan.ingested` イベントを受信し、所在一覧の更新と REST フォールバックを維持する。
- DocumentViewer iframe や工具一覧 UI を段階的に移設し、テスト容易性を確保する。
- systemd ドロップインや環境ファイルを新構成に合わせて整備する。
