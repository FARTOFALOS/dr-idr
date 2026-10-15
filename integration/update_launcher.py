from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'start-dr-lab-integration.ps1'
s=p.read_text(encoding='utf-8-sig')
s=s.replace("[string]$Page = '24/#trial=pre,arrive,paths'","[string]$Page = '24/#date=2025-12-17&inst=NQ&session=RDR&at=11:10&scope=all&trial=pre,arrive,paths&det=1'")
s=s.replace("        if (Test-Path -LiteralPath $tvCli) { & node $tvCli launch | Out-Null }", """        $runningTV = Get-Process TradingView -ErrorAction SilentlyContinue
        if ($runningTV) { Write-Output 'TradingView открыт без канала 9222; он не перезапускался. История доступна.' }
        elseif (Test-Path -LiteralPath $tvCli) {
            & node $tvCli launch | Out-Null
            for ($i=0; $i -lt 60; $i++) {
                Start-Sleep -Milliseconds 500
                try { Invoke-RestMethod 'http://127.0.0.1:9222/json/version' -TimeoutSec 2 | Out-Null; break } catch {}
            }
        }""")
p.write_bytes(b'\xef\xbb\xbf'+s.replace('\r\n','\n').replace('\n','\r\n').encode('utf-8'))
