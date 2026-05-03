# Copilot 実装ワークフロー設計

## 1. 目的

この文書は、`demo03_am` で Copilot CLI を使って実装や文書更新を進めるときに、**毎回の指示を短くしつつ、Python / Django 前提を維持する運用方法**を整理したものです。

このプロジェクトの正本は `doc\spec\it-asset-management-demo.md` であり、この文書はその正本を効率よく参照させるための運用ガイドです。

## 2. 結論

このプロジェクトでは、以下の 4 層構成が最も扱いやすいです。

1. **instructions** で恒久ルールを自動適用する
2. **`doc\tips\copilot`** を人間向けの詳細ルールとして維持する
3. **prompt template** で毎回の依頼文を短くする
4. 必要に応じて **plan / review / agents** を補助的に使う

つまり、**常設ルールは instructions、詳細説明は docs、毎回の差分は prompt、重い作業は補助機能**という分担にします。

## 3. このプロジェクトで重要な前提

- 技術の中心は **Python / Django**
- 画面は **Django Templates + HTMX または最小限の JavaScript**
- 管理導線は **Django Admin**
- 業務ルール、認証、認可、状態遷移はサーバー側に寄せる
- 認証は **tanoshimi.dev ポータルからの引継ぎ**
- アプリ単独のログイン画面は作らない
- 中核業務は **資産台帳、貸出、返却、故障/紛失/廃棄、棚卸し、監査**

## 4. Copilot CLI で使う主な仕組み

| 仕組み | 主用途 | このプロジェクトでの位置づけ |
| --- | --- | --- |
| `instructions` | 恒久ルール、禁止事項、参照順の補助 | **最優先** |
| `doc\tips\copilot` | 詳細ルール、テンプレート、運用説明 | **正本補助** |
| prompt template | 毎回の依頼文の標準化 | **実務必須** |
| `/plan` | 複雑な実装前の整理 | 大きい作業で有効 |
| `/review` | 差分レビュー | 重要変更で有効 |
| agents / subagents | 調査や分担 | 大きい作業で有効 |
| MCP / skills | 能力拡張 | 必要になってから検討 |

## 5. 各仕組みの使いどころ

### 5.1 instructions

向いていること:

- 毎回必ず守ってほしいルール
- Python / Django の固定前提
- 認証の恒久制約
- README や docs に書く内容の制約

このプロジェクトでは最重要です。

### 5.2 `doc\tips\copilot`

向いていること:

- instructions だけでは短すぎる説明
- 参照順の明文化
- 依頼テンプレート
- 運用の背景説明

このプロジェクトでは、**人間向けに見返すための補助正本**です。

### 5.3 prompt template

向いていること:

- 実装依頼の標準化
- 読むべき文書の明示
- 毎回の差分指示の最小化

### 5.4 `/plan`

向いていること:

- 複数アプリにまたがる実装
- 認証と業務ルールが同時に絡む変更
- 資産、貸出、棚卸し、監査をまたぐ大きいタスク

### 5.5 `/review`

向いていること:

- 認証変更
- 状態遷移変更
- データ整合性に関わる変更
- 権限制御や監査ログの変更

### 5.6 agents / subagents

向いていること:

- 影響範囲の調査
- 複数ファイルの文書整理
- 実装後のレビュー補助

## 6. 本プロジェクトでの推奨構成

```text
Layer 1: 自動適用
  .github/copilot-instructions.md
  .github/instructions/*.instructions.md

Layer 2: 詳細ルール
  doc/tips/copilot/01-mandatory-rules.md
  doc/tips/copilot/02-reference-order.md
  doc/tips/copilot/workflow/README.md

Layer 3: 実装・設計の正本
  README.md
  doc/spec/it-asset-management-demo.md
  doc/spec-auth/prompt.md

Layer 4: 毎回の差分指示
  doc/tips/copilot/03-prompt-template.md

Layer 5: 補助能力
  /plan
  /review
  /agent
```

## 7. 推奨運用手順

### 7.1 毎回の開始時

1. `01-mandatory-rules.md`
2. `02-reference-order.md`
3. `README.md`
4. `doc\spec\it-asset-management-demo.md`
5. 認証タスクなら `doc\spec-auth\prompt.md`

### 7.2 通常の依頼

依頼文は次のレベルまで短くしてよいです。

```text
doc/tips/copilot のルールに従って、
貸出申請まわりの Django 実装を進めてください。
必要なら関連ドキュメントも更新してください。
```

### 7.3 大きい作業のとき

以下を併用します。

1. `/plan`
2. `/review`
3. agents / subagents

### 7.4 重要箇所のとき

以下を追加します。

1. 認証文書の再確認
2. 状態遷移と監査ログの確認
3. 実装後の `/review`

## 8. 採用しない運用

このプロジェクトでは、以下を主軸にはしません。

### 8.1 毎回長文 prompt

理由:

- 更新コストが高い
- 文言の揺れで品質がぶれやすい

### 8.2 フロントエンド中心の責務分担

理由:

- このプロジェクトの計画書は Django 中心構成を前提としている
- 認証や業務ルールをクライアントへ寄せると設計方針とずれる

### 8.3 `demo02_ferms` 前提の再利用

理由:

- 題材も技術の見せ場も異なる
- 予約管理前提を持ち込むとドキュメントがぶれる

## 9. 実務上のおすすめ

1. `.github` の instruction には短い恒久ルールだけを書く
2. 詳細説明は `doc\tips\copilot` に寄せる
3. 設計判断は `doc\spec\it-asset-management-demo.md` を正本にする
4. 認証は `doc\spec-auth\prompt.md` を参照して判断する
5. 大きい作業だけ `/plan` と `/review` を併用する
