"""Bounded tests of semantic transitions, using existing engines/reference functions; no product changes.

Detailed historical case identities remain in lab/.runtime. Only aggregates and synthetic examples are reported.
"""
import hashlib
import importlib.util
import itertools
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
PACKAGE=ROOT/'meaning/lens/2026-10-14-integration'
LOCAL=ROOT/'lab/.runtime/integration-spec'
sys.path.insert(0,str(ROOT/'lab'))
import contract as C
from q1 import engine as Q

def tri_or(a,b):
    return 'yes' if 'yes' in (a,b) else 'no' if a==b=='no' else 'unknown'

def temporal():
    grid=[5,10,15,20]
    atoms=[None,[-4,-1,-2],[-1,2,1],[2,5,3]]
    counts=Counter()
    for p in itertools.product(atoms,repeat=4):
        for cut in [0,*grid]:
            for a,b in [(-1,2),(0,1),(1,2)]:
                for up in (False,True):
                    whole=C.ref_reach(p,grid,0,20,a,b,4,up)
                    before=C.ref_reach(p,grid,0,cut,a,b,4,up)
                    after=C.ref_reach(p,grid,cut,20,a,b,4,up)
                    assert whole==tri_or(before,after)
                    counts['reach_segment_composition']+=1
            if None not in p:
                for ev,pick in [('R',min),('X',max)]:
                    whole=C.ref_final_extreme(p,grid,0,20,ev)
                    parts=[C.ref_final_extreme(p,grid,s,e,ev) for s,e in ((0,cut),(cut,20))]
                    known=[x for x in parts if x['s']=='known']
                    v=pick(x['v'] for x in known)
                    ties=sorted(t for x in known if x['v']==v for t in x['ties'])
                    assert whole==dict(s='known',v=v,t=ties[0],ties=ties)
                    counts['extreme_segment_composition']+=1
        for c in range(4):
            prefix=p[:c+1]
            if None in prefix: continue
            for ev,j in [('R',0),('X',1)]:
                seen=(min if ev=='R' else max)(x[j] for x in prefix)
                residual=C.ref_residual(p,c,seen,ev)
                threshold=seen+(-1 if ev=='R' else 1)
                event=C.ref_reach(p,grid,grid[c],20,threshold,4,4,ev=='X')
                assert residual['new']==event.upper()
                counts['now_as_own_prefix_barrier']+=1
    # A repeated extreme reaches the inclusive barrier but is not a new extreme.
    p=[[0,4,2],[0,3,2],[1,3,2],[1,3,2]]
    assert C.ref_reach(p,grid,5,20,0,1,4,False)=='yes'
    assert C.ref_residual(p,0,0,'R')['new']=='NO'
    return dict(id='TR-1',status='PASS',checks=dict(counts),
                conclusion='Reach composes with three-valued OR; complete extrema compose with min/max plus ties; NOW new is an inclusive barrier one OWN tick beyond its own prefix extreme.',
                boundary='Aligned M5 cuts, unchanged observation revision and same case/frame; empty reach is NO, empty extreme is NO_PERIOD; does not equate cohorts or forecasts.')

def reflection():
    grid=[5,10,15,20]; w=10; n=0
    atoms=[None,[-4,-1,-2],[-1,2,1],[2,5,3]]
    for p in itertools.product(atoms,repeat=4):
        new=[None if q is None else [-q[1]-w,-q[0]-w,-q[2]-w] for q in p]
        for act in (0,5,10):
            for ev,other in [('R','X'),('X','R')]:
                old=C.ref_final_extreme(p,grid,act,20,other)
                got=C.ref_final_extreme(new,grid,act,20,ev)
                want=dict(old)
                for field in ('v','bound'):
                    if field in want: want[field]=-want[field]-w
                assert got==want
                n+=1
            for a,b in [(0,1),(-1,2),(-7,10)]:
                old=C.ref_reach(p,grid,act,20,a,b,w,False)
                got=C.ref_reach(new,grid,act,20,-a-b,b,w,True)
                assert old==got
                n+=1
    # Independent physical coordinate check with the two IDR edges 100 and 90.
    physical=[102,105,98,101]   # o,h,l,c in ticks
    old=C.ref_directed(physical,1,100); new=C.ref_directed(physical,-1,90)
    assert new==(-old[1]-w,-old[0]-w,-old[2]-w)
    p=[[-2,4,1],[-12,-3,-11],[-5,2,1],[-2,1,0]]
    mirror=[[-q[1]-w,-q[0]-w,-q[2]-w] for q in p]
    full=C.ref_final_extreme(mirror,grid,0,20,'R')
    after_break=C.ref_final_extreme(mirror,grid,10,20,'R')
    assert full['v']!=after_break['v']
    # The exact frame map cannot always be recovered from a quantised source cell.
    assert [C.ref_cell(v,20) for v in (0,1)]==[0,0]
    mirrored_cells=[C.ref_cell(-v-20,20) for v in (0,1)]
    assert mirrored_cells==[-10,-11]
    return dict(id='TR-2',status='PASS',checks=n+4,
                conclusion="For the same physical horizon the opposite IDR-edge frame gives u'=-u-1, R'=-X-1 and X'=-R-1; first times/ties exchange. A break also changes activation and cohort, so whole-horizon reflection cannot produce its answer.",
                level_correspondence={'old_0':'new_-1','old_-1/2':'new_-1/2','old_-7/10':'new_-3/10'},
                quantisation_witness=dict(width_ticks=20,old_directed_ticks=[0,1],old_cells=[0,0],new_cells=mirrored_cells,
                    conclusion='Transform exact values first, then quantise. One old cell does not determine a unique reflected cell at half-open boundaries.'),
                boundary='Same box and width, opposite IDR edge and orientation; separate break interval and family are still required.')

def fixtures():
    spec=importlib.util.spec_from_file_location('transition_fixtures',ROOT/'tests/q1_pilot.py')
    obj=importlib.util.module_from_spec(spec); spec.loader.exec_module(obj)
    return obj

def synthetic_rematching():
    f=fixtures(); t=f.tgt_case()
    cases=[t]+[f.analogue(k,after='yes',k6=(10,50,40)) for k in range(1,11)]
    cases +=[f.analogue(k,after='no') for k in range(11,21)]
    cases +=[f.analogue(k,close=40,after='no',k6=(10,30,20)) for k in range(21,31)]
    tbl=f.table(cases)
    a,b=[tbl.attempt(0,c,'0','GEO') for c in (5,6)]
    old={m['id'] for m in a['members']}; new={m['id'] for m in b['members']}
    assert all(x['state']['status']=='OPEN' and x['estimate']['publication']=='PUBLISHED' for x in (a,b))
    assert a['estimate']['point']==dict(num=10,den=20) and b['estimate']['point']==dict(num=0,den=20)
    # Every individual label, eligibility and not-yet condition is unchanged, even for leavers and entrants.
    assert (a['mask']['reach']==b['mask']['reach']).all() and (a['mask']['unk']==b['mask']['unk']).all()
    assert (a['mask']['valid']==b['mask']['valid']).all() and (a['mask']['notyet']==b['mask']['notyet']).all()
    assert len(old&new)==len(old-new)==len(new-old)==10
    return dict(id='TR-3',status='PASS',kind='SYNTHETIC_COUNTEREXAMPLE',
                before=dict(n=20,yes=10,no=10,unknown=0,point=.5),after=dict(n=20,yes=0,no=20,unknown=0,point=0),
                retained=10,left=10,entered=10,
                conclusion='Same target, unchanged individual labels and applicability; the displayed frequency changes solely because comparison members change. Equal support size hides this change.',
                boundary='Not a market effect estimate or evidence of an incorrect forecast; demonstrates what reading two C1 answers as one fixed-cohort update would lose.')

def reason_map(att,tbl):
    return {tbl.ids[int(j)]:str(reason) for j,reason in zip(att['par'],att['reason'])}

def real_rematching():
    Q.bind_corpus(ROOT/'lab/.runtime'); tbl=Q.table('NQ','RDR')
    assert all(str(d)<'2026-01-01' for d in tbl.dates)
    witness=None
    for date in ('2025-12-17','2025-12-10'):
        i=tbl.row(date)
        for minute in range(665,721,5):
            if minute not in tbl.grid or minute+5 not in tbl.grid: continue
            for level in ('-1/2','0','-7/10'):
                a,b=[tbl.attempt(i,tbl.grid.index(c),level,'NODEPOS_ALL') for c in (minute,minute+5)]
                if any(x['state']['status']!='OPEN' or x['estimate']['publication']!='PUBLISHED' for x in (a,b)): continue
                before={m['id']:m['label'] for m in a['members']}; after={m['id']:m['label'] for m in b['members']}
                old,new=set(before),set(after)
                if not(old-new and new-old): continue
                assert all(before[k]==after[k] for k in old&new)
                ra,rb=reason_map(a,tbl),reason_map(b,tbl)
                witness=dict(instrument='NQ',block='RDR',date=date,cut_before=minute,cut_after=minute+5,level=level,
                             estimator='NODEPOS_ALL',before=before,after=after,
                             left={k:rb[k] for k in old-new},entered={k:ra[k] for k in new-old},retained=sorted(old&new),
                             before_counts=a['counts'],after_counts=b['counts'])
                break
            if witness: break
        if witness: break
    assert witness, 'no qualifying real transition found; do not claim this real witness exists'
    LOCAL.mkdir(parents=True,exist_ok=True)
    (LOCAL/'transition-witness.local.json').write_text(json.dumps(witness,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    return dict(id='TR-4',status='PASS',kind='REAL_HISTORY_WITNESS',
                selector={k:witness[k] for k in ('instrument','block','date','cut_before','cut_after','level','estimator')},
                retained=len(witness['retained']),left=len(witness['left']),entered=len(witness['entered']),
                leaving_reasons=dict(Counter(witness['left'].values())),entering_previous_reasons=dict(Counter(witness['entered'].values())),
                conclusion='A real pair of adjacent open, published Q1 answers both loses and gains historical members. Retained members keep their labels.',
                boundary='One discriminating witness within 2006-2025, not prevalence, predictive quality, or operator interpretation; case ids stay local.')

def nested_questions():
    f=fixtures()
    # All three targets are still open today. Historical members already at 0 are excluded only from that question.
    cases=[f.tgt_case()]+[f.analogue(k,after='no') for k in range(1,21)]
    cases +=[f.analogue(k,after='no',k3=(-1,30,20),k8=(-35,30,5)) for k in range(21,41)]
    tbl=f.table(cases)
    answer={level:tbl.attempt(0,5,level,'NODEPOS_ALL') for level in ('0','-1/2','-7/10')}
    assert all(a['state']['status']=='OPEN' and a['estimate']['publication']=='PUBLISHED' for a in answer.values())
    assert answer['0']['estimate']['point']==dict(num=0,den=20)
    assert answer['-1/2']['estimate']['point']==dict(num=20,den=40)
    assert answer['-7/10']['estimate']['point']==dict(num=20,den=40)
    # On one fixed group the same paths obey nesting. It is the question-specific not-yet selection that differs.
    indices=[j for j in range(1,len(cases))]
    rates=[]
    for level in ('0','-1/2','-7/10'):
        a,b=Q.LEVELS[level]
        rates.append(sum(C.ref_reach(tbl.P[j].tolist(),tbl.grid,tbl.grid[5],tbl.end,a,b,int(tbl.w[j]),False)=='yes' for j in indices)/len(indices))
    assert rates[0]>=rates[1]>=rates[2]
    return dict(id='TR-5',status='PASS',kind='SYNTHETIC_COUNTEREXAMPLE',
                question_specific_points={'0':0,'-1/2':.5,'-7/10':.5},same_group_points=rates,
                conclusion='Nested price barriers can have reversed, individually correct C1 frequencies when each question excludes a different already-reached group. Sorting the answers would falsify their meanings.',
                prior_source='PR5 SRS FR24 and Q1 section 5 already warn about this. The contribution here is an executable witness in the existing candidate engine, not a claim of discovering the principle.',
                boundary='Not an observed market frequency or a forecast violation; do not impose common-group probability constraints on differently conditioned descriptive answers.')

def main():
    results=[temporal(),reflection(),synthetic_rematching(),real_rematching(),nested_questions()]
    stamped=['lab/contract.py','lab/scene24.py','lab/now24.py','lab/q1/engine.py','tests/q1_pilot.py',str(Path(__file__).relative_to(ROOT)).replace('\\','/')]
    source={p:hashlib.sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in stamped}
    report=dict(version='DR-LAB-TRANSITIONS-1',status='PASS',source_commit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD']).decode().strip(),
                source_sha256_lf=source,results=results,
                no_2026=True,no_product_change=True,no_ui_change=True,no_profile_admission=True,
                scope='Relations over existing definitions and one real transition. No full ontology-completeness claim and no independent market law discovery.')
    (PACKAGE/'transition-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    for r in results: print(r['id'],r['status'],r['conclusion'],flush=True)

if __name__=='__main__': main()
