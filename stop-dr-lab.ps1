# DR Lab: stop the local server (TradingView is left running).
$c = Get-NetTCPConnection -LocalPort 8767 -State Listen -ErrorAction SilentlyContinue
if ($c) { Stop-Process -Id $c.OwningProcess -Force; Write-Host '  DR Lab остановлен' } else { Write-Host '  DR Lab не был запущен' }
Start-Sleep -Seconds 2
