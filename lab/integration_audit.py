"""Explicit audit of an actual integrated publication, reusing Semantic Trace/FOM functions, outside the hot path."""
import importlib.util
import sys
from pathlib import Path
import integration24 as I

ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/'integration/reference'
_modules=None

def modules():
    global _modules
    if _modules is None:
        sys.path.insert(0,str(REF/'trace'))
        spec=importlib.util.spec_from_file_location('_integration_semtrace',REF/'lab/semtrace.py')
        t=importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
        t.ROOT=ROOT
        t.C=I.review_gate()              # same numerical definitions; candidate registry adds the two review profiles
        t.family_of=lambda scene:(scene['_family'],scene['_bars'],scene['_tick'])
        _modules=(t,t.F)
    return _modules

def audit(packet,params):
    T,F=modules(); results=[]; envelope_errors=[]
    for key,route,body in [('BASE','/api/d24/family',packet.get('family')),('NOW','/api/d24/now',packet.get('now')),
                           ('PRE','/api/d24/pre',packet.get('candidates',{}).get('pre')),('ARRIVE','/api/d24/arrive',packet.get('candidates',{}).get('arrive'))]:
        if not body: continue
        if not body.get('contract'):
            envelope_errors.append(dict(block=key,status=body.get('status','MISSING_CONTRACT')))
            continue
        if body['contract'].get('status')!='CONFORMANT': envelope_errors.append(dict(block=key,status=body['contract'].get('status')))
        for b in body['contract'].get('bundles',[]):
            est=b['estimand']; par=T.params_of(b)
            covered=(key=='BASE' and est.startswith('EST:B-ZONE-') and not est.startswith('EST:B-ZONE-RESIDUAL')) or \
                    (key=='NOW' and est.startswith('EST:N-NEW-') and par.get('role')=='MAIN' and any(e.get('value_kind')=='BOUNDS' and e.get('denominator',0)>0 for e in b['estimates'])) or \
                    (key=='ARRIVE' and est=='EST:K-ARRIVE')
            if not covered:
                results.append(dict(block=key,estimand=est,status='NOT_COVERED',evidence='SC gate verified; outside the extra Trace recount scope'))
                continue
            # The existing Trace function recounts the response's own primary case records and supports.
            scene=dict(id='INTEGRATION:CURRENT',route='ROUTE:'+route,instrument=params['instrument'],session=params['session'],
                       cut=packet['context']['cut'],date=params.get('date'),view=params.get('view','auto'),scope=params.get('scope','weekday'),
                       _family=packet['family'],_bars=packet['day']['bars'],_tick=float(packet['day'].get('tick') or .25))
            evidence=T.check_bundle_counts(scene,body,b)
            warnings=[v for v in evidence['violations'] if v.get('severity')=='WARNING']
            results.append(dict(block=key,estimand=b['estimand'],status='NOT_COVERED' if warnings else evidence['outcome'],evidence=evidence))
    now=packet.get('now') or {}; arr=packet.get('candidates',{}).get('arrive') or {}
    raw=dict(fom=dict(cut=packet['context']['cut'],base=dict(family_id=packet['context'].get('family_id')),
                     now_cut=now.get('cut'),now_status=now.get('status'),arrive_cut=arr.get('cut')),
             elements=[dict(estimand=r['estimand'],block=r['block'],bound_kind='BUNDLE') for r in results])
    relation=F.screen_relations(raw)
    ok=not envelope_errors and results and not any(r['status']=='FAIL' for r in results) and relation['outcome']=='PASS'
    status=('PASS_SCOPED' if any(r['status']=='PASS' for r in results) else 'NO_ADDITIONAL_COVERAGE') if ok else 'FAIL'
    return dict(status=status,
                context=packet['context']['id'],bundle_checks=results,relations=relation,
                envelope_errors=envelope_errors,
                source='Semantic Trace + FOM functions retained from f954046',
                coverage='Actual published bundles and cross-cut/family relations. Full historical catalog not rebound; human acceptance not performed.')
