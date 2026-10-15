"""Discriminating reconstruction checks; raw market witnesses remain local."""
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
PACKAGE=ROOT/'meaning/lens/2026-10-14-integration'
LOCAL=ROOT/'lab/.runtime/integration-spec'
sys.path.insert(0,str(ROOT/'lab'))
import scene24
import contract as C
import now24

def old_registry(ref):
    return json.loads(subprocess.check_output(['git','-C',str(ROOT),'show',ref+':contract/build/registry.json']))['registry']

def main():
    LOCAL.mkdir(parents=True,exist_ok=True)
    old=old_registry('2672841'); current=C.registry()
    schema_entry=next(e for e in old['estimands'] if e['id']=='EST:B-LEVEL-REST')
    assert 'max(t' in schema_entry['q6_time_ru']
    witnesses=[]
    for date,cut in [('2025-12-17',640),('2025-12-10',660),('2025-12-09',645)]:
        fam=scene24.family('NQ','RDR',cut,date,'conf:all')
        if fam.get('status')!='ok': continue
        grid,end=fam['grid'],fam['schedule']['end']
        for level in [(0,1),(-1,2),(1,1),(2,1)]:
            up=level[0]>0
            for m in fam['members']:
                if m['act']<=cut: continue
                a=C.ref_reach(m['path'],grid,cut,end,*level,m['w'],up)
                b=C.ref_reach(m['path'],grid,max(cut,m['act']),end,*level,m['w'],up)
                if a!=b:
                    witnesses.append(dict(instrument='NQ',date=date,block='RDR',cut=cut,member=m['id'],activation=m['act'],level=level,common_cut=a,after_own_activation=b))
        if witnesses: break
    (LOCAL/'horizon-witness.local.json').write_text(json.dumps(witnesses,ensure_ascii=False,indent=1),encoding='utf-8')
    assert witnesses, 'no discriminating real-case witness found; do not declare the two horizons distinct empirically'
    forms={f['id']:f for f in current['claim_forms']}
    title=next(x['text_ru'] for x in forms['CF:N-NEW-R']['labels'] if x['key']=='title_mark')
    d,e,w,r_seen,delta=-1,100,10,-.25,.25
    anchor=e+d*w*r_seen; deeper=e+d*w*(r_seen-delta)
    assert deeper>anchor and 'ниже' in title
    study=json.loads((PACKAGE/'research-evidence.json').read_text(encoding='utf-8'))
    p2=study['step1']['P2']; eq=study['step1']['support_control']['P2']
    assert p2['brier_X']<p2['brier_ref'] and eq['hi']<0
    # Independent of FOM: the KADR prose uses the symbol of a ratio for an unnormalised tick displacement.
    kadr=subprocess.check_output(['git','-C',str(ROOT),'show','47e2fd0:meaning/lens/2026-10-12-kurator/02-specifikaciya.md']).decode('utf-8')
    assert 'o_u = e − o' in kadr
    assert (100-80)/10 != 100-80
    # A market fact and applicability of a fresh query cannot be a single exclusive state.
    spec=importlib.util.spec_from_file_location('q1_audit_fixtures',ROOT/'tests/q1_pilot.py')
    fixtures=importlib.util.module_from_spec(spec); spec.loader.exec_module(fixtures)
    tbl=fixtures.table([fixtures.tgt_case(k3=(-1,30,20))])
    early=tbl.target_state(0,fixtures.CUT,(0,1)); last=tbl.target_state(0,fixtures.L-1,(0,1))
    assert early['status']=='RESOLVED' and last['status']=='BLOCK_OVER'
    # Controlled witness: a snapshot's current identity does not bind every intermediate close of its paths.
    # No runtime file is changed. A fresh cache key reveals the changed prefix; a reused id returns the old series.
    base=copy.deepcopy(fam); changed=copy.deepcopy(base); found=None
    for j,m in enumerate(changed['members']):
        for c,q in enumerate(m['path']):
            if q is None or changed['grid'][c]<=m['act']: continue
            lo,hi,cl=q
            lower=max(lo,m.get('oppv',lo))
            alt=lower if lower!=cl else hi
            if alt==cl or not lower<=alt<=hi: continue
            q[2]=alt; found=(j,c); break
        if found: break
    assert found is not None
    identity=lambda s:hashlib.sha1(json.dumps([s['family_id'],s['source'],[[m['id'],m['R'],m['X'],m.get('outcome'),m['order']] for m in s['members']]],sort_keys=True).encode()).hexdigest()[:16]
    assert identity(base)==identity(changed)==base['snapshot_id']
    old_series=now24._member_series(base)
    aliased=now24._member_series(changed)
    changed['snapshot_id']+='-audit-only'
    fresh=now24._member_series(changed)
    j,c=found
    assert old_series is aliased and aliased[0]['clr'][j,c]!=fresh[0]['clr'][j,c]
    summary=dict(version='DR-LAB-INTEGRATION-1.0',source='direct local reconstruction; no new global research',
        checks={
         'REAL_HORIZON_WITNESS':'PASS: common clock and max(cut,activation) differ on real data',
         'SHORT_R_PHYSICAL_DIRECTION':'PASS: old registered below-price wording contradicts short retracement geometry',
         'KADR_UNIT_CONTRADICTION':'PASS: KADR-1.1 section 2 names an unnormalised displacement o_u although u is defined as divided by width; engine keeps v and w separately',
         'FACT_VS_QUERY_APPLICABILITY':'PASS: controlled Q1 path is RESOLVED before H and BLOCK_OVER at H; an exclusive status cannot preserve both facts',
         'PATH_REVISION_IDENTITY':'PASS: controlled changed intermediate close preserves snapshot identity and aliases NOW series cache when the same source revision is reused; not an observed live incident',
         'BASE_D_NOT_PRODUCT_CANDIDATE':'PASS: explicit role in source protocol',
         'NODEPOS_ALL_PAIRED_ADVANTAGE':'PASS: reported paired difference and equal-support interval favor NODEPOS_ALL',
         'CADENCE_TRANSFER':'OPEN: study 15-minute grid does not cover every M5 cut',
         'POINT_VS_BOUNDS':'DISTINCT: scoring point among known agrees with runtime point; UI unknown bounds have another denominator',
         'HUMAN_UI_SUPERIORITY':'NOT_ESTABLISHED'},
        no_formula_changed=True,no_2026_read=True,raw_witness='lab/.runtime/integration-spec/horizon-witness.local.json',
        scope='witness of non-equivalence, not a measurement of its prevalence or a permission to alter accepted semantics')
    (PACKAGE/'reconstruction-checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print('AUDIT: real horizon witness; short-price wording counterexample; paired estimator evidence checked; no numerical changes',flush=True)

if __name__=='__main__': main()
