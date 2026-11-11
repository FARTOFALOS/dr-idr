# Stops the 23.5 server (port 8735 of this working copy only); screen 24 on 8767 and every other stand are never touched.
$ErrorActionPreference = 'Stop'
$health = $null
try { $health = Invoke-RestMethod 'http://127.0.0.1:8735/api/health' -TimeoutSec 3 } catch {}
if (-not $health) { Write-Host '  Сервер 23.5 не запущен'; exit 0 }
if (-not $health.workspace -or [IO.Path]::GetFullPath($health.workspace) -ne [IO.Path]::GetFullPath($PSScriptRoot)) {
    Write-Host '  На 8735 другая рабочая копия; она не остановлена'; exit 1
}
# by its command line: Windows may report the socket's owner as PID 0
Get-CimInstance Win32_Process -Filter "Name LIKE 'python%'" | Where-Object { $_.CommandLine -match 'server\.py' -and $_.CommandLine -match '--port\s+8735(\s|$)' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort 8735 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -gt 4 } | ForEach-Object { $q = Get-CimInstance Win32_Process -Filter "ProcessId = $_"; if ($q -and $q.Name -match '^python') { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } }
Write-Host '  Сервер 23.5 остановлен'
