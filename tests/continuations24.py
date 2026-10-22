"""Actual publication and deliberate number/witness mismatches, with no issue/data writes."""
import copy
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab'))
import continuations24 as W
import contract as C
import integration24 as I
import scene24 as S


def check(ok,name):
    if not ok: raise AssertionError(name)
    print('PASS '+name,flush=True)


def main():
    req=dict(instrument='NQ',session='RDR',date='2025-12-17',at=670,scope='all',
             target=dict(low=[17,10],high=[19,10],first_close=690,last_close=700,created_at=670))
    started=time.perf_counter();a=W.response(req)
    check(a['contract']['status']=='CONFORMANT' and len(a['proof']['witnesses'])==97,'first published answer has all 97 exact witness paths')
    check(a['proof']['counts']['outside_F']==60,'paths include all 60 cases outside original F')
    check(a['proof']['support']==dict(n_total=97,n_known=96,yes=39,no=57,unknown=1),'published count and UNKNOWN match the independent historical result')
    check(a['release_id']==W.revision(a['proof']),'one content revision binds target, context, outcomes, supports and complete paths')
    raw=W._releases[a['release_id']]
    fam,_,day=S._family('NQ','RDR',670,'2025-12-17','conf:all')
    day=dict(day,_F_ids=fam['ids']);cases,grid=W.corpus('NQ','RDR');today=W.rows_today(fam,day,grid,670)
    for fault in ('missing','foreign_path','wrong_outcome','wrong_width','wrong_activation'):
        paths=copy.deepcopy(a['proof']['witnesses'])
        if fault=='missing':paths.pop()
        elif fault=='foreign_path':
            paths[0]['path'][-1]=[999,1000,999]  # outside target window: the correct numerical outcome is unchanged
            paths[0]['revision']=W.revision({k:v for k,v in paths[0].items() if k!='revision'})
        elif fault=='wrong_outcome':paths[0]['outcome']='NO' if paths[0]['outcome']=='YES' else 'YES'
        elif fault=='wrong_activation':
            paths[0]['activation']=grid[-1]  # correct path/count, but a renderer would hide the entire witness
            paths[0]['revision']=W.revision({k:v for k,v in paths[0].items() if k!='revision'})
        else:paths[0]['w']+=1
        bad=W.publish(raw,paths,cases,today,grid,day)
        check(bad['status']=='WITNESS_MISMATCH' and 'proof' not in bad and not bad['contract'].get('bundles'),
              'correct underlying count cannot publish with '+fault)
    req['previous']=a['release_id'];req['at']=690;b=W.response(req)
    check(b['proof']['target']==a['proof']['target'],'new M5 preserves exact physical target and absolute window')
    check(b['proof']['counts']['position']==81 and b['proof']['support']['n_total']==39 and b['proof']['support']['yes']==20,
          'residual question names its own risk set (39 of 81 position matches)')
    check(not b['comparison']['same_question'] and 'PREFIX_CONDITION_CHANGED' in b['comparison']['reasons'],
          'transition explicitly identifies the changed residual question')
    req['previous']=b['release_id'];req['at']=695;f=W.response(req)
    check(f['status']=='FACT_YES' and f['proof']['observed']['available_at']==695 and not f['proof']['witnesses'] and not f['contract']['bundles'],
          'known M5 visit withdraws conditional statistic and all dependent future paths')
    req['at']=700;again=W.response(req)
    check(again['proof']['observed']==f['proof']['observed'],'later M5 preserves the established fact')
    req['at']=970;late=W.response(req)
    check(late['status']=='FACT_YES' and late['proof']['observed']==f['proof']['observed'],'an established fact survives the block end without a new future percentage')
    req['at']=665;early=W.response(req)
    check(early['status']=='BEFORE_TARGET' and 'proof' not in early,'replay before pin time does not issue a retroactive target answer')
    req['at']=670;req['date']='2026-01-01'
    check(W.response(req)['status']=='OUT_OF_SCOPE','closed 2026 tape cannot be opened through continuation API')
    # since 2026-10-21 the proposed edition also holds the two estimands of the candidate DR-LAB-PB-0.1 (tests/pullbacks24.py)
    check(len(C.registry()['estimands'])==53 and len([e for e in I.review_gate().registry()['estimands'] if not e['id'].startswith('EST:PB-')])==60,'accepted 53-estimand registry is separate from 60-estimand proposed candidate registry')
    print('ALL GOOD; elapsed',round(time.perf_counter()-started,2),'s',flush=True)


if __name__=='__main__':main()
