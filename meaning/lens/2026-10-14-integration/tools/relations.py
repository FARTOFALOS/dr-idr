"""Discriminating checks of reconstructed relations, not new market hypotheses or a new ontology stack."""
import importlib.util
import itertools
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
PACKAGE=ROOT/'meaning/lens/2026-10-14-integration'
sys.path.insert(0,str(ROOT/'lab'))
import contract as C
import now24 as N

def main():
    results=[]
    grid=[5,10,15]; n=0
    for lows in itertools.product(range(-3,4),repeat=3):
        p=[[lo,lo+5,lo+2] for lo in lows]
        r=C.ref_final_extreme(p,grid,0,15,'R')
        hit=C.ref_reach(p,grid,0,15,-1,2,2,False)
        assert (r['v']*2<=-1*2)==(hit=='yes')
        if lows[0]>-1:
            assert hit==C.ref_reach(p,grid,5,15,-1,2,2,False)
        n+=1
    results.append(dict(id='REL-1',status='PASS',checks=n,relation='complete own-horizon final-R threshold equals reach; when not yet reached by cut, full/rest reach agree per case',
                        boundary='same frame, level and horizon; does not equate family percentages or first times'))
    p=[[-2,3,1],None,[1,6,3]]
    assert C.ref_final_extreme(p,grid,0,15,'R')['s']=='unknown'
    assert C.ref_reach(p,grid,0,15,-1,2,2,False)=='yes'
    results.append(dict(id='REL-2',status='PASS',relation='truth-related projections can have different knowledge: known reach YES while final R UNKNOWN'))
    a=[[-2,4,1],[0,3,0],[0,3,1]]; b=[[-2,4,1],[0,3,3],[0,3,1]]
    assert all(C.ref_final_extreme(a,grid,0,15,e)==C.ref_final_extreme(b,grid,0,15,e) for e in ('R','X'))
    assert bool(N._near(0,4,0,4,(1,4))) and not bool(N._near(3,4,0,4,(1,4)))
    results.append(dict(id='REL-3',status='PASS',relation='same final R/X and times do not determine comparability at cut; aggregation cannot reconstruct a conditional set'))
    x=[[-2,4,1],[0,3,0],[0,3,1]]
    y=[[0,4,1],[-2,3,0],[0,3,1]]
    assert C.ref_final_extreme(x,grid,0,15,'R')['t']!=C.ref_final_extreme(y,grid,0,15,'R')['t']
    assert [q[2] for q in x]==[q[2] for q in y]
    results.append(dict(id='REL-4',status='PASS',relation='same close paths do not determine wick arrival or the time of final R'))
    # Same marginal distributions of final R and X, different coupling on one historical witness.
    population1=[(-2,1),(0,3)]; population2=[(-2,3),(0,1)]
    assert sorted(r for r,x in population1)==sorted(r for r,x in population2)
    assert sorted(x for r,x in population1)==sorted(x for r,x in population2)
    assert sum(r<=-1 and x>=2 for r,x in population1)!=sum(r<=-1 and x>=2 for r,x in population2)
    results.append(dict(id='REL-5',status='PASS',relation='equal R and X marginals do not determine a joint path claim; preserve case identity as the coupling witness'))
    # A nonempty proper selected subset changes a percentage even when the event predicate is identical.
    labels=[True,True,True,False]; chosen=[2,3]
    assert sum(labels)/len(labels)!=sum(labels[i] for i in chosen)/len(chosen)
    results.append(dict(id='REL-6',status='PASS',relation='per-case event equivalence does not equate measures under different case sets/denominators'))
    out=dict(status='PASS',role='mathematical/discriminating examples over existing reference functions; not empirical predictive validation',
             results=results,no_market_data_export=True,no_semantic_contract_changed=True)
    (PACKAGE/'relation-checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print('RELATIONS: 6 discriminating checks passed; 343 complete-path cases; unknown, conditional loss, close/wick and marginal coupling separated')

if __name__=='__main__': main()
