# Copilot 運用ガイド

## 1. 目的

このディレクトリは、`demo03_am` で GitHub Copilot に作業を依頼するときの**固定ルール**、**参照順**、**依頼テンプレート**をまとめる場所です。

このプロジェクトの正本は `doc\spec\it-asset-management-demo-plan.md` です。Copilot 向け文書は、その計画書に沿って実装や文書更新をぶらさないための補助資料として扱います。

## 2. このプロジェクトの前提

- 題材は **IT資産・端末管理デモ**
- 技術の中心は **Python / Django**
- 構成は **Django 中心のモノリシック構成**
- DB は **PostgreSQL**
- 利用者向け画面は **Django Templates + HTMX または最小限の JavaScript**
- 管理導線は **Django Admin**
- 認証は **tanoshimi.dev ポータルからの引継ぎ**
- アプリ単独のログイン画面は持たない

## 3. 推奨ファイル構成

```text
doc/
  tips/
    copilot/
      README.md
      01-mandatory-rules.md
      02-reference-order.md
      03-prompt-template.md
      workflow/
        README.md
```

## 4. 各ファイルの役割

| ファイル | 役割 | 使い方 |
| --- | --- | --- |
| `README.md` | 入口説明 | Copilot 運用の全体像を確認する |
| `01-mandatory-rules.md` | 必須ルール | 実装前に必ず守らせる |
| `02-reference-order.md` | 参照順 | 作業内容ごとに読む文書をそろえる |
| `03-prompt-template.md` | 依頼文の雛形 | 毎回の依頼文を短く保つ |
| `workflow\README.md` | 運用設計 | CLI での実務運用方針を確認する |

## 5. どう利用するか

### 5.1 毎回の作業開始時

Copilot には最初に次を前提として読ませます。

1. `doc\tips\copilot\01-mandatory-rules.md`
2. `doc\tips\copilot\02-reference-order.md`
3. 今回のタスクに関係する正本ドキュメント

### 5.2 実装や文書更新を依頼するとき

`03-prompt-template.md` をベースにして、今回の依頼内容だけを書き換えて使います。

### 5.3 ルールを更新するとき

- 長期的に守らせたいことは `01-mandatory-rules.md`
- 読む順番や対象文書の整理は `02-reference-order.md`
- 毎回の依頼フォーマットは `03-prompt-template.md`
- CLI 運用の考え方は `workflow\README.md`

## 6. この構成にする理由

- Python / Django 前提の設計制約を毎回説明しなくて済む
- 正本の計画書と Copilot 向けルールを分離できる
- 認証や業務ルールをサーバー側に寄せる方針を維持しやすい
- 依頼文を短くしても仕様逸脱を減らせる
