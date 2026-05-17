# portal 認証方式の比較と本番デプロイ前の対応事項

## 概要

VPS デプロイの準備中に、`demo03_am` の認証が **本番環境で動作しない**ことが判明した。  
このドキュメントでは、現状の問題、他デモとの比較、および必要な対応を記録する。

---

## 1. 現状の問題（本番 AUTH_MODE=portal で無限リダイレクトが発生する）

`accounts/services.py` の `resolve_portal_identity()` は、`AUTH_MODE=portal` のとき  
**HTTP ヘッダー** から以下の情報を読み取る。

| ヘッダー名 | 役割 |
|-----------|------|
| `X-Portal-Subject` / `X-Portal-User-Sub` | ユーザー識別子 |
| `X-Portal-Email` / `X-Portal-User-Email` | メールアドレス |
| `X-Portal-Name` / `X-Portal-User-Name` | 表示名 |
| `X-Portal-Verified` | `1` のときのみ認証済みと判定 |

VPS 上では**これらのヘッダーを注入する仕組みが存在しない**。  
結果として、本番で `/auth/handover` を呼ぶと以下の無限ループが発生する。

```
ユーザーが demo03-am.tanoshimi.dev にアクセス
  → Django: X-Portal-Verified ヘッダーなし → None を返す
  → PORTAL_LOGIN_URL (tanoshimi.dev/login) へリダイレクト
  → ポータル: 認証済み → returnTo (handover) へリダイレクト
  → Django: 再び X-Portal-Verified なし → 同じ処理を繰り返す ♻️
```

---

## 2. 他デモとの認証方式比較

| プロジェクト | 言語 | 本番認証方式 | portal_token の扱い |
|---|---|---|---|
| `demo01_crm` | Node.js (Express) | バックエンドが `portal_token` cookie を読み JWT 検証 | JWKS エンドポイントで自力検証 |
| `demo02_ferms` | Node.js (NestJS) | バックエンドが `portal_token` cookie を読み JWT 検証 | JWKS エンドポイントで自力検証 |
| `demo03_am` | Python (Django) | `X-Portal-*` ヘッダーを受け取ることを期待（**ヘッダー注入元が存在しない**） | settings に定義済みだが**コードで未使用** |

### ポータル構成（VPS）

- 認証基盤: Keycloak (`auth.tanoshimi.dev`)
- ポータル API: Spring Boot (`api.tanoshimi.dev`)
  - JWKS: `https://api.tanoshimi.dev/v1/.well-known/jwks.json`
  - セッション確認: `https://api.tanoshimi.dev/api/auth/get-session`
- **Traefik ForwardAuth ミドルウェアは設定されていない**

---

## 3. 必要な対応

### 対応方針: Django 側で portal_token を直接検証する

demo01/demo02 と同じアプローチで、Django バックエンドが `portal_token` cookie を読み取り、JWKS エンドポイントに対して JWT 検証を行うよう `accounts/services.py` を修正する。

ヘッダーベースの方式は `AUTH_MODE=dev-header` のみに限定し、`AUTH_MODE=portal` では cookie + JWT 検証に切り替える。

### 変更対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `sys/requirements.txt` | `PyJWT[crypto]` を追加（JWT デコード + JWKS 検証） |
| `sys/app/accounts/services.py` | `resolve_portal_identity()` に `portal` モード用の cookie 読み取り・JWT 検証パスを追加 |
| `sys/app/config/settings.py` | `PORTAL_JWKS_URL`、`PORTAL_COOKIE_NAMES` が既存定義済み（変更不要） |

### 実装の流れ（portal モード）

```
1. PORTAL_COOKIE_NAMES に定義された名前でリクエストから cookie を取得
2. JWT のヘッダーから kid (Key ID) を取得
3. PORTAL_JWKS_URL から公開鍵セット（JWKS）を取得（キャッシュ推奨）
4. 対応する公開鍵で JWT を検証（署名・有効期限・issuer）
5. ペイロードからsubject・email・name・roles を取得
6. PortalIdentity を構築して返す
```

### 環境変数（docker-compose.prod.yml に定義済み、変更不要）

```
PORTAL_COOKIE_NAMES=portal_token,authjs.session-token,...
PORTAL_ISSUER=https://tanoshimi.dev
PORTAL_JWKS_URL=https://api.tanoshimi.dev/v1/.well-known/jwks.json
```

---

## 4. 影響範囲

- `AUTH_MODE=dev-header` の動作は変更しない（ローカル開発に影響なし）
- `AUTH_MODE=portal` のパスのみ変更する
- `handover_view`、`PortalSessionMiddleware`、`demo_switch_view` は変更不要
- 既存テスト（`test_auth.py`）は `dev-header` モードで書かれているため、`portal` モード用テストを追加する

---

## 5. このドキュメントの位置づけ

この対応は VPS デプロイ（`dev-plan.md`）の **Step 3 の前提条件** となる。  
実装完了後、`dev-plan.md` の Step 1 ステータスを更新し、実装結果を `result/step1-auth-fix-result.md` に記録する。

### dev-plan 更新案

| Step | タイトル | Status |
|------|----------|--------|
| Step 1 | 本番用 Docker Compose を整える | Done ✅ |
| **Step 1.5** | **portal_token JWT 検証を実装する（デプロイ前提条件）** | **Not Started** |
| Step 2 | 本番用環境変数テンプレートを作る | Not Started |
| Step 3 | VPS にデプロイする | Not Started |
| Step 4 | 動作確認とデプロイ後チェック | Not Started |
