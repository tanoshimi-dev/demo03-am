# Step 2 Result — 本番用環境変数テンプレート

## 実施内容

`sys/.env.production.example` を新規作成。本番デプロイ時に VPS 上で `sys/.env` を作成するためのテンプレート。

## 作成ファイル

| ファイル | 説明 |
|---|---|
| `sys/.env.production.example` | 本番環境変数テンプレート（実値なし） |

## テンプレートに含む変数

| 変数 | 本番値の方針 |
|---|---|
| `DJANGO_SECRET_KEY` | `secrets.token_hex(50)` で生成 |
| `DJANGO_DEBUG` | `0` 固定 |
| `DJANGO_ALLOWED_HOSTS` | `demo03-am.tanoshimi.dev` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://demo03-am.tanoshimi.dev` |
| `POSTGRES_DB` | `demo03_am` |
| `POSTGRES_USER` | `demo03_am` |
| `POSTGRES_PASSWORD` | `secrets.token_urlsafe(32)` で生成 |
| `AUTH_MODE` | `portal` 固定 |
| `SESSION_COOKIE_NAME` | `demo03_am_session` |
| `PORTAL_COOKIE_NAME` | `portal_token` |
| `PORTAL_COOKIE_NAMES` | portal 実装に合わせてカンマ区切りで列挙 |
| `PORTAL_ISSUER` | portal チームに確認（`/auth/jwt-check` で検証可能） |
| `PORTAL_JWKS_URL` | `https://api.tanoshimi.dev/v1/.well-known/jwks.json` |
| `PORTAL_LOGIN_URL` | `https://tanoshimi.dev/login` |
| `PORTAL_ALLOWED_RETURN_TO_HOSTS` | `demo03-am.tanoshimi.dev` |

## 検証

実値を含まないことを確認（`<...>` プレースホルダーのみ）。  
`.gitignore` で除外対象でないことを確認（`example` ファイルはコミット可能）。

## 次のステップ

Step 3: VPS にデプロイする

1. VPS に SSH 接続し、リポジトリをクローン
2. `sys/.env.production.example` をコピーして `sys/.env` を作成し実値を設定
3. `docker-compose.prod.yml` を手動配置
4. `docker compose up --build -d` でコンテナ起動
