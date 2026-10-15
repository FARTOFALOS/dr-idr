param([switch]$NoBrowser, [switch]$HistoryOnly, [string]$Page = '24/#date=2025-12-17&inst=NQ&session=RDR&at=11:10&scope=all&trial=continuations&mode=continuations&cont=17,19,685,700,670')
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$lab = Join-Path $root 'lab'
$runtime = Join-Path $lab '.runtime'
$baseUrl = 'http://127.0.0.1:8773'
$python = Join-Path $env:LOCALAPPDATA 'Python\bin\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Не найден Python DR Lab' }
$env:PYTHONUTF8 = '1'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$common = & git -C $root rev-parse --git-common-dir
$sourceRoot = Split-Path ([IO.Path]::GetFullPath($common)) -Parent
foreach ($inst in @('nq','es','ym')) {
    foreach ($file in @("boxes_$inst.npz","boxes_$($inst)_meta.json","market_$inst.npz","market_$($inst)_meta.json")) {
        $target = Join-Path $runtime $file
        if (-not (Test-Path -LiteralPath $target)) {
            $source = Join-Path (Join-Path $sourceRoot 'lab\.runtime') $file
            if (-not (Test-Path -LiteralPath $source)) { throw "Нет локальной истории: $file" }
            Copy-Item -LiteralPath $source -Destination $target
        }
    }
}
if (-not $HistoryOnly) {
    $cdpReady = $false
    try { Invoke-RestMethod 'http://127.0.0.1:9222/json/version' -TimeoutSec 2 | Out-Null; $cdpReady = $true } catch {}
    if (-not $cdpReady) {
        $tvRoot = if ($env:TV_MCP_DIR) { $env:TV_MCP_DIR } else { Join-Path $env:USERPROFILE 'Claude\tradingview-mcp' }
        $tvCli = Join-Path $tvRoot 'src\cli\index.js'
        $runningTV = Get-Process TradingView -ErrorAction SilentlyContinue
        if ($runningTV) { Write-Output 'TradingView открыт без канала 9222; он не перезапускался. История доступна.' }
        elseif (Test-Path -LiteralPath $tvCli) {
            & node $tvCli launch | Out-Null
            for ($i=0; $i -lt 60; $i++) {
                Start-Sleep -Milliseconds 500
                try { Invoke-RestMethod 'http://127.0.0.1:9222/json/version' -TimeoutSec 2 | Out-Null; break } catch {}
            }
        }
    }
}
$health = $null
try { $health = Invoke-RestMethod "$baseUrl/api/health" -TimeoutSec 2 } catch {}
if ($health) {
    if (-not $health.integration -or [IO.Path]::GetFullPath($health.workspace) -ne [IO.Path]::GetFullPath($root)) {
        throw 'Порт 8773 занят другой сборкой. Рабочий сервер не изменён.'
    }
}
$taskExpectedRevision = & $python -B (Join-Path $lab 'runtime_identity.py')
if ($health -and ($health.source_revision -ne $taskExpectedRevision -or $health.data_revision -ne $health.current_data_revision)) {
    $taskOwners = @(Get-NetTCPConnection -LocalPort 8773 -State Listen | Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($taskOwner in $taskOwners) { Stop-Process -Id $taskOwner -ErrorAction Stop }
    $health = $null
}
if (-not $health) {
    for ($taskWait = 0; $taskWait -lt 30; $taskWait++) {
        if (-not @(Get-NetTCPConnection -LocalPort 8773 -State Listen -ErrorAction SilentlyContinue).Count) { break }
        Start-Sleep -Milliseconds 100
    }
    if (@(Get-NetTCPConnection -LocalPort 8773 -State Listen -ErrorAction SilentlyContinue).Count) { throw 'Порт 8773 занят, но сервер не ответил. Второй процесс не запущен.' }
    Start-Process -FilePath $python -ArgumentList '-u','-B','server.py','--port','8773','--integration' -WorkingDirectory $lab -WindowStyle Hidden `
      -RedirectStandardOutput (Join-Path $runtime 'integration.out.log') -RedirectStandardError (Join-Path $runtime 'integration.err.log')
    for ($i=0; $i -lt 60; $i++) {
        Start-Sleep -Milliseconds 500
        try { $health = Invoke-RestMethod "$baseUrl/api/health" -TimeoutSec 2; if ($health.integration) { break } } catch {}
    }
    if (-not $health.integration) { throw 'Интеграционный сервер не запустился; журнал lab/.runtime/integration.err.log' }
}
if (-not $NoBrowser) { Start-Process ($baseUrl + '/' + $Page) }
Write-Output ('DR Lab: ' + $baseUrl + '/' + $Page)
