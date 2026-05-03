# Copilot 依頼テンプレート

以下は、このプロジェクトで Copilot に作業を依頼するときの基本テンプレートです。  
毎回この形をベースに、タスク内容だけ差し替えて使います。

## 1. 基本テンプレート

```text
作業前に以下を読んでください。

1. doc\tips\copilot\01-mandatory-rules.md
2. doc\tips\copilot\02-reference-order.md
3. 今回のタスクに関係する文書

今回のタスク:
[ここに依頼内容を書く]

期待すること:
- doc\spec\it-asset-management-demo.md に沿って進める
- Python / Django 前提を崩さない
- 必要なら関連ドキュメントも更新する
- 変更は今回のタスクに必要な範囲へ絞る
```

## 2. 認証タスク用テンプレート

```text
作業前に以下を読んでください。

1. doc\tips\copilot\01-mandatory-rules.md
2. doc\tips\copilot\02-reference-order.md
3. doc\spec\it-asset-management-demo.md
4. doc\spec-auth\prompt.md

今回のタスク:
[認証まわりの依頼を書く]

注意:
- tanoshimi.dev ポータルの認証引継ぎを前提にする
- アプリ単独のログイン画面を作らない
- portal_token を frontend JavaScript で扱わない
- 認証の最終判定は Django サーバー側に置く
```

## 3. Django 機能実装用テンプレート

```text
作業前に以下を読んでください。

1. doc\tips\copilot\01-mandatory-rules.md
2. doc\tips\copilot\02-reference-order.md
3. doc\spec\it-asset-management-demo.md

今回のタスク:
[機能実装の依頼を書く]

注意:
- Python / Django のモノリシック構成に従う
- 業務ルールはサーバー側で保証する
- Django Templates / Admin / Form を素直に活かす
- 必要なら spec や README も更新する
```

## 4. dev-plan step 実装用テンプレート

```text
作業前に以下を読んでください。

1. doc\tips\copilot\01-mandatory-rules.md
2. doc\tips\copilot\02-reference-order.md
3. doc\spec\it-asset-management-demo.md
4. 対象の doc\dev-plan\<phase>\dev-plan.md
5. 認証に関わる場合は doc\spec-auth\prompt.md

今回のタスク:
Implement E:\dev\vs_code\products\tanoshimi.dev\sys\demo03_am\doc\dev-plan\01\dev-plan.md step1.

注意:
- 指定された step の範囲だけを実装する
- 作業結果は `doc\dev-plan\01\result\step1-result.md` に出力する
- 確認は Docker コンテナで実際に実施する
- Docker で確認できない場合は、その理由を result 文書にも明記する
- 必要なら spec、README、dev-plan も更新する
```

## 5. ドキュメント更新用テンプレート

```text
作業前に以下を読んでください。

1. doc\tips\copilot\01-mandatory-rules.md
2. doc\tips\copilot\02-reference-order.md
3. README.md
4. doc\spec\it-asset-management-demo.md
5. 関連する既存ドキュメント

今回のタスク:
[文書作成・更新の依頼を書く]

注意:
- 計画書と矛盾しない内容にする
- 本番運用詳細は明示的な指示がない限り広げすぎない
- 既存文書との重複や矛盾を避ける
```

## 6. 運用のコツ

- 固定ルールは `doc\tips\copilot` に寄せる
- タスク本文には「今回だけ違うこと」を中心に書く
- 依頼のたびに読むべき文書を明示する
- 認証と業務ルールはフロントエンドへ逃がさない
- dev-plan 実装では step と result 出力先をセットで指定する
