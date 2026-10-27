"""23.5, approved 2026-10-22 plan: local time x SD cores and peak projections.

PB-L and FINAL-X remain named outcomes. F is immutable; one case votes once in a region.
No temporal dilation/connected-component growth: every core is exactly 0.3 IDR x 15 minutes.
The old PB packet is retained as verified source evidence; only EST:TS-* describes the new carriers.
"""
from __future__ import annotations
from collections import defaultdict, OrderedDict
import copy
import hashlib
import json
import math
from pathlib import Path
import threading

import contract as C
import integration24 as I
import pullbacks24 as P
import scene24 as S

VERSION = "DR-LAB-TIME-SD-1.0"
PROFILE = "PROFILE:TIME-SD-235"
ROUTE = "/api/integration/time-sd"
CODE_REVISION = hashlib.sha256(b"".join((Path(__file__).parent / f).read_bytes().replace(b"\r\n", b"\n")
    for f in ("time_sd235.py", "time_sd235_ref.py", "pullbacks24.py", "pullbacks_ref.py"))).hexdigest()
_lock = threading.RLock()
_OUT = OrderedDict()


def bounds(value):
    if value is None: return None
    if isinstance(value, str): value = json.loads(value)
    if not isinstance(value, list) or len(value) != 4 or any(v is not None and (type(v) is not int or abs(v) > 100000) for v in value):
        raise ValueError("region: four integer or null bounds")
    if any(value[i] is not None and value[i + 1] is not None and value[i] >= value[i + 1] for i in (0, 2)):
        raise ValueError("region: lower bound must precede upper bound")
    return value


def inside(q, box):
    a, z, b, e = box
    return (a is None or q["k"] >= a) and (z is None or q["k"] < z) and (b is None or q["b"] >= b) and (e is None or q["b"] < e)


def x_possible(fam):
    """Possible FINAL-X cells: first observed maximum, or a missing eligible M5 at/above all observed highs.
    Bounds are in integer SD cells; region membership additionally requires an actual exchange tick."""
    result = {}
    formed = fam["schedule"]["formed"]
    for m in fam["members"]:
        if m["X"]["s"] != "unknown": continue
        rows = [(j, T, q) for j, (T, q) in enumerate(zip(fam["grid"], m["path"])) if T > m["act"]]
        known = [q[1] for _, _, q in rows if q is not None]
        hi = max(known) if known else None
        seen = False; rects = []
        for _, T, q in rows:
            b = (T - 5 - formed) // 15
            if q is None:
                v = None if hi is None else hi + int(seen)
                rects.append((b, b, None if v is None else (10 * v) // m["w"], None))
            elif q[1] == hi and not seen:
                k = (10 * hi) // m["w"]
                rects.append((b, b, k, k)); seen = True
        result[m["id"]] = rects
    return result


def possible_hit(rects, box, width):
    a, z, b, e = box
    for rb, re, ra, rz in rects:
        if (b is not None and re < b) or (e is not None and rb >= e): continue
        lo = max(v for v in (a, ra) if v is not None) if a is not None or ra is not None else None
        hi = min(v for v in (z, None if rz is None else rz + 1) if v is not None) if z is not None or rz is not None else None
        if lo is not None and hi is not None:
            if lo >= hi or math.ceil(lo * width / 10) >= math.ceil(hi * width / 10): continue
        return True
    return False


def region(points, possible, widths, box, cut):
    use = [q for q in points if inside(q, box)]
    yes = sorted({q["case"] for q in use})
    late = {q["case"] for q in use if q["open"] + 5 > cut}
    unk = sorted(cid for cid, rects in possible.items() if cid not in yes and possible_hit(rects, box, widths[cid]))
    return dict(k0=box[0], k1=box[1], b0=box[2], b1=box[3], members=yes, possible=unk,
                n_known=len(yes), n_possible=len(unk), earlier=len(yes) - len(late), later=len(late))


def local_centres(points, N, first_b, last_b):
    """Centres are local maxima of unique-case support; neighbour TIMES compare, never join the footprint.
    Equal adjacent maxima in PRICE within a single window get the canonical near-zero representative."""
    cells = defaultdict(set)
    for q in points: cells[q["k"], q["b"]].add(q["case"])
    candidates = {(k + d, b) for k, b in cells for d in (-1, 0, 1) if first_b <= b <= last_b}
    counts = {}
    def density(k, b):
        if not first_b <= b <= last_b: return 0
        key = (k, b)
        if key not in counts: counts[key] = len(set().union(*(cells.get((k + d, b), set()) for d in (-1, 0, 1))))
        return counts[key]
    need = max(4, math.ceil(N / 20))
    peaks = {q for q in candidates if density(*q) >= need and all(
        density(*q) >= density(q[0] + dk, q[1] + db) for dk in (-1, 0, 1) for db in (-1, 0, 1))}
    output = []
    while peaks:
        k, b = min(peaks, key=lambda q: (q[1], q[0])); value = density(k, b)
        run = [(k, b)]; peaks.remove((k, b)); j = k + 1
        while (j, b) in peaks and density(j, b) == value:
            run.append((j, b)); peaks.remove((j, b)); j += 1
        anchor = min(run, key=lambda q: (abs(2 * q[0] + 1), q[0]))
        output.append((anchor[0], anchor[1], value))
    return sorted(output, key=lambda q: (q[1], -q[2], abs(2 * q[0] + 1), q[0])), need


def event_points(proof, fam, scale):
    formed = proof["context"]["formed"]
    return dict(R=[copy.deepcopy(q) for q in proof["points"] if q["kt"] >= scale],
                X=[dict(id=m["id"] + "|FINAL-X", case=m["id"], v=m["X"]["v"], open=m["X"]["t"],
                        k=(10 * m["X"]["v"]) // m["w"], b=(m["X"]["t"] - formed) // 15, episodes=[])
                   for m in fam["members"] if m["X"]["s"] == "known"])


def event_map(ev, points, possible, proof, fam, scale, requested):
    ctx = proof["context"]; cut, N = ctx["cut"], ctx["N"]
    formed, end = ctx["formed"], ctx["end"]
    widths = {m["id"]: m["w"] for m in fam["members"]}
    cache = {}
    def get(box):
        key = tuple(box)
        if key not in cache: cache[key] = region(points, possible, widths, box, cut)
        return copy.deepcopy(cache[key])
    cells = sorted({(q["k"], q["b"]) for q in points}, key=lambda q: (q[1], q[0]))
    joint = [dict(k=k, b=b, **get([k, k + 1, b, b + 1])) for k, b in cells]
    m5 = []
    for k, t in sorted({(q["k"], q["open"]) for q in points}, key=lambda q: (q[1], q[0])):
        ids = sorted({q["case"] for q in points if q["k"] == k and q["open"] == t})
        m5.append(dict(k=k, open=t, members=ids, n_known=len(ids)))
    first_b = (fam["key"]["window"][0] - formed) // 15
    anchors, need = local_centres(points, N, first_b, (end - 5 - formed) // 15)
    cores = []
    for i, (k, b, d) in enumerate(anchors):
        box = [k - 1, k + 2, b, b + 1]; v = get(box)
        use = [q for q in points if inside(q, box)]
        zid = hashlib.sha1(f"{VERSION}|{fam['snapshot_id']}|{ev}|{scale if ev=='R' else 0}|{k}|{b}".encode()).hexdigest()[:16]
        cores.append(dict(**v, zone_id=zid, label=ev + str(i + 1), anchor=[k, b], apex_D=d,
                          cell_mask=[[j, b] for j in range(k - 1, k + 2)], n_points=len(use),
                          n_episodes=len({e for q in use for e in q["episodes"] if next((p["kt"] for p in proof["episodes"] if p["id"]==e), 0)>=scale}),
                          price_low=k-1, price_high=k+2, time_start=formed+15*b, time_end=formed+15*(b+1)))
    price = []
    for k in sorted({q["k"] for q in joint}):
        chosen = min((q for q in joint if q["k"] == k), key=lambda q: (-q["n_known"], q["b"]))
        price.append(dict(axis="price", index=k, **get([k,k+1,chosen["b"],chosen["b"]+1])))
    time = []
    for b in sorted({q["b"] for q in joint}):
        chosen = min((q for q in joint if q["b"] == b), key=lambda q: (-q["n_known"],abs(2*q["k"]+1),q["k"]))
        time.append(dict(axis="time", index=b, **get([chosen["k"],chosen["k"]+1,b,b+1])))
    # Full-band/whole-window queries are retained as their own named question, never fed to a peak carrier.
    regions = []
    for k in sorted({q["k"] for q in points}):
        for box in ([k,k+1,None,None],[None,k+1,None,None],[k,None,None,None]): regions.append(get(box))
    for b in range((end-formed)//15): regions.append(get([None,None,b,b+1]))
    if requested is not None:
        for box in (requested,[requested[0],requested[1],None,None],[None,None,requested[2],requested[3]]):
            v=get(box)
            if not any(all(v[n]==p[n] for n in ('k0','k1','b0','b1')) for p in regions):regions.append(v)
    union = {cid for z in cores for cid in z["members"]}
    known = {q["case"] for q in points}; unknown = set(possible) - known
    cats = dict(IN_ZONES=len(union), OUTSIDE=len(known-union), UNKNOWN=len(unknown), NONE=N-len(known)-len(unknown))
    return dict(event="PB_L" if ev=="R" else "FINAL_X", need=need, points=points, m5=m5, cells=joint, cores=cores,
                price_peaks=price, time_peaks=time, regions=regions, sessions=cats)


def following(source, target, points, possible, proof):
    """A true joint chain from a core's own L, on subsequent complete M5 bars. Full F denominator.
    A target's unrelated FINAL-X event/members never enter this calculation."""
    sbox=[source[k] for k in ('k0','k1','b0','b1')]
    tbox=[target[k] for k in ('k0','k1','b0','b1')]
    formed=proof['context']['formed']; grid=proof['grid']; known=defaultdict(list)
    for q in points:
        if inside(q,sbox):known[q['case']].append(q)
    yes=[];unknown=[];witnesses=[];eligible=[]
    for w in proof['sessions']:
        cid=w['id']; lows=known.get(cid,[]); hit=None; missed=False; period=False
        if tbox[0] is not None and tbox[1] is not None and math.ceil(tbox[0]*w['w']/10)>=math.ceil(tbox[1]*w['w']/10):continue
        for q in lows:
            for j,T in enumerate(grid):
                b=(T-5-formed)//15
                if T-5<q['open']+5 or (tbox[2] is not None and b<tbox[2]) or (tbox[3] is not None and b>=tbox[3]):continue
                period=True;bar=w['bars'][j]
                if bar is None:missed=True;continue
                if (tbox[0] is None or 10*bar[1]>=tbox[0]*w['w']) and (tbox[1] is None or 10*bar[2]<tbox[1]*w['w']):
                    hit=dict(case=cid,point_id=q['id'],l_open=q['open'],target_open=T-5,target_close=T);break
            if hit:break
        if period:eligible.append(cid)
        if hit:yes.append(cid);witnesses.append(hit);continue
        if missed:unknown.append(cid);continue
        # Unresolved source membership can widen only a temporally possible chain with an observed/missing target bar.
        if cid not in source['possible']:continue
        earliest=max(w['act']+5,formed+15*source['b0']+5)
        for j,T in enumerate(grid):
            b=(T-5-formed)//15
            if T-5<earliest or (tbox[2] is not None and b<tbox[2]) or (tbox[3] is not None and b>=tbox[3]):continue
            bar=w['bars'][j]
            if bar is None or ((tbox[0] is None or 10*bar[1]>=tbox[0]*w['w']) and (tbox[1] is None or 10*bar[2]<tbox[1]*w['w'])):
                unknown.append(cid);break
    return dict(source_id=source['zone_id'],target_id=target.get('zone_id','selected'),**dict(zip(('k0','k1','b0','b1'),tbox)),
                members=sorted(yes),possible=sorted(set(unknown)-set(yes)),n_known=len(yes),n_possible=len(set(unknown)-set(yes)),
                eligible=sorted(eligible),witnesses=witnesses)


def today_cores(proof,fam,maps,scale):
    from zonemap24 import status as x_status
    T=proof['today'];grid=proof['grid'];formed=proof['context']['formed'];cut=T['cut'];out={}
    for ev,m in maps.items():
        values=[]
        for z in m['cores']:
            cells={tuple(c) for c in z['cell_mask']};hit=None;gap=False;eligible=0
            for j,bar in enumerate(T['bars']):
                close=grid[j];b=(close-5-formed)//15
                if close<=T['act'] or not any(cb==b for _,cb in cells):continue
                eligible+=1
                if bar is None:gap=True;continue
                if any(cb==b and math.ceil(k*T['w']/10)<math.ceil((k+1)*T['w']/10) and 10*bar[1]>=k*T['w'] and 10*bar[2]<(k+1)*T['w'] for k,cb in cells):
                    if hit is None:hit=close
            ended=cut>=z['time_end'];clock='AHEAD' if cut<=z['time_start'] else 'PAST' if ended else 'CURRENT'
            visit=dict(state='VISITED' if hit is not None else 'UNKNOWN' if gap else 'NO_PERIOD' if ended and not eligible else 'MISSED' if ended else 'PENDING',close=hit,eligible=eligible)
            history_clock='FUTURE_PRESENT' if z['later'] else 'PAST_ONLY' if ended else 'FUTURE_EMPTY'
            completion=dict(state='NONE');status='POSSIBLE'
            if ev=='R':
                done=[e for e in T['episodes'] if e['status']=='KNOWN' and e['kt']>=scale and (e['k'],e['cb']) in cells]
                waiting=[e for e in T['episodes'] if e['status']=='NOT_YET' and e['kt']>=scale and e.get('L') is not None and (e['k'],e['cb']) in cells]
                if done:
                    e=min(done,key=lambda e:e['b_close']);completion=dict(state='COMPLETED',b_close=e['b_close'],h_open=e['h_open'])
                elif waiting:completion=dict(state='IN_ZONE_NOT_UPDATED',h_open=max(e['h_open'] for e in waiting))
            else:
                old=fam['today']['zones']['X']
                status='STATUS_UNKNOWN' if old['state']=='unknown' else x_status(z['cell_mask'],'X',tuple(old['q']) if old.get('q') else None,old.get('v10'),T['w'],cut,formed,proof['context']['end']-5)
            values.append(dict(zone_id=z['zone_id'],clock=clock,history_clock=history_clock,visit=visit,completion=completion,status=status))
        out[ev]=values
    return out


def derive(proof, fam, scale=1, requested=None, linked=None):
    points=event_points(proof,fam,scale)
    poss=dict(R=P.uncertainty(proof,fam,scale),X=x_possible(fam))
    maps={ev:event_map(ev,points[ev],poss[ev],proof,fam,scale,requested) for ev in ('R','X')}
    links=[following(z,t,points['R'],poss['R'],proof) for z in maps['R']['cores'] for t in maps['X']['cores']]
    if linked:
        z=next((z for z in maps['R']['cores'] if z['zone_id']==linked['source_id']),None)
        if z is None:raise ValueError('link source is not a core of this snapshot')
        target=dict(zip(('k0','k1','b0','b1'),linked['region']))
        links.append(following(z,target,points['R'],poss['R'],proof))
    return dict(version=VERSION,scale=scale,definition=dict(time_minutes=15,price_cells=3,price_cell_num=1,price_cell_den=10,
        atom_minutes=5,min_abs=4,min_frac_num=1,min_frac_den=20,projection='MAX_KNOWN_JOINT_CELL',temporal_growth=False),
        maps=maps,links=links,today=today_cores(proof,fam,maps,scale))


def publish(proof, fam, upstream, check):
    gate=I.review_gate();ctx=proof['context'];N=ctx['N'];ts=proof['time_sd'];scale=ts['scale']
    env=gate.Envelope(ROUTE,PROFILE,dict(instrument=ctx['instrument'],session=ctx['session'],date=ctx['date'],cut=ctx['cut'],scale=scale))
    env.check('PB source independently verified by pullbacks_ref',upstream['contract']['status']=='CONFORMANT')
    env.check('time-SD cores, peaks, membership, clocks and linked paths independently re-derived',check['outcome']=='PASS',check.get('checked'))
    if check['outcome']!='PASS':
        env.violate('TIME_SD_REFERENCE_MISMATCH',['P1','V2'], '; '.join(check['errors'][:5]),withheld=['TIME_SD'])
        return dict(status='REFERENCE_MISMATCH',contract=env.finish(),message='Расчёт времени и SD не подтвердился: слой снят')
    # Source PB bundles keep their own estimands and upstream release identity. They are evidence, not TS carriers.
    env.bundles=copy.deepcopy(upstream['contract']['bundles'])
    release=P.revision(proof);sid=ctx['snapshot_id'];cs=ctx['case_set']
    inputs=gate._inputs(fam,[dict(input_kind='CODE',ref=VERSION,version=CODE_REVISION),dict(input_kind='PARAMETERS',ref='release',version=release)])
    def add(est,v,kind,extra=None):
        n,u=v['n_known'],v['n_possible']
        estimates=[dict(estimator=est.replace('EST:','ESTR:'),value_kind='POINT',value=n/N,numerator=n,denominator=N,unit='share of N_base')]
        if u:estimates.append(dict(estimator=est.replace('EST:','ESTR:'),value_kind='BOUNDS',lower=n/N,upper=(n+u)/N,denominator=N,unit='share of N_base'))
        pars=dict(scale=scale,kind=kind,release=release,**{k:v.get(k) for k in ('k0','k1','b0','b1')},**(extra or {}))
        env.bundle(est,cs,sid,'lab/time_sd235.py::'+kind,inputs,estimates,
            [dict(case_set=sid,n_base=N,components=[dict(component='MEMBERSHIP',of=N,yes=n,unknown=u,no=N-n-u)])],
            dict(yes=n,unknown=u,N=N,scale=scale,label=v.get('label',''),kind=kind),parameters=pars)
    for ev,m in ts['maps'].items():
        for z in m['cores']:add('EST:TS-CORE-'+ev,z,'core',dict(zone_id=z['zone_id']))
        for axis in ('price','time'):
            for v in m[axis+'_peaks']:add('EST:TS-PEAK-'+ev,v,'peak',dict(axis=axis,index=v['index']))
        for v in m['regions']+m['cells']:add('EST:TS-REGION-'+ev,v,'region')
        cats=m['sessions'];est='EST:TS-SESSIONS-'+ev
        env.bundle(est,cs,sid,'lab/time_sd235.py::event_map',inputs,
            [dict(estimator=est.replace('EST:','ESTR:'),value_kind='CATEGORY_SHARES',unit='categories of N_base',denominator=N,categories=[dict(category=k,count=v) for k,v in cats.items()])],
            [dict(case_set=sid,n_base=N,components=[dict(component='CATEGORY',of=N,known=N-cats['UNKNOWN'],unknown=cats['UNKNOWN'])])],
            dict(N=N,in_zones=cats['IN_ZONES'],outside=cats['OUTSIDE'],unknown=cats['UNKNOWN'],none=cats['NONE']),parameters=dict(scale=scale,release=release))
    for v in ts['links']:add('EST:TS-LINK',v,'following',dict(source_id=v['source_id'],target_id=v['target_id']))
    result=dict(status='OK',release_id=release,proof=proof,contract=env.finish(),review=dict(decision='CANDIDATE',implementation='AUTHORIZED_2026-10-22',human_acceptance='PENDING',edition=I.REVIEW_EDITION))
    if result['contract']['status']!='CONFORMANT':return dict(status='CONTRACT_VIOLATION',contract=result['contract'],message='Слой не прошёл контракт')
    return gate.finalize(ROUTE,result)


def response(params):
    if str(params.get('scale','1')) not in ('1','2','3','6'):raise ValueError('scale: 1 | 2 | 3 | 6')
    scale=int(params.get('scale',1));requested=bounds(params.get('region'));linked=None
    if params.get('link'):
        linked=json.loads(params['link'])
        if not isinstance(linked,dict) or not isinstance(linked.get('source_id'),str):raise ValueError('link: source_id and region')
        linked=dict(source_id=linked['source_id'],region=bounds(linked.get('region')))
        if linked['region'] is None:raise ValueError('link requires a target region')
    with _lock:
        upstream=P.response(params)
        if upstream.get('status')!='OK':return upstream
        key=P.revision([upstream['release_id'],scale,requested,linked,CODE_REVISION])
        if key in _OUT:return _OUT[key]
        status,fam,B,day,_=P.build(params.get('instrument','NQ'),params.get('session','RDR'),int(params['at']),
            params.get('date') or None,params.get('view','auto'),params.get('scope','weekday'),requested)
        if status!='OK':return dict(status=status,message='Семья изменилась во время расчёта')
        proof=copy.deepcopy(upstream['proof']);proof['time_sd_source']=upstream['release_id']
        proof['time_sd']=derive(proof,fam,scale,requested,linked)
        import time_sd235_ref as ref
        check=ref.check(proof,fam,requested,linked)
        result=publish(proof,fam,upstream,check)
        _OUT[key]=result
        while len(_OUT)>8:_OUT.popitem(last=False)
        return result
