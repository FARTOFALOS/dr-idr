"""Independent reference for the approved time x SD plan.

Reads the already independently verified PB witnesses and accepted FINAL-X records. Reconstructs region sets,
finite cores, projection targets and post-L chains without importing the production time_sd235 implementation.
PB ambiguity is rederived by the existing explicit-path reference, not by the production uncertainty rectangles.
"""
from __future__ import annotations
import hashlib
import json
import math
from collections import defaultdict, OrderedDict
from functools import lru_cache
import pullbacks_ref as PR

VERSION='DR-LAB-TIME-SD-1.0'
_UNC=OrderedDict()


def r_uncertainty(p, scale):
    key=(p['context']['snapshot_id'],p['context']['code_revision'],scale)
    if key not in _UNC:
        members={w['id']:w for w in p['sessions']}
        src={cid:(w['bars'],w['act_i'],w['w']) for cid,w in members.items()}
        eps={cid:PR.episodes_of(w['bars'],p['first_i'],w['act_i'],w['oppv'],6) for cid,w in members.items()}
        pts={(q['case'],q['i'],q['v']):{'kt':q['kt']} for q in p['points']}
        _UNC[key]=PR.possible_by_case(eps,src,pts,members,scale,p['grid'],p['context']['formed'])
        while len(_UNC)>12:_UNC.popitem(last=False)
    return _UNC[key]


def in_box(k,b,box):
    lo,hi,start,end=box
    return (lo is None or lo<=k) and (hi is None or k<hi) and (start is None or start<=b) and (end is None or b<end)


def tick_room(lo,hi,w):
    return lo is None or hi is None or (hi*w-1)//10 >= -((-lo*w)//10)


def possible_r(cells,box,w):
    lo,hi,start,end=box
    if not tick_room(lo,hi,w):return False
    for item in cells.items:
        if len(item)==2 and in_box(item[0],item[1],box):return True
        if len(item)==3 and (start is None or item[2]>=start) and (end is None or item[2]<end):
            if item[0]=='*':return True
            # A downward half-plane. Check the intersection, including price cells narrower than a tick.
            top=min(hi,item[1]+1) if hi is not None else item[1]+1
            if (lo is None or lo<top) and tick_room(lo,top,w):return True
    return False


def possible_x(m,grid,formed,box):
    if m['X']['s']!='unknown':return False
    lo,hi,start,end=box
    if not tick_room(lo,hi,m['w']):return False
    observed=[q[1] for T,q in zip(grid,m['path']) if T>m['act'] and q is not None]
    maximum=max(observed) if observed else None
    previous_max=False
    for T,row in zip(grid,m['path']):
        if T<=m['act']:continue
        b=(T-5-formed)//15
        eligible=(start is None or b>=start) and (end is None or b<end)
        if row is None and eligible:
            low_tick=maximum+int(previous_max) if maximum is not None else None
            if lo is not None:low_tick=max(low_tick,-((-lo*m['w'])//10)) if low_tick is not None else -((-lo*m['w'])//10)
            high_tick=(hi*m['w']-1)//10 if hi is not None else None
            if low_tick is None or high_tick is None or low_tick<=high_tick:return True
        if row is not None and row[1]==maximum:
            if eligible and not previous_max and in_box((10*maximum)//m['w'],b,box):return True
            previous_max=True
    return False


def tables(p,fam,scale):
    f=p['context']['formed']
    return {'R':[dict(q) for q in p['points'] if q['kt']>=scale],
            'X':[dict(id=m['id']+'|FINAL-X',case=m['id'],v=m['X']['v'],open=m['X']['t'],
                      k=(10*m['X']['v'])//m['w'],b=(m['X']['t']-f)//15,episodes=[])
                 for m in fam['members'] if m['X']['s']=='known']}


def region_reference(ev,pts,box,p,fam,unc):
    yes=set();late=set()
    for q in pts:
        if in_box(q['k'],q['b'],box):
            yes.add(q['case'])
            if q['open']+5>p['context']['cut']:late.add(q['case'])
    unknown=[]
    for m in fam['members']:
        if m['id'] in yes:continue
        hit=possible_r(unc[m['id']],box,m['w']) if ev=='R' and m['id'] in unc else possible_x(m,fam['grid'],p['context']['formed'],box) if ev=='X' else False
        if hit:unknown.append(m['id'])
    return (sorted(yes),sorted(unknown),len(yes),len(unknown),len(yes-late),len(late))


def core_centres(pts,N,first,last):
    # Direct query of cases per rectangular footprint, not a dilation, convolution or connected region.
    anchors=sorted({(q['k']+off,q['b']) for q in pts for off in [-1,0,1] if first<=q['b']<=last},key=lambda c:(c[1],c[0]))
    @lru_cache(None)
    def n(k,b):return len({q['case'] for q in pts if first<=b<=last and q['b']==b and k-1<=q['k']<=k+1})
    candidates=[]
    for k,b in anchors:
        support=n(k,b)
        if support<max(4,(N+19)//20):continue
        if any(n(kk,bb)>support for kk in range(k-1,k+2) for bb in range(b-1,b+2)):continue
        candidates.append((k,b,support))
    groups=[]
    for item in candidates:
        if groups and groups[-1][-1][1:]==item[1:] and groups[-1][-1][0]+1==item[0]:groups[-1].append(item)
        else:groups.append([item])
    keep=[sorted(g,key=lambda q:(abs(2*q[0]+1),q[0]))[0] for g in groups]
    return sorted(keep,key=lambda q:(q[1],-q[2],abs(2*q[0]+1),q[0]))


def following_reference(source,target,pts,p):
    sb=[source[k] for k in ('k0','k1','b0','b1')];tb=[target[k] for k in ('k0','k1','b0','b1')]
    formed=p['context']['formed'];yes=[];unknown=[];eligible=[];witnesses=[]
    for w in p['sessions']:
        source_points=[q for q in pts if q['case']==w['id'] and in_box(q['k'],q['b'],sb)]
        reached=None;missing=False;has_time=False
        for point in source_points:
            for index,T in enumerate(p['grid']):
                b=(T-5-formed)//15
                if T<=point['open']+5 or (tb[2] is not None and b<tb[2]) or (tb[3] is not None and b>=tb[3]):continue
                if not tick_room(tb[0],tb[1],w['w']):continue
                has_time=True;row=w['bars'][index]
                if row is None:missing=True;continue
                low_ok=tb[0] is None or row[1]*10>=tb[0]*w['w']
                high_ok=tb[1] is None or row[2]*10<tb[1]*w['w']
                if low_ok and high_ok:
                    reached=dict(case=w['id'],point_id=point['id'],l_open=point['open'],target_open=T-5,target_close=T);break
            if reached:break
        if has_time:eligible.append(w['id'])
        if reached:yes.append(w['id']);witnesses.append(reached);continue
        if missing:unknown.append(w['id']);continue
        if w['id'] not in source['possible'] or not tick_room(tb[0],tb[1],w['w']):continue
        earliest=max(w['act']+5,formed+15*source['b0']+5)
        may_reach=False
        for T,row in zip(p['grid'],w['bars']):
            b=(T-5-formed)//15
            if T<=earliest or (tb[2] is not None and b<tb[2]) or (tb[3] is not None and b>=tb[3]):continue
            if row is None or ((tb[0] is None or row[1]*10>=tb[0]*w['w']) and (tb[1] is None or row[2]*10<tb[1]*w['w'])):may_reach=True;break
        if may_reach:unknown.append(w['id'])
    return dict(members=sorted(yes),possible=sorted(set(unknown)-set(yes)),n_known=len(yes),n_possible=len(set(unknown)-set(yes)),
                eligible=sorted(eligible),witnesses=witnesses)


def check(p,fam,requested=None,linked=None):
    errors=[];checked=0;ts=p.get('time_sd') or {};scale=ts.get('scale');ctx=p['context']
    def ck(ok,why):
        nonlocal checked
        checked+=1
        if not ok:errors.append(why)
    ck(ts.get('version')==VERSION,'version')
    original={k:v for k,v in p.items() if k not in ('time_sd','time_sd_source')}
    ck(hashlib.sha256(json.dumps(original,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()==p.get('time_sd_source'),'unchanged verified source proof')
    ck(scale in (1,2,3,6),'scale')
    if errors:return dict(outcome='FAIL',errors=errors,checked=checked)
    ck(ts.get('definition')==dict(time_minutes=15,price_cells=3,price_cell_num=1,price_cell_den=10,atom_minutes=5,min_abs=4,min_frac_num=1,min_frac_den=20,projection='MAX_KNOWN_JOINT_CELL',temporal_growth=False),'frozen definition')
    pts=tables(p,fam,scale);unc=r_uncertainty(p,scale)
    rkeys=('members','possible','n_known','n_possible','earlier','later')
    first=(fam['key']['window'][0]-ctx['formed'])//15;last=(ctx['end']-5-ctx['formed'])//15
    for ev in ('R','X'):
        m=ts.get('maps',{}).get(ev,{})
        ck(m.get('event')==('PB_L' if ev=='R' else 'FINAL_X'),ev+' event identity')
        ck(m.get('points')==pts[ev],ev+' source points')
        ck(m.get('need')==max(4,(ctx['N']+19)//20),ev+' minimum support')
        cells=sorted({(q['k'],q['b']) for q in pts[ev]},key=lambda q:(q[1],q[0]))
        ck([(v['k'],v['b']) for v in m.get('cells',[])]==cells,ev+' joint cell coverage')
        ms=[]
        for k,t in sorted({(q['k'],q['open']) for q in pts[ev]},key=lambda q:(q[1],q[0])):
            ids=sorted({q['case'] for q in pts[ev] if q['k']==k and q['open']==t})
            ms.append(dict(k=k,open=t,members=ids,n_known=len(ids)))
        ck(m.get('m5')==ms,ev+' M5 cells')
        centres=core_centres(pts[ev],ctx['N'],first,last)
        ck([tuple(z['anchor'])+(z['apex_D'],) for z in m.get('cores',[])]==centres,ev+' core centres')
        for index,z in enumerate(m.get('cores',[])):
            k,b=z['anchor'];box=[k-1,k+2,b,b+1]
            ck([z[n] for n in ('k0','k1','b0','b1')]==box and z['cell_mask']==[[j,b] for j in range(k-1,k+2)],ev+' finite core mask')
            ck((z['price_low'],z['price_high'],z['time_start'],z['time_end'])==(k-1,k+2,ctx['formed']+15*b,ctx['formed']+15*(b+1)),ev+' core bounds')
            zid=hashlib.sha1(f"{VERSION}|{fam['snapshot_id']}|{ev}|{scale if ev=='R' else 0}|{k}|{b}".encode()).hexdigest()[:16]
            ck(z['zone_id']==zid and z['label']==ev+str(index+1),ev+' core identity')
            use=[q for q in pts[ev] if in_box(q['k'],q['b'],box)]
            links={eid for q in use for eid in q['episodes']};epis={e['id'] for e in p['episodes'] if e['kt']>=scale}
            ck(z['n_points']==len(use) and z['n_episodes']==len(links&epis),ev+' core witness counts')
        for axis in ('price','time'):
            coordinate=0 if axis=='price' else 1
            expected=[]
            for index in sorted({c[coordinate] for c in cells}):
                pool=[c for c in cells if c[coordinate]==index]
                def rank(c):
                    support=len({q['case'] for q in pts[ev] if (q['k'],q['b'])==c})
                    return (-support,c[1]) if axis=='price' else (-support,abs(2*c[0]+1),c[0])
                k,b=min(pool,key=rank);expected.append((axis,index,k,k+1,b,b+1))
            ck([tuple(v[n] for n in ('axis','index','k0','k1','b0','b1')) for v in m.get(axis+'_peaks',[])]==expected,ev+' '+axis+' peak selection')
        for v in m.get('cores',[])+m.get('cells',[])+m.get('price_peaks',[])+m.get('time_peaks',[])+m.get('regions',[]):
            box=[v[n] for n in ('k0','k1','b0','b1')]
            ck(tuple(v[n] for n in rkeys)==region_reference(ev,pts[ev],box,p,fam,unc),ev+' membership/unknown/clock '+str(box))
        expected_regions={(k,k+1,None,None) for k,_ in cells}|{(None,k+1,None,None) for k,_ in cells}|{(k,None,None,None) for k,_ in cells}|{(None,None,b,b+1) for b in range((ctx['end']-ctx['formed'])//15)}
        if requested is not None:expected_regions|={tuple(requested),(requested[0],requested[1],None,None),(None,None,requested[2],requested[3])}
        ck({tuple(v[n] for n in ('k0','k1','b0','b1')) for v in m.get('regions',[])}==expected_regions,ev+' region coverage')
        known={q['case'] for q in pts[ev]};inz={cid for z in m.get('cores',[]) for cid in z['members']}
        unknown=set(unc)-known if ev=='R' else {v['id'] for v in fam['members'] if v['X']['s']=='unknown'}
        cats=dict(IN_ZONES=len(inz),OUTSIDE=len(known-inz),UNKNOWN=len(unknown),NONE=ctx['N']-len(known)-len(unknown))
        ck(m.get('sessions')==cats,ev+' categories')
    sources={z['zone_id']:z for z in ts['maps']['R']['cores']};targets={z['zone_id']:z for z in ts['maps']['X']['cores']}
    expected_links={(s,t) for s in sources for t in targets}
    if linked:expected_links.add((linked['source_id'],'selected'))
    ck({(v['source_id'],v['target_id']) for v in ts.get('links',[])}==expected_links,'linked path coverage')
    for link in ts.get('links',[]):
        source=sources.get(link['source_id']);target=targets.get(link['target_id'])
        if link['target_id']=='selected' and linked:target=dict(zip(('k0','k1','b0','b1'),linked['region']))
        if not source or not target:ck(False,'linked source/target identity');continue
        ck(all(link[k]==target[k] for k in ('k0','k1','b0','b1')),'linked target region')
        expected=following_reference(source,target,pts['R'],p)
        ck(all(link[k]==expected[k] for k in expected),'same-episode post-L witnesses')
    # Core-relative today facts: recompute against the same verified closed prefix, with the NEW finite masks.
    T=p['today'];formed=ctx['formed'];cut=ctx['cut']
    for ev in ('R','X'):
        actual=ts.get('today',{}).get(ev,[]);cores=ts['maps'][ev]['cores']
        ck(len(actual)==len(cores),ev+' today core coverage')
        for z,a in zip(cores,actual):
            mask=set(map(tuple,z['cell_mask']));eligible=[];reached=[];gap=False
            for close,row in zip(p['grid'],T['bars']):
                b=(close-5-formed)//15
                if close<=T['act'] or not any(bb==b for _,bb in mask):continue
                eligible.append(close)
                if row is None:gap=True
                elif any(bb==b and tick_room(k,k+1,T['w']) and row[1]*10>=k*T['w'] and row[2]*10<(k+1)*T['w'] for k,bb in mask):reached.append(close)
            end=cut>=z['time_end'];clock='AHEAD' if cut<=z['time_start'] else 'PAST' if end else 'CURRENT'
            v=dict(state='VISITED' if reached else 'UNKNOWN' if gap else 'NO_PERIOD' if end and not eligible else 'MISSED' if end else 'PENDING',close=min(reached) if reached else None,eligible=len(eligible))
            history='FUTURE_PRESENT' if z['later'] else 'PAST_ONLY' if end else 'FUTURE_EMPTY'
            comp={'state':'NONE'};status='POSSIBLE'
            if ev=='R':
                es=[e for e in T['episodes'] if e['kt']>=scale and e.get('L') is not None and (e['k'],e['cb']) in mask]
                done=sorted((e for e in es if e['status']=='KNOWN'),key=lambda e:e['b_close'])
                wait=[e for e in es if e['status']=='NOT_YET']
                if done:comp=dict(state='COMPLETED',b_close=done[0]['b_close'],h_open=done[0]['h_open'])
                elif wait:comp=dict(state='IN_ZONE_NOT_UPDATED',h_open=max(e['h_open'] for e in wait))
            else:
                rows=[(close,row) for close,row in zip(p['grid'],T['bars']) if close>T['act']]
                if any(row is None for _,row in rows):status='STATUS_UNKNOWN'
                else:
                    peak=max((row[1] for _,row in rows),default=None)
                    first=next((close for close,row in rows if row[1]==peak),None)
                    location=((10*peak)//T['w'],(first-5-formed)//15) if first is not None else None
                    if location in mask:status='HOLDS'
                    else:status='POSSIBLE' if any((peak is None or (k+1)*T['w']>10*peak) and formed+15*b+10>=cut and formed+15*b<=ctx['end']-5 for k,b in mask) and cut<=ctx['end']-5 else 'IMPOSSIBLE'
            ck(a==dict(zone_id=z['zone_id'],clock=clock,history_clock=history,visit=v,completion=comp,status=status),ev+' today joint place/completion/finality')
    return dict(outcome='FAIL' if errors else 'PASS',errors=errors,checked=checked)
