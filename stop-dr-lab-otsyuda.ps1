# Stops the variant's server (port 8772 only; the working DR Lab on 8767 and the pilot's stand on 8771 are never touched).
$c = Get-NetTCPConnection -LocalPort 8772 -State Listen -ErrorAction SilentlyContinue
foreach ($x in $c) { Stop-Process -Id $x.OwningProcess -Force -ErrorAction SilentlyContinue }
Write-Host '  Вариант «Отсюда» остановлен'
