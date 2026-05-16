# Step 8 Result: 監査ログとデモ仕上げ

## 実装内容

Step 8 として、`auditlogs` アプリ追加、主要操作の監査ログ記録、デモ用シードコマンド、最小 UI 調整、README / dev-plan 更新、監査ログ関連テスト補完を実施しました。

### 監査ログ

- `AuditLog` モデルと `log_action()` を追加
- 貸出申請、承認、却下、返却申請、返却確認、インシデント報告・解決、棚卸し結果記録・完了を同一トランザクション内で記録するよう既存 service に統合
- 管理者向け `/auditlogs/` 一覧画面、絞り込み、Admin 登録を追加

### デモシードデータ

- `python manage.py load_demo_seed` を追加
- カテゴリ 3 種、資産 8 件、`demo_employee` / `demo_admin`、貸出履歴、インシデント、棚卸しサンプルを投入可能にした
- 再実行してもエラーにならないことを確認した

### UI / ドキュメント

- 共通ナビゲーションに主要導線と監査ログへのリンクを追加
- ホーム画面に監査ログリンクと Step 8 相当の説明を追加
- `README.md` を Step 8 時点の内容へ更新し、監査ログ現状・デモシードデータを追記
- `doc/dev-plan/01/dev-plan.md` の Step 8 を Done に更新

### テスト補完

- `auditlogs` のサービス / ビュー単体テストを追加
- `loans` / `incidents` / `inventory` に監査ログ連携の単体テストを追加
- 合計 103 テストが成功

## 変更ファイル

### 新規作成

- `sys/app/auditlogs/__init__.py`
- `sys/app/auditlogs/apps.py`
- `sys/app/auditlogs/models.py`
- `sys/app/auditlogs/services.py`
- `sys/app/auditlogs/views.py`
- `sys/app/auditlogs/urls.py`
- `sys/app/auditlogs/admin.py`
- `sys/app/auditlogs/migrations/__init__.py`
- `sys/app/auditlogs/migrations/0001_initial.py`
- `sys/app/auditlogs/tests/__init__.py`
- `sys/app/auditlogs/tests/test_models.py`
- `sys/app/auditlogs/tests/test_views.py`
- `sys/app/templates/auditlogs/auditlog_list.html`
- `sys/app/assets/management/__init__.py`
- `sys/app/assets/management/commands/__init__.py`
- `sys/app/assets/management/commands/load_demo_seed.py`
- `doc/dev-plan/01/result/step8-result.md`

### 更新

- `README.md`
- `doc/dev-plan/01/dev-plan.md`
- `sys/app/config/settings.py`
- `sys/app/config/urls.py`
- `sys/app/loans/services.py`
- `sys/app/loans/views.py`
- `sys/app/loans/tests/test_models.py`
- `sys/app/incidents/services.py`
- `sys/app/incidents/tests/test_models.py`
- `sys/app/inventory/services.py`
- `sys/app/inventory/tests/test_models.py`
- `sys/app/templates/base.html`
- `sys/app/templates/home.html`
- `sys/app/static/styles/app.css`

## Docker 検証コマンド

```sh
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py makemigrations auditlogs
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py migrate
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py test
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py load_demo_seed
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py load_demo_seed
```

## 実際の検証結果

```text
Migrations for 'auditlogs':
  auditlogs/migrations/0001_initial.py
    + Create model AuditLog

Applying auditlogs.0001_initial... OK

Found 103 test(s).
Ran 103 tests in 19.868s
OK

カテゴリと資産の初期データを確認します。
デモユーザーを確認します。
貸出履歴データを確認します。
インシデントデータを確認します。
棚卸しデータを確認します。
デモシードデータの投入が完了しました。

カテゴリと資産の初期データを確認します。
デモユーザーを確認します。
貸出履歴データを確認します。
インシデントデータを確認します。
棚卸しデータを確認します。
デモシードデータの投入が完了しました。
```

全 103 テスト合格。シードコマンドは 2 回連続実行でも成功しました。

## 残課題・フォローアップ

- Step 9 でフロント側や追加スモーク観点を含むテスト整備を継続する
