# DR Lab trade journal: register (or remove with -Remove) the Windows task that runs
#   pythonw lab\trades.py collect
# every 15 minutes for the current user, only while the user is logged on (no password is stored), hidden.
# spec/DR-LAB-TRADE-JOURNAL.md
param(
    [switch]$Remove,
    [string]$Python = "$env:LOCALAPPDATA\Python\bin\pythonw.exe"
)
$ErrorActionPreference = 'Stop'
$name = 'DR Lab - trade journal'
$root = Split-Path -Parent $PSScriptRoot
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name   # DOMAIN\user; $env:USERNAME is refused

if ($Remove) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
    "removed: $name"
    return
}
if (-not (Test-Path $Python)) { $Python = (Get-Command pythonw.exe).Source }

$action = New-ScheduledTaskAction -Execute $Python -Argument 'lab\trades.py collect' -WorkingDirectory $root
$daily = New-ScheduledTaskTrigger -Daily -At 00:00
$daily.Repetition = (New-ScheduledTaskTrigger -Once -At 00:00 -RepetitionInterval (New-TimeSpan -Minutes 15) `
    -RepetitionDuration (New-TimeSpan -Days 1)).Repetition
$logon = New-ScheduledTaskTrigger -AtLogOn -User $user
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -Hidden
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $name -Action $action -Trigger @($daily, $logon) -Settings $settings `
    -Principal $principal -Description 'Copies the NinjaTrader base and updates lab\.runtime\trades\journal.sqlite3 (spec/DR-LAB-TRADE-JOURNAL.md)' -Force -ErrorAction Stop | Out-Null
"registered: $name -> $Python lab\trades.py collect (in $root), every 15 minutes"
