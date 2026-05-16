# demo03_am

`demo03_am` は、tanoshimi.dev 向けの **IT資産・端末管理デモ** を整理・実装していくための作業ディレクトリです。

現時点では `Step 8` まで進み、Django / PostgreSQL / Docker Compose の土台、ポータル認証引継ぎを受けるための `accounts` 基盤、資産台帳の `assets` 基盤、資産一覧 / 詳細の参照導線、貸出申請フロー、承認・返却フロー、インシデント管理、棚卸しセッション管理、監査ログ、デモシードデータまで実装済みです。主要な方向性は `doc/spec/it-asset-management-demo.md` を基準にしています。

## 概要

このデモでは、社内で利用する IT資産・端末管理システムを題材に、次のような業務を扱います。

- 資産台帳管理
- 貸出申請と承認
- 返却受付
- 故障・紛失・廃棄の記録
- 棚卸しと操作履歴の管理

詳細なスコープ、ユースケース、エピック分割、MVP の考え方は以下の計画書を参照してください。

- `doc/spec/it-asset-management-demo.md`

## 現在の位置づけ

このディレクトリは、IT資産管理デモの仕様整理と実装を進めるための場所です。現在は Step 8 まで進み、Django プロジェクト本体、認証受け皿、資産台帳の中核モデルと Admin 基盤、利用者向け / 管理者向けの資産参照導線、貸出申請フロー、承認・返却フロー、故障 / 紛失 / 廃棄のインシデント管理、棚卸しセッションと差異確認、監査ログ一覧、デモシード投入コマンドまで整備しています。

## ローカル開発の前提

計画書では、ローカル開発の前提を次のように置いています。
認証まわりは demo01_crm と同様の方式を継続する想定で、専用のログインフローは設けない予定です。
docker-composeファイルのサービス名は、tdev-demo03-を接頭辞として付ける。他サービスとの衝突を避けるため。

- アプリ構成: Django 中心のモノリシック構成
- データベース: PostgreSQL
- 開発環境: Docker Compose で `tdev-demo03-web` / `tdev-demo03-db` / `tdev-demo03-adminer` を起動
- 本番環境: tanoshimi.dev 上の専用サブドメイン（`demo03-am.tanoshimi.dev`）

## ローカル起動手順

1. `sys\.env.example` を `sys\.env` にコピーする
2. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml up --build` を実行する
3. ブラウザで `http://localhost:18003` を開く
4. DB ビューアは `http://localhost:18081` で開く

## 認証基盤の現状

- `accounts` アプリでポータル連携済み利用者、ロール、ローカルセッション補助を管理する
- アプリ単独のログイン画面は作らず、バックエンドの `/auth/handover` が認証引継ぎ入口になる
- `portal_token` はフロントエンド JavaScript で扱わず、サーバー側で認証状態を受ける
- ローカル開発では `AUTH_MODE=dev-header` により、`X-Portal-*` ヘッダーを使って handover を確認できる

## 資産台帳基盤の現状

- `assets` アプリで `AssetCategory` と `Asset` を管理する
- 資産状態は `in_stock` / `on_loan` / `in_repair` / `lost` / `retired` で表現する
- シリアル番号と資産コードは一意制約で管理する
- Django Admin からカテゴリと資産台帳を登録・更新できる

## 資産参照導線の現状

- `/assets/` で認証済みユーザー向けの資産一覧を表示する
- `/assets/<asset_code>/` で資産詳細を表示する
- 資産一覧ではキーワード、状態、カテゴリで検索・絞り込みできる
- `asset-admin` または `sysadmin` ロールでは管理者向け表示を出し、それ以外では利用者向け表示を出し分ける

## 貸出申請フローの現状

- `loans` アプリで貸出申請・貸出記録・返却記録を管理する
- `/loans/request/<asset_code>/` で認証済みユーザーが貸出申請を行える
- `/loans/mine/` で自分の申請一覧を確認できる（承認済みの場合は返却申請ボタンあり）
- `/loans/admin/` で管理者が全申請を一覧できる（`asset-admin` / `sysadmin` ロール限定）
- 貸出可否（在庫状態確認・重複申請チェック）はサーバー側で判定する

## 承認・返却フローの現状

- `/loans/admin/<pk>/approve/` で管理者が申請を承認し、Asset を on_loan に更新する
- `/loans/admin/<pk>/reject/` で管理者が申請を却下する
- `/loans/mine/<pk>/return-request/` で申請者本人が返却申請を提出できる
- `/loans/admin/return-confirm/<pk>/` で管理者が返却確認し、通常は Asset を `in_stock` に戻す（インシデントで別状態に変更済みの場合はその状態を維持する）
- すべての状態遷移は `@transaction.atomic` で整合性を保証する

## インシデント管理の現状

- `incidents` アプリで故障・紛失・廃棄の記録を管理する
- `/incidents/` で管理者がインシデント一覧を確認できる（`asset-admin` / `sysadmin` ロール限定）
- `/incidents/report/<asset_code>/` で資産ごとにインシデントを記録できる
- 故障は解決処理により `in_repair` から `in_stock` に戻せるが、紛失・廃棄は恒久状態として扱う
- `in_repair` / `lost` / `retired` の資産は既存の貸出可否判定で貸出不可になる

## 棚卸しの現状

- `inventory` アプリで棚卸しセッションの開始・結果入力・完了を管理する
- `/inventory/` で管理者がセッション一覧を確認し、`/inventory/new/` で新規セッションを開始できる
- `/inventory/<pk>/` で全資産の実査結果（確認済み / 所在不明）を入力できる
- 所在不明として記録された `in_stock` 資産を差異として確認できる

## 監査ログの現状

- `auditlogs` アプリで主要な申請、承認、返却、インシデント、棚卸し操作を記録する
- `/auditlogs/` で管理者が操作履歴を一覧・絞り込みできる
- 主要な状態変更は更新処理と同じトランザクション単位で保存する

## デモシードデータ

- `python manage.py load_demo_seed` でデモ用カテゴリ、資産、ユーザー、貸出履歴、インシデント、棚卸しデータを投入できる
- `demo_employee / demo1234` と `demo_admin / demo1234` を利用して正常系と例外系を再現しやすくする
- ローカルでは次のコマンドで投入する

```sh
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py load_demo_seed
```

## 台帳初期データ方針

- デモ用初期データは Step 8 で `python manage.py load_demo_seed` から投入できるようにした
- 実演シナリオに合わせて、貸出履歴、インシデント、棚卸しサンプルも同じ管理コマンドで補完する

## 現在のディレクトリ構成

```text
demo03_am/
  doc/
  sys/
    .env
    .env.example
    requirements.txt
    app/
      accounts/
      assets/
      loans/
      incidents/
      inventory/
      auditlogs/
      manage.py
      config/
      templates/
      static/
    infra/
      docker/
        web/
      compose/
        docker-compose.yml
```

## ドキュメント案内

- 企画・実装方針: `doc/spec/it-asset-management-demo.md`
- 認証メモ: `doc/spec-auth/prompt.md`
