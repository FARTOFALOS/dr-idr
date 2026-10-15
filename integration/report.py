"""Current verification/source inventory, not a new statistical model or a claim of operator acceptance."""
import hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HERE=Path(__file__).resolve().parent
LOG=ROOT/'lab/.runtime/integration-checks'
def sha(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def main():
    checks={}
    for name in ('smoke','sem24','now24','q1_pilot','contract_sc11','run_candidate_checks','integration24','swpc11','flow','faults','swpc-browser'):
        p=LOG/(name+'.log'); text=p.read_text(encoding='utf-8',errors='replace') if p.exists() else ''
        checks[name]=dict(status='PASS' if 'ALL GOOD' in text and not re.search(r'\bFAIL(?:ED)?\b',text) else 'PENDING_OR_FAIL',log_sha256=sha(p) if p.exists() else None)
    baseline=json.loads((LOG/'baseline.json').read_text(encoding='utf-8'))
    protected=['spec/DR-LAB-Semantic-Contract-1.1-(patched).md','contract/schema/dr_lab_sc.yaml',
               *['contract/registry/'+p for p in ('00-editions.yaml','10-observation-strategy-measurement.yaml','20-cases-outcomes.yaml','30-questions-estimands.yaml','40-claims.yaml','50-validation.yaml','70-obligations.yaml')],
               'lab/scene24.py','lab/zonemap24.py','start-dr-lab.cmd','start-dr-lab.ps1','start-dr-lab-24.cmd']
    identical={p:sha(ROOT/p)==hashlib.sha256(subprocess.check_output(['git','-C',str(ROOT),'show','2672841:'+p]).replace(b'\r\n',b'\n')).hexdigest() for p in protected}
    assert all(identical.values())
    source_paths=[*ROOT.glob('lab/*24.py'),*ROOT.glob('lab/q1/*.py'),ROOT/'lab/contract.py',ROOT/'lab/server.py',ROOT/'lab/integration_audit.py',
                  *ROOT.glob('design/sozvezdiya-24/src/*'),ROOT/'contract/build/registry.json',ROOT/'integration/candidates/build/registry.json']
    sources={p.relative_to(ROOT).as_posix():sha(p) for p in source_paths if p.is_file()}
    out=dict(version='DR-LAB-INTEGRATION-FIRST-1',date='2026-10-15',baseline='2672841',checks=checks,
             accepted_definitions_unchanged=identical,accepted_executable_comparison=baseline['status'],
             source_sha256_lf=sources,source_scope='local code, immutable source units and separate accepted/candidate editions',
             human_acceptance='NOT_PERFORMED',full_trace_fom_catalog='NOT_REBOUND; original sources preserved; bounded runtime checks active',
             live='ACTUAL_FEED_NOT_VERIFIED; existing TradingView has no accessible 9222; it was not restarted; unavailable-live withdrawal tested',
             main='UNCHANGED; no merge or publication',screenshots={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'spec/ekran-24/img/integration-first').glob('*.png')})
    (HERE/'verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({k:v['status'] for k,v in checks.items()}));print('Protected definitions/launchers identical; accepted calculations comparison',baseline['status'])
    # Update provenance with adaptations without losing the original transferred bytes' witnesses.
    p=HERE/'source-manifest.json'; manifest=json.loads(p.read_text(encoding='utf-8'))
    manifest['current_sources']=sources
    manifest['decisions']=dict(implementation='current operator request, no acceptance of candidates',
        preserved='main/SC text/BASE/NOW meanings/spatial host/Q1 immutable store/FOM reference',
        adapted='atomic context, path-revision cache, independent target facts, explicit candidate gate, linked existing details',
        not_selected='BASE_D default, GEO default, P9 summary/main-mode replacement, implicit SC amendments')
    p.write_text(json.dumps(manifest,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
if __name__=='__main__':main()
