# デモ実演手順

## 事前準備

1. Docker Compose を起動する
2. シードデータを投入する: `docker compose --env-file sys\.env -f sys\infra\compose\docker-compose.yml exec -T tdev-demo03-web python manage.py load_demo_seed`
3. `AUTH_MODE=dev-header` の状態で handover を確認する
4. 必要に応じて `X-Portal-Subject` ヘッダーを付けて `/auth/handover?returnTo=/` を呼び出す

## デモアカウント

| ユーザー名 | パスワード | ロール | 用途 |
|---|---|---|---|
| demo_employee | demo1234 | なし | 社員（申請者） |
| demo_admin | demo1234 | asset-admin | 情シス担当者 |

## シナリオA: 正常系（貸出〜返却）

### 手順 1: 社員として貸出申請する（demo_employee）

1. `/auth/handover?returnTo=/assets/` へ `X-Portal-Subject: demo_employee` ヘッダー付きでアクセスする
2. `/assets/` で在庫状態の資産 `LAPTOP-001` を確認する
3. `/loans/request/LAPTOP-001/` で申請フォームを送信する
4. `/loans/mine/` で申請が「審査中」になっていることを確認する

### 手順 2: 管理者として承認する（demo_admin）

1. handover で `demo_admin` としてログインする
2. `/loans/admin/` で pending 申請を確認する
3. 承認ボタンを押し、`LAPTOP-001` が「貸出中」になることを確認する

### 手順 3: 返却申請〜返却確認

1. `demo_employee` に戻って `/loans/mine/` を開く
2. 承認済み申請の「返却申請」ボタンを押す
3. `demo_admin` として `/loans/admin/` から返却確認へ進む
4. 返却確認後、`LAPTOP-001` が「在庫」に戻ることを確認する

## シナリオB: 例外系

### 故障端末への貸出制限

1. `demo_employee` で `/loans/request/LAPTOP-003/` にアクセスする
2. 故障中のため申請不可メッセージが表示されることを確認する

### インシデント記録

1. `demo_admin` として `/incidents/report/PHONE-001/` へアクセスする
2. 種別「紛失」で報告する
3. `/incidents/` と `/assets/PHONE-001/` で `PHONE-001` が「紛失」状態になったことを確認する

### 棚卸し

1. `demo_admin` として `/inventory/new/` でセッションを作成する
2. 対象資産ごとに「確認済み」または「所在不明」を入力する
3. セッション詳細の差異一覧で所在不明資産を確認する
4. セッションを完了する

## 監査ログ確認

1. `demo_admin` として `/auditlogs/` を開く
2. 貸出申請、承認、返却確認、インシデント報告、棚卸し記録の履歴を確認する
