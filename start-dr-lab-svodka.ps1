# DR Lab 24 · «Сводка» (candidate of 13.10.2026) — screen 24 with the reorganised summary (Сегодня / По цене / Ориентир),
# for the operator's acceptance. The desktop shortcut «DR Lab 24 · сводка (вариант)» points to start-dr-lab-svodka.cmd.
# Starts this branch's own server on 127.0.0.1:8774 (hidden, logs in lab/.runtime) and opens screen 24 on ES RDR
# 04.03.2024, 11:20 — a pullback after +0,5. The working DR Lab (127.0.0.1:8767) and the stands 8771, 8772 are never
# touched. Idempotent.
param([switch]$NoBrowser)

$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$port = 8774
$base = "http://127.0.0.1:$port/"
$scene = $base + '24/#date=2024-03-04&inst=ES&session=RDR&at=11:20'
$runtime = Join-Path $root 'lab\.runtime'

function Test-Url($u) { try { Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 3 | Out-Null; return $true } catch { return $false } }
function Fail($msg) { Write-Host "  [!] $msg" -ForegroundColor Red; Read-Host '  Enter — закрыть'; exit 1 }

Write-Host ''
Write-Host '  DR Lab 24 · «Сводка» (вариант для приёмки)' -ForegroundColor Cyan
Write-Host ''

if (Test-Url ($base + 'api/contract')) {
    Write-Host '  [ok] Вариант уже запущен'
} else {
    if (-not (Test-Path (Join-Path $runtime 'boxes_nq_meta.json'))) { Fail "Нет базы сессий в $runtime (копия lab\.runtime рабочего DR Lab)." }
    $python = $null
    foreach ($cand in @((Join-Path $env:LOCALAPPDATA 'Python\bin\python.exe'), 'python', 'py')) {
        try { & $cand -c "import numpy, pandas" 2>$null; if ($LASTEXITCODE -eq 0) { $python = $cand; break } } catch { }
    }
    if (-not $python) { Fail 'Не найден Python с numpy и pandas.' }
    Write-Host '  [..] Запускаю вариант экрана 24 (отдельно от рабочего DR Lab)'
    Start-Process -FilePath $python -ArgumentList @('-B', 'server.py', '--port', "$port") -WorkingDirectory (Join-Path $root 'lab') -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $runtime 'server8774.out.log') -RedirectStandardError (Join-Path $runtime 'server8774.err.log')
    $ready = $false
    for ($i = 0; $i -lt 120; $i++) { Start-Sleep -Seconds 1; if (Test-Url ($base + 'api/contract')) { $ready = $true; break } }
    if (-not $ready) { Fail "Вариант не ответил за 120 секунд. Журнал: $runtime\server8774.err.log" }
    Write-Host '  [ok] Вариант запущен'
}
if (-not $NoBrowser) { Start-Process $scene }
