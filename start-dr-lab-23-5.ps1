# DR Lab 23.5 — the successor candidate of screen 24 (operator 19.10.2026: keep 24 as it works; put the new semantic
# contour on a copy, «не 24, а 23.5», on its own port). The desktop shortcut «DR Lab 23.5» points to start-dr-lab-23-5.cmd.
# Screen 24 on 127.0.0.1:8767 (main) is never touched. This branch's own server runs on 127.0.0.1:8735 (hidden, logs in
# this working copy's lab/.runtime) with the candidate trials (--integration). The history files are copied once from
# the main working copy's lab/.runtime (git-ignored, never published). The 23.5 shortcut may restart TradingView
# Desktop once if the candle channel is missing (operator 2026-11-10). -HistoryOnly never touches it. Idempotent.
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

# 2. TradingView Desktop with the candle channel (port 9222). Only the 23.5 launcher may restart the app.
$tvRoot = if ($env:TV_MCP_DIR) { $env:TV_MCP_DIR } else { Join-Path $env:USERPROFILE 'Claude\tradingview-mcp' }
$tvCli = Join-Path $tvRoot 'src\cli\index.js'

function Start-CandleChannel {
    $cdp = $null
    try { $cdp = Invoke-RestMethod 'http://127.0.0.1:9222/json/version' -TimeoutSec 2 } catch {}
    if ($cdp) {
        if ($cdp.'User-Agent' -match '\bTVDesktop/') {
            Write-Host '  [ok] TradingView уже запущен с каналом для свечей'
        } else {
            Write-Host '  [!] Канал 9222 занят другим приложением. Живые свечи TradingView пока недоступны.' -ForegroundColor Yellow
        }
        return
    }
    if (-not (Test-Path -LiteralPath $tvCli)) {
        Write-Host "  [!] Не найден tradingview-mcp ($tvRoot): живое окно работать не будет, история работает" -ForegroundColor Yellow
        return
    }

    # Use the registered Store executable for both operations so the app keeps its signed-in profile.
    $tvPackage = Get-AppxPackage -Name TradingView.Desktop -ErrorAction SilentlyContinue | Select-Object -First 1
    $tvExe = if ($tvPackage) { Join-Path $tvPackage.InstallLocation 'TradingView.exe' }
    $running = @(Get-Process -Name TradingView -ErrorAction SilentlyContinue)
    if ($running.Count) {
        if (-not $tvExe -or @($running | Where-Object Path -ne $tvExe).Count) {
            Write-Host '  [!] Не удалось сопоставить открытый TradingView с установленным приложением. Живые свечи пока недоступны.' -ForegroundColor Yellow
            return
        }
        Write-Host '  [..] TradingView открыт без канала. Штатно перезапускаю приложение.'
        # This is the installed app's own taskbar Exit command, routed to the existing instance.
        Start-Process -FilePath $tvExe -ArgumentList '--exit' -WindowStyle Hidden
        for ($i = 0; $i -lt 60; $i++) {
            if (-not (Get-Process -Name TradingView -ErrorAction SilentlyContinue)) { break }
            Start-Sleep -Milliseconds 250
        }
        if (Get-Process -Name TradingView -ErrorAction SilentlyContinue) {
            Write-Host '  [!] TradingView не завершил штатный выход. Живые свечи пока недоступны.' -ForegroundColor Yellow
            return
        }
    }

    Write-Host '  [..] Запускаю TradingView с каналом для свечей'
    if ($tvExe) {
        Start-Process -FilePath $tvExe -ArgumentList '--remote-debugging-port=9222'
    } else {
        & node $tvCli launch --no-kill | Out-Null
    }
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

if ($HistoryOnly) {
    Write-Host '  [ok] Исторический запуск без изменения TradingView'
} else {
    $candleLaunch = [Threading.Mutex]::new($false, 'Local\DRLab235CandleLaunch')
    $ownsCandleLaunch = $false
    try {
        try { $ownsCandleLaunch = $candleLaunch.WaitOne([TimeSpan]::FromSeconds(85)) }
        catch [Threading.AbandonedMutexException] { $ownsCandleLaunch = $true }
        if ($ownsCandleLaunch) { Start-CandleChannel }
        else { Write-Host '  [!] Другой запуск 23.5 ещё ждёт TradingView.' -ForegroundColor Yellow }
    } catch {
        Write-Host "  [!] Канал свечей TradingView не запущен: $($_.Exception.Message)" -ForegroundColor Yellow
    } finally {
        if ($ownsCandleLaunch) { $candleLaunch.ReleaseMutex() }
        $candleLaunch.Dispose()
    }
}

# 3. This branch's server on its own port: an alive old process of this working copy is not the current build
$health = $null
try { $health = Invoke-RestMethod "$base/api/health" -TimeoutSec 3 } catch {}
if ($health -and (-not $health.workspace -or [IO.Path]::GetFullPath($health.workspace) -ne [IO.Path]::GetFullPath($root))) {
    Fail "Порт $port занят другой рабочей копией; ничего не изменено"
}
$expected = & $python -B (Join-Path $lab 'runtime_identity.py')
if ($health -and ($health.source_revision -ne $expected -or $health.data_revision -ne $health.current_data_revision -or -not $health.integration -or (-not $HistoryOnly -and -not $health.passive_live_refresh))) {
    # the old server of this working copy (its /api/health named this folder) is restarted. Windows may report the owner
    # of the listening socket as PID 0 («System Idle Process»), so the server is found by its own command line
    # (server.py --port <port>, as started below); a real owner of the socket is added if it is python. Anything that is
    # not python is never stopped.
    $procs = @(Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" | Where-Object { $_.CommandLine -match 'server\.py' -and $_.CommandLine -match "--port\s+$port(\s|$)" })
    $owners = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -gt 4 })
    foreach ($owner in $owners) {
        if (@($procs | ForEach-Object { $_.ProcessId }) -contains $owner) { continue }
        $p = Get-CimInstance Win32_Process -Filter "ProcessId = $owner"
        if (-not $p) { continue }
        if ($p.Name -notmatch '^python') { Fail "На порту $port чужой процесс (PID $owner, $($p.Name)); ничего не остановлено" }
        $procs += $p
    }
    if (-not $procs.Count) { Fail "Старый сервер 23.5 отвечает на $port, но его процесс не найден: закройте python в Диспетчере задач или перезагрузите компьютер" }
    Write-Host '  [..] Останавливаю старый сервер 23.5 (код обновился)'
    foreach ($p in $procs) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
    $gone = $false
    for ($i = 0; $i -lt 40 -and -not $gone; $i++) {
        Start-Sleep -Milliseconds 250
        try { Invoke-RestMethod "$base/api/health" -TimeoutSec 1 | Out-Null } catch { $gone = $true }
    }
    if (-not $gone) { Fail "Старый сервер 23.5 не остановился (PID $(@($procs | ForEach-Object { $_.ProcessId }) -join ', '))" }
    $health = $null
}
if ($health) {
    Write-Host '  [ok] Сервер 23.5 уже работает'
} else {
    for ($i = 0; $i -lt 30; $i++) {
        if (-not @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -gt 4 }).Count) { break }
        Start-Sleep -Milliseconds 100
    }
    if (@(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -gt 4 }).Count) { Fail "Порт $port занят, но сервер не ответил" }
    Write-Host '  [..] Запускаю сервер 23.5'
    $serverArgs = @('-u', '-B', 'server.py', '--port', "$port", '--integration')
    if (-not $HistoryOnly) { $serverArgs += '--passive-live-refresh' }
    Start-Process -FilePath $python -ArgumentList $serverArgs -WorkingDirectory $lab -WindowStyle Hidden `
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
