# Stops the Q1 pilot's server (port 8771 only; the working DR Lab on 8767 is never touched).
$c = Get-NetTCPConnection -LocalPort 8771 -State Listen -ErrorAction SilentlyContinue
foreach ($x in $c) { Stop-Process -Id $x.OwningProcess -Force -ErrorAction SilentlyContinue }
Write-Host '  Сцена пилота остановлена'
