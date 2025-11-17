# Pi4 / Pi5 再起動チェックリスト

開発期間中に Pi4 (Window A) / Pi5 (RaspberryPiServer) を再起動したとき、機能が完全に復旧するまでに迷わないよう確認手順をまとめる。**本番リリース後はリリースタグ＋自動起動だけで済むようにする予定**だが、現段階では以下の手順を毎回実施する。

## 共通前提
- すべての作業は `~/RaspberryPiSystem_001` ワークツリーで行う。
- ブランチは開発用の `feature/repo-structure-plan` を checkout する（`git status -sb` で確認）。
- `git pull` で最新差分を取得してからサービスを再起動する。

## Pi5 (RaspberryPiServer)
1. `feature/repo-structure-plan` であることを確認し、必要なら切り替え。
   ```bash
   cd ~/RaspberryPiSystem_001
   git fetch origin
   git checkout feature/repo-structure-plan
   git pull
   ```
2. `server/src/raspberrypiserver.egg-info/*` が変更扱いのときは editable install をクリーンにし、再インストールする。
   ```bash
   cd ~/RaspberryPiSystem_001/server
   .venv/bin/python -m pip uninstall raspberrypiserver -y
   git checkout -- src/raspberrypiserver.egg-info/*
   .venv/bin/python -m pip install -e '.[dev]'
   ```
3. systemd を再起動し、待ち受けと REST API を確認。
   ```bash
   cd ~/RaspberryPiSystem_001
   sudo systemctl restart raspberrypiserver.service
   sudo systemctl status raspberrypiserver.service --no-pager
   sudo ss -ltnp | grep 8501
   curl -i http://127.0.0.1:8501/healthz
   curl -i http://127.0.0.1:8501/api/v1/loans
   curl -i http://127.0.0.1:8501/api/toolmgmt/overview
   curl -i http://127.0.0.1:8501/api/logistics/jobs
   ```
   すべて `HTTP/1.1 200 OK` で戻れば Pi4 から呼び出しても問題ない。

## Pi4 (Window A)
1. `feature/repo-structure-plan` → `git pull` を実施。
   ```bash
   cd ~/RaspberryPiSystem_001
   git checkout feature/repo-structure-plan
   git pull
   ```
2. `toolmgmt.service` を再起動し、ログにエラーが出ていないか確認。
   ```bash
   sudo systemctl restart toolmgmt.service
   sudo journalctl -u toolmgmt.service -n 40 --no-pager
   ```
   `/api/toolmgmt/overview HTTP/1.1 200` が繰り返し出ていれば Pi5 との連携は復旧している。
3. ブラウザでダッシュボードを開き、NFC スキャン → 貸出一覧の自動更新 → DocumentViewer / ログ更新などを手動テストして `docs/test-notes/2025-11/window-a-demo.md` に記録する。

## 本番運用に向けた TODO
- リリースタグを作成し、現場にはタグ単位で配布する方針に切り替える。
- systemd ユニットの `Restart=always` と自動起動手順を検証し、電源投入のみでサービスが立ち上がる状態を確認する。
- git pull や `pip install -e` といった手作業は開発チーム側でのみ行い、現場オペレータには再起動 → 動作確認のみにしてもらう。
