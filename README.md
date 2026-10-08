# Python 開発環境（Docker Compose + Dev Containers）

Docker Compose と VS Code Dev Containers で動く、Python の開発環境です。
コマンド1つで、Python（FastAPI）・PostgreSQL・メール確認がそろい、Claude API（生成 AI）を呼ぶサンプルも入っています。Windows（PowerShell）向けの操作コマンド `dev.ps1` 付き。

動作確認済み（2026-10-09）：Windows 11 + Docker Desktop で、環境チェック画面・API の説明ページ・Ruff・pytest・メール送信（Mailpit）・保存時の自動再読み込み。Claude API の要約は、キー未設定時の応答と、テスト用の偽クライアントでの組み立てを確認（実際の API 呼び出しは、キーを設定して各自で確認してください）。

| 画面 | URL | 用途 |
|---|---|---|
| アプリ | http://localhost:8000 | 環境チェック画面 |
| API の説明 | http://localhost:8000/docs | FastAPI が自動で作る API の説明と試し打ち |
| Mailpit | http://localhost:8027 | アプリが送ったメールを受け止めて表示（外部には送られない） |

## 入っているもの

- Python 3.13 ＋ uv（高速なパッケージ管理。仮想環境もコンテナ側に作る）
- FastAPI ＋ Uvicorn（保存すると自動で再読み込み）
- PostgreSQL 17（`psycopg`）、メール送信（`smtplib` → Mailpit）
- Claude API のサンプル：`POST /api/summarize` で文章を要約（モデル `claude-opus-5-5`、Anthropic 公式 SDK）
- 品質チェック：pytest（テスト）、Ruff（検査と整形）

## 初回だけの準備

1. Docker Desktop を起動する（初めての PC は、先に管理者の PowerShell で `wsl --install` と再起動が必要）
2. このフォルダで準備コマンドを実行する
   ```powershell
   cd py-dev-env
   .\dev.ps1 setup
   ```
   終わったら http://localhost:8000 を開いて、DB が「接続できました」になっていれば完了です。

## Claude API のサンプルを試す

1. `.env` の `ANTHROPIC_API_KEY=` に API キーを書く（`.env` は Git に入らない設定）
2. `.\dev.ps1 restart`
3. http://localhost:8000/docs の `POST /api/summarize` で「Try it out」→ 文章を入れて実行

キーが無いときは 503（未設定）を返します。安全上の理由で断られた場合は、サーバー側で自動的に別のモデルへ切り替える設定（fallbacks）を入れています。

## 普段の使い方

```powershell
.\dev.ps1 up              # 起動
.\dev.ps1 down            # 停止
.\dev.ps1 check           # Ruff の検査とテストをまとめて実行
.\dev.ps1 uv add pandas   # ライブラリを追加
.\dev.ps1 help            # コマンド一覧
```

## VS Code で開発する（おすすめ）

VS Code でこのフォルダを開き、「コンテナーで再度開く（Reopen in Container）」を選ぶと、コンテナの中で補完・Ruff・テストがそのまま使えます（拡張機能「Dev Containers」が必要）。

## お客さまのソースを扱うときの注意

- お客さまのソースや個人情報を AI（Claude など）に渡す前に、秘密保持契約で外部の AI サービスの利用が認められているかを確認する
- API キーは `.env` にだけ書き、ソースコードには書かない
- 納品前に、自分で画面を動かして確認し、確認の手順と結果を添える

## フォルダ構成

```
py-dev-env/
├─ compose.yaml          … どのサービスを起動するか
├─ env.example           … 設定の見本（setup で .env にコピーされる）
├─ dev.ps1               … 操作コマンド
├─ docker/python/        … Python のイメージ
├─ src/                  … アプリのソース（ここを案件ごとに入れ替える）
│  ├─ app/main.py        … 画面と API
│  ├─ app/ai.py          … Claude API の呼び出し
│  ├─ app/templates/     … 画面の HTML
│  ├─ tests/             … テスト
│  └─ pyproject.toml     … 依存ライブラリ（uv.lock で版を固定）
└─ .devcontainer/        … VS Code Dev Containers の設定
```
