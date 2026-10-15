"""An atomic screen scene over existing accepted calculations and explicitly enabled review candidates.

No new estimator, probabilities, family matching or normative edition. Compute/present/persist remain separate.
"""
from __future__ import annotations
import importlib.util
import json
import threading
from pathlib import Path
import numpy as np
import contract as C
import now24 as N
import scene24 as S
from revisions24 import digest,path_revision,prefix_revision

ROOT=Path(__file__).resolve().parents[1]
REVIEW_ROOT=ROOT/'integration/candidates'
REVIEW_EDITION='DR-LAB-CANDIDATES-1'
_gate=None
_lock=threading.RLock()
PROFILES={'pre':'PROFILE:PRE-24','arrive':'PROFILE:ARRIVE-24'}

def review_gate():
    global _gate
    with _lock:
        if _gate is None:
            spec=importlib.util.spec_from_file_location('_dr_lab_candidate_gate',ROOT/'lab/contract.py')
            obj=importlib.util.module_from_spec(spec); spec.loader.exec_module(obj)
            obj.BUILD=REVIEW_ROOT/'build'; obj.REG_DIR=REVIEW_ROOT/'registry'
            obj.REGISTRY_FILE=obj.BUILD/'registry.json'; obj.SPEC_FILE=obj.BUILD/'runtime_spec.json'
            obj.EDITION=REVIEW_EDITION
            _gate=obj
    return _gate

def configuration(enabled):
    page=REVIEW_ROOT/'build/page_registry.json'
    return dict(enabled=enabled,standing='CANDIDATES_FOR_REVIEW',accepted_edition=C.EDITION,
                registry=json.loads(page.read_text(encoding='utf-8')) if enabled and page.exists() else None,
                profiles={k:dict(id=v,decision='CANDIDATE',human_acceptance='PENDING') for k,v in PROFILES.items()})

def _facts(fam,bars,tick,cut):
    """A target fact is independent of whether a fresh ARRIVE question is admissible after a break or at H."""
    if not fam or not fam.get('today',{}).get('c0'): return {}
    import arrive24 as A
    t=A.today_case(fam,bars,tick)
    result={}
    for name,(a,b) in A.LEVELS.items():
        act=fam['today']['c0']; end=min(cut,fam['schedule']['end'])
        reach=C.ref_reach([None if np.isnan(q[0]) else q.tolist() for q in t['P']],fam['grid'],act,end,a,b,t['w'],False)
        seen=[(j,q) for j,q in enumerate(t['P']) if act<fam['grid'][j]<=end and not np.isnan(q[0]) and q[0]*b<=a*t['w']]
        first=seen[0][0] if seen else None
        known=first is not None and not any(np.isnan(t['P'][j,0]) for j,T in enumerate(fam['grid']) if act<T<fam['grid'][first])
        result[name]=dict(reached=reach.upper(),bar_close=fam['grid'][first] if known else None,
                          bar_open=fam['grid'][first]-5 if known else None,time_known=known,available_at=fam['grid'][first] if known else None)
    return result

def scene(inst,session,cut,date=None,view='auto',scope='weekday',trials=()):
    if scope not in S.SCOPES: raise ValueError('scope: weekday | all')
    trials=sorted(set(trials))
    if any(k not in PROFILES for k in trials): raise ValueError('unknown candidate profile')
    cut=int(cut)//5*5
    with _lock:             # one immutable publication unit; existing caches remain local
        day=S.day_view(inst,date)
        if day.get('status')!='ok': return dict(status='NO_DAY',day=day)
        bars=day['bars']; tick=float(day.get('tick') or .25)
        view_arg=view+(':all' if scope=='all' else '')
        raw_family,base,family_day=S._family(inst,session,cut,date,view_arg)
        if family_day and family_day.get('status')=='ok' and prefix_revision(family_day['bars'],cut,tick)!=prefix_revision(bars,cut,tick):
            return dict(status='SCENE_CHANGED',message='Наблюдения изменились во время расчёта')
        fam=C.attach_family(raw_family,inst,base,family_day,dict(instrument=inst,session=session,at=cut,date=date,view=view_arg))
        valid=fam.get('status')=='ok' and 'today' in fam
        now=(C.attach_now(N.payload(fam,bars,tick),fam,bars,tick,dict(instrument=inst,session=session,at=cut,date=date,view=view_arg))
             if valid and fam.get('N') else None)
        result=dict(status='OK',day=C.attach_day(day,dict(instrument=inst,date=date)),family=fam,now=now,candidates={})
        original=fam if valid and fam['view']=='conf' else None
        for name in trials:
            gate=review_gate()
            if C.stale() or gate.stale():
                result['candidates'][name]=dict(status='CONTRACT_STALE',review=dict(decision='CANDIDATE',human_acceptance='PENDING'))
                continue
            if name=='pre':
                import pre24
                raw,B,pday=pre24._pre(inst,session,cut,date,scope)
                value=gate.attach_pre(raw,inst,B,pday,dict(instrument=inst,session=session,at=cut,date=date,scope=scope))
            else:
                import arrive24
                raw,parent,pbars,ptick=arrive24._arrive(inst,session,cut,date,scope)
                value=gate.attach_arrive(raw,parent,pbars,ptick,dict(instrument=inst,session=session,at=cut,date=date,scope=scope))
                if parent and parent.get('status')=='ok' and parent.get('today'):
                    original=parent
                    if prefix_revision(pbars,cut,ptick)!=prefix_revision(bars,cut,tick):
                        return dict(status='SCENE_CHANGED',message='Наблюдения изменились во время расчёта')
            result['candidates'][name]=gate.finalize('/api/d24/'+name,value)
            result['candidates'][name]['review']=dict(decision='CANDIDATE',human_acceptance='PENDING',edition=REVIEW_EDITION)
        prefix=prefix_revision(bars,cut,tick)
        context=dict(instrument=inst,date=day['date'],session=session,cut=cut,scope=scope,
                     view=fam.get('view',view),family_id=fam.get('family_id'),snapshot_id=fam.get('snapshot_id'),
                     path_revision=path_revision(fam) if valid else None,prefix_revision=prefix,registry_hash=C.registry_hash(),trials=trials)
        context['candidate_registry_hash']=review_gate().registry_hash() if trials else None
        context['models']={k:v.get('model') or v.get('profile') for k,v in result['candidates'].items()}
        context['id']=digest(context)
        result['context']=context
        result['target_facts']=_facts(original,bars,tick,cut) if original and 'arrive' in trials and session in ('ODR','RDR') else {}
        return result
