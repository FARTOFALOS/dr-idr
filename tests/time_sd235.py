"""Meaning discriminators for the approved 23.5 plan, then real source-bound releases and fault withdrawal.
No training data or per-case evidence is published by this test.
"""
import copy
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab'))
import time_sd235 as T
import time_sd235_ref as R
import pullbacks24 as P
import contract as C
import integration24 as I

checks=[]
def ck(ok,name):
    if not ok:raise AssertionError(name)
    checks.append(name);print('PASS '+name,flush=True)

def point(cid,k,b,t=None):
    return dict(id=f'{cid}|{k}|{b}|{t}',case=cid,k=k,b=b,open=630+15*b if t is None else t,v=k,kt=1,kn=1,episodes=[])

def model(pts,N=100,cut=630):
    members=[dict(id=str(i),w=10,X=dict(s='none')) for i in range(N)]
    fam=dict(N=N,members=members,snapshot_id='test',key=dict(window=[630,645]))
    proof=dict(context=dict(N=N,formed=630,end=960,cut=cut),episodes=[])
    return T.event_map('R',pts,{},proof,fam,1,None)

def synthetic():
    points=[point(str(i),0,i//5) for i in range(90)]
    a,need=T.local_centres(points,90,0,21)
    ck(a==R.core_centres(points,90,0,21) and len(a)==18 and all(n==5 for _,_,n in a),'90 cases across hours make separate 5-case local cores, never one 90-case constellation')
    m=model(points,90)
    ck(all(z['time_end']-z['time_start']==15 and z['price_high']-z['price_low']==3 for z in m['cores']),'all masks are exactly 15 minutes x 0.3 IDR')
    ck(m['price_peaks'][0]['n_known']==5 and m['price_peaks'][0]['b0']==0 and next(v for v in m['regions'] if v['k0']==0 and v['k1']==1 and v['b0'] is None)['n_known']==90,'price peak retains the earliest strongest TIME cell; full-horizon union is a different count')
    ck(len(m['time_peaks'])==18 and all(v['n_known']==5 and v['k0']==0 for v in m['time_peaks']),'each time peak retains its exact PRICE cell')
    q=[point('one',0,0,630+5*(j%3)) for j in range(7)]
    ck(T.local_centres(q,20,0,2)[0]==[],'seven episodes of one day cannot manufacture the minimum independent support')
    q=[point(str(i),0,0) for i in range(5)]+[point(str(i+5),0,12) for i in range(5)]
    a,_=T.local_centres(q,20,0,21)
    ck(len(a)==2 and {b for _,b,_ in a}=={0,12},'the same price in two distant windows is two distinct joint places')
    q=[point('0',0,0,630),point('0',0,0,640)]
    a=T.region(q,{}, {'0':10},[0,1,0,1],635)
    b=T.region(q,{}, {'0':10},[0,1,0,1],645)
    ck((a['n_known'],a['earlier'],a['later'])==(1,0,1) and (b['n_known'],b['earlier'],b['later'])==(1,1,0),'known clock parts are disjoint even when one case has early and late events')
    ck(not T.possible_hit([(0,0,None,None)],[1,2,0,1],1) and T.possible_hit([(0,0,None,None)],[0,1,0,1],1),'UNKNOWN cannot put a point in an SD cell without an exchange tick')
    for bad in ([True,1,0,1],[1,0,0,1],[0,1,2,1],[0.5,1,0,1],[0,1,0]):
        try:T.bounds(bad);ok=False
        except ValueError:ok=True
        ck(ok,'invalid region rejected: '+str(bad))
    ck(T.bounds([None,None,0,2])==[None,None,0,2],'unbounded price is an explicit joint query, not Infinity or a silent zero')
    # Link witnesses: only bars after the source L M5, and only the same historical case.
    source=dict(zone_id='r',k0=8,k1=9,b0=1,b1=2,possible=[])
    target=dict(zone_id='x',k0=10,k1=11,b0=1,b1=2)
    pts=[point('a',8,1,645)]
    p=dict(context=dict(formed=630),grid=[635,640,645,650,655,660],sessions=[dict(id='a',w=10,act=630,bars=[(8,20,7,9),(9,11,8,9),(9,9,8,8),(8,12,8,9),(9,9,8,9),(9,9,8,9)])])
    link=T.following(source,target,pts,{},p)
    ck(link['n_known']==0 and link['n_possible']==0,'earlier global X and a high inside the L M5 are not post-L continuation')
    p['sessions'][0]['bars'][4]=(9,11,9,10)
    link=T.following(source,target,pts,{},p)
    expected=R.following_reference(source,target,pts,p)
    ck(link['n_known']==1 and link['witnesses'][0]['target_close']==655 and all(link[k]==v for k,v in expected.items()),'same-case later M5 establishes one linked vote, with its actual witness time')
    earlier=dict(target,b0=0,b1=1)
    ck(T.following(source,earlier,pts,{},p)['n_known']==0,'a target window before L cannot be revived by FINAL-X')
    p['sessions'][0]['bars'][4]=None
    link=T.following(source,target,pts,{},p)
    ck(link['n_known']==0 and link['n_possible']==1,'missing post-L target bar widens bounds without a fabricated YES')
    p['sessions'][0]['bars'][4]=(9,9,8,9)
    p['sessions'].append(dict(id='b',w=10,act=630,bars=[(8,20,7,10)]*6))
    ck(T.following(source,target,pts,{},p)['n_known']==0,'an unrelated case reaching X cannot be paired with another case bottom')
    m=dict(id='x',w=10,act=630,X={'s':'unknown'},path=[None,(2,5,3),(2,5,3)])
    fam=dict(members=[m],grid=[635,640,645],schedule=dict(formed=630))
    possible=T.x_possible(fam)['x']
    ck(not T.possible_hit(possible,[0,1,0,1],10) and R.possible_x(m,fam['grid'],630,[5,6,0,1]),'unknown FINAL-X cannot lie below an already observed higher extreme')


def real():
    t=time.monotonic()
    packet=T.response(dict(instrument='NQ',session='RDR',at='670',date='2025-12-17',scope='weekday',view='auto',scale='1'))
    ck(packet.get('status')=='OK','real NQ RDR publishes after independent source and time-SD references: '+str(packet.get('message') or packet.get('contract',{}).get('violations')))
    p=packet['proof'];ts=p['time_sd'];status,fam,B,day,_=P.build('NQ','RDR',670,'2025-12-17','auto','weekday')
    ck(all(z['time_end']-z['time_start']==15 for m in ts['maps'].values() for z in m['cores']),'real broad PB ridge is represented only by finite declared cores')
    ck(all(v['n_known']==max((c['n_known'] for c in m['cells'] if c['k']==v['index']),default=0) for m in ts['maps'].values() for v in m['price_peaks']),'real price-column counts are joint-cell maxima, never sums across times')
    ck(not I.review_gate().undeclared_numbers(T.ROUTE,packet),'every numeric carrier/evidence field has a declared meaning')
    ck(not C.validate(packet['contract'],'ContractEnvelope'),'separate candidate envelope is structurally valid')
    for name,mutate in [
        ('wide core',lambda q:q['time_sd']['maps']['R']['cores'][0]['cell_mask'].append([0,20])),
        ('wrong peak',lambda q:q['time_sd']['maps']['R']['price_peaks'][0].update(b0=20,b1=21)),
        ('duplicate vote',lambda q:q['time_sd']['maps']['R']['cells'][0].update(n_known=999)),
        ('changed source',lambda q:q['points'][0].update(v=q['points'][0]['v']+1)),
        ('missing clock',lambda q:q['time_sd']['maps']['R']['cores'][0].update(earlier=999)),
        ('wrong today window',lambda q:q['time_sd']['today']['R'][0].update(clock='fiction')),
    ]:
        broken=copy.deepcopy(p);mutate(broken);ref=R.check(broken,fam)
        ck(ref['outcome']=='FAIL',name+' is rejected by independent reconstruction')
        withheld=T.publish(broken,fam,packet,ref)
        ck(withheld['status']=='REFERENCE_MISMATCH' and 'proof' not in withheld,name+' withdraws numbers and geometry together')
    later=T.response(dict(instrument='NQ',session='RDR',at='675',date='2025-12-17',scope='weekday',view='auto',scale='1'))
    signature=lambda q:[(ev,[(z['zone_id'],z['members'],z['cell_mask']) for z in m['cores']],[(v['index'],v['k0'],v['b0'],v['members']) for v in m['price_peaks']+m['time_peaks']]) for ev,m in q['proof']['time_sd']['maps'].items()]
    ck(signature(later)==signature(packet),'next M5 preserves F, core geometry and peak target membership')
    selected=T.response(dict(instrument='NQ',session='RDR',at='670',date='2025-12-17',scope='weekday',view='auto',scale='1',region='[-2,1,0,3]'))
    ck(selected.get('status')=='OK' and all(any([v[k] for k in ('k0','k1','b0','b1')]==[-2,1,0,3] for v in m['regions']) for m in selected['proof']['time_sd']['maps'].values()),'selected joint area reaches both source-bound event calculations')
    for scale in (2,3,6):
        release=T.response(dict(instrument='NQ',session='RDR',at='670',date='2025-12-17',scope='weekday',view='auto',scale=str(scale)))
        q=release.get('proof',{}).get('time_sd',{})
        ck(release.get('status')=='OK' and q['scale']==scale and all(pt['kt']>=scale for pt in q['maps']['R']['points']) and q['maps']['X']==ts['maps']['X'],
           'explicit scale '+str(scale)+' selects its own episodes and preserves the FINAL-X map')
    source=ts['maps']['R']['cores'][0]
    linked=T.response(dict(instrument='NQ',session='RDR',at='670',date='2025-12-17',scope='weekday',view='auto',scale='1',link=json.dumps(dict(source_id=source['zone_id'],region=[0,4,5,9]))))
    link=next(v for v in linked['proof']['time_sd']['links'] if v['target_id']=='selected')
    ck(linked['status']=='OK' and link['source_id']==source['zone_id'] and [link[k] for k in ('k0','k1','b0','b1')]==[0,4,5,9] and all(w['target_open']>=w['l_open']+5 for w in link['witnesses']),
       'an arbitrary linked target preserves its source, full-family denominator and same-case chronological witnesses')
    ck(T.response(dict(instrument='NQ',session='RDR',at='670',date='2026-01-01'))['status']=='OUT_OF_SCOPE','closed 2026 history remains closed')
    print('Real reference checks:',round(time.monotonic()-t,2),'seconds',flush=True)


if __name__=='__main__':
    synthetic();real();print('ALL GOOD',len(checks),'checks')
