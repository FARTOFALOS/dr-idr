$ErrorActionPreference = 'Stop'
$previewPidFile = Join-Path $PSScriptRoot 'lab\.runtime\server8775.pid'
if (Test-Path -LiteralPath $previewPidFile) {
    $previewPid = [int](Get-Content -LiteralPath $previewPidFile)
    $previewProcess = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $previewPid) -ErrorAction SilentlyContinue
    if ($previewProcess -and $previewProcess.CommandLine -match [regex]::Escape($PSScriptRoot) -and $previewProcess.CommandLine -match '--port\s+8775') { Stop-Process -Id $previewPid }
}
