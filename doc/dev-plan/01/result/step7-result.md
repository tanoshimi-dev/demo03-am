# Step 7 Result: インシデントと棚卸し

## 実装内容

Step 7 として、`incidents` アプリと `inventory` アプリを追加し、故障・紛失・廃棄の記録、棚卸しセッション作成、実査結果入力、差異確認を実装しました。

### incidents

- `IncidentReport` モデルを追加
- `report_incident()` でインシデント記録と資産状態更新（故障 → `in_repair`、紛失 → `lost`、廃棄 → `retired`）を実装
- `resolve_incident()` で故障インシデントのみ解決可能にし、解決時は資産を `in_stock` に復帰
- 管理者向け一覧、報告画面、故障解決画面を追加
- 資産詳細画面から管理者がインシデント報告へ遷移可能にした

### inventory

- `InventorySession` / `InventoryResult` モデルを追加
- セッション開始、結果入力、セッション完了、差異抽出のサービスを実装
- 管理者向けセッション一覧、作成画面、詳細画面を追加
- セッション詳細で全資産の実査結果を入力でき、`in_stock` 資産の所在不明を差異として表示

### 既存機能との連携

- `incidents` / `inventory` を `INSTALLED_APPS` と URL ルートへ追加
- ホーム画面にインシデント一覧・棚卸し一覧へのリンクを追加
- 返却確認時、資産状態がすでに incident によって変更されている場合は `in_stock` に上書きしないよう調整
- インシデント制約・棚卸し差異判定・管理者ビューを担保する単体テストを追加

## 変更ファイル

### 新規作成

- `sys/app/incidents/__init__.py`
- `sys/app/incidents/apps.py`
- `sys/app/incidents/models.py`
- `sys/app/incidents/forms.py`
- `sys/app/incidents/services.py`
- `sys/app/incidents/views.py`
- `sys/app/incidents/urls.py`
- `sys/app/incidents/admin.py`
- `sys/app/incidents/migrations/__init__.py`
- `sys/app/incidents/migrations/0001_initial.py`
- `sys/app/incidents/tests/__init__.py`
- `sys/app/incidents/tests/test_models.py`
- `sys/app/incidents/tests/test_views.py`
- `sys/app/inventory/__init__.py`
- `sys/app/inventory/apps.py`
- `sys/app/inventory/models.py`
- `sys/app/inventory/forms.py`
- `sys/app/inventory/services.py`
- `sys/app/inventory/views.py`
- `sys/app/inventory/urls.py`
- `sys/app/inventory/admin.py`
- `sys/app/inventory/migrations/__init__.py`
- `sys/app/inventory/migrations/0001_initial.py`
- `sys/app/inventory/tests/__init__.py`
- `sys/app/inventory/tests/test_models.py`
- `sys/app/inventory/tests/test_views.py`
- `sys/app/templates/incidents/incident_list.html`
- `sys/app/templates/incidents/incident_report_form.html`
- `sys/app/templates/incidents/incident_resolve_form.html`
- `sys/app/templates/inventory/session_list.html`
- `sys/app/templates/inventory/session_create_form.html`
- `sys/app/templates/inventory/session_detail.html`
- `doc/dev-plan/01/result/step7-result.md`

### 更新

- `sys/app/config/settings.py`
- `sys/app/config/urls.py`
- `sys/app/loans/services.py`
- `sys/app/templates/home.html`
- `sys/app/templates/assets/asset_detail.html`
- `sys/app/static/styles/app.css`
- `doc/dev-plan/01/dev-plan.md`
- `README.md`

## Docker 検証コマンド

```sh
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py makemigrations incidents
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py makemigrations inventory
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py migrate
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py test
```

## 実際の検証結果

```text
Migrations for 'incidents':
  incidents/migrations/0001_initial.py
    + Create model IncidentReport
Migrations for 'inventory':
  inventory/migrations/0001_initial.py
    + Create model InventorySession
    + Create model InventoryResult

Applying incidents.0001_initial... OK
Applying inventory.0001_initial... OK

Found 92 test(s).
Ran 92 tests in 17.794s
OK
```

全 92 テスト合格。

## 残課題・フォローアップ

- Step 8 の監査ログ実装で、インシデント記録・解決と棚卸し結果入力も監査対象に含める
- デモ用シードデータで故障端末、紛失端末、棚卸し差異あり端末を追加すると実演しやすい
