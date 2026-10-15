"""Atomic continuation publication: estimate + exact cases/paths + source-bound scene.

All raw records remain local. This is a separately registered C1 candidate; no
accepted BASE/NOW calculation, immutable issue or market-data file is changed.
"""
from __future__ import annotations

from collections import Counter, OrderedDict
import copy
import hashlib
import json
from pathlib import Path
import threading

import numpy as np

import continuity24 as E
import continuity_audit as A
import contract as C
import integration24 as I
import now24_validate as V
import scene24 as S

ROOT=Path(__file__).resolve().parents[1]
ROUTE='/api/integration/continuations'
EST='EST:C-WINDOW'
_lock=threading.RLock()
_corpora={}
_releases=OrderedDict()
_publications=OrderedDict()
CODE_REVISION=hashlib.sha256(b''.join((Path(__file__).parent/p).read_bytes().replace(b'\r\n',b'\n') for p in ('continuations24.py','continuity24.py','continuity_audit.py'))).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)


def revision(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def corpus(inst,block):
    b=S._base(inst)
    files=[S.RUNTIME/f'boxes_{inst.lower()}{tail}' for tail in ('.npz','_meta.json')]
    stamp=tuple((p.stat().st_mtime_ns,p.stat().st_size) for p in files)
    key=(inst,block)
    if key in _corpora:
        old, cases, grid=_corpora[key]
        if old!=stamp: raise ValueError('Историческая база обновилась: перезапустите сборку, цель не переносится молча')
        return cases,grid
    cases,grid=V.universe(inst,block,'conf')
    assert all(c['date']<='2025-12-31' for c in cases)
    for c in cases:
        c.update(instrument=inst,block=block)
        m=b['boxes'][b['idx'][(c['date'],block)]]
        c['edge_ticks']=int(m['idr_high'] if c['side']==1 else m['idr_low'])
        c['P'].setflags(write=False)
    _corpora[key]=(stamp,cases,grid)
    return cases,grid


def rows_today(family,day,grid,cut):
    t=family['today']; d=t['side']; tick=E.ratio(day.get('tick') or .25)
    edge=t['idrH'] if d==1 else t['idrL']
    width=t['idrH']-t['idrL']
    P=np.full((len(grid),3),np.nan)
    by={int(b[0])+5:b for b in day['bars'] if int(b[0])+5<=cut}
    for j,T in enumerate(grid):
        if T not in by: continue
        b=by[T]; vals=[int(E.ratio(p)/tick) for p in (b[3],b[2],b[4])]
        e=int(E.ratio(edge)/tick)
        lo,hi=sorted(d*(v-e) for v in vals[:2]); P[j]=[lo,hi,d*(vals[2]-e)]
    return dict(id=f"{family['key']['instrument']}-{day['date']}-{family['key']['session']}",date=day['date'],
                instrument=family['key']['instrument'],block=family['key']['session'],side=d,
                a=(t['c0']-family['schedule']['formed']-5)//5,w=int(E.ratio(width)/tick),
                oppv=int(d*(E.ratio(t['drL'] if d==1 else t['drH'])-E.ratio(edge))/tick),
                edge=str(edge),tick=str(day.get('tick') or .25),P=P)


def witnesses(raw,cases,grid):
    if raw['estimate'] is None: return []
    by={c['id']:c for c in cases}
    out=[]
    for cid in raw['risk_set']['ids']:
        c=by[cid]
        path=[None if not np.isfinite(p).all() else [int(v) for v in p] for p in c['P']]
        w=dict(id=cid,date=c['date'],w=int(c['w']),direction=int(c['side']),edge_ticks=c['edge_ticks'],activation=int(grid[c['a']]) if c['a']>=0 else int(grid[0])-5,
               outcome=raw['labels'][cid],path=path)
        w['revision']=revision(w)
        out.append(w)
    return out


def verify_witnesses(raw,paths,cases,grid):
    expected=raw['risk_set']['ids'] if raw['estimate'] is not None else []
    if [w['id'] for w in paths]!=expected: return False
    by={c['id']:c for c in cases}
    for w in paths:
        c=by[w['id']]
        if w['outcome']!=raw['labels'][w['id']] or w['w']!=c['w'] or w['date']!=c['date'] or w['direction']!=c['side'] or w['edge_ticks']!=c['edge_ticks']: return False
        activation=int(grid[c['a']]) if c['a']>=0 else int(grid[0])-5
        if w['activation']!=activation: return False
        if w['revision']!=revision({k:v for k,v in w.items() if k!='revision'}): return False
        real=[None if not np.isfinite(p).all() else [int(v) for v in p] for p in c['P']]
        if w['path']!=real or len(w['path'])!=len(grid): return False
    return True


def publish(raw,paths,cases,today,grid,day,previous=None):
    gate=I.review_gate()
    env=gate.Envelope(ROUTE,'PROFILE:CONTINUATIONS-24',dict(context=raw['context']['id']))
    check=gate.ref_continuation(raw,cases,today,grid)
    good=check['outcome']=='PASS' and verify_witnesses(raw,paths,cases,grid)
    env.check('independent scene, membership, outcomes and exact witness paths',good,len(paths))
    if not good:
        env.violate('CONTINUATION_WITNESS_MISMATCH',['E1','H2','V2'],'Number and complete witness set must refer to the same release',withheld=[EST])
        return dict(status='WITNESS_MISMATCH',contract=env.finish(),message='Число и пути не связаны: зависимый слой снят')
    t=raw['target']; ctx=raw['context']; s=raw['support']; tick=E.ratio(today['tick'])
    _,close=E.prefix(today,grid,ctx['cut'])
    context=dict(ctx,today_w=int(today['w']),today_close=close if close is not None else 0,
                 code_revision=CODE_REVISION,
                 tick_num=tick.numerator,tick_den=tick.denominator,
                 registry_hash=gate.registry_hash(),base_registry_hash=C.registry_hash())
    prefix=[[int(b[0])+5,*[int(E.ratio(p)/tick) for p in b[1:5]]] for b in day['bars'] if int(b[0])+5<=ctx['cut']]
    f_ids={c['id'] for c in cases if c['id'] in day.get('_F_ids',[])}
    proof=dict(context=context,target=t,question=raw['question'],observed=raw['observed'],
               status=raw['status'],grid=list(grid),today_prefix=prefix,
               counts=dict(G=len(raw['selection']['G']),eligible=len(raw['selection']['eligible']),
                           position=len(raw['selection']['M']),risk=len(raw['risk_set']['ids']),
                           in_F=len(set(raw['risk_set']['ids'])&f_ids),outside_F=len(set(raw['risk_set']['ids'])-f_ids)),
               position_ids=raw['selection']['M'],risk_ids=raw['risk_set']['ids'],
               support={k:s[k] for k in ('n_total','n_known','yes','no','unknown')},witnesses=paths,
               source_kind='POSITION_AT_COMMON_CLOCK',full_path_compared=False,
               empirical_scope='FIXED_WINDOW_EXTENSION_NOT_PREDICTIVELY_ADMITTED',
               candidate='PROFILE:CONTINUATIONS-24')
    release_id=revision(proof)
    if raw['estimate'] is not None:
        y,n,u,k=s['yes'],s['n_total'],s['unknown'],s['n_known']
        estimates=[dict(estimator='ESTR:C-WINDOW',value_kind='BOUNDS',lower=y/n,upper=(y+u)/n,denominator=n,unit='share of the risk set')]
        estimates.append(dict(estimator='ESTR:C-WINDOW',value_kind='POINT',value=y/k,numerator=y,denominator=k,unit='share among known outcomes'))
        support=dict(case_set='CS:C-RISK',n_base=proof['counts']['G'],n_eligible=proof['counts']['eligible'],n_match=n,
                     components=[dict(component='EXISTENCE',of=n,yes=y,no=s['no'],unknown=u,condition_ru='Близкое положение и явно указанное условие вопроса')])
        env.bundle(EST,'CS:C-RISK',raw['risk_set']['snapshot_id'],'lab/continuity24.py::release',
                   [dict(input_kind='TODAY_PREFIX',ref='today',version=ctx['prefix_revision']),
                    dict(input_kind='CODE',ref=E.VERSION,version=CODE_REVISION),
                    dict(input_kind='CASE_SET_SNAPSHOT',ref='G',version=ctx['history_revision'])],estimates,[support],
                   dict(cut=S.clk(ctx['cut']),n=n,yes=y,unknown=u,window=S.clk(raw['question']['first_close']-5)+'–'+S.clk(t['last_close'])),
                   parameters=dict(release=release_id,target=t['id'],question=raw['question']['id'],cut=ctx['cut']),
                   claim_extra=dict(parent_case_set=raw['selection']['snapshot_id'],cut=ctx['cut']))
    comparison=None
    if previous and previous['context']['target_id']==ctx['target_id'] and previous['context']['cut']<ctx['cut']:
        tr=A.transition(previous,raw)
        if tr['outcome']!='PASS':
            env.violate('CONTINUATION_TRANSITION',['E1','H2'],'Incompatible transition',withheld=[EST])
        else: comparison=tr['details']
    out=dict(status=raw['status'],release_id=release_id,proof=proof,comparison=comparison,
             contract=env.finish(),review=dict(decision='CANDIDATE',human_acceptance='PENDING',edition=I.REVIEW_EDITION))
    if out['contract']['status']!='CONFORMANT':
        return dict(status='CONTRACT_VIOLATION',contract=out['contract'],message='Ответ не прошёл проверку')
    return gate.finalize(ROUTE,out)


def response(req):
    with _lock:
        inst=req.get('instrument','NQ'); block=req.get('session','RDR'); date=req.get('date') or None
        if inst not in ('NQ','ES','YM') or block not in ('ODR','RDR'): return dict(status='OUT_OF_SCOPE',message='Продолжения: ODR и RDR')
        if date and date>'2025-12-31': return dict(status='OUT_OF_SCOPE',message='История после 2025 закрыта')
        cut=int(req['at'])
        if cut%5: raise ValueError('только закрытые M5')
        if C.stale() or I.review_gate().stale(): return dict(status='CONTRACT_STALE',message='Реестр изменился: слой снят')
        fam,_,day=S._family(inst,block,cut,date,'conf'+(':all' if req.get('scope')=='all' else ''))
        if fam.get('status')!='ok' or 'c0' not in fam.get('today',{}): return dict(status='NO_CONFIRMATION',message='Нужно подтверждение')
        raw_target=req['target']; t=fam['today']; d=t['side']
        frame=E.Frame(inst,day['date'],block,d,str(t['idrH'] if d==1 else t['idrL']),str(t['idrH']-t['idrL']),t['c0'],fam['schedule']['end'])
        supplied=raw_target.get('frame')
        if supplied and (any(supplied.get(k)!=v for k,v in E.asdict(frame).items() if k not in ('edge','width')) or
                         any(E.ratio(supplied[k])!=E.ratio(getattr(frame,k)) for k in ('edge','width'))):
            return dict(status='TARGET_FRAME_CHANGED',message='Исходная рамка изменилась: выберите цель заново')
        created=int(raw_target['created_at'])
        if cut<created: return dict(status='BEFORE_TARGET',message='На этом срезе цель ещё не была закреплена')
        target=E.pin(frame,E.Q(*raw_target['low']),E.Q(*raw_target['high']),int(raw_target['first_close']),int(raw_target['last_close']),created)
        cases,grid=corpus(inst,block); today=rows_today(fam,day,grid,cut)
        cache_key=revision(dict(instrument=inst,block=block,date=day['date'],cut=cut,scope=req.get('scope'),target=target.record(),
                                prefix=[[int(T),[None if not np.isfinite(v) else int(v) for v in p]] for T,p in zip(grid,today['P']) if T<=cut],
                                source_stamp=_corpora[(inst,block)][0],registry=I.review_gate().registry_hash(),previous=req.get('previous')))
        if cache_key in _publications:return copy.deepcopy(_publications[cache_key])
        raw=E.release(cases,today,grid,target,cut,fam)
        paths=witnesses(raw,cases,grid)
        day=dict(day,_F_ids=fam['ids'])
        previous=_releases.get(req.get('previous'))
        out=publish(raw,paths,cases,today,grid,day,previous)
        if out.get('release_id'):
            _releases[out['release_id']]=raw
            while len(_releases)>64: _releases.popitem(last=False)
            _publications[cache_key]=copy.deepcopy(out)
            while len(_publications)>8:_publications.popitem(last=False)
        return out
