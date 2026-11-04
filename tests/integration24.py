"""End-to-end semantic tests of integrated scenes. No market data or issue store is written."""
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab'))
import contract as C
import integration24 as I
import integration_audit as A
import now24 as N
import scene24 as S
from revisions24 import path_revision

def check(ok,text):
    print(('PASS ' if ok else 'FAIL ')+text,flush=True)
    if not ok: raise AssertionError(text)

def scene(cut,date='2025-12-10',scope='all',view='auto',trials=('pre','arrive')):
    return I.scene('NQ','RDR',cut,date,view,scope,trials)

def main():
    check(C.EDITION=='DR-LAB-SC-1.1' and len(C.registry()['estimands'])==53,'normal contract is the accepted 53-estimand edition')
    g=I.review_gate()
    ed=next(e for e in g.registry()['editions'] if e['id']==g.EDITION)
    check(g is not C and ed['edition_status']=='PROPOSED' and not ed.get('acceptances') and len([e for e in g.registry()['estimands'] if not e['id'].startswith(('EST:PB-','EST:TS-'))])==60,'candidate gate preserves the original continuation set separately from later PB/TS; no acceptance is inferred')
    p=scene(635,'2025-12-17'); check(p['candidates']['pre']['status']=='ok' and not p['family'].get('N'),'preconfirmation uses PRE without inventing BASE family')
    check(p['candidates']['pre']['contract']['status']=='CONFORMANT','PRE rederived by its own reference gate')
    start=scene(660); check(start['candidates']['arrive']['status']=='NO_PREFIX','activating M5 is excluded from ARRIVE prefix')
    a,b=scene(665),scene(670)
    check(a['family']['snapshot_id']==b['family']['snapshot_id'] and a['family']['members']==b['family']['members'],'BASE snapshot and outcomes unchanged on the next M5')
    check(a['context']['prefix_revision']!=b['context']['prefix_revision'] and a['context']['id']!=b['context']['id'],'new prefix is a new publication context')
    reached=scene(680)
    check(all(x['state']['status']=='RESOLVED' and 'counts' not in x for x in reached['candidates']['arrive']['places']),'reached places withdraw future percentages')
    check(all(x['reached']=='YES' and x['bar_close']==x['available_at'] and x['bar_open']==x['bar_close']-5 for x in reached['target_facts'].values()),'fact records distinguish bar interval and knowledge close')
    broken,original,end=scene(870,scope='weekday'),scene(870,scope='weekday',view='conf'),scene(960)
    check(broken['family']['view']=='brk' and original['family']['view']=='conf' and broken['family']['family_id']!=original['family']['family_id'],'DR break switches to separate family; original is explicitly accessible')
    check(original['now']['status']=='FROZEN_AT_BREAK' and original['now']['cut']['cut']==original['family']['today']['brk']-5,'original NOW remains frozen at the last close before the break')
    check(broken['candidates']['arrive']['status']=='DR_BROKEN' and original['candidates']['arrive']['status']=='DR_BROKEN','return to original family cannot resurrect intact-DR Q1')
    check(any(f['reached']=='YES' for f in broken['target_facts'].values()) and any(f['reached']=='YES' for f in end['target_facts'].values()),'observed target fact survives DR break and block end')
    few=scene(670,'2025-12-17','weekday')
    check(all(p['publication']=='WITHHELD_FEW_SESSIONS' for p in few['candidates']['arrive']['places']) and not few['candidates']['arrive']['contract']['bundles'],'small ARRIVE support withholds statistics without widening')
    check(broken['family']['N']<20 and bool(broken['family']['contract']['bundles']),'small nonempty BASE break family retains its published shares')
    off=scene(670,'2025-12-17',trials=())
    check(not off['candidates'],'review candidates are independently opt-in')
    adr=I.scene('NQ','ADR',0,'2025-12-17','auto','weekday',('arrive',))
    check(adr['candidates']['arrive']['status']=='OUT_OF_SCOPE' and not adr['target_facts'],'ADR remains outside the ARRIVE review profile')
    # Same member list object/id, changed valid intermediate close: the full path consumer must not alias.
    fam=copy.deepcopy(b['family']); before=path_revision(fam); old=N._member_series(fam)
    changed=False
    for i,m in enumerate(fam['members']):
        for j,q in enumerate(m['path']):
            if q and q[0]<q[1] and fam['grid'][j]>m['act']:
                alt=q[0] if q[2]!=q[0] else q[1]
                q[2]=alt; changed=True; break
        if changed: break
    new=N._member_series(fam)
    check(changed and before!=path_revision(fam) and old is not new and old[0]['clr'][i,j]!=new[0]['clr'][i,j],'path correction invalidates NOW cache even when BASE snapshot id stays the same')
    # Future-only target mutation: calculations and all selection inputs at the old cut stay identical.
    original_day=S.day_view
    def changed_day(inst,date=None):
        d=copy.deepcopy(original_day(inst,date))
        if date=='2025-12-10':
            for q in d['bars']:
                if q[0]+5>670:
                    q[1:5]=[q[1]+1000,q[2]+1000,q[3]+1000,q[4]+1000]
        return d
    S.day_view=changed_day
    try: future=scene(670)
    finally: S.day_view=original_day
    check(future['context']==b['context'] and future['family']['ids']==b['family']['ids'] and future['now']['R']==b['now']['R'] and future['candidates']['arrive']['places']==b['candidates']['arrive']['places'],'replaced target future cannot change the cut answer or analogue selection')
    audit=A.audit(scene(670,'2025-12-17'),dict(instrument='NQ',session='RDR',date='2025-12-17',scope='all',view='auto'))
    check(audit['status']=='PASS_SCOPED' and any(x['status']=='PASS' for x in audit['bundle_checks']) and audit['relations']['outcome']=='PASS','actual scene reuses Trace/FOM recounts and relation checks with explicit coverage')
    bad=scene(670,'2025-12-17');bad['family']['contract']['status']='VIOLATION'
    check(A.audit(bad,dict(instrument='NQ',session='RDR',date='2025-12-17',scope='all',view='auto'))['status']=='FAIL','a failed child envelope cannot receive a scoped PASS certificate')
    counts={x['status']:sum(y['status']==x['status'] for y in audit['bundle_checks']) for x in audit['bundle_checks']}
    print('Trace coverage',counts,'full catalog explicitly not rebound',flush=True)
    print('ALL GOOD',flush=True)

if __name__=='__main__': main()
