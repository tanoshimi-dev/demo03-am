# VPS デプロイ構成リファレンス

デプロイ作業中に発生した問題点・注意事項をまとめたリファレンスです。

---

## デプロイ方式

VPS への配置は **SFTP アップロード**（git clone ではない）。

ローカルの `sys/` ディレクトリをそのまま VPS にアップロードするため、
**VPS 上のディレクトリ構成はローカル PC と完全に一致する**。

---

## ディレクトリ構成（ローカル PC と VPS で共通）

```
tanoshimi.dev.demo03-am/            ← リポジトリ root
├── .gitignore
├── README.md
├── doc/
└── sys/                            ← ★ SFTP でアップロードするディレクトリ
    ├── .env                        ← gitignore 対象（ローカル・VPS それぞれ手動作成）
    ├── .env.example                ← ローカル開発用テンプレート（コミット対象）
    ├── .env.production.example     ← 本番用テンプレート（コミット対象）
    ├── requirements.txt
    ├── app/                        ← Django アプリケーション
    │   ├── manage.py
    │   ├── config/
    │   ├── accounts/
    │   └── ...
    └── infra/
        ├── compose/
        │   ├── docker-compose.yml          ← ローカル開発用（コミット対象）
        │   └── docker-compose.prod.yml     ← 本番用（gitignore 対象・VPS に手動配置）
        └── docker/
            └── web/
                └── Dockerfile              ← ローカル・VPS 共用（context から sys/ prefix あり）
```

---

## VPS 上で手動管理するファイル

以下は gitignore 対象のため、SFTP で別途アップロードする:

| ファイル | VPS 配置パス | 備考 |
|---|---|---|
| `sys/.env` | `tanoshimi.dev.demo03-am/sys/.env` | `.env.production.example` をコピーして実値を設定 |
| `sys/infra/compose/docker-compose.prod.yml` | `tanoshimi.dev.demo03-am/sys/infra/compose/docker-compose.prod.yml` | ローカル PC の最新版をそのまま使用 |

---

## デプロイコマンドの正規形

**VPS 上での実行はリポジトリ root から行う**:

```sh
cd ~/traefik/tanoshimi.dev.demo03-am

# 起動（初回 or リビルド）
docker compose --env-file sys/.env -f sys/infra/compose/docker-compose.prod.yml up --build -d

# 停止
docker compose --env-file sys/.env -f sys/infra/compose/docker-compose.prod.yml down

# ログ確認
docker compose --env-file sys/.env -f sys/infra/compose/docker-compose.prod.yml logs -f tdev-demo03-web

# マイグレーション（手動実行が必要な場合）
docker compose --env-file sys/.env -f sys/infra/compose/docker-compose.prod.yml exec tdev-demo03-web python manage.py migrate

# デモシード投入
docker compose --env-file sys/.env -f sys/infra/compose/docker-compose.prod.yml exec tdev-demo03-web python manage.py load_demo_seed
```

---

## 注意: Docker Compose プロジェクト名と Traefik

### 問題

`docker compose` を `sys/infra/compose/` ディレクトリ内から実行すると、
Docker Compose がそのフォルダ名 `compose` をプロジェクト名として使用する。

```
# ✗ 悪い例（sys/infra/compose/ から実行）
cd sys/infra/compose
docker compose --env-file ../../.env -f docker-compose.prod.yml up -d
→ プロジェクト名 = "compose"
→ 内部ネットワーク名 = "compose_tdev-demo03-network"
→ Traefik がコンテナを検出できない（404 page not found）
```

### 原因

Docker Compose のプロジェクト名の優先順:

1. `docker-compose.yml` の `name:` フィールド
2. `-p` / `--project-name` オプション
3. `COMPOSE_PROJECT_NAME` 環境変数
4. **compose ファイルが存在するディレクトリ名**（デフォルト）

`sys/infra/compose/` から実行するとディレクトリ名 `compose` がプロジェクト名になり、
`traefik.docker.network=traefik-network` ラベルが正しく機能しない。

### 解決策

`docker-compose.prod.yml` の先頭に `name: tanoshimidevdemo03am` を定義済み。
**`-p` オプション不要**で、どのディレクトリから実行してもプロジェクト名が固定される。

| 項目 | 値 |
|---|---|
| プロジェクト名 | `tanoshimidevdemo03am`（compose ファイルの `name:` で固定） |
| 内部ネットワーク | `tanoshimidevdemo03am_tdev-demo03-network` |
| demo02 との命名パターン | 一致（`tanoshimidevdemo02-ferms_tdev-demo02-network`） |
