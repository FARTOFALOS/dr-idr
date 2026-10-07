# Creates .venv-linkml, the LinkML environment of the machine contract, and checks that the committed products equal
# what the sources produce. Run from anywhere:  powershell -ExecutionPolicy Bypass -File contract\setup-linkml.ps1
# The running tool does not need it (lab/contract.py reads contract/build/ with the standard library).
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root '.venv-linkml'
$py = $null
foreach ($cand in @((Join-Path $env:LOCALAPPDATA 'Python\bin\python.exe'), 'python', 'py')) {
    try { & $cand -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null; if ($LASTEXITCODE -eq 0) { $py = $cand; break } } catch { }
}
if (-not $py) { throw 'Python 3.10 or newer not found' }
$vpy = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path $vpy)) { & $py -m venv $venv }
& $vpy -m pip install --upgrade pip
& $vpy -m pip install -r (Join-Path $PSScriptRoot 'requirements-linkml.txt')
$env:PYTHONUTF8 = '1'
& $vpy (Join-Path $PSScriptRoot 'tools\build.py') --check
if ($LASTEXITCODE -ne 0) { throw 'contract/tools/build.py --check failed' }
