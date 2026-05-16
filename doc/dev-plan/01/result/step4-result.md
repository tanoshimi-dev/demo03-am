# Step 4 Result

## 実装内容

- `assets` アプリに資産一覧画面と資産詳細画面を追加した
- `/assets/` でキーワード、状態、カテゴリによる検索・絞り込みをできるようにした
- `/assets/<asset_code>/` で資産コード、カテゴリ、状態、シリアル番号、保管場所などの詳細を参照できるようにした
- 未認証時は `accounts` の handover へ戻す `PortalLoginRequiredMixin` を追加し、アプリ単独ログイン画面なしで資産参照導線を保護した
- `asset-admin` または `sysadmin` ロールでは管理者向け表示、それ以外では利用者向け表示を出し分けるようにした
- Step 4 の単体テストを追加し、一覧、詳細、検索、未認証リダイレクト、表示差分を確認できるようにした
- `README.md` と `doc\dev-plan\01\dev-plan.md` を更新し、Step 4 完了状態と資産参照導線の現状を反映した

## 変更ファイル

- `sys\app\accounts\mixins.py`
- `sys\app\assets\urls.py`
- `sys\app\assets\views.py`
- `sys\app\assets\tests\test_views.py`
- `sys\app\templates\assets\asset_list.html`
- `sys\app\templates\assets\asset_detail.html`
- `sys\app\config\urls.py`
- `sys\app\templates\home.html`
- `README.md`
- `doc\dev-plan\01\dev-plan.md`

## Docker で使った検証コマンド

1. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml run --rm --entrypoint python tdev-demo03-web manage.py test`
2. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml up -d --build`
3. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py check`
4. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py shell -c "...AssetCategory.objects.update_or_create(...); Asset.objects.update_or_create(...)" `
5. `curl -I http://localhost:18003/assets/`
6. `curl -L -c <cookie-file> -b <cookie-file> -H "X-Portal-Subject: portal-asset-admin" -H "X-Portal-Email: asset-admin@example.com" -H "X-Portal-Name: Asset Admin User" -H "X-Portal-Roles: asset-admin" "http://localhost:18003/auth/handover?returnTo=/assets/"`
7. `curl -b <cookie-file> "http://localhost:18003/assets/?q=ThinkPad&status=in_stock&category=laptop"`
8. `curl -b <cookie-file> "http://localhost:18003/assets/ASSET-001/"`
9. `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml down`

## 実際の検証結果

- `manage.py test` は 23 件のテストを成功させた
- `manage.py check` は成功し、設定エラーは出なかった
- 未認証状態の `GET /assets/` は `302` で handover 導線へリダイレクトした
- handover 後の `GET /assets/?q=ThinkPad&status=in_stock&category=laptop` で対象資産 `ThinkPad X1 Carbon` を表示できた
- handover 後の一覧画面では管理者ロール向けの表示を確認できた
- `GET /assets/ASSET-001/` で対象資産の詳細画面を表示できた

## 残課題 / フォローアップ

- 貸出申請ボタンや貸出中一覧などの業務導線は Step 5 以降で追加する
- 管理者向けの専用一覧や運用導線は、今後の承認・返却フロー実装に合わせて拡張する
