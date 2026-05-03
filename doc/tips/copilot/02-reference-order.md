# Copilot 参照順

このファイルは、Copilot が `demo03_am` で作業するときに**どの文書をどの順で読むか**を定義します。

## 1. 常に最初に読む

1. `doc\tips\copilot\01-mandatory-rules.md`
2. `README.md`
3. `doc\spec\it-asset-management-demo-plan.md`

## 2. タスク別に追加で読む

| 作業内容 | 追加で読む文書 |
| --- | --- |
| 認証、セッション、ポータル連携 | `doc\spec-auth\prompt.md` |
| 資産台帳、カテゴリ、状態管理 | `doc\spec\it-asset-management-demo-plan.md` の「スコープ」「Python / Django アーキテクチャ」「プロジェクト構成案」「データモデルの中心」 |
| 貸出申請、承認、返却 | `doc\spec\it-asset-management-demo-plan.md` の「デモで扱う業務フロー」「主要エピック」「最初のデモ対象ユースケース」「MVP機能セット」 |
| 故障、紛失、廃棄、棚卸し、監査 | `doc\spec\it-asset-management-demo-plan.md` の「スコープ」「主要エピック」「デモで見せるシナリオ」 |
| README や補助文書の更新 | `README.md` と `doc\spec\it-asset-management-demo-plan.md` |
| Copilot 運用文書の更新 | `doc\tips\copilot\README.md` と `doc\tips\copilot\workflow\README.md` |

## 3. 読み方のルール

1. まず固定ルールを読む
2. 次に README で現在の前提を確認する
3. 次に計画書で設計・スコープ・業務フローを確認する
4. 認証に触るときだけ `doc\spec-auth\prompt.md` を追加で読む
5. 実装後、必要なら関連ドキュメントも更新する

## 4. 参照時の注意

1. 存在しない文書を前提にして実装しない
2. `demo02_ferms` 用の spec や dev-plan を混ぜない
3. 補助文書よりも `doc\spec\it-asset-management-demo-plan.md` を優先する
