# Step 3 Result

## 実装内容

- `sys\app\assets` アプリを追加し、`AssetCategory` と `Asset` の中核モデルを実装した
- 資産状態を `in_stock` / `on_loan` / `in_repair` / `lost` / `retired` の choices で表現できるようにした
- 資産コードとシリアル番号に一意制約を設定し、カテゴリ、メーカー、型番、保管場所、取得日、メモなどの台帳管理情報を保持できるようにした
- Django Admin に `AssetCategoryAdmin` と `AssetAdmin` を追加し、カテゴリと資産台帳を管理画面から登録・更新できるようにした
- `README.md` に Step 3 の到達状態と、台帳初期データは後続で fixture または管理コマンドから投入する方針を追記した
- `doc\dev-plan\01\dev-plan.md` の Phase Status で Step 3 を `Done` に更新した
- 追加の単体テストとして `sys\app\assets\tests\test_models.py` を追加し、一意制約、貸出可否判定、Admin 登録を確認できるようにした

## 変更ファイル

- `sys\app\assets\__init__.py`
- `sys\app\assets\apps.py`
- `sys\app\assets\models.py`
- `sys\app\assets\admin.py`
- `sys\app\assets\migrations\__init__.py`
- `sys\app\assets\migrations\0001_initial.py`
- `sys\app\assets\tests\test_models.py`
- `sys\app\config\settings.py`
- `README.md`
- `doc\dev-plan\01\dev-plan.md`

## Docker で使った検証コマンド

1. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml run --rm --entrypoint python tdev-demo03-web manage.py makemigrations assets`
2. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml up -d --build`
3. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py check`
4. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py shell -c "...AssetCategory.objects.update_or_create(...); Asset.objects.update_or_create(...); site.is_registered(...)" `
5. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml run --rm --entrypoint python tdev-demo03-web manage.py test`
6. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml down`

## 実際の検証結果

- `manage.py check` は成功した
- `AssetCategory` と `Asset` の migration を生成できた
- Docker 上の Django shell でカテゴリ `laptop` と資産 `ASSET-001` を登録できた
- 登録した資産は `in_stock` 状態として扱え、`is_available_for_loan` が `True` を返した
- `AssetCategory` と `Asset` はどちらも Django Admin に登録済みであることを確認した
- `manage.py test` で資産モデルの一意制約、貸出可否判定、Admin 登録を含む単体テストが成功した

## 残課題 / フォローアップ

- 実際の初期データ投入処理そのものは後続ステップで fixture または管理コマンドとして追加する
- 利用者向けの資産一覧・詳細画面は Step 4 で実装する
- 貸出中や修理中への状態遷移ロジックは Step 5 以降で業務フローに接続する
