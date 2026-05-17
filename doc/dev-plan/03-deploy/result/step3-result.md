# Step 3 結果: VPS デプロイ

## 実施日

2026-05-17

---

## 実施内容

VPS（`hannari-dev-server`）に `demo03_am` をデプロイし、`https://demo03-am.tanoshimi.dev/` を公開した。

---

## デプロイ手順（実際に行った作業）

### 1. VPS へのファイル配置（SFTP アップロード）

ローカルの `sys/` ディレクトリをそのまま SFTP で以下へアップロード:

```
/home/mitakik25/traefik/tanoshimi.dev.demo03-am/sys/
```

VPS 上の最終的なディレクトリ構成:

```
tanoshimi.dev.demo03-am/
└── sys/
    ├── .env                            ← 実値入り（手動作成・gitignore対象）
    ├── .env.production.example
    ├── requirements.txt
    ├── app/
    └── infra/
        ├── compose/
        │   └── docker-compose.prod.yml ← 手動配置（gitignore対象）
        └── docker/
            └── web/
                └── Dockerfile
```

### 2. コンテナ起動

```sh
cd ~/traefik/tanoshimi.dev.demo03-am
docker compose --env-file sys/.env -f sys/infra/compose/docker-compose.prod.yml up --build -d
```

### 3. デモシード投入（Step 4 で実施予定）

```sh
docker compose --env-file sys/.env -f sys/infra/compose/docker-compose.prod.yml exec tdev-demo03-web python manage.py load_demo_seed
```

---

## トラブルシューティング記録

### 問題 1: ビルドエラー `lstat /home/mitakik25/traefik/sys: no such file or directory`

**原因:** 最初のアップロード時、`sys/` の中身を直接 VPS ルートに置いてしまった。`sys/` ラッパーなしの構造になっていた。  
**解決:** `sys/` ディレクトリごとアップロードし直した。

### 問題 2: 404 page not found（Traefik がルーターを認識しない）

**原因:** `docker-compose.prod.yml` に `name:` が未設定の古いファイルが VPS に置かれていた。  
`sys/infra/compose/` ディレクトリから実行するとプロジェクト名が `compose` になり、
内部ネットワークが `compose_tdev-demo03-network` となって Traefik がコンテナを認識できなかった。  
**解決:** `docker-compose.prod.yml` の先頭に `name: tanoshimidevdemo03am` を追加し、VPS に再アップロード。

### 問題 3: コンテナが `unhealthy` のまま → Traefik がルーティングしない

**原因:** ヘルスチェックが `curl http://localhost:8000/` だったため、`Host` ヘッダなしでリクエストが届き、
Django の ALLOWED_HOSTS チェックで 400 が返っていた。  
**解決:** ヘルスチェックを以下に修正:

```yaml
healthcheck:
  test: ['CMD-SHELL', 'curl --fail -H "Host: demo03-am.tanoshimi.dev" http://localhost:8000/ || exit 1']
```

---

## 検証結果

### コンテナ状態

```
NAMES                                    STATUS
tanoshimidevdemo03am-tdev-demo03-web-1   Up (healthy)
tanoshimidevdemo03am-tdev-demo03-db-1    Up (healthy)
```

### ネットワーク確認

```
tanoshimidevdemo03am_tdev-demo03-network
traefik-network
```

### 疎通確認

```
$ curl -I https://demo03-am.tanoshimi.dev/
HTTP/2 200
content-type: text/html; charset=utf-8
server: cloudflare
x-frame-options: DENY
x-content-type-options: nosniff
```

---

## 変更ファイル

| ファイル | 変更内容 |
|---|---|
| `sys/infra/compose/docker-compose.prod.yml` | `name: tanoshimidevdemo03am` 追加、ヘルスチェック修正（Host ヘッダ付き） |
| `doc/dev-plan/03-deploy/vps-directory-structure.md` | SFTP デプロイ方式・正しいディレクトリ構成に全面改訂 |

---

## 残課題

- Step 4: 認証フロー（portal JWT 検証）の動作確認
- Step 4: デモシード投入
- Step 4: 主要機能（資産一覧・貸出申請・返却）の確認
