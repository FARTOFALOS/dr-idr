# DR Lab 23.5 — the successor candidate of screen 24 (operator 19.10.2026: keep 24 as it works; put the new semantic
# contour on a copy, «не 24, а 23.5», on its own port). The desktop shortcut «DR Lab 23.5» points to start-dr-lab-23-5.cmd.
# Screen 24 on 127.0.0.1:8767 (main) is never touched. This branch's own server runs on 127.0.0.1:8735 (hidden, logs in
# this working copy's lab/.runtime) with the candidate trials (--integration). The history files are copied once from
# the main working copy's lab/.runtime (git-ignored, never published). TradingView as in DR Lab 24's launcher (the
# operator's rule of 19.10, AGENTS.md): one opened without the candle channel (port 9222) is restarted with it, the window
# opens again; -HistoryOnly never touches it. Idempotent.
param([switch]$NoBrowser, [switch]$HistoryOnly, [string]$Page = '23-5/', [ValidateRange(1024,65535)][int]$Port = 8735)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$lab = Join-Path $root 'lab'
$runtime = Join-Path $lab '.runtime'
$base = "http://127.0.0.1:$port"

function Fail($msg) { Write-Host "  [!] $msg" -ForegroundColor Red; if (-not $NoBrowser) { Read-Host '  Enter — закрыть' }; exit 1 }

Write-Host ''
Write-Host '  DR Lab 23.5 · кандидат на смену экрана 24 (экран 24 не меняется)' -ForegroundColor Cyan
Write-Host ''

$python = Join-Path $env:LOCALAPPDATA 'Python\bin\python.exe'
if (-not (Test-Path -LiteralPath $python)) { Fail 'Не найден Python DR Lab' }
$env:PYTHONUTF8 = '1'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null

# 1. The history base: a copy of the main working copy's files (built from the G3 tape; never published)
$common = & git -C $root rev-parse --git-common-dir
$commonPath = if ([IO.Path]::IsPathRooted($common)) { $common } else { Join-Path $root $common }
$sourceRoot = Split-Path ([IO.Path]::GetFullPath($commonPath)) -Parent
foreach ($inst in @('nq', 'es', 'ym')) {
    foreach ($file in @("boxes_$inst.npz", "boxes_$($inst)_meta.json", "market_$inst.npz", "market_$($inst)_meta.json")) {
        $target = Join-Path $runtime $file
        if (-not (Test-Path -LiteralPath $target)) {
            $source = Join-Path (Join-Path $sourceRoot 'lab\.runtime') $file
            if (-not (Test-Path -LiteralPath $source)) { Fail "Нет локальной истории: $file (сначала запустите DR Lab 24)" }
            Copy-Item -LiteralPath $source -Destination $target
        }
    }
}
# the walk-forward passport of «Сейчас» (lab/now24_validate.py): without it 23.5 said «проверка на истории не прогнана»
# where 24 says «путь не добавил к базе по времени»; kept current with the main working copy's
$validation = Join-Path (Join-Path $sourceRoot 'lab\.runtime') 'now24_validation.json'
if (Test-Path -LiteralPath $validation) {
    $targetValidation = Join-Path $runtime 'now24_validation.json'
    if ([IO.Path]::GetFullPath($validation) -ne [IO.Path]::GetFullPath($targetValidation)) { Copy-Item -LiteralPath $validation -Destination $targetValidation -Force }
}
else { Write-Host '  [!] Нет проверки «Сейчас» на истории (now24_validation.json): строка проверки будет «не прогнана»' -ForegroundColor Yellow }

# 2. TradingView Desktop with the candle channel (port 9222), the same step as DR Lab 24's launcher: without the port
#    the screen has no live candles, so a TradingView opened without it is restarted with it
$tvRoot = if ($env:TV_MCP_DIR) { $env:TV_MCP_DIR } else { Join-Path $env:USERPROFILE 'Claude\tradingview-mcp' }
$tvCli = Join-Path $tvRoot 'src\cli\index.js'
$cdpReady = $false
try { Invoke-RestMethod 'http://127.0.0.1:9222/json/version' -TimeoutSec 2 | Out-Null; $cdpReady = $true } catch {}
if ($HistoryOnly) {
    Write-Host '  [ok] Исторический запуск без изменения TradingView'
} elseif ($cdpReady) {
    Write-Host '  [ok] TradingView уже запущен с каналом для свечей'
} elseif (-not (Test-Path -LiteralPath $tvCli)) {
    Write-Host "  [!] Не найден tradingview-mcp ($tvRoot): живое окно работать не будет, история работает" -ForegroundColor Yellow
} else {
    if (Get-Process TradingView -ErrorAction SilentlyContinue) {
        Write-Host '  [..] TradingView открыт без канала для свечей: перезапускаю его с каналом (окно откроется заново)'
    } else {
        Write-Host '  [..] Запускаю TradingView с каналом для свечей'
    }
    & node $tvCli launch | Out-Null
    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 1
        try {
            $pages = Invoke-RestMethod -Uri 'http://127.0.0.1:9222/json/list' -TimeoutSec 3
            if ($pages | Where-Object { $_.url -like '*tradingview.com/chart*' }) { $ready = $true; break }
        } catch { }
    }
    if ($ready) { Write-Host '  [ok] TradingView запущен' } else { Write-Host '  [!] TradingView не ответил за минуту: живое окно покажет ошибку, история работает' -ForegroundColor Yellow }
}

# 3. This branch's server on its own port: an alive old process of this working copy is not the current build
$health = $null
try { $health = Invoke-RestMethod "$base/api/health" -TimeoutSec 3 } catch {}
if ($health -and (-not $health.workspace -or [IO.Path]::GetFullPath($health.workspace) -ne [IO.Path]::GetFullPath($root))) {
    Fail "Порт $port занят другой рабочей копией; ничего не изменено"
}
$expected = & $python -B (Join-Path $lab 'runtime_identity.py')
if ($health -and ($health.source_revision -ne $expected -or $health.data_revision -ne $health.current_data_revision -or -not $health.integration)) {
    foreach ($owner in @(Get-NetTCPConnection -LocalPort $port -State Listen | Select-Object -ExpandProperty OwningProcess -Unique)) {
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $owner"
        if ($proc.CommandLine -notmatch 'server\.py') { Fail "Неподтверждённый процесс на $port" }
        Stop-Process -Id $owner -ErrorAction Stop
    }
    $health = $null
}
if ($health) {
    Write-Host '  [ok] Сервер 23.5 уже работает'
} else {
    for ($i = 0; $i -lt 30; $i++) {
        if (-not @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue).Count) { break }
        Start-Sleep -Milliseconds 100
    }
    if (@(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue).Count) { Fail "Порт $port занят, но сервер не ответил" }
    Write-Host '  [..] Запускаю сервер 23.5'
    Start-Process -FilePath $python -ArgumentList '-u', '-B', 'server.py', '--port', "$port", '--integration' -WorkingDirectory $lab -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $runtime "server$port.out.log") -RedirectStandardError (Join-Path $runtime "server$port.err.log")
    for ($i = 0; $i -lt 120; $i++) {
        Start-Sleep -Milliseconds 500
        try { $health = Invoke-RestMethod "$base/api/health" -TimeoutSec 2; if ($health.integration) { break } } catch {}
    }
    if (-not $health -or -not $health.integration) { Fail "Сервер 23.5 не запустился; журнал $runtime\server$port.err.log" }
    Write-Host '  [ok] Сервер 23.5 запущен'
}
Write-Host "  [ok] $base/$Page"
if (-not $NoBrowser) { Start-Process ($base + '/' + $Page) }
