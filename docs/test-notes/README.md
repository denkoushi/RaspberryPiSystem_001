# 手動テスト記録ガイド

本ディレクトリは手動テストの実施ログや証跡を資産として保存する場所です。以下のルールに従って運用してください。

## 1. ファイル命名規則
- 日次ログ: `YYYY-MM-DD-handheld-flow.md` のように日付とシナリオ名を組み合わせる。
- 週次・まとめ: `YYYY-Www-summary.md` など、期間が分かる名称を付ける。
- 追加シナリオ: `YYYY-MM-DD-<scenario>.md` の `<scenario>` は `usb-dist`, `viewer-check` など短く記述する。

## 2. テンプレート
テンプレートは `templates/` に配置する。必要に応じてコピーして利用する。

```bash
cp docs/test-notes/templates/daily-handheld.md \
  docs/test-notes/$(date +%F)-handheld-flow.md
cp docs/test-notes/templates/pi-zero-integration.md \
  docs/test-notes/$(date +%F)-pi-zero-integration.md
```

## 3. 記録する内容
- 実施者・日時
- 対象機器（Pi Zero / Pi5 / Window A / DocumentViewer など）
- 実行コマンドと結果（成功/失敗、ログ抜粋）
- 期待結果との比較、観察事項
- 次回へのメモ・改善点

コマンドは必ず以下のようにコードブロックで残す。

```bash
sudo journalctl -u handheld@tools01.service -n 30 --no-pager
```

## 4. 保存手順
1. テンプレートをコピーして当日のファイルを作成。
2. 実施内容を記入し、スクリーンショットがある場合は画像へのパスまたはメモを残す。
3. 作業終了後、`git add docs/test-notes/<ファイル名>` を実行。
4. コミット・プッシュ後は Raspberry Pi 側でも最新化する。

```bash
git add docs/test-notes/2025-11-03-handheld-flow.md
git commit -m "Add handheld flow log for 2025-11-03"
git push
```

## 5. テンプレートの更新
テンプレートを改訂した場合は、変更理由と適用対象をこの `README.md` に追記し、既存ログへの反映要否を記録する。
- 例: `pi-zero-integration.md` を更新した場合、Pi Zero 実機テスト記録にどこまで再適用するか検討する。
