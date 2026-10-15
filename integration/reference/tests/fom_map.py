"""FOM acceptance: definition queries, discriminating faults, valid market transformations,
and optional real rendered states via the existing trace_page.mjs harness.

Run python -B tests/fom_map.py [--screens]. Case-level evidence stays in lab/.runtime/fom.
"""
from __future__ import annotations
import argparse
import copy
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab'))
import semtrace as T
import scene24
import arrive24
import now24

sys.stdout.reconfigure(encoding='utf-8',errors='replace')
F=T.F
EVIDENCE=ROOT/'lab/.runtime/fom'
failures=[]
results=[]

def check(ok, name, evidence=None):
    results.append(dict(test=name,outcome='PASS' if ok else 'FAIL',evidence=evidence))
    print(('  ok   ' if ok else '  FAIL ')+name,flush=True)
    if not ok: failures.append(name)

def family(date,cut,view='conf:all'):
    return T.C.finalize('/api/d24/family',scene24.family('NQ','RDR',cut,date,view))

def fixed(body):
    return dict(family_id=body.get('family_id'),snapshot_id=body.get('snapshot_id'),N=body.get('N'),
        counts=body.get('counts'),zones=body.get('zones'),members=sorted(body.get('members',[]),key=lambda x:x['id']))

def mt_01():
    body=family('2025-12-17',670)
    transformed=copy.deepcopy(body); transformed['members'].reverse()
    validated=T.C.finalize('/api/d24/family',transformed)
    check(body['contract']['status']=='CONFORMANT' and validated['contract']['status']=='CONFORMANT','MT-01: permutation input and transformed input both pass the production reference')
    check(fixed(body)==fixed(validated),'MT-01: permutation preserves family, points, distributions, zones and denominators')

def mt_02():
    date='2025-12-10'; cuts=[660,665,670,675,680,685,690,695]
    families=[family(date,c) for c in cuts]
    check(all(b['contract']['status']=='CONFORMANT' for b in families),'MT-02: sequential closed-M5 states are reference-conformant')
    check(all(fixed(b)==fixed(families[0]) for b in families[1:]),'MT-02: every fixed family measurement survives the observed pullback')
    check(all(b['today']['slice']==c for b,c in zip(families,cuts)) and families[0]['today']['zones']!=families[-1]['today']['zones'],'MT-02: prefix/cut/reachability change while the historical mass does not')
    answers=[]
    for c in cuts[1:]:
        for route,fn in [('/api/d24/now',lambda:now24.live('NQ','RDR',c,date,'conf:all')),('/api/d24/arrive',lambda:arrive24.arrive('NQ','RDR',c,date,'all'))]:
            body=T.C.finalize(route,fn()); answers.append(dict(cut=c,route=route,body=body))
            check(body['contract']['status']=='CONFORMANT',f'MT-02: {route} at closed cut {c} passes its own reference')
            check(body['cut']['cut']==c,f'MT-02: {route} snapshot names its own knowledge cut {c}')
            check(all((b.get('claim') or {}).get('claim_class') in (T.C.C0,T.C.C1) for b in body['contract'].get('bundles',[])),f'MT-02: {route} at {c} creates no C2/C3')
    (EVIDENCE/'transitions.local.json').write_text(json.dumps(answers,ensure_ascii=False,indent=1),encoding='utf-8')
    return families

def mt_03():
    before=T.C.finalize('/api/d24/arrive',arrive24.arrive('NQ','RDR',675,'2025-12-10','all'))
    after=T.C.finalize('/api/d24/arrive',arrive24.arrive('NQ','RDR',680,'2025-12-10','all'))
    check(before['contract']['status']==after['contract']['status']=='CONFORMANT','MT-03: reached-place transition has valid primary and derived inputs')
    a={p['level']:p for p in before['places']}; b={p['level']:p for p in after['places']}
    check(all(a[l]['state']['status']=='OPEN' and b[l]['state']['status']=='RESOLVED' for l in ('0','-1/2','-7/10')),'MT-03: arrival resolves each formerly open question at the next close')
    check(not after['contract'].get('bundles'),'MT-03: reached places carry facts, no old future-arrival percentages')

def mt_04():
    before=family('2025-12-10',845,'auto:all'); after=family('2025-12-10',850,'auto:all'); original=family('2025-12-10',850,'conf:all')
    check(before['contract']['status']==after['contract']['status']==original['contract']['status']=='CONFORMANT','MT-04: break and explicit original-family return pass the reference')
    check(before['view']=='conf' and after['view']=='brk' and before['family_id']!=after['family_id'] and before['scale']['orientation']==-after['scale']['orientation'],'MT-04: break changes family identity and orientation explicitly')
    check(fixed(before)==fixed(original),'MT-04: explicit return recovers the original snapshot and values')

def mt_05():
    body=T.C.finalize('/api/d24/arrive',arrive24.arrive('NQ','RDR',670,'2025-12-17','weekday'))
    check(body['contract']['status']=='CONFORMANT' and all(p['publication']=='WITHHELD_FEW_SESSIONS' for p in body['places']) and not body['contract']['bundles'],'MT-05: insufficient support is an absence with its own counts, never a zero probability')
    from trace_arch import future_ohlc_unit,future_break_unit,failures as tf
    future_ohlc_unit(); future_break_unit()
    check(not tf,'MT-05: future OHLC mutation keeps observation invariants and rederives DR break; invalid moved prefix is rejected')

def screens(st):
    fragments=['#date=2025-12-17&inst=NQ&session=RDR&at=11:10&scope=all',
        '#date=2025-12-10&inst=NQ&session=RDR&at=11:00&scope=all',
        '#date=2025-12-10&inst=NQ&session=RDR&at=11:05&scope=all',
        '#date=2025-12-10&inst=NQ&session=RDR&at=11:10&scope=all',
        '#date=2025-12-10&inst=NQ&session=RDR&at=11:15&scope=all',
        '#date=2025-12-10&inst=NQ&session=RDR&at=11:20&scope=all',
        '#date=2025-12-10&inst=NQ&session=RDR&at=14:05&scope=all',
        '#date=2025-12-10&inst=NQ&session=RDR&at=14:10&scope=all',
        '#date=2025-12-17&inst=NQ&session=RDR&at=11:10']
    raw=T.collect_screens(fragments,EVIDENCE/'screens',fom=True)
    for key,screen in raw.items():
        r=F.screen_relations(screen)
        check(r['outcome']=='PASS','UI: relationship/source identity '+key,r['violations'])
        check(not screen['contract']['violations'] and screen['contract']['unchecked']==0,'UI: every shown passport checked by the reference '+key)
    first=raw[fragments[0]]; perm=raw[fragments[0]+'|PERMUTED_MEMBERS']
    check(perm['transformed_responses']>0 and first['fom']['base']==perm['fom']['base'],'MT-01 UI: reordered cases preserve actual rendered meaning, coordinates, membership and support')
    base=[raw[f]['fom'] for f in fragments[1:6]]
    check(all(b['base']==base[0]['base'] for b in base),'MT-02 UI: unchanged historical distributions in actual sequential rendering')
    check(base[0]['prefix']!=base[1]['prefix'] and len(base[1]['prefix'])>len(base[0]['prefix']),'MT-02 UI: new closed observation remains visibly bound to its prefix')
    check(all(p['state']['status']=='RESOLVED' and not p['has_bundle'] for p in base[-1]['places']),'MT-03 UI: reached place presents a fact and removes its future share')
    before,after=(raw[f]['fom'] for f in fragments[6:8])
    check(before['base']['family_id']!=after['base']['family_id'] and before['orientation']==-after['orientation'] and before['base']['view']=='conf' and after['base']['view']=='brk','MT-04 UI: family switch and orientation are bound to the new context')
    check(not any(e['bound_kind']=='BUNDLE' for e in raw[fragments[7]]['elements'] if e['block']=='ARRIVE'),'MT-04 UI: ARRIVE does not carry its old percentage across the DR break')
    low=raw[fragments[8]]
    check(all(e['bound_kind']=='ABSENCE' and e['absence_reason']=='FEW_SESSIONS' and e['shown'] in ('','—') for e in low['elements'] if e['block']=='ARRIVE'),'MT-05 UI: few sessions are not zeros or retained percentages')
    tampered=copy.deepcopy(first)
    next(e for e in tampered['elements'] if e['block']=='NOW')['block']='ARRIVE'
    check(F.screen_relations(tampered)['outcome']=='FAIL','FX-UI: every number kept correct, false relationship placement is detected')
    stale=copy.deepcopy(first); stale['fom']['now_cut']['cut']-=5
    check(F.screen_relations(stale)['outcome']=='FAIL','FX-CUT: correct old answer cannot acquire the next M5 time')
    return len(raw)

def main():
    a=argparse.ArgumentParser(); a.add_argument('--screens',action='store_true'); a=a.parse_args()
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    st=T.load(); check(not T.stale_reasons(st),'source stamps current')
    res,g,code=T.static_checks(st)
    for c in res: check(c['outcome']=='PASS',c['check'],c['violations'])
    check(T.why(g,'RULE:DRIDR-24-1','EST:B-DR') is not None,'method rule reaches DR with a typed path')
    check(T.why(g,'MF:CONFIRMATION-1','EST:K-ARRIVE') is not None,'confirmation frame reaches ARRIVE without merging estimands')
    check(not any(k.startswith('EST:P-') for k in F.dependents(g,'FND:COORDINATE')) and len([k for k in F.dependents(g,'FND:IDR-UNIT') if k.startswith('EST:')])==59,'PRE has its own un-directed anchor; only the shared IDR unit spans all 59 estimands')
    check(T.validate(st['cat'],'FomCatalog',st['spec'])==[],'closed FomCatalog structure validates in stdlib')
    modified=copy.deepcopy(st); modified['cat']['terms'][0]['definition_ru']='silently substituted'
    check(any('catalog content' in r for r in T.stale_reasons(modified)),'compiled catalog mutation is stale even when source files did not change')
    edition=T.check_edition(st)
    check(len(edition['details'].get('extended_lines_review',[]))==2 and all(r['status']=='SEMANTIC_REVIEW_OPEN' for r in edition['details']['extended_lines_review']),'the two extended accepted SC lines are listed for semantic review, never ratified by a textual PASS')
    check(set(F.term_query(st,'откат от максимума')['matches'][0]['denotes'])=={'EST:B-LEVEL-REST'},'trader pullback question keeps the registered C0 level-rest answer')
    check(len(F.term_query(st,'место')['matches'])==3,'context distinguishes the three meanings of place')
    q17=next(q for q in F.questions(st,g) if q['id']=='CQ-17')
    check(q17['status']=='YES' and 'EST:P-R' not in q17['answer'] and 'EST:ZM3-STUDY' not in q17['answer'],'facet query excludes PRE/retrospective false positives')
    held=F.questions(st,g,True); check(len(held)==3 and all(q['status']=='YES' for q in held),'prespecified held-out questions answered within their boundaries')
    for c in F.counterexamples(st,lambda s:T.build_graph(s,code)): check(c['detected'],c['id']+': '+c['tamper'],c['violations'])
    mt_01(); mt_02(); mt_03(); mt_04(); mt_05()
    n=screens(st) if a.screens else 0
    report=dict(status='PASS' if not failures else 'FAIL',checks=len(results),failures=failures,screens=n,
        sources=st['stamps'],results=results,scope='NQ RDR 2025-12-17 and sequential 2025-12-10; no 2026; machine relationships, no human perception')
    (EVIDENCE/'acceptance.local.json').write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print('ALL GOOD' if not failures else 'FAILED',len(results),'checks;',n,'rendered states',flush=True)
    return bool(failures)

if __name__=='__main__': raise SystemExit(main())
