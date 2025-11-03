# ハンディ端末モジュール再構築メモ

## 1. API 送信
- `/api/v1/scans` への送信ロジックをモジュール化し、エラーハンドリング・再送キューを整理する。
- 既存の `check_connection.sh` や `handheld_scan_display.py` を参考に再構築する。

## 2. mirrorctl 運用
- `mirror_mode` チェック、ログローテーション、14 日連続監視を仕様化する。
- `docs/test-handbook.md` の手順に沿って日次記録ができるよう、スクリプトとテンプレートを整備する。

## 3. テスト
- Pi Zero 実機での手動テストをテンプレート化（送信 → Pi5 → Window A 連携）。
- 再送キュー挙動をログとともに確認する仕組みを用意する。
- mirrorctl との連動テストを `docs/test-handbook.md` に沿って定義し、送信失敗時のアラートと復旧手順をまとめる。
