"""Source census independent of FOM: PR deltas, registry definitions and executable anchors.

An audit index, not a new ontology or an assertion that a hash/anchor establishes meaning.
"""
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
PACKAGE=ROOT/'meaning/lens/2026-10-14-integration'

def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args],stderr=subprocess.DEVNULL)

def save(out):
    # One source record per line keeps this audit inventory small and reviewable; no new schema or graph.
    fields=[]
    for key,value in out.items():
        encoded='[\n'+',\n'.join('  '+json.dumps(r,ensure_ascii=False) for r in value)+'\n ]' if key=='files' else json.dumps(value,ensure_ascii=False)
        fields.append(' '+json.dumps(key)+': '+encoded)
    (PACKAGE/'ontology-sources.json').write_text('{\n'+',\n'.join(fields)+'\n}\n',encoding='utf-8')

def main():
    src=json.loads((PACKAGE/'sources.json').read_text(encoding='utf-8'))
    files={}; requests={}
    baseline=dict(pr='main',head=src['refs']['accepted'],changed_files=git('ls-tree','-r','--name-only',src['refs']['accepted']).decode().splitlines())
    for layer in [baseline]+src['layers']:
        ref=layer['head']
        paths=layer['changed_files']
        for p in paths:
            if not p.endswith(('.md','.py','.js','.mjs','.yaml','.json','.ps1','.cmd')): continue
            if not p.startswith(('docs/','meaning/','spec/','lab/','contract/','trace/','tests/','studies/')): continue
            if p.startswith(('lab/dist/','contract/build/','trace/build/')) or '/img/' in p or '/raw/' in p: continue
            key=ref+':'+p
            requests.setdefault(key,dict(path=p,ref=ref,prs=[]))['prs'].append(layer['pr'])
    batch=subprocess.run(['git','-C',str(ROOT),'cat-file','--batch'],input=('\n'.join(requests)+'\n').encode(),capture_output=True,check=True).stdout
    pos=0
    for key,request in requests.items():
            end=batch.index(b'\n',pos); header=batch[pos:end]; pos=end+1
            if header.endswith(b' missing'): continue
            size=int(header.rsplit(b' ',1)[1]); b=batch[pos:pos+size]; pos+=size+1
            p,ref=request['path'],request['ref']
            text=b.decode('utf-8-sig',errors='replace')
            rec=dict(path=p,ref=ref,prs=request['prs'],sha256_lf=hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest())
            if p.endswith('.py'):
                try: rec['anchors']=sorted({n.name for n in ast.walk(ast.parse(text)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))})
                except SyntaxError: rec['parse']='NOT_PARSED'
            elif p.endswith(('.js','.mjs')):
                rec['anchors']=sorted(set(re.findall(r'\bfunction\s+([A-Za-z_$][\w$]*)',text)))
            elif p.endswith('.md'):
                rec['sections']=[s.strip() for s in re.findall(r'^#{1,4}\s+(.+)$',text,re.M)]
            files[key]=rec
    main=json.loads(git('show',src['refs']['accepted']+':contract/build/registry.json'))['registry']
    cur=json.loads(git('show',src['refs']['paths']+':contract/build/registry.json'))['registry']
    compact=lambda r:{k:[{f:v for f,v in o.items() if f in ('id','profile','question','q4_case_set','q4_denominator','q5_outcome','q5_region','q6_time_ru','q6_cut','implementations','reference_definition','sc_ref','grounds','parent','rule','projection','horizon_start','horizon_end','source_refs','statuses','estimands','claims')} for o in r[k]] for k in ('questions','estimands','outcomes','case_sets','comparisons','estimators','measurement_frames','observation_sources')}
    out=dict(version='I24-ONTOLOGY-SOURCE-CENSUS-1',purpose='audit inventory, independent of FOM graph; not semantic acceptance',
             refs=src['refs'],prs=list(range(1,14)),files=list(files.values()),
             baseline_definitions=compact(main),candidate_definitions=compact(cur),
             counts=dict(files=len(files),baseline_estimands=len(main['estimands']),candidate_estimands=len(cur['estimands'])),
             boundary='Inventory existence/hashes and callable anchors do not prove semantic closure; substantive relations are reconstructed and judged in 01-ontology-reconstruction.md.')
    save(out)
    print('CENSUS',out['counts'],'PR1-13 represented; no FOM input',flush=True)

if __name__=='__main__': main()
