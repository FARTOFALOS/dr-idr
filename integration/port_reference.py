"""Keep the existing Trace/FOM sources as a versioned reference; runtime checks reuse their actual functions."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REF='f954046'
paths=subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-r','--name-only',REF,'trace','lab/semtrace.py','tests/fom_map.py','tests/trace_arch.py','tests/trace_page.mjs']).decode().splitlines()
items=[]
for p in paths:
    b=subprocess.check_output(['git','-C',str(ROOT),'show',REF+':'+p]); dst=ROOT/'integration/reference'/p
    dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(b)
    items.append(dict(source=p,destination=dst.relative_to(ROOT).as_posix(),sha256_lf=hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest()))
(ROOT/'integration/reference/source.json').write_text(json.dumps(dict(commit=REF,standing='FROZEN_REFERENCE_NOT_CURRENT_CATALOG',files=items),indent=1)+'\n',encoding='utf-8')
print('Retained',len(items),'Trace/FOM source artifacts; no claim of a current full catalog')
