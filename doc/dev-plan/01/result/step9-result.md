# Step 9 Result: テストとドキュメントの整備

## 実装内容

Step 9 として、既存機能に対する単体テストの補完、テンプレート内容を含む画面テストの追加、URL / View 一覧とデモ実演手順の新規作成、README / dev-plan 更新、coverage によるカバレッジ確認を実施しました。

### 追加したテスト

- `inventory.tests.test_views.InventoryViewTests.test_admin_can_view_session_list`
- `incidents.tests.test_views.IncidentViewTests.test_admin_can_filter_incident_list_by_type`
- `incidents.tests.test_views.IncidentViewTests.test_admin_resolve_get_renders_form`
- `assets.tests.test_views.AssetViewTests.test_asset_detail_shows_incident_report_link_for_admin`
- `auditlogs.tests.test_models.AuditLogServiceTests.test_audit_log_str_representation`
- `accounts.tests.test_foundation.ProjectFoundationTests.test_home_page_shows_key_links`
- `loans.tests.test_views.MyLoanListViewTests.test_my_loan_list_shows_pending_status_label`
- `loans.tests.test_models.ReturnServiceTests.test_confirm_return_with_no_return_requested_still_works`
- `incidents.tests.test_models.IncidentServiceTests.test_report_breakdown_on_on_loan_asset_succeeds`
- `inventory.tests.test_models.InventoryServiceTests.test_close_already_closed_session_raises_error`

### テスト件数

- 変更前: 103 tests
- 変更後: 113 tests

### ドキュメント整備

- `doc/spec/url-view-list.md` を追加し、全ルートの URL / View / 認証要件を一覧化
- `doc/spec/demo-procedure.md` を追加し、正常系・例外系の実演手順を整理
- `README.md` を Step 9 完了時点の内容へ更新し、関連ドキュメントへの導線を追加
- `doc/dev-plan/01/dev-plan.md` の Step 9 を Done に更新

## 変更ファイル

### 新規作成

- `doc/spec/url-view-list.md`
- `doc/spec/demo-procedure.md`
- `doc/dev-plan/01/result/step9-result.md`

### 更新

- `README.md`
- `doc/dev-plan/01/dev-plan.md`
- `sys/requirements.txt`
- `sys/app/accounts/tests/test_foundation.py`
- `sys/app/assets/tests/test_views.py`
- `sys/app/auditlogs/tests/test_models.py`
- `sys/app/incidents/tests/test_models.py`
- `sys/app/incidents/tests/test_views.py`
- `sys/app/inventory/tests/test_models.py`
- `sys/app/inventory/tests/test_views.py`
- `sys/app/loans/tests/test_models.py`
- `sys/app/loans/tests/test_views.py`

## Docker コマンド（検証で使用）

```sh
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml up -d --build tdev-demo03-web
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python -m coverage --version
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py test
docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web sh -c "python -m coverage run manage.py test && python -m coverage report --omit='*/migrations/*,*/tests/*,manage.py'"
```

## 実際の検証結果

### coverage 利用可否

```text
Coverage.py, version 7.14.0 with C extension
Full documentation is at https://coverage.readthedocs.io/en/7.14.0
```

### テスト結果

```text
Found 113 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.................................................................................................................
----------------------------------------------------------------------
Ran 113 tests in 22.692s
OK
Destroying test database for alias 'default'...
```

### カバレッジ結果

```text
Found 113 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.................................................................................................................
----------------------------------------------------------------------
Ran 113 tests in 22.479s
OK
Destroying test database for alias 'default'...
Name                                     Stmts   Miss  Cover
------------------------------------------------------------
accounts/__init__.py                         0      0   100%
accounts/admin.py                           17      0   100%
accounts/apps.py                             4      0   100%
accounts/middleware.py                      21      2    90%
accounts/mixins.py                           9      0   100%
accounts/models.py                          43      2    95%
accounts/services.py                       126     25    80%
accounts/urls.py                             4      0   100%
accounts/views.py                           42      2    95%
assets/__init__.py                           0      0   100%
assets/admin.py                             15      0   100%
assets/apps.py                               4      0   100%
assets/management/__init__.py                0      0   100%
assets/management/commands/__init__.py       0      0   100%
assets/models.py                            43      1    98%
assets/urls.py                               4      0   100%
assets/views.py                             48      1    98%
auditlogs/__init__.py                        0      0   100%
auditlogs/admin.py                           9      0   100%
auditlogs/apps.py                            4      0   100%
auditlogs/models.py                         26      0   100%
auditlogs/services.py                        3      0   100%
auditlogs/urls.py                            4      0   100%
auditlogs/views.py                          39      1    97%
config/__init__.py                           0      0   100%
config/env.py                               24      2    92%
config/settings.py                          32      0   100%
config/urls.py                               4      0   100%
incidents/__init__.py                        0      0   100%
incidents/admin.py                          10      0   100%
incidents/apps.py                            4      0   100%
incidents/forms.py                          10      0   100%
incidents/models.py                         28      0   100%
incidents/services.py                       39      2    95%
incidents/urls.py                            4      0   100%
incidents/views.py                          96     18    81%
inventory/__init__.py                        0      0   100%
inventory/admin.py                          17      0   100%
inventory/apps.py                            4      0   100%
inventory/forms.py                          14      0   100%
inventory/models.py                         35      0   100%
inventory/services.py                       32      1    97%
inventory/urls.py                            4      0   100%
inventory/views.py                          80      9    89%
loans/__init__.py                            0      0   100%
loans/admin.py                              20      0   100%
loans/apps.py                                4      0   100%
loans/forms.py                              15      0   100%
loans/models.py                             57      0   100%
loans/services.py                           70      1    99%
loans/urls.py                                4      0   100%
loans/views.py                             106     10    91%
------------------------------------------------------------
TOTAL                                     1178     77    93%
```

- 主要アプリコードで 70% 未満のファイルはありませんでした
- 参考として、相対的に低めなのは `incidents/views.py` の 81% です

## 残課題・フォローアップ

- 現時点の coverage では 70% 未満の主要ファイルはなし
- さらに厚くする場合は `accounts/services.py` と `incidents/views.py` の分岐追加テストが候補
