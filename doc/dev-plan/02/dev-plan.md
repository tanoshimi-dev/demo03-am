# dev-plan 02: デモ用ユーザー切替機能

## 概要

デモ実演時に、画面上のウィジェットからワンクリックでデモユーザーを切り替えられる機能を追加する。  
`AUTH_MODE=dev-header` の場合にのみ有効にし、本番環境（`portal` モード）では完全に非表示かつ無効にする。

---

## 背景・制約

- 認証は portal ハンドオーバー方式を維持する（`doc/spec-auth/prompt.md` 準拠）
- アプリ独自ログイン画面は作らない
- 認証ロジックはすべてサーバー側で完結させる（フロントに認証責務を持たせない）
- 既存の `handover_view` / `establish_account_session` を再利用する

---

## デモユーザー

`load_demo_seed` コマンドで作成される以下の2ユーザーを対象とする。

| 表示名 | portal_subject | ロール |
|---|---|---|
| Demo Employee | `portal-demo-employee` | なし（社員） |
| Demo Admin | `portal-demo-admin` | asset-admin（管理者） |

切替対象は `settings.DEMO_SWITCH_SUBJECTS`（リスト）で設定し、デフォルト値をこの2ユーザーに設定する。

---

## 実装ステップ

### Step 1: `demo_switch_view` の追加（accounts アプリ）

**ファイル**: `sys/app/accounts/views.py`、`sys/app/accounts/urls.py`

- `POST /auth/demo-switch` を新設
- ガード: `settings.AUTH_MODE != "dev-header"` のとき `403 Forbidden` を返す
- `portal_subject` を POST パラメータで受け取る
- `settings.DEMO_SWITCH_SUBJECTS` に含まれない subject は `400 Bad Request`
- `Account.objects.get(portal_subject=portal_subject)` で取得
  - 存在しない場合は `400`（シードデータ未投入を示すメッセージ付き）
- 既存セッションを `end_account_session` で終了
- `establish_account_session` → `login` → `sync_account_session` を実行
- `returnTo`（POST パラメータ）を `sanitize_return_to` で検証してリダイレクト

**URL**: `path("auth/demo-switch", views.demo_switch_view, name="demo_switch")`

---

### Step 2: コンテキストプロセッサの追加

**ファイル**: `sys/app/accounts/context_processors.py`（新規）

```python
def demo_context(request):
    # AUTH_MODE=dev-header のときのみデモ切替情報を提供する
    # 返り値に含めるもの:
    #   - auth_mode: settings.AUTH_MODE の値
    #   - demo_accounts: DEMO_SWITCH_SUBJECTS に対応する Account のリスト
    #                    (シードデータ未投入時は空リストにフォールバック)
    #   - current_account: request.account（None の場合あり）
```

**設定変更**: `sys/app/config/settings.py` の `TEMPLATES[0]["OPTIONS"]["context_processors"]` にプロセッサを追加

---

### Step 3: `DEMO_SWITCH_SUBJECTS` の設定追加

**ファイル**: `sys/app/config/settings.py`

```python
DEMO_SWITCH_SUBJECTS = get_list(
    "DEMO_SWITCH_SUBJECTS",
    ["portal-demo-employee", "portal-demo-admin"],
)
```

---

### Step 4: `base.html` への切替ウィジェット追加

**ファイル**: `sys/app/templates/base.html`

- `auth_mode == "dev-header"` の場合のみウィジェットを描画
- ウィジェット内容:
  - 現在のユーザー表示名（未ログイン時は「未ログイン」）
  - `demo_accounts` リストをループして切替ボタンを生成
  - 各ボタンは `<form method="post" action="{% url 'accounts:demo_switch' %}">` + CSRF トークン + `portal_subject` hidden フィールド + `returnTo` hidden フィールド（現在のパス）
  - 現在ログイン中のユーザーのボタンは `disabled`
- ヘッダーの右端に配置（既存ナビとの干渉を避ける）
- スタイルは既存の CSS クラスに合わせる（Bootstrap は使用していないため `.site-header` スタイルに倣う）

---

### Step 5: テストの追加

**ファイル**: `sys/app/accounts/tests/test_demo_switch.py`（新規）

| テストケース | 内容 |
|---|---|
| `test_switch_success_employee` | demo_employee に切替後、セッションが正しく設定される |
| `test_switch_success_admin` | demo_admin に切替後、ロールが反映される |
| `test_switch_returns_to` | returnTo 指定のパスにリダイレクトされる |
| `test_switch_blocked_in_portal_mode` | `AUTH_MODE=portal` のとき 403 |
| `test_switch_invalid_subject` | 許可リスト外の subject は 400 |
| `test_switch_seed_not_loaded` | Account が存在しない subject で 400 |
| `test_context_processor_dev_mode` | dev-header モードで demo_accounts が返る |
| `test_context_processor_portal_mode` | portal モードで demo_accounts が空リスト |

---

### Step 6: 検証・ドキュメント整備

- Docker Compose で `python manage.py test accounts` を実行し、全テスト通過を確認
- `doc/dev-plan/02/result/step1-result.md`（全ステップ完了後に作成）
- `doc/spec/demo-procedure.md` にデモ切替ウィジェットの操作説明を追記

---

## フェーズ進捗

| Step | 内容 | 状態 |
|---|---|---|
| 1 | demo_switch_view と URL | Not Started |
| 2 | コンテキストプロセッサ | Not Started |
| 3 | DEMO_SWITCH_SUBJECTS 設定 | Not Started |
| 4 | base.html ウィジェット | Not Started |
| 5 | テスト追加 | Not Started |
| 6 | 検証・ドキュメント | Not Started |

---

## ファイル変更一覧（予定）

| ファイル | 変更種別 |
|---|---|
| `sys/app/accounts/views.py` | 編集（`demo_switch_view` 追加） |
| `sys/app/accounts/urls.py` | 編集（URL パターン追加） |
| `sys/app/accounts/context_processors.py` | 新規 |
| `sys/app/accounts/tests/test_demo_switch.py` | 新規 |
| `sys/app/config/settings.py` | 編集（DEMO_SWITCH_SUBJECTS、コンテキストプロセッサ登録） |
| `sys/app/templates/base.html` | 編集（ウィジェット追加） |
| `doc/spec/demo-procedure.md` | 編集（切替操作の説明追記） |
| `doc/dev-plan/02/result/step1-result.md` | 新規（完了時） |
