# demo03_am

`demo03_am` は、tanoshimi.dev 向けの **IT資産・端末管理デモ** を整理・実装していくための作業ディレクトリです。

現時点では `Step 1` として Django / PostgreSQL / Docker Compose の最小土台まで実装済みで、主要な方向性は `doc/spec/it-asset-management-demo.md` を基準にしています。

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

このディレクトリは、IT資産管理デモの仕様整理と実装を進めるための場所です。現在は Step 1 として、Django プロジェクト本体、PostgreSQL 接続設定、Docker Compose によるローカル起動基盤まで整備しています。

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

## 現在のディレクトリ構成

```text
demo03_am/
  doc/
  sys/
    .env
    .env.example
    requirements.txt
    app/
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
