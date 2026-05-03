# Step 2 Result

## 実装内容

- `sys\app\accounts` アプリを追加し、ポータル連携済み利用者、ロール、ローカルセッション補助を扱う `Account` / `AppRole` / `AccountSession` モデルを実装
- `accounts.middleware.PortalSessionMiddleware` を追加し、認証済みユーザーの `request.account` 解決とセッション最終アクセス更新をサーバー側で処理
- `/auth/me`、`/auth/handover`、`/auth/logout` を追加し、アプリ単独ログイン画面を作らずにバックエンドの handover 入口でローカルセッションを確立できるようにした
- `returnTo` を許可ホスト付きでサニタイズし、未認証時はポータルログイン URL へのリダイレクト、または 401 応答に統一した
- `AUTH_MODE`、`PORTAL_*`、`SESSION_COOKIE_NAME` などの環境変数を追加し、`dev-header` モードでローカル検証できるようにした
- `README.md` と `doc\dev-plan\01\dev-plan.md` を更新し、Step 2 完了状態と認証基盤の現状を反映した

## 変更ファイル

- `sys\app\accounts\__init__.py`
- `sys\app\accounts\apps.py`
- `sys\app\accounts\models.py`
- `sys\app\accounts\admin.py`
- `sys\app\accounts\middleware.py`
- `sys\app\accounts\services.py`
- `sys\app\accounts\urls.py`
- `sys\app\accounts\views.py`
- `sys\app\accounts\migrations\__init__.py`
- `sys\app\accounts\migrations\0001_initial.py`
- `sys\app\config\settings.py`
- `sys\app\config\urls.py`
- `sys\app\templates\home.html`
- `sys\.env.example`
- `README.md`
- `doc\dev-plan\01\dev-plan.md`

## Docker で使った検証コマンド

1. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml run --rm --entrypoint python tdev-demo03-web manage.py makemigrations accounts`
2. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml up -d --build`
3. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py check`
4. `curl http://localhost:18003/auth/me`
5. `curl -L -c <cookie-file> -b <cookie-file> -H "X-Portal-Subject: portal-user-001" -H "X-Portal-Email: user1@example.com" -H "X-Portal-Name: Demo User One" -H "X-Portal-Roles: asset-admin,employee" "http://localhost:18003/auth/handover?returnTo=/auth/me"`
6. `curl -b <cookie-file> http://localhost:18003/auth/me`
7. `curl -L -b <cookie-file> -c <cookie-file> "http://localhost:18003/auth/logout?returnTo=/"`
8. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml down`

## 実際の検証結果

- `manage.py check` は成功し、設定エラーは出なかった
- 未認証状態の `GET /auth/me` は `401` を返し、`handoverUrl` を含む JSON 応答になった
- `AUTH_MODE=dev-header` のまま `X-Portal-*` ヘッダー付きで `GET /auth/handover?returnTo=/auth/me` を呼ぶと、ローカルセッション Cookie を発行して認証済み状態へ遷移した
- 認証後の `GET /auth/me` は `authenticated: true` と `portalSubject: portal-user-001`、`roles: ["asset-admin", "employee"]` を返した
- `GET /auth/logout?returnTo=/` 後の `GET /auth/me` は再度 `401` を返し、ローカルセッション破棄を確認できた

## 残課題 / フォローアップ

- 本番向けの `portal_token` / JWKS 検証そのものは今後のポータル連携実装で追加する必要がある
- 現時点のローカル検証は `AUTH_MODE=dev-header` を使った trusted header ベースで行っている
- 認可の実運用ルールは、今後 `accounts` と各業務アプリの権限実装で具体化する
