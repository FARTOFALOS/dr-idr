import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rows=[]
for ref,folder in [('af90505','meaning/lens/2026-10-12-film-i-moment'),('2a36608','studies/q1_sopostavimost_2026_10_13')]:
    for p in subprocess.check_output(['git','-C',str(ROOT),'ls-tree','-r','--name-only',ref,folder]).decode().splitlines():
        b=subprocess.check_output(['git','-C',str(ROOT),'show',ref+':'+p]);dst=ROOT/p
        dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
        rows.append(dict(source_commit=ref,path=p,sha256_lf=hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest(),standing='RESEARCH_OR_PROPOSAL_NOT_PRODUCT_ADMISSION'))
(ROOT/'integration/research-sources.json').write_text(json.dumps(rows,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
print('Preserved',len(rows),'research sources; no study rerun or estimator selection')
