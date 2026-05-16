# URL・ビュー一覧

## common

| URL | ビュー | 説明 | 認証 |
|-----|--------|------|------|
| / | TemplateView (`home.html`) | ホーム | 不要 |
| /admin/ | Django Admin | 管理画面 | Django Admin 認証 |

## accounts

| URL | ビュー | 説明 | 認証 |
|-----|--------|------|------|
| /auth/handover | `handover_view` | ポータル認証引継ぎ | 不要 |
| /auth/me | `me_view` | 認証状態確認 | 不要 |
| /auth/logout | `logout_view` | ログアウト | 不要 |

## assets

| URL | ビュー | 説明 | 認証 |
|-----|--------|------|------|
| /assets/ | `AssetListView` | 資産一覧 | 要認証 |
| /assets/<asset_code>/ | `AssetDetailView` | 資産詳細 | 要認証 |

## loans

| URL | ビュー | 説明 | 認証 |
|-----|--------|------|------|
| /loans/request/<asset_code>/ | `LoanRequestCreateView` | 貸出申請 | 要認証 |
| /loans/mine/ | `MyLoanListView` | 自分の申請一覧 | 要認証 |
| /loans/admin/ | `LoanRequestAdminListView` | 申請管理一覧 | 管理者 |
| /loans/admin/<pk>/approve/ | `LoanApproveView` | 申請承認 | 管理者 |
| /loans/admin/<pk>/reject/ | `LoanRejectView` | 申請却下 | 管理者 |
| /loans/mine/<pk>/return-request/ | `ReturnRequestView` | 返却申請 | 要認証 |
| /loans/admin/return-confirm/<pk>/ | `ReturnConfirmView` | 返却確認 | 管理者 |

## incidents

| URL | ビュー | 説明 | 認証 |
|-----|--------|------|------|
| /incidents/ | `IncidentListView` | インシデント一覧 | 管理者 |
| /incidents/report/<asset_code>/ | `IncidentReportCreateView` | インシデント報告 | 管理者 |
| /incidents/<pk>/resolve/ | `IncidentResolveView` | 故障解決 | 管理者 |

## inventory

| URL | ビュー | 説明 | 認証 |
|-----|--------|------|------|
| /inventory/ | `InventorySessionListView` | 棚卸し一覧 | 管理者 |
| /inventory/new/ | `InventorySessionCreateView` | セッション作成 | 管理者 |
| /inventory/<pk>/ | `InventorySessionDetailView` | セッション詳細 | 管理者 |
| /inventory/<pk>/close/ | `InventorySessionCloseView` | セッション完了 | 管理者 |
| /inventory/<session_pk>/record/<asset_code>/ | `InventoryResultInputView` | 実査結果入力 | 管理者 |

## auditlogs

| URL | ビュー | 説明 | 認証 |
|-----|--------|------|------|
| /auditlogs/ | `AuditLogListView` | 監査ログ一覧 | 管理者 |
