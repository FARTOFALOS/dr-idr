# Stops the 23.5 server (port 8735 of this working copy only); screen 24 on 8767 and every other stand are never touched.
$ErrorActionPreference = 'Stop'
$health = $null
try { $health = Invoke-RestMethod 'http://127.0.0.1:8735/api/health' -TimeoutSec 3 } catch {}
if (-not $health) { Write-Host '  Сервер 23.5 не запущен'; exit 0 }
if (-not $health.workspace -or [IO.Path]::GetFullPath($health.workspace) -ne [IO.Path]::GetFullPath($PSScriptRoot)) {
    Write-Host '  На 8735 другая рабочая копия; она не остановлена'; exit 1
}
Get-NetTCPConnection -LocalPort 8735 -State Listen | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ }
Write-Host '  Сервер 23.5 остановлен'
