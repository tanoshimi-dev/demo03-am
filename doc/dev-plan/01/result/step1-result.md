# Step 1 Result

## 実装内容

- `sys\app\manage.py` と `sys\app\config\*` を追加し、Django プロジェクトの最小構成を作成
- PostgreSQL 接続を環境変数ベースで読む `settings.py` と `env.py` を追加
- ルート `/` で起動確認できる最小テンプレート `sys\app\templates\home.html` を追加
- `sys\infra\docker\web\Dockerfile` と `sys\infra\compose\docker-compose.yml` を追加し、`tdev-demo03-` 接頭辞の `web` / `db` / `adminer` サービスを構成
- `sys\.env.example`、`sys\requirements.txt`、`README.md`、`doc\dev-plan\01\dev-plan.md` を更新し、ローカル起動手順と Step 1 完了状態を反映
- 追加の単体テストとして `sys\app\accounts\tests\test_foundation.py` を追加し、環境変数 helper とトップページ応答を確認できるようにした

## 変更ファイル

- `sys\requirements.txt`
- `sys\.env.example`
- `sys\infra\compose\docker-compose.yml`
- `sys\app\manage.py`
- `sys\app\config\__init__.py`
- `sys\app\config\env.py`
- `sys\app\config\settings.py`
- `sys\app\config\urls.py`
- `sys\app\config\wsgi.py`
- `sys\app\config\asgi.py`
- `sys\app\templates\home.html`
- `sys\app\static\.gitkeep`
- `sys\infra\docker\web\Dockerfile`
- `sys\infra\compose\docker-compose.yml`
- `sys\app\accounts\tests\test_foundation.py`
- `README.md`
- `doc\dev-plan\01\dev-plan.md`

## Docker で使った検証コマンド

1. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml config`
2. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml up -d --build`
3. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml ps`
4. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py check`
5. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml run --rm --entrypoint python tdev-demo03-web manage.py test`
6. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml down`

補足:

- ローカル疎通確認として `http://localhost:18003/` へ HTTP アクセスも実施

## 実際の検証結果

- Compose 設定の解決に成功
- `tdev-demo03-db` は healthy、`tdev-demo03-web` も healthy で起動
- `python manage.py migrate` が起動時に完了し、Django 標準 migration が PostgreSQL に適用された
- `http://localhost:18003/` でトップページの HTML 応答を確認
- `tdev-demo03-adminer` を追加し、DB ビューアを `http://localhost:18081/` で開ける構成にした
- `python manage.py check` は `System check identified no issues (0 silenced).` を返却
- `manage.py test` で Step 1〜3 分を含む 17 件の単体テストが成功した

## 残課題 / フォローアップ

- Step 2 の `accounts` アプリとポータル認証引継ぎ基盤は未実装
- 管理ユーザー作成、業務アプリ追加、デモデータ投入は今後のステップで対応
