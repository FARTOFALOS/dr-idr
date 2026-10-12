# DR Lab · Q1: the isolated historical pilot (Q1-PILOT-0.2, C1). The desktop shortcut «DR Lab Q1» points to start-q1-pilot.cmd.
# Starts the pilot's own local server on 127.0.0.1:8771 (hidden, logs in lab/.q1-pilot) and opens its page.
# The working DR Lab (127.0.0.1:8767, the shortcuts «DR Lab» / «DR Lab 24») is never touched. Idempotent.
param([switch]$NoBrowser)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$port = 8771
$url = "http://127.0.0.1:$port/"
$runtime = Join-Path $root 'lab\.q1-pilot'

function Test-Url($u) { try { Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 3 | Out-Null; return $true } catch { return $false } }
function Fail($msg) { Write-Host "  [!] $msg" -ForegroundColor Red; Read-Host '  Enter — закрыть'; exit 1 }

Write-Host ''
Write-Host '  DR Lab · Q1 (исторический пилот)' -ForegroundColor Cyan
Write-Host ''

if (Test-Url ($url + 'api/q1/meta')) {
    Write-Host '  [ok] Сцена пилота уже запущена'
} else {
    $python = $null
    foreach ($cand in @((Join-Path $env:LOCALAPPDATA 'Python\bin\python.exe'), 'python', 'py')) {
        try { & $cand -c "import numpy, pandas, scipy" 2>$null; if ($LASTEXITCODE -eq 0) { $python = $cand; break } } catch { }
    }
    if (-not $python) { Fail 'Не найден Python с numpy, pandas и scipy.' }
    # A git worktree has no built base of its own: read the main checkout's lab/.runtime (read only)
    if (-not (Test-Path (Join-Path $root 'lab\.runtime\boxes_nq_meta.json'))) {
        $gitFile = Join-Path $root '.git'
        if ((Test-Path $gitFile) -and -not (Get-Item -Force $gitFile).PSIsContainer) {     # .git is a hidden file in a worktree
            $gitdir = ([System.IO.File]::ReadAllText($gitFile) -replace '^gitdir:\s*', '').Trim()
            $main = Split-Path (Split-Path (Split-Path $gitdir))
            $env:DR_IDR_RUNTIME = Join-Path $main 'lab\.runtime'
        }
    }
    New-Item -ItemType Directory -Force $runtime | Out-Null
    Write-Host '  [..] Запускаю сцену пилота (отдельно от рабочего DR Lab)'
    Start-Process -FilePath $python -ArgumentList @('-B', 'lab/q1/server.py', '--port', "$port") -WorkingDirectory $root -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $runtime 'server.out.log') -RedirectStandardError (Join-Path $runtime 'server.err.log')
    $ready = $false
    for ($i = 0; $i -lt 90; $i++) { Start-Sleep -Seconds 1; if (Test-Url ($url + 'api/q1/meta')) { $ready = $true; break } }
    if (-not $ready) { Fail "Сцена не ответила за 90 секунд. Журнал: $runtime\server.err.log" }
    Write-Host '  [ok] Сцена пилота запущена'
}
if (-not $NoBrowser) { Start-Process $url }
