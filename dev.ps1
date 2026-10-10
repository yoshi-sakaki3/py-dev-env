<#
  Python 開発環境の操作コマンド（PowerShell）
  使い方:  .\dev.ps1 <コマンド> [引数]
  一覧:    .\dev.ps1 help
#>
# 引数は param() で受けず、そのまま読む。
# param() を使うと、-c・-e・-v のようにハイフンで始まる指定を PowerShell がこのスクリプトあての指定と解釈して、
# エラーになったり、黙って消えたりするため（例：python -c ...、mvn -e ...）。
$Command = if ($args.Count -gt 0) { [string]$args[0] } else { 'help' }
$Rest = @(if ($args.Count -gt 1) { $args[1..($args.Count - 1)] })

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

function Invoke-Compose { docker compose @args; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } }

function Test-Docker {
    docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Docker が起動していません。Docker Desktop を起動してから、もう一度実行してください。' -ForegroundColor Yellow
        exit 1
    }
}

switch ($Command) {
    'setup' {
        if (-not (Test-Path .env)) { Copy-Item env.example .env; Write-Host '.env を作成しました。' }
        Test-Docker
        Invoke-Compose build
        Invoke-Compose run --rm --no-deps app uv sync
        Invoke-Compose up -d
        Write-Host ''
        Write-Host '準備ができました。' -ForegroundColor Green
        & $PSCommandPath urls
    }
    'up'      { Test-Docker; Invoke-Compose up -d; & $PSCommandPath urls }
    'down'    { Invoke-Compose down }
    'restart' { Invoke-Compose restart }
    'rebuild' { Test-Docker; Invoke-Compose build --no-cache; Invoke-Compose run --rm --no-deps app uv sync; Invoke-Compose up -d }
    'status'  { Invoke-Compose ps }
    'logs'    { Invoke-Compose logs -f --tail 100 @Rest }
    'sh'      { Invoke-Compose exec app bash }
    'uv'      { Invoke-Compose exec app uv @Rest }
    'python'  { Invoke-Compose exec app uv run python @Rest }
    'test'    { Invoke-Compose exec app uv run pytest @Rest }
    'lint'    { Invoke-Compose exec app uv run ruff check . ; Invoke-Compose exec app uv run ruff format --check . }
    'format'  { Invoke-Compose exec app uv run ruff check --fix . ; Invoke-Compose exec app uv run ruff format . }
    'check'   { & $PSCommandPath lint; & $PSCommandPath test }
    'db'      { Invoke-Compose exec db sh -c 'psql -U "$POSTGRES_USER" "$POSTGRES_DB"' }
    'urls' {
        Write-Host '  アプリ       http://localhost:8000'
        Write-Host '  API の説明   http://localhost:8000/docs'
        Write-Host '  Mailpit      http://localhost:8027'
        Write-Host '  DB           localhost:5434（ユーザー app / パスワード app）'
    }
    'clean' {
        $ans = Read-Host 'DB と仮想環境を含めて全部消します。よろしいですか？ (yes/no)'
        if ($ans -eq 'yes') { Invoke-Compose down -v --rmi local }
    }
    default {
        @'
使い方: .\dev.ps1 <コマンド>

  setup        初回の準備（.env 作成・ビルド・uv sync・起動）
  up / down    起動 / 停止
  restart      再起動（.env を変えたときも）
  rebuild      イメージを作り直して起動
  status       動いているサービスの一覧
  logs [名前]  ログを見る（例: .\dev.ps1 logs app）
  sh           アプリのコンテナの中に入る
  uv ...       uv コマンド（例: .\dev.ps1 uv add pandas）
  python ...   Python を実行（例: .\dev.ps1 python -c "print(1)"）
  test         テストを実行（pytest）
  lint         Ruff で検査（直さない）
  format       Ruff で自動修正・整形
  check        lint と test をまとめて実行
  db           PostgreSQL に接続
  urls         各画面の URL を表示
  clean        データごと全部消す（確認あり）
'@ | Write-Host
    }
}
