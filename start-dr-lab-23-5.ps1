# DR Lab 23.5 — the successor candidate of screen 24 (operator 19.10.2026: keep 24 as it works; put the new semantic
# contour on a copy, «не 24, а 23.5», on its own port). The desktop shortcut «DR Lab 23.5» points to start-dr-lab-23-5.cmd.
# Screen 24 on 127.0.0.1:8767 (main) is never touched. This branch's own server runs on 127.0.0.1:8735 (hidden, logs in
# this working copy's lab/.runtime) with the candidate trials (--integration). The history files are copied once from
# the main working copy's lab/.runtime (git-ignored, never published). TradingView is started with the candle channel
# only when it is not running; an open TradingView is not restarted here (DR Lab 24's launcher does that). Idempotent.
param([switch]$NoBrowser, [switch]$HistoryOnly, [string]$Page = '')

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$lab = Join-Path $root 'lab'
$runtime = Join-Path $lab '.runtime'
$port = 8735
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
$sourceRoot = Split-Path ([IO.Path]::GetFullPath($common)) -Parent
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

# 2. TradingView (today's candles): started with the channel only when it is not running
if (-not $HistoryOnly) {
    $cdpReady = $false
    try { Invoke-RestMethod 'http://127.0.0.1:9222/json/version' -TimeoutSec 2 | Out-Null; $cdpReady = $true } catch {}
    if (-not $cdpReady) {
        $tvRoot = if ($env:TV_MCP_DIR) { $env:TV_MCP_DIR } else { Join-Path $env:USERPROFILE 'Claude\tradingview-mcp' }
        $tvCli = Join-Path $tvRoot 'src\cli\index.js'
        if (Get-Process TradingView -ErrorAction SilentlyContinue) {
            Write-Host '  [..] TradingView открыт без канала для свечей: свечи дня появятся после запуска «DR Lab 24»; история доступна'
        } elseif (Test-Path -LiteralPath $tvCli) {
            Write-Host '  [..] Запускаю TradingView с каналом для свечей'
            & node $tvCli launch
            for ($i = 0; $i -lt 60; $i++) {
                Start-Sleep -Milliseconds 500
                try { Invoke-RestMethod 'http://127.0.0.1:9222/json/version' -TimeoutSec 2 | Out-Null; break } catch {}
            }
        }
    }
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
Write-Host "  [ok] $base/"
if (-not $NoBrowser) { Start-Process ($base + '/' + $Page) }
