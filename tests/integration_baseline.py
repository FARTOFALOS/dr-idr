"""Compare the actual accepted code and the integrated code on the same local tape; code/registry provenance may differ."""
import hashlib,io,json,shutil,subprocess,sys,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'lab/.runtime/integration-checks/accepted'
PROGRAM=r'''
import hashlib,json,sys
sys.path.insert(0,'lab')
import scene24 as S, now24 as N
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def bundle(b):return dict(estimand=b['estimand'],parameters=json.loads(b.get('parameters','{}')),estimates=[{k:v for k,v in x.items() if k!='estimate_id'} for x in b['estimates']],supports=[{k:v for k,v in x.items() if k!='support_id'} for x in b['supports']],claim=b.get('claim'),admissible_claims=b.get('admissible_claims'))
out=[]
for inst,date,cut,view in [('NQ','2025-12-17',670,'conf:all'),('NQ','2025-12-10',675,'conf:all'),('NQ','2025-12-10',870,'auto'),('NQ','2025-12-10',870,'conf'),('ES','2025-12-17',720,'auto')]:
 f=S.family(inst,'RDR',cut,date,view);n=N.live(inst,'RDR',cut,date,view)
 out.append(dict(selector=[inst,date,cut,view],family=f.get('family_id'),snapshot=f.get('snapshot_id'),N=f.get('N'),members=digest(f.get('members')),counts=digest(f.get('counts')),zones=digest(f.get('zones')),
    BASE=digest([bundle(b) for b in f.get('contract',{}).get('bundles',[])]),NOW=digest([bundle(b) for b in n.get('contract',{}).get('bundles',[])])))
print(json.dumps(out))
'''

def main():
 BASE.mkdir(parents=True,exist_ok=True)
 data=subprocess.check_output(['git','-C',str(ROOT),'archive','2672841'])
 with tarfile.open(fileobj=io.BytesIO(data)) as archive:
  for item in archive.getmembers():
   if not (BASE/item.name).resolve().is_relative_to(BASE.resolve()) or not(item.isdir() or item.isfile()):raise ValueError('unsafe archive')
  archive.extractall(BASE,filter='data')
 runtime=BASE/'lab/.runtime';runtime.mkdir(parents=True,exist_ok=True)
 for src in (ROOT/'lab/.runtime').iterdir():
  if src.is_file() and (src.name.startswith(('boxes_','market_')) or src.name=='now24_validation.json'):shutil.copy2(src,runtime/src.name)
 old=json.loads(subprocess.check_output([sys.executable,'-B','-c',PROGRAM],cwd=BASE))
 new=json.loads(subprocess.check_output([sys.executable,'-B','-c',PROGRAM],cwd=ROOT))
 assert old==new, [(a['selector'],[k for k in a if a[k]!=b[k]]) for a,b in zip(old,new) if a!=b]
 (ROOT/'lab/.runtime/integration-checks/baseline.json').write_text(json.dumps(dict(status='PASS',scenes=old,scope='case identities, primary measurements, zones, estimates/supports/claims; new code/registry provenance intentionally distinct'),indent=1)+'\n',encoding='utf-8')
 print('ALL GOOD: accepted main and integrated code agree on five scenes, including break/original and ES',flush=True)

if __name__=='__main__':main()
