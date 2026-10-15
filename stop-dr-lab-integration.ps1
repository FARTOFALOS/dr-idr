$ErrorActionPreference = 'Stop'
$health = Invoke-RestMethod 'http://127.0.0.1:8773/api/health' -TimeoutSec 3
if (-not $health.integration -or [IO.Path]::GetFullPath($health.workspace) -ne [IO.Path]::GetFullPath($PSScriptRoot)) {
    throw 'На 8773 другая сборка; она не остановлена.'
}
Get-NetTCPConnection -LocalPort 8773 -State Listen | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ }
