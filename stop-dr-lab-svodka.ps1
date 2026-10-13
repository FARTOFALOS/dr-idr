# Stops the candidate's server (port 8774 only; the working DR Lab on 8767 and the stands 8771, 8772 are never touched).
$c = Get-NetTCPConnection -LocalPort 8774 -State Listen -ErrorAction SilentlyContinue
foreach ($x in $c) { Stop-Process -Id $x.OwningProcess -Force -ErrorAction SilentlyContinue }
Write-Host '  Вариант «Сводка» остановлен'
