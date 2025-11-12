# 2025-10-26 DocumentViewer `/etc/default/docviewer` 設定メモ

## 目的
- Window A 実機で `document-viewer.service` が参照する環境ファイル `/etc/default/docviewer` をテンプレートから展開し、環境変数の整合性を確認する。
- `VIEWER_LOG_PATH` を利用したアクセスログの出力先を明示し、14 日チェックシートへ転記できる手順を整理する。

## 手順

1. 環境ファイル展開
    - 自動化スクリプトを利用する場合
      ```bash
      sudo ./scripts/install_docviewer_env.sh \
        --owner tools01:tools01 \
        --api-base http://raspi-server.local:8501 \
        --docs-dir /home/tools01/RaspberryPiSystem_001/document_viewer/documents \
        --log-path /var/log/document-viewer/client.log
      ```
      - 既存の `/etc/default/docviewer` がある場合は `--force` オプションでバックアップを残しつつ上書きできる。
      - `--dry-run` を付けると作業内容のみ確認できる。
    - 手動で行う場合
    ```bash
    sudo install -m 640 ~/RaspberryPiSystem_001/document_viewer/config/docviewer.env.sample /etc/default/docviewer
    sudo nano /etc/default/docviewer
    ```
    - `VIEWER_API_BASE` / `VIEWER_SOCKET_BASE` を `http://raspi-server.local:8501` に合わせる。
    - `VIEWER_LOCAL_DOCS_DIR=/home/tools01/RaspberryPiSystem_001/document_viewer/documents`（Window A 側で PDF を参照する場合）。
    - `VIEWER_LOG_PATH=/var/log/document-viewer/client.log` を指定。

2. ディレクトリ準備（スクリプト利用時は自動作成される）
    ```bash
    sudo install -d -o tools01 -g tools01 -m 750 /var/log/document-viewer
    sudo touch /var/log/document-viewer/client.log
    sudo chown tools01:tools01 /var/log/document-viewer/client.log
    ```

3. サービス再起動
    ```bash
    sudo systemctl restart document-viewer.service
    sudo systemctl status document-viewer.service
    ```

4. 動作確認
    - `curl http://127.0.0.1:5000/api/documents/testpart`（Window A 側 Flask のポート）で 200 / 404 を確認。
    - `tail -f /var/log/document-viewer/client.log` でアクセスログが追記されることを確認。
    - Socket.IO イベント発火後に自動表示されることをメイン画面で確認。必要なら `VIEWER_ACCEPT_DEVICE_IDS` のフィルタを一時解除してテスト。
    - RaspberryPiServer 側 `/srv/RaspberryPiSystem_001/server/logs/document_viewer.log`（旧 `/srv/rpi-server/logs/document_viewer.log`）と突き合わせ、同一タイムスタンプで記録されているか確認する。
    - オプション: `~/RaspberryPiSystem_001/document_viewer/scripts/docviewer_check.py --part <部品番号>` を利用して API 応答を確認し、ローカル PDF の有無も自動チェックする。

## ログ取り扱い
- `/var/log/document-viewer/client.log` は最大 3MB × 3世代でローテーションされる（Flask 側設定）。
- 14 日チェックシート（RaspberryPiServer 側）には、`client.log` のディレクトリパスと確認日時を記録する欄を追加予定。
- RaspberryPiServer 側の `/srv/RaspberryPiSystem_001/server/logs/document_viewer.log`（旧 `/srv/rpi-server/logs/document_viewer.log`）と併せて、サーバー側・クライアント側双方のログを比較できるよう日付・時刻形式（ISO8601）で記録する。
- ログの保管方針は RaspberryPiServer リポジトリの `docs/mirror-verification.md`・`docs/requirements.md` にも追記済み。双方の記載が一致しているか定期的に確認する。
- RUNBOOK 上のトラブルシュート（RaspberryPiServer `RUNBOOK.md`）にも追記されたため、運用手順を更新した際は双方の記述を同期させる。

## 未確認事項
- Window A の Chromium kiosk モードで、初回起動時に Socket.IO クライアントが `VIEWER_SOCKET_BASE` を正しく参照するか要確認。
- `VIEWER_ACCEPT_DEVICE_IDS` を設定した際、ハンディリーダ複数台を想定した運用テストが未実施。
