# dev-plan 03: VPS デプロイ

## 概要

ローカル開発環境（Docker Compose + runserver）で動作している `demo03_am` を、VPS 上の本番相当環境へデプロイする。

公開 URL は `demo03-am.tanoshimi.dev` を想定する。  
認証は `demo01_crm` と同じポータルハンドオーバー方式を維持し、VPS 上でも同じ仕組みを成立させる。

---

## 前提

- VPS に Docker / Docker Compose がインストール済みであること
- VPS 上で Traefik がすでに稼働しており、`traefik-network`（external）が存在すること（`demo02_ferms` と同じ構成）
- Traefik が Cloudflare DNS チャレンジで SSL 証明書を自動取得・更新すること
- ドメイン `demo03-am.tanoshimi.dev` の DNS が VPS のパブリック IP に向いていること
- `demo01_crm` ポータルとの連携設定（JWKS URL、Issuer など）は本番値に差し替える
- `.env` ファイルはリポジトリに含めず、VPS 上で直接管理する
- `sys/infra/compose/docker-compose.prod.yml` は `.gitignore` で除外し、VPS 上で直接配置する

---

## フェーズ構成

| Step | タイトル | 目的 | Status |
|------|----------|------|--------|
| Step 1 | 本番用 Docker Compose を整える | runserver → Gunicorn 切替、Traefik ラベル設定 | Done |
| Step 1.5 | portal_token JWT 検証を実装する | 本番 AUTH_MODE=portal で動作させるための前提条件（詳細: `auth-production-blocker.md`） | Done |
| Step 2 | 本番用環境変数テンプレートを作る | 本番設定の網羅、`.env.production.example` 作成 | Done |
| Step 3 | VPS にデプロイする | リポジトリ配置、`.env` 設置、コンテナ起動、マイグレーション | Done |
| Step 4 | 動作確認とデプロイ後チェック | 疎通・認証・主要機能の確認、結果記録 | Not Started |

---

## Step 1: 本番用 Docker Compose を整える ✅

### 目的

ローカル用の `docker-compose.yml` をそのまま本番に使わず、本番向けの `docker-compose.prod.yml` を用意する。  
Traefik がリバースプロキシ・SSL 終端を担うため、Nginx の設定は不要。

### 実施済み内容

- `sys/infra/compose/docker-compose.prod.yml` を作成済み
  - `command`: `migrate --noinput` → `collectstatic --noinput` → `gunicorn` の順で起動
  - `ports` → `expose` に変更（Traefik 経由のみアクセス）
  - `restart: unless-stopped` を追加
  - `postgres:16-alpine` を使用、DB ポートはホスト側に非公開
  - Adminer コンテナは含まない
  - `tdev-demo03-network`（internal）と `traefik-network`（external）の両方に接続
  - Traefik ラベルで `demo03-am.tanoshimi.dev` にルーティング・SSL 設定
- `sys/requirements.txt` に `gunicorn>=21.0,<23.0` を追加済み
- `sys/app/config/settings.py` に Traefik 対応設定を追加済み
  - `SECURE_PROXY_SSL_HEADER`、`USE_X_FORWARDED_HOST`
  - `SESSION_COOKIE_SECURE = not DEBUG`、`CSRF_COOKIE_SECURE = not DEBUG`
- `docker-compose.prod.yml` を `.gitignore` に追加済み（VPS 上で直接管理）

### Traefik ラベル（`docker-compose.prod.yml` 内）

```yaml
labels:
  - 'traefik.enable=true'
  - 'traefik.http.routers.tdev-demo03-am.rule=Host(`demo03-am.tanoshimi.dev`)'
  - 'traefik.http.routers.tdev-demo03-am.entrypoints=https'
  - 'traefik.http.routers.tdev-demo03-am.tls=true'
  - 'traefik.http.routers.tdev-demo03-am.tls.certresolver=cloudflare'
  - 'traefik.http.services.tdev-demo03-am.loadbalancer.server.port=8000'
  - 'traefik.docker.network=traefik-network'
```

---

## Step 2: 本番用環境変数テンプレートを作る

### 目的

本番環境で必要な全環境変数を網羅した `.env.production.example` を作成し、VPS 設置時の設定漏れを防ぐ。

### やること

1. `sys/.env.production.example` を新規作成する（実値は含めない）

   ```
   # Django
   DJANGO_SECRET_KEY=<本番用の強固な乱数値>
   DJANGO_DEBUG=0
   DJANGO_ALLOWED_HOSTS=demo03-am.tanoshimi.dev
   DJANGO_CSRF_TRUSTED_ORIGINS=https://demo03-am.tanoshimi.dev

   # PostgreSQL
   POSTGRES_DB=demo03_am
   POSTGRES_USER=demo03_am
   POSTGRES_PASSWORD=<強固なパスワード>

   # 認証
   AUTH_MODE=portal
   SESSION_COOKIE_NAME=demo03_am_session
   PORTAL_COOKIE_NAME=portal_token
   PORTAL_COOKIE_NAMES=portal_token,authjs.session-token,__Secure-authjs.session-token,better-auth.session_token,__Secure-better-auth.session_token
   PORTAL_ISSUER=https://tanoshimi.dev
   PORTAL_JWKS_URL=https://api.tanoshimi.dev/v1/.well-known/jwks.json
   PORTAL_LOGIN_URL=https://tanoshimi.dev/login
   PORTAL_ALLOWED_RETURN_TO_HOSTS=demo03-am.tanoshimi.dev
   ```

### 完了条件

- `.env.production.example` が `sys/` 直下に配置されている
- 実値を含まない（シークレットのコミット禁止ルール遵守）
- 設定項目に抜けがない

---

## Step 3: VPS にデプロイする

### 目的

VPS 上でリポジトリを配置し、`docker-compose.prod.yml` を設置してコンテナを起動する。

### やること

1. VPS へ SSH 接続し、作業ディレクトリを決める（例: `/srv/tanoshimi/demo03_am`）

2. リポジトリをクローンする
   ```sh
   git clone <repo_url> /srv/tanoshimi/demo03_am
   cd /srv/tanoshimi/demo03_am
   ```

3. `docker-compose.prod.yml` を配置する（`.gitignore` 対象のため手動設置）
   ```sh
   # VPS 上でファイルを作成またはコピーする
   vi sys/infra/compose/docker-compose.prod.yml
   ```

4. `.env` を設置する
   ```sh
   cp sys/.env.production.example sys/.env
   # エディタで実値に差し替える（SECRET_KEY、POSTGRES_PASSWORD など）
   vi sys/.env
   ```

5. `traefik-network` が存在することを確認する
   ```sh
   docker network ls | grep traefik-network
   ```

6. コンテナをビルドして起動する（`migrate` + `collectstatic` + `gunicorn` は command に含まれる）
   ```sh
   docker compose --env-file sys/.env -f sys/infra/compose/docker-compose.prod.yml up --build -d
   ```

7. ログを確認する
   ```sh
   docker compose --env-file sys/.env -f sys/infra/compose/docker-compose.prod.yml logs -f tdev-demo03-web
   ```

8. デモシードを投入する（必要な場合）
   ```sh
   docker compose --env-file sys/.env -f sys/infra/compose/docker-compose.prod.yml exec tdev-demo03-web python manage.py load_demo_seed
   ```

### 完了条件

- `docker compose ps` で全コンテナが `healthy` または `running` になっている
- マイグレーションがログ上で正常に完了している
- Traefik がコンテナを検出して `demo03-am.tanoshimi.dev` にルーティングしている

---

## Step 4: 動作確認とデプロイ後チェック

### 目的

本番デプロイ後に最低限の疎通・認証・主要業務フローを確認し、問題がなければデプロイ完了とする。

### やること

1. **疎通確認**
   - `curl -I https://demo03-am.tanoshimi.dev/` でステータス 200 または 302 を確認する
   - 静的ファイル（`/static/` パス）が 200 で返ることを確認する

2. **認証確認**
   - ポータル（`tanoshimi.dev`）からログインし、`demo03-am.tanoshimi.dev` へ認証引継ぎが成功することを確認する
   - `AUTH_MODE=portal` で handover が動くことを確認する

3. **主要機能確認**
   - `/assets/` で資産一覧が表示される
   - 管理者ユーザーで貸出申請・承認・返却の基本フローが通る
   - Django Admin（`/admin/`）にアクセスできる

4. 確認結果を `result/step4-result.md` に記録する

### 完了条件

- 上記すべての確認項目がパスしている
- エラーログにクリティカルなエラーがない
- `result/step4-result.md` に結果が記録されている

---

## 注意事項

- `AUTH_MODE=dev-header` と `DJANGO_DEBUG=1` は本番環境では絶対に使わない
- `.env` と `docker-compose.prod.yml` は Git にコミットしない（`.gitignore` で除外済み）
- `DJANGO_SECRET_KEY` は本番用に再生成する（ローカルの値を使い回さない）
- DB ポートはホスト側に公開しない（Traefik + tdev-demo03-network 経由のみ）
- Adminer コンテナは本番では起動しない
- Traefik が稼働していない場合はコンテナは起動するがルーティングされない

