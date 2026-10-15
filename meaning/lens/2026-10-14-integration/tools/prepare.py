"""Frozen source inventory and isolated real-data comparison stand. Does not modify a product checkout.

python -B meaning/lens/2026-10-14-integration/tools/prepare.py
"""
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
PACKAGE=ROOT/'meaning/lens/2026-10-14-integration'
LOCAL=ROOT/'lab/.runtime/integration-spec'

def git(*args,binary=False):
    data=subprocess.check_output(['git','-c','core.quotepath=false','-C',str(ROOT),*args])
    return data if binary else data.decode('utf-8').strip()

def digest(b): return hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest()
def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=1)+'\n',encoding='utf-8',newline='\n')

def extract(ref,folder):
    folder.mkdir(parents=True,exist_ok=True)
    archive=git('archive','--format=tar',ref,binary=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as src:
        for m in src.getmembers():
            target=(folder/m.name).resolve()
            if not target.is_relative_to(folder.resolve()) or not (m.isdir() or m.isfile()):
                raise ValueError('unsafe source archive path '+m.name)
        src.extractall(folder,filter='data')
    runtime=folder/'lab/.runtime'; runtime.mkdir(parents=True,exist_ok=True)
    for p in (ROOT/'lab/.runtime').iterdir():
        if p.is_file() and (p.name.startswith(('boxes_','market_')) or p.name=='now24_validation.json'):
            shutil.copy2(p,runtime/p.name)

def main():
    PACKAGE.mkdir(parents=True,exist_ok=True); LOCAL.mkdir(parents=True,exist_ok=True)
    incoming=Path('C:/Users/Admin/Downloads/deep-research-report (16).md')
    saved=PACKAGE/'input-deep-research.md'
    if not saved.exists(): shutil.copyfile(incoming,saved)
    elif incoming.exists() and digest(incoming.read_bytes())!=digest(saved.read_bytes()):
        raise ValueError('incoming research changed; preserve its new version explicitly before replacing the frozen source')
    refs={k:git('rev-parse',v) for k,v in dict(accepted='2672841',pr1='a406160',pr1_base='30459b6',pr1_merge='09dee1b',swpc='c9e61ec',decisions08='b7a52f1',kadr10='af90505',kadr11='47e2fd0',handoff='3dac913',q1='e9b5bc6',arrive='1412567',trace='3031c95',fom='f954046',summary='a2d076a',paths='0f1ae26',comparability='2a36608').items()}
    source_files={}
    paths=['AGENTS.md','docs/UI_RULES.md','docs/SEMANTICS.md','meaning/17-rabota-treidera.md','meaning/13-zhurnal-vizualizacii.md','spec/DR-LAB-Semantic-Contract-1.1-(patched).md','spec/DR-LAB-SWPC-1.1.md','contract/build/registry.json','lab/scene24.py','lab/now24.py','lab/q1/engine.py','lab/arrive24.py','lab/contract.py','trace/fom.py']
    for key in ('accepted','fom','summary','paths','comparability'):
        for path in paths:
            try: b=git('show',refs[key]+':'+path,binary=True)
            except subprocess.CalledProcessError: continue
            source_files[key+':'+path]=digest(b)
    rows=[]
    bases={1:'pr1_base',2:'accepted',3:'accepted',4:'kadr10',5:'kadr11',6:'handoff',7:'decisions08',8:'arrive',9:'trace',10:'trace',11:'accepted',12:'trace',13:'trace'}
    names={1:'pr1',2:'decisions08',3:'kadr10',4:'kadr11',5:'handoff',6:'q1',7:'arrive',8:'trace',9:'paths',10:'fom',11:'decisions08',12:'comparability',13:'summary'}
    for pr,key in names.items():
        head=refs[key]; base=refs[bases[pr]] if bases[pr] else head
        rows.append(dict(pr=pr,key=key,head=head,comparison_base=base,
            commits=git('rev-list','--first-parent',base+'..'+head).splitlines(),
            changed_files=git('diff','--name-only',base,head).splitlines(),
            same_head_as=[other for other,k in names.items() if k==key and other!=pr],
            inherited_branches=['kadr10','kadr11','handoff','q1'] if pr in (7,8,9,10,12,13) else [],
            decision='MERGED_HISTORICAL_SOURCE' if pr==1 else 'CANDIDATE_OR_ANALYTICAL_SOURCE'))
    manifest=dict(version='DR-LAB-INTEGRATION-1.0',date='2026-10-14',baseline=refs['accepted'],refs=refs,
        source_sha256_lf=source_files,input_sha256_lf=digest(saved.read_bytes()),layers=rows,
        note='Git ancestry and hashes are facts, not consent. Main remains untouched; no PR merged. #10/#12/#13 public main bases are cumulative, semantic comparison bases are listed here.')
    dump(PACKAGE/'sources.json',manifest)
    study=json.loads(git('show',refs['comparability']+':studies/q1_sopostavimost_2026_10_13/checks.json'))
    dump(PACKAGE/'research-evidence.json',dict(source_commit=refs['comparability'],rows=study['rows'],domain=study['domain'],anchors=study['anchors'],
        step1={k:study['step1'][k] for k in ('P1','P2','P3','context_CLOCK','support_control')},
        controls=study['controls'],source_role='REPORTED_EXISTING_EXPLORATION_NOT_RERUN',
        product_method='OPEN',BASE_D='MEASUREMENT_REFERENCE_NOT_PRODUCT_CANDIDATE',
        evaluate_cadence='declared 15 minute common-clock grid',runtime_cadence='closed M5',
        scored_quantity='yes/(yes+no); targets with unknown outcome excluded from scoring',
        published_quantities='POINT among known separately from BOUNDS [yes/n_match,(yes+unknown)/n_match]'))
    if '--inventory-only' in sys.argv:
        print('INVENTORY updated: actual PR1 head/base/merge distinct from current main',flush=True)
        return
    extract(refs['accepted'],LOCAL/'accepted')
    extract(refs['paths'],LOCAL/'candidate')
    # Controlled presentation-only variant of the PR #9 source. Not a new estimator or a production build.
    p=LOCAL/'candidate/lab/dist/24/d24.js'
    js=p.read_text(encoding='utf-8')
    original=js
    before="lbl(GRAPH_FF, F.brk ? 'family_break' : 'family', { n: F.N })"
    if js.count(before)!=1: raise ValueError('family frame patch source drift')
    js=js.replace(before,"''")
    before="meta = lbl(GRAPH_FF, 'support_mode', { mode: lbl(GRAPH_FF, E.mode === 'PATH_CONDITIONED' ? 'by_path' : 'by_time'), n: k.N_match_total });"
    if js.count(before)!=1: raise ValueError('NOW support patch source drift')
    js=js.replace(before,"meta = lbl(GRAPH_FF, E.mode === 'PATH_CONDITIONED' ? 'by_path' : 'by_time');")
    before="if (P.counts) meta = lbl(GRAPH_FF, 'support', { n: P.counts.n_match });"
    if js.count(before)!=1: raise ValueError('ARRIVE support patch source drift')
    js=js.replace(before,"if (P.counts) meta = '';")
    before="else if (P.publication === 'NO_KNOWN_OUTCOME') title = lbl(T, 'none_known');"
    if js.count(before)!=1: raise ValueError('UNKNOWN label patch source drift')
    js=js.replace(before,"else if (P.publication === 'NO_KNOWN_OUTCOME') { title = lbl(T, 'none_known'); meta = title; }")
    p.write_text(js,encoding='utf-8',newline='\n')
    dump(PACKAGE/'preview-definition.json',dict(version='I24-B-PREVIEW-1',source=refs['paths'],
        source_js_sha256_lf=digest(original.encode()),preview_js_sha256_lf=digest(js.encode()),
        changes=['bounds view selected explicitly as baseline; clouds retain primary position',
                 'remove unconditional family N and routine support counts from summary; retain in original inspector',
                 'retain profile-specific low support warning; percentages and their source bundles unchanged',
                 'do not introduce permanent right rail; use existing summary toggle',
                 'unknown-outcome absence keeps its registered reason'],
        standing='COMPARISON_PROTOTYPE_NOT_ACCEPTED_UI',
        implementation_note='Asset substitution in an isolated stand, like existing SWPC_SERVE tests; production must edit source and rebuild. No repository dist or contract was edited.'))
    print('PREPARED',len(rows),'PR sources; two isolated real-data backends; candidate preview patch',flush=True)

if __name__=='__main__': main()
