# Step 5 実装結果

## 実装内容

`loans` アプリを新規作成し、貸出申請フローの前半（申請作成・一覧参照）を実装した。

### 追加したモデル

| モデル | 役割 |
|---|---|
| `LoanRequest` | 貸出申請。ステータス: 審査中 / 承認済み / 却下 / キャンセル |
| `LoanRecord` | 貸出確定後の記録（Step 6 で使用）|
| `ReturnRecord` | 返却記録（Step 6 で使用）|

### 追加したビュー・URL

| URL | ビュー | 説明 |
|---|---|---|
| `/loans/request/<asset_code>/` | `LoanRequestCreateView` | 貸出申請フォーム（認証済みユーザー向け）|
| `/loans/mine/` | `MyLoanListView` | 自分の貸出申請一覧 |
| `/loans/admin/` | `LoanRequestAdminListView` | 管理者向け申請一覧（`asset-admin` / `sysadmin` ロール限定）|

### 貸出可否の業務ルール（サーバー側判定）

`loans/services.py` に `check_loan_eligibility()` を実装。

- 資産の状態が `in_stock` でなければ申請を弾く
- 申請者が同一資産に `pending` または `approved` の申請を持つ場合も弾く

### 資産詳細・一覧テンプレートの更新

- `asset_detail.html`: 在庫状態の資産に「貸出申請する」ボタンを追加
- `asset_list.html`: 利用者向けセクションに自分の申請一覧リンクを追加

---

## 変更ファイル

### 新規作成

```
sys/app/loans/__init__.py
sys/app/loans/apps.py
sys/app/loans/models.py
sys/app/loans/forms.py
sys/app/loans/services.py
sys/app/loans/views.py
sys/app/loans/urls.py
sys/app/loans/admin.py
sys/app/loans/migrations/__init__.py
sys/app/loans/migrations/0001_initial.py  (makemigrations で自動生成)
sys/app/loans/tests/__init__.py
sys/app/loans/tests/test_models.py
sys/app/loans/tests/test_views.py
sys/app/templates/loans/loan_request_form.html
sys/app/templates/loans/my_loan_list.html
sys/app/templates/loans/loan_request_admin_list.html
```

### 更新

```
sys/app/config/settings.py        - INSTALLED_APPS に loans を追加
sys/app/config/urls.py             - loans.urls を include
sys/app/templates/assets/asset_detail.html  - 貸出申請ボタン追加
sys/app/templates/assets/asset_list.html    - 申請一覧リンク追加
doc/dev-plan/01/dev-plan.md        - Step 5 を Done に更新
```

---

## Docker による検証

### マイグレーション

```
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py makemigrations loans
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py migrate
```

結果: `loans.0001_initial` が正常に適用された。

### テスト実行

```
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py test
```

結果:

```
Found 46 test(s).
Ran 46 tests in 4.609s
OK
```

loans アプリの 23 テストを含む全 46 テストがパス。

---

## テスト内容

### `loans/tests/test_models.py` (9 テスト)

- `LoanRequest.__str__` の表現確認
- `is_active` プロパティの動作確認（pending/approved → True、それ以外 → False）
- デフォルトステータスが `pending` であること
- 貸出不可資産への申請が `LoanEligibilityError` を発生させること
- 未処理申請が存在する場合に重複申請を弾くこと
- キャンセル済み申請後の再申請が許可されること
- `create_loan_request` の正常系・異常系

### `loans/tests/test_views.py` (14 テスト)

- 未認証アクセスの `/auth/handover` へのリダイレクト
- 申請フォームの表示（在庫あり・在庫なし）
- 申請 POST の正常系（作成 + my_list へリダイレクト）
- 申請 POST の異常系（貸出不可、重複申請、返却日チェック）
- 自分の申請一覧（自分の申請のみ表示・空状態表示）
- 管理者向け申請一覧（一般ユーザーは my_list へリダイレクト・asset-admin/sysadmin はアクセス可・状態絞り込み）

---

## 残課題・後続ステップ

- Step 6 で `LoanRecord` と `ReturnRecord` を使った承認・返却フローを実装する
- 承認 View と返却 View は Step 6 で追加する
- 管理者向け申請一覧の「承認・却下」ボタンは Step 6 で追加する
