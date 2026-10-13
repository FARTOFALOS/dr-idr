# Isolated, operator-authorized candidate. Only its own server on 127.0.0.1:8775 is started.
param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$previewRoot = $PSScriptRoot
$previewRuntime = Join-Path $previewRoot 'lab\.runtime'
$previewBase = 'http://127.0.0.1:8775/'
$previewScene = $previewBase + '24/#date=2024-03-04&inst=ES&session=RDR&at=11:20&mode=path'
function Preview-Ready { try { $null = Invoke-WebRequest -Uri ($previewBase + 'api/contract') -UseBasicParsing -TimeoutSec 2; return $true } catch { return $false } }
if (-not (Preview-Ready)) {
    if (-not (Test-Path -LiteralPath (Join-Path $previewRuntime 'boxes_es_meta.json'))) { throw 'У кандидата нет локальной базы сессий.' }
    $previewPython = Join-Path $env:LOCALAPPDATA 'Python\bin\python.exe'
    if (-not (Test-Path -LiteralPath $previewPython)) { throw 'Не найден Python с данными DR Lab.' }
    $previewServer = Join-Path $previewRoot 'lab\server.py'
    $previewProcess = Start-Process -FilePath $previewPython -ArgumentList @('-B', ('"' + $previewServer + '"'), '--port', '8775') -WorkingDirectory (Join-Path $previewRoot 'lab') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $previewRuntime 'server8775.out.log') -RedirectStandardError (Join-Path $previewRuntime 'server8775.err.log')
    Set-Content -LiteralPath (Join-Path $previewRuntime 'server8775.pid') -Value $previewProcess.Id -Encoding ASCII
    $previewReady = $false
    for ($previewAttempt=0; $previewAttempt -lt 40; $previewAttempt++) { Start-Sleep -Milliseconds 500; if (Preview-Ready) { $previewReady=$true; break } }
    if (-not $previewReady) { throw 'Стенд 8775 не ответил. Журнал: lab\.runtime\server8775.err.log' }
}
Write-Host 'DR Lab 24: Путь семьи и ответы на графике — 127.0.0.1:8775'
if (-not $NoBrowser) { Start-Process $previewScene }
