# 再送・mirrorctl 連携設計（ドラフト）

## 再送キュー
- 送信失敗時は JSON キューに `status=queued` で保存し、定期的に再送する。
- 再送上限・間隔を設定し、超過時は mirrorctl アラート対象とする。
- `handheld/src/retry_queue.py` に簡易キュー処理を追加済み。今後、ステータス管理と再送ループを実装する。
- `handheld/src/types.py` に ScanPayload / RetryItem を定義し、再送キューでメタデータを保持する。

## mirrorctl 連携
- `mirrorctl status` の OK/NOK で再送状態を確認し、14 日カウントを更新する。
- 再送上限超過やバックログ滞留が発生した場合は `mirrorctl disable` → 原因調査 → `mirrorctl enable` の手順を明文化。
- `retry_loop` から成功/失敗件数を出力し、`mirrorctl status` に記録する項目を整理する予定。`mirrorctl_hook` で件数を受け取り、CLI から status 更新できるようにする。
