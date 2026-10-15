# DR Lab: one-click start for the operator (the desktop shortcut "DR Lab" points to start-dr-lab.cmd).
# 1) TradingView Desktop with the debugging port 9222 (live candles), 2) the history base (built once),
# 3) the local server on 127.0.0.1:8767 (hidden, logs in lab/.runtime), 4) the page.
# Idempotent: whatever already runs is left as is. Everything stays on this computer.
# The root / opens the working screen, design 24 since 2026-10-01 night (the server redirects / to /24/); design 22 is at
# /22/. -Page 24/ opens design 24 directly (the shortcut "DR Lab 24", start-dr-lab-24.cmd).
param([switch]$NoBrowser, [switch]$HistoryOnly, [string]$Page = '')

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$lab = Join-Path $root 'lab'
$runtime = Join-Path $lab '.runtime'
$mcp = if ($env:TV_MCP_DIR) { $env:TV_MCP_DIR } else { Join-Path $env:USERPROFILE 'Claude\tradingview-mcp' }
$tvCli = Join-Path $mcp 'src\cli\index.js'

function Test-Url($url) {
    try { Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3 | Out-Null; return $true } catch { return $false }
}
function Fail($msg) { Write-Host "  [!] $msg" -ForegroundColor Red; Read-Host '  Enter — закрыть'; exit 1 }

# A Python that has numpy and pandas
$python = $null
foreach ($cand in @((Join-Path $env:LOCALAPPDATA 'Python\bin\python.exe'), 'python', 'py')) {
    try { & $cand -c "import numpy, pandas" 2>$null; if ($LASTEXITCODE -eq 0) { $python = $cand; break } } catch { }
}

Write-Host ''
Write-Host '  DR Lab' -ForegroundColor Cyan
Write-Host ''
if (-not $python) { Fail 'Не найден Python с numpy и pandas.' }

# 1. TradingView Desktop with the debugging port
if ($HistoryOnly) {
    Write-Host '  [ok] Исторический запуск без изменения TradingView'
} elseif (Test-Url 'http://127.0.0.1:9222/json/version') {
    Write-Host '  [ok] TradingView уже запущен с каналом для свечей'
} elseif (Get-Process TradingView -ErrorAction SilentlyContinue) {
    Write-Host '  [!] TradingView открыт без канала 9222; история доступна, окно не перезапускалось' -ForegroundColor Yellow
} elseif (-not (Test-Path $tvCli)) {
    Write-Host "  [!] Не найден tradingview-mcp ($mcp): живое окно работать не будет, история работает" -ForegroundColor Yellow
} else {
    Write-Host '  [..] Запускаю TradingView с каналом для свечей (открытый TradingView перезапустится)'
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

# 2. The history base (NQ, ES, YM 2006-2025), built once from the G3 market tape
$missing = @('nq', 'es', 'ym') | Where-Object { -not (Test-Path (Join-Path $runtime "market_$($_)_meta.json")) }
if ($missing) {
    Write-Host "  [..] Собираю историю ($($missing -join ', ')): около 30 секунд на инструмент"
    Push-Location $root
    & $python -B lab/build_market.py @($missing | ForEach-Object { $_.ToUpper() }) | Out-Null
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) { Fail 'История не собралась: нет ленты G3 (см. AGENTS.md, переменная DR_IDR_MARKET).' }
    Write-Host '  [ok] История собрана'
}
$missingBoxes = @('nq', 'es', 'ym') | Where-Object { -not (Test-Path (Join-Path $runtime "boxes_$($_).npz")) }
if ($missingBoxes) {
    Write-Host "  [..] Собираю базу сессий для экрана ($($missingBoxes -join ', ')): около 20 секунд на инструмент"
    Push-Location $root
    & $python -B lab/build_boxes.py @($missingBoxes | ForEach-Object { $_.ToUpper() }) | Out-Null
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) { Fail 'База сессий не собралась: нет ленты G3 (см. AGENTS.md, переменная DR_IDR_MARKET).' }
    Write-Host '  [ok] База сессий собрана'
}

# 3. The local server: an alive old process is not the current build.
$taskHealth = $null
try { $taskHealth = Invoke-RestMethod 'http://127.0.0.1:8767/api/health' -TimeoutSec 3 } catch {}
$taskExpectedRevision = & $python -B (Join-Path $lab 'runtime_identity.py')
if ($taskHealth -and $taskHealth.workspace -and [IO.Path]::GetFullPath($taskHealth.workspace) -ne [IO.Path]::GetFullPath($root)) { Fail 'Порт 8767 занят другой рабочей копией' }
if ($taskHealth -and ($taskHealth.source_revision -ne $taskExpectedRevision -or $taskHealth.data_revision -ne $taskHealth.current_data_revision -or -not $taskHealth.integration)) {
    $taskOwners = @(Get-NetTCPConnection -LocalPort 8767 -State Listen | Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($taskOwner in $taskOwners) {
        $taskProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $taskOwner"
        if ($taskProcess.CommandLine -notmatch 'server\.py') { Fail 'Неподтверждённый процесс на 8767' }
    }
    foreach ($taskOwner in $taskOwners) { Stop-Process -Id $taskOwner -ErrorAction Stop }
    $taskHealth = $null
}
if ($taskHealth) {
    Write-Host '  [ok] Сервер DR Lab уже работает'
} else {
    Write-Host '  [..] Запускаю сервер DR Lab'
    for ($taskWait = 0; $taskWait -lt 30; $taskWait++) {
        if (-not @(Get-NetTCPConnection -LocalPort 8767 -State Listen -ErrorAction SilentlyContinue).Count) { break }
        Start-Sleep -Milliseconds 100
    }
    if (@(Get-NetTCPConnection -LocalPort 8767 -State Listen -ErrorAction SilentlyContinue).Count) { Fail 'Порт 8767 занят, но сервер не ответил. Второй процесс не запущен.' }
    New-Item -ItemType Directory -Force -Path $runtime | Out-Null
    Start-Process -FilePath $python -ArgumentList '-B', 'server.py', '--integration' -WorkingDirectory $lab -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $runtime 'server.out.log') -RedirectStandardError (Join-Path $runtime 'server.err.log')
    $ok = $false
    for ($i = 0; $i -lt 60; $i++) { Start-Sleep -Seconds 1; if (Test-Url 'http://127.0.0.1:8767/api/health') { $ok = $true; break } }
    if (-not $ok) { Fail "Сервер не поднялся, журнал: $(Join-Path $runtime 'server.err.log')" }
    Write-Host '  [ok] Сервер запущен'
}

# 4. The page
if (-not $NoBrowser) { Start-Process ('http://127.0.0.1:8767/' + $Page) }
Write-Host ('  [ok] http://127.0.0.1:8767/' + $Page)
Write-Host ''
Start-Sleep -Seconds 2
