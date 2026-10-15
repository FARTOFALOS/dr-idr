"""Transfer only declared source units from frozen PRs; never merge branches or copy market data into Git."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
manifest=[]

def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args])

def take(ref,path,dest=None,role='IMPLEMENTATION_CANDIDATE'):
    data=git('show',ref+':'+path)
    dst=ROOT/(dest or path); dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(data)
    manifest.append(dict(source_commit=git('rev-parse',ref).decode().strip(),source_path=path,
                         destination=dst.relative_to(ROOT).as_posix(),role=role,
                         sha256_lf=hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()))

def main():
    for p in ('app.js','panel.js','panel.css'):
        take('c9e61ec','design/sozvezdiya-24/src/'+p,role='SWPC_INTEGRITY_FIXES')
    take('1412567','lab/contract.py',role='EXISTING_GATE_WITH_OPTIONAL_CANDIDATE_REFERENCES')
    for p in git('ls-tree','-r','--name-only','e9b5bc6','lab/q1').decode().splitlines(): take('e9b5bc6',p)
    for p in ('lab/pre24.py','lab/arrive24.py'): take('1412567',p)
    for p in ('tests/q1_pilot.py','tests/arrive24.py'): take('1412567',p)
    take('c9e61ec','tests/swpc11.py'); take('c9e61ec','tests/swpc11_browser.mjs')
    for p in git('ls-tree','-r','--name-only','1412567','contract/registry').decode().splitlines():
        take('1412567',p,p.replace('contract/','integration/candidates/'))
    take('1412567','spec/DR-LAB-Semantic-Contract-1.1-(patched).md','integration/candidates/SC11-proposal.md','PROPOSAL_NOT_ACCEPTED_EDITION')
    for ref,folder in [('3dac913','meaning/lens/2026-10-12-independent-srs'),('47e2fd0','meaning/lens/2026-10-12-kurator')]:
        for p in git('ls-tree','-r','--name-only',ref,folder).decode().splitlines(): take(ref,p,role='DEFINITION_OR_RESEARCH_SOURCE')
    take('1641017','meaning/17-rabota-treidera.md',role='TRADER_TASK_SOURCE')
    for p in git('ls-tree','-r','--name-only','bf525e2','meaning/lens/2026-10-14-integration','spec/DR-LAB-INTEGRATION-1.0.md').decode().splitlines():
        take('bf525e2',p,role='INTEGRATION_RECONSTRUCTION_SOURCE')
    for p in ('04-transition-synthesis.md','transition-checks.json','tools/transitions.py'):
        src=REPO/'.worktrees/fom/meaning/lens/2026-10-14-integration'/p
        dst=ROOT/'meaning/lens/2026-10-14-integration'/p; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst)
    for name in ('boxes_*.npz','boxes_*_meta.json','market_*.npz','market_*_meta.json','now24_validation.json'):
        for src in (REPO/'lab/.runtime').glob(name):
            dst=ROOT/'lab/.runtime'/src.name; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
    out=ROOT/'integration/source-manifest.json'
    out.write_text(json.dumps(dict(baseline='2672841',units=manifest),ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print('SOURCE UNITS',len(manifest),'transferred; accepted SC text/schema/registry/build untouched; runtime data local only')

if __name__=='__main__': main()
