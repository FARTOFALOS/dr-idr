"""Additive FOM queries and checks. No market calculator, gate or screen imports this module.

Relations inferred from fields point from dependent to foundation. Expected answers,
terms, research and presentation obligations are annotations, never computational inputs.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_CLASS = 'FomCatalog'
CHECKS = {
 'FOUNDATION-REACH': 'foundations reach the declared estimands; explicit exceptions remain bounded',
 'ENUM-BINDING-COMPLETE': 'dependency-bearing enum fields have applicable foundation rules',
 'EDGE-TYPE': 'foundation edges name their type, field, scope and information availability',
 'IMPACT-EXPECTED': 'possible impact matches preregistered affected and unaffected estimand sets',
 'FOM-REFS': 'FOM annotations resolve without making them inputs of market estimands',
 'TERM-COLLISION': 'homonyms have explicit context and guarded distinctions',
 'MISREADING-GUARD': 'negative mappings have resolvable guards; exact mappings require interchangeable referents',
 'FACET-BASIS': 'facets have one basis, an applicable projection, cardinality and unknown rule',
 'FACET-PERMANENCE': 'derived facets are deterministic for this source version',
 'RESEARCH-COVERAGE': 'research inventory distinguishes mapped claims from unextracted areas',
 'NEGATIVE-SCOPE': 'negative findings name population, uncertainty and restricted conclusions',
 'NO-PROMOTION': 'hypotheses and computation evidence cannot mint transfer, policy or acceptance',
 'PRESENTATION-RELATIONS': 'alpha/omega pairs name existing meanings, bindings, work distinctions and tests',
 'PROTECTED-IDENTITY': 'FOM leaves the frozen calculators, contract, UI and launchers unchanged',
 'CQ-PREREG': 'question expectations were committed before the FOM implementation',
}
FOM_COLLECTIONS = {'mapped_artifacts','mapped_lines','foundations','foundation_bindings','terms',
                   'term_relations','facet_definitions','research_findings','research_coverage',
                   'competency_questions','presentation_obligations'}

def result(name, checked, errors=(), details=None):
    return dict(check=name,outcome='FAIL' if errors else 'PASS',checked=checked,
                violations=[dict(code=name,arch_ref=['FOM-1.2'],where=w,message=m,severity='BLOCKING') for w,m in errors],details=details or {})

def registry_objects(st):
    return {o['id']:o for rows in st['reg'].values() if isinstance(rows,list) for o in rows if isinstance(o,dict) and 'id' in o}

def records(st, collection):
    return st['cat'].get(collection, [])

def evidence_path(ref):
    return ref.split('#',1)[0]

def matches(rule, obj):
    value = obj.get(rule['field'])
    return rule['match_value'] in value if isinstance(value,list) else value == rule['match_value']

def foundation_edges(st):
    """Return data, not expected answers; no relation is copied from a CQ oracle."""
    out=[]
    for rule in records(st,'foundation_bindings'):
        for obj in st['reg'].get(rule['collection'],[]):
            if matches(rule,obj):
                for dependency in rule['depends_on']:
                    out.append(dict(dependent=obj['id'],foundation=dependency,rule=rule['id'],
                        kind=rule['dependency_kind'],field=rule['collection']+'.'+rule['field'],
                        value=rule['match_value'],scope=rule['scope_ru'],availability=rule['availability'],evidence=rule['evidence']))
    return out

def extend_graph(st, g):
    for f in records(st,'foundations'):
        if '#' in f['id']:
            g.edge(f['id'],'clause_of',f['registry_id'],'dep')
    for e in foundation_edges(st):
        rel=f"fom:{e['kind']}:{e['field']}={e['value']} [{e['rule']}]"
        g.edge(e['dependent'],rel,e['foundation'],'dep')

def dependents(g, start):
    """Definition dependency closure, excluding check/source annotations and possible code callers."""
    seen, todo={start},deque([start])
    while todo:
        y=todo.popleft()
        for _,x,cat in g.inn.get(y,[]):
            if cat=='dep' and x not in seen:
                seen.add(x); todo.append(x)
    return seen-{start}

def ancestors(g, start):
    seen,todo={start},deque([start])
    while todo:
        y=todo.popleft()
        for _,x,cat in g.out.get(y,[]):
            if cat=='dep' and x not in seen: seen.add(x); todo.append(x)
    return seen

def facets(st):
    reg=registry_objects(st)
    forms={f['estimand']:f for f in st['reg']['claim_forms']}
    bindings=defaultdict(set)
    for b in records(st,'bindings'):
        if b.get('estimand'): bindings[b['estimand']].add(b['binding'])
    def ancestry(ids):
        seen, todo=set(),list(ids)
        while todo:
            x=todo.pop()
            if x in seen: continue
            seen.add(x); todo.extend(reg.get(x,{}).get('parent',[]))
        return [reg[x] for x in sorted(seen) if x in reg]
    out={}
    schema_slots=st['spec']['classes']['Registry']['slots']
    for coll,rows in st['reg'].items():
        if not isinstance(rows,list): continue
        for obj in rows:
            if not isinstance(obj,dict) or 'id' not in obj: continue
            oid=obj['id']; item={'class':schema_slots.get(coll,{}).get('range','UNKNOWN'), 'level':'DEFINITION','grounds':obj.get('grounds','UNKNOWN')}
            if 'role' in obj and oid.startswith('CS:'): item['set_role']=obj['role']
            if oid.startswith('EST:'):
                sets=ancestry(obj['q4_case_set']); outcome=reg[obj['q5_outcome']]
                retrospective=any(s.get('role')=='RETROSPECTIVE_RESEARCH' for s in sets)
                activation={s.get('activation_kind') for s in sets}
                phase=(['AFTER_BLOCK_END'] if retrospective else ['BEFORE_CONFIRMATION'] if obj['profile']=='PROFILE:PRE-24'
                       else [v for k,v in [('CONFIRMATION','AFTER_CONFIRMATION'),('DR_BREAK','AFTER_BREAK')] if k in activation])
                knowledge={s['condition_availability'] for s in sets if s.get('condition_availability')}
                if outcome.get('uses_case_future_as_label'): knowledge.add('CASE_FUTURE_LABEL')
                frames=[v for k,v in [('CONFIRMATION','MF:CONFIRMATION-1'),('DR_BREAK','MF:BREAK-1')] if k in activation]
                if obj['profile']=='PROFILE:PRE-24': frames=['FND:PRE-COORDINATE']
                times={'OWN_HORIZON' if outcome.get('horizon_start')=='OWN_ACTIVATION_CLOSE_EXCLUSIVE' else 'COMMON_SESSION_CLOCK'}
                item.update(phase=sorted(phase) or ['UNKNOWN'],knowledge=sorted(knowledge),price=frames or ['UNKNOWN'],
                    time=sorted(times),denominator=obj['q4_denominator'],claim=forms[oid]['claim_class'],surface=sorted(bindings[oid]),
                    event=outcome['event'],projection=outcome['projection'],profile=obj['profile'],retrospective=retrospective)
            out[oid]=item
    for entry in records(st,'entries'):
        out[entry['id']]={'class':entry['entry_kind'],'level':'DEFINITION','stage':entry.get('realized_by',[]) or ['UNKNOWN']}
    return out

def facet_query(st, filters):
    """Conjunction of facet=value. Multi-valued facets use membership, never equality to one arbitrary role."""
    parsed=[]
    valid={f['projection'] for f in records(st,'facet_definitions')}|{'event','projection','profile','retrospective'}
    for field_value in filters:
        field,sep,value=field_value.partition('=')
        if not sep or field not in valid: raise ValueError('unknown facet/filter: '+field_value)
        parsed.append((field,value))
    def selected(x):
        for field,want in parsed:
            actual=x.get(field,'NOT_APPLICABLE')
            if isinstance(actual,list):
                if want not in actual: return False
            elif str(actual).lower()!=want.lower(): return False
        return True
    return {k:v for k,v in facets(st).items() if selected(v)}

def term_query(st, word, scheme=None):
    want=word.casefold().strip()
    matches_=[t for t in records(st,'terms') if (scheme is None or t['scheme']==scheme) and want in {w.casefold() for w in [t['title_ru']]+t.get('aliases',[])}]
    ids={t['id'] for t in matches_}
    reg=registry_objects(st)
    return dict(term=word,ambiguous=len(matches_)>1,matches=[dict(t,questions=sorted({reg[e]['question'] for e in t.get('denotes',[]) if e in reg and reg[e].get('question')})) for t in matches_],
        relations=[r for r in records(st,'term_relations') if r['left'] in ids or r['right'] in ids],
        boundary='Context chooses the question; CLOSE mappings are not transitive. Empty denotes means no admitted numerical answer, not zero.')

def impact_evidence(st,g,start):
    ids=dependents(g,start)
    return dict(changed=start,estimands=sorted(x for x in ids if x.startswith('EST:')),
        typed_edges=[e for e in foundation_edges(st) if e['foundation']==start or e['dependent'] in ids],
        analysis='STATIC_POSSIBLE_DEPENDENCY',
        boundary='An annotated possible dependency is not an observed change of every number. In particular a positive rescaling preserves DR truth; a frame can change interpretation or selection. Missing edges do not prove independence. Runtime transitions provide evidence only for exercised inputs.')

def protected_check(st):
    errors=[]
    for a in records(st,'mapped_artifacts'):
        if not a['protected']: continue
        p=ROOT/a['path']
        got=hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest() if p.is_file() else None
        if got!=a['sha256_lf']: errors.append((a['path'],'protected source differs from frozen 3031c95'))
    return result('PROTECTED-IDENTITY',sum(a['protected'] for a in records(st,'mapped_artifacts')),errors)

def checks(st,g):
    cat=st['cat']; reg=registry_objects(st); edges=foundation_edges(st); res=[]
    known=set(reg)|{f['id'] for f in records(st,'foundations')}
    errors=[]
    for f in records(st,'foundations'):
        if f['registry_id'] not in reg or f['field'] not in reg[f['registry_id']]: errors.append((f['id'],'foundation field is missing'))
        if not f.get('exception_ru') and not any(x.startswith('EST:') for x in dependents(g,f['id'])): errors.append((f['id'],'no dependent estimand'))
    res.append(result('FOUNDATION-REACH',len(records(st,'foundations')),errors,dict(exceptions=[f['id'] for f in records(st,'foundations') if f.get('exception_ru')])))
    errors=[]
    significant={'activation_kind':{'CONFIRMATION','DR_BREAK'},'horizon_end':{'BLOCK_END_CLOSE_INCLUSIVE','SINGLE_M5'},'horizon_start':{'BOX_END','COMMON_CUT_EXCLUSIVE'}}
    for coll in ('measurement_frames','case_sets','outcomes'):
        for o in st['reg'][coll]:
            for field,values in significant.items():
                if o.get(field) in values and not any(e['dependent']==o['id'] and e['field']==coll+'.'+field for e in edges):
                    errors.append((o['id']+'.'+field,'dependency-bearing field has no binding'))
    res.append(result('ENUM-BINDING-COMPLETE',len(edges),errors,dict(scope='activation kind and horizon enums; remaining enum dependencies are outside this first map, not proven absent')))
    errors=[]
    expected_types={('measurement_frames','activation_kind','CONFIRMATION'):'DEFINING',('measurement_frames','activation_kind','DR_BREAK'):'DEFINING',('outcomes','event','DR'):'COMPUTATIONAL'}
    for b in records(st,'foundation_bindings'):
        if not any(e['rule']==b['id'] for e in edges): errors.append((b['id'],'rule matches no object'))
        for dep in b['depends_on']:
            if dep not in known: errors.append((b['id'],'unresolved foundation '+dep))
        want=expected_types.get((b['collection'],b['field'],b['match_value']))
        if b['collection']=='case_sets': want='DEFINING' if b['field']=='activation_kind' and b['match_value']=='CONFIRMATION' else 'CONTROL_SELECTION'
        if b['collection']=='comparisons': want='CONTROL_SELECTION'
        if b['collection']=='outcomes' and b['field'].startswith('horizon_'): want='TEMPORAL'
        if want and b['dependency_kind']!=want: errors.append((b['id'],'wrong dependency type; expected '+want))
        if b['availability'] != 'DEFINITION_VERSION': errors.append((b['id'],'a definition dependency cannot admit future case data into selection'))
        if b['collection']=='measurement_frames' and b['field']=='activation_kind':
            clause='break_rule' if b['match_value']=='DR_BREAK' else 'confirmation_rule'
            if 'RULE:DRIDR-24-1#'+clause not in b['depends_on']: errors.append((b['id'],'activation bound to wrong rule clause'))
    res.append(result('EDGE-TYPE',len(edges),errors))
    errors=[]; measured=[]
    for q in records(st,'competency_questions'):
        if q['query']!='impact': continue
        got={x for x in dependents(g,q['argument']) if x.startswith('EST:')}; want=set(q['expected_ids'])
        fp=sorted(got-want); fn=sorted(want-got); forbidden=sorted(got&set(q['forbidden_ids']))
        if fp or fn or forbidden: errors.append((q['id'],f'false positive={fp}; missing={fn}; forbidden={forbidden}'))
        measured.append(dict(question=q['id'],affected=len(got),expected=len(want),false_positive=fp,missing=fn))
    res.append(result('IMPACT-EXPECTED',len(measured),errors,dict(comparisons=measured,analysis='definition dependency closure, not full call-graph or causal proof')))
    errors=[]
    terms={t['id']:t for t in records(st,'terms')}; bindings={b['binding'] for b in records(st,'bindings')}
    for coll in FOM_COLLECTIONS:
        for o in records(st,coll):
            for ref in o.get('evidence',[]):
                if not (ROOT/evidence_path(ref)).is_file(): errors.append((o.get('id',o.get('path',coll)),'missing evidence '+ref))
    for t in terms.values():
        for target in t.get('denotes',[]):
            if target not in reg: errors.append((t['id'],'unresolved denotation '+target))
    for r in records(st,'research_findings'):
        for target in r['validates']:
            if target not in known: errors.append((r['id'],'unresolved research subject '+target))
    for o in records(st,'presentation_obligations'):
        for target in o['semantic_refs']:
            if target not in reg: errors.append((o['id'],'unresolved semantic ref '+target))
        for b in o['bindings']:
            if b not in bindings: errors.append((o['id'],'unresolved binding '+b))
    res.append(result('FOM-REFS',len(terms)+len(records(st,'presentation_obligations')),errors))
    errors=[]; labels=defaultdict(list)
    for t in terms.values():
        for label in [t['title_ru']]+t.get('aliases',[]): labels[label.casefold()].append(t)
    pairs={frozenset((r['left'],r['right'])) for r in records(st,'term_relations')}
    for label,ts in labels.items():
        for i,a in enumerate(ts):
            for b in ts[i+1:]:
                if a['id']==b['id']: continue
                if a['scheme']==b['scheme'] or frozenset((a['id'],b['id'])) not in pairs:
                    errors.append((label,'unresolved homonym '+a['id']+' / '+b['id']))
    res.append(result('TERM-COLLISION',len(labels),errors))
    guards=set(re.findall(r'\b(?:W\d{2}|M\d{2})\b',(ROOT/'spec/DR-LAB-SWPC-1.1.md').read_text(encoding='utf-8')))|{'K16','K33','NOTATION-LINT'}
    errors=[]
    for r in records(st,'term_relations'):
        if not r.get('guards') or not set(r['guards'])<=guards: errors.append((r['id'],'missing or unresolved misreading guard'))
        a,b=terms.get(r['left']),terms.get(r['right'])
        if not a or not b: errors.append((r['id'],'term relation has unresolved endpoint')); continue
        if r['mapping']=='EXACT' and (a.get('denotes')!=b.get('denotes') or a.get('legacy_reference')!=b.get('legacy_reference') or a['definition_ru']!=b['definition_ru'] or a['scheme']!=b['scheme']):
            errors.append((r['id'],'exact mapping substitutes different objects'))
        if r['mapping']=='EXACT' and a['id']=='TERM:ARCH-R': errors.append((r['id'],'notation homonym is not a conceptual equivalence'))
    mappings=defaultdict(set)
    for r in records(st,'term_relations'): mappings[frozenset((r['left'],r['right']))].add(r['mapping'])
    for pair,kinds in mappings.items():
        if 'EXACT' in kinds and kinds & {'BROAD','NARROW','RELATED','NOT_IDENTICAL'}: errors.append((' / '.join(sorted(pair)),'exact mapping conflicts with a non-equivalence mapping'))
    res.append(result('MISREADING-GUARD',len(records(st,'term_relations')),errors))
    errors=[]; projections={'class','level','stage','phase','knowledge','price','time','set_role','denominator','claim','grounds','surface'}
    for f in records(st,'facet_definitions'):
        if f['projection'] not in projections or f['cardinality'] not in ('ONE','MANY') or not f.get('used_by'):
            errors.append((f['id'],'mixed, mutable status, unused or unknown projection'))
        if f['projection'] in {'decision','lifecycle','human_acceptance'}: errors.append((f['id'],'standing is not a facet'))
    res.append(result('FACET-BASIS',len(records(st,'facet_definitions')),errors))
    res.append(result('FACET-PERMANENCE',len(facets(st)),[] if facets(st)==facets(copy.deepcopy(st)) else [('facets','projection depends on transient object identity')]))
    errors=[]; research=records(st,'research_findings'); coverage={o['path']:o for o in records(st,'research_coverage')}
    required={p.relative_to(ROOT).as_posix() for top in ('studies','research') for p in (ROOT/top).iterdir() if p.is_dir()}
    for p in required-coverage.keys(): errors.append((p,'research area has no mapped claim or explicit limit'))
    for p,o in coverage.items():
        if o['disposition']=='MAPPED' and not o.get('findings'): errors.append((p,'mapped research without a finding'))
    res.append(result('RESEARCH-COVERAGE',len(required),errors,dict(inventory=len(required),mapped=sum(coverage[p]['disposition']=='MAPPED' for p in required if p in coverage),not_extracted=sorted(p for p in required if p in coverage and coverage[p]['disposition']=='NOT_EXTRACTED'))))
    errors=[]; promotion=[]
    for r in research:
        if r['conclusion'] in ('NOT_DETECTED','INCONCLUSIVE','EQUIVALENCE','REFUTED_IN_SCOPE') and not all(r.get(f) for f in ('negative_scope_ru','corpus_ru','uncertainty_ru')):
            errors.append((r['id'],'negative conclusion lacks scope/population/uncertainty'))
        if r['conclusion']=='EQUIVALENCE' and not all(r.get(f) for f in ('sesoi','equivalence_method','dependence_control')):
            errors.append((r['id'],'absence of meaningful effect requires justified SESOI and dependence-aware equivalence evidence'))
        if r['accepted_basis'] or r['conclusion']=='HYPOTHESIS' and r['lifecycle']!='NOT_PROMOTED': promotion.append((r['id'],'research record mints acceptance'))
        if r['grounds']=='HYPOTHESIS' and r['conclusion']!='HYPOTHESIS': promotion.append((r['id'],'a hypothesis is presented as an established result'))
        if r['validation_kind'] in ('STRUCTURE','COMPUTATIONAL_INVARIANT') and r['claim_level']!='A_CORRECTNESS': promotion.append((r['id'],'structural/correctness evidence promoted to statistical transfer or policy'))
    res.append(result('NEGATIVE-SCOPE',len(research),errors)); res.append(result('NO-PROMOTION',len(research),promotion))
    errors=[]
    for o in records(st,'presentation_obligations'):
        if o['test_id'] not in {'MT-01','MT-02','MT-03','MT-04','MT-05'} or not set(o['work_refs'])<=guards:
            errors.append((o['id'],'unresolved transformation test or work distinction'))
    res.append(result('PRESENTATION-RELATIONS',len(records(st,'presentation_obligations')),errors))
    res.append(protected_check(st))
    qpath='trace/catalog/70-questions.yaml'
    prereg=subprocess.run(['git','-C',str(ROOT),'log','--format=%H','--diff-filter=A','--',qpath],capture_output=True,text=True).stdout.splitlines()
    revisions=subprocess.run(['git','-C',str(ROOT),'log','--format=%H','--',qpath],capture_output=True,text=True).stdout.splitlines()
    committed=subprocess.run(['git','-C',str(ROOT),'show',f'{revisions[0]}:{qpath}'],capture_output=True).stdout if revisions else b''
    expected=json.loads(committed).get('competency_questions',[]) if committed else []
    # Ignore encoding/newline differences; compare semantic expectations, not formatting.
    amended=bool(revisions and prereg and revisions[0]!=prereg[0])
    amendment_note=ROOT/'meaning/lens/2026-10-14-fom-expectation-amendment.md'
    ok=expected==records(st,'competency_questions') and (not amended or amendment_note.is_file())
    res.append(result('CQ-PREREG',len(expected),[] if ok else [(qpath,'expectations differ from committed preregistration or have no amendment reason')],dict(preregistered_commit=prereg[0] if prereg else None,expectation_revision=revisions[0] if revisions else None,amended=amended)))
    return res

def answer(st,g,q):
    query,arg=q['query'],q.get('argument',''); reg=registry_objects(st)
    status='YES'; out=None
    if query=='impact': out=impact_evidence(st,g,arg)
    elif query=='term':
        out=term_query(st,arg)
        if not out['matches']: status='NO'
    elif query=='accepted_words':
        ids=dependents(g,arg)
        out=dict(forms=[f for f in st['reg']['claim_forms'] if f['estimand'] in ids and f['acceptance']=='ACCEPTED_BY_OPERATOR'],
            boundary='Explicit definition links only; a change of shared code or of the wider X concept can affect more forms.')
        status='PARTIAL'
    elif query=='denominators':
        out=[dict(estimand=e,denominator=reg[e]['q4_denominator'],case_sets=reg[e]['q4_case_set'],outcome=reg[e]['q5_outcome']) for e in q['expected_ids']]
    elif query=='same_value': out=[b['id'] for b in records(st,'bindings') if b.get('estimand')==arg]
    elif query in ('research','negative_results'):
        out=[r for r in records(st,'research_findings') if (not arg or r['id']==arg) and (query!='negative_results' or r['conclusion'] in ('NOT_DETECTED','REFUTED_IN_SCOPE','INCONCLUSIVE','EQUIVALENCE'))]
        if not arg: status='PARTIAL'  # explicit unextracted research inventory
    elif query=='claims': out=dict(C1=[f['estimand'] for f in st['reg']['claim_forms'] if f['claim_class']=='ConditionalDescriptiveClaim'],C2=[],C3=[],boundary='No predictive or decision admission is instantiated; a generic schema class is not authority.')
    elif query=='boundary': out=[b for b in records(st,'boundaries') if b['id']==arg]
    elif query=='standing': out=dict(profiles=records(st,'standings'),lines=records(st,'mapped_lines'),boundary='Records preserve attributed standing; they do not establish fresh human consent.')
    elif query=='layer': out=[l for l in records(st,'mapped_lines') if l['line'].get('pull_request')==int(arg)]
    elif query=='protected': out=dict(protected=protected_check(st),boundary='Byte identity protects this implementation; additive text comparison cannot prove unchanged meaning of candidate amendments.')
    elif query=='pullback_facet':
        selected=facet_query(st,['phase=AFTER_CONFIRMATION','claim=ConditionalDescriptiveClaim','retrospective=false'])
        out=sorted(k for k,v in selected.items() if v.get('event') in ('NEW_R','DELTA_R','TAU_R'))
        if out!=sorted(q['expected_ids']): status='NO'
    elif query=='case_sets': out={p['id']:[c['id'] for c in st['reg']['case_sets'] if c['profile']==p['id']] for p in st['reg']['profiles']}
    elif query=='lineage':
        upstream=ancestors(g,arg)
        out=dict(target=arg,edges=[e for e in foundation_edges(st) if e['dependent'] in upstream],snapshot_fields=['spec','family_id','parent_snapshot','cut_close_minute','data_revision'],boundary='CaseSetSnapshot already binds specification, parent and cut; a new family per minute is unnecessary.')
    elif query=='obligations': out=[o for o in records(st,'presentation_obligations') if not arg or o['test_id']==arg]
    elif query=='impact_limits': out=dict(static='possible dependencies of annotated definitions',dynamic='observed effects on exercised inputs',absence='an absent static edge is not proof of independence',where='raw minute provenance remains GAP-09')
    elif query=='operations': out=dict(operations=['COMPUTE','PRESENT','ISSUE'],implication='none implies another; human reading requires independent evidence')
    else: status='NO'; out=dict(error='unknown question query '+query)
    return dict(id=q['id'],question=q['title_ru'],kind=q['question_kind'],baseline=q['baseline_status'],status=status,
        answer=out,evidence=q['evidence'],boundary=q['boundary_ru'],held_out=q['held_out'],machine_gate=q['machine_gate'])

def questions(st,g,holdout=None):
    return [answer(st,g,q) for q in records(st,'competency_questions') if holdout is None or q['held_out']==holdout]

def counterexamples(st, graph_builder):
    """Each mutation is judged by the named protection, not by any convenient failure."""
    def mutate(state, collection, index, field, value): state['cat'][collection][index][field]=value
    cases=[
      ('FX-01','missing foundation','FOUNDATION-REACH',lambda s:s['cat']['foundation_bindings'].clear()),
      ('FX-02','break bound to confirmation','EDGE-TYPE',lambda s:mutate(s,'foundation_bindings',1,'depends_on',['RULE:DRIDR-24-1#confirmation_rule'])),
      ('FX-03','wrong dependency type','EDGE-TYPE',lambda s:mutate(s,'foundation_bindings',9,'dependency_kind','EVIDENTIAL')),
      ('FX-04','place equals zone','MISREADING-GUARD',lambda s:mutate(s,'term_relations',4,'mapping','EXACT')),
      ('FX-05','removed false equivalence guard','MISREADING-GUARD',lambda s:mutate(s,'term_relations',4,'guards',[])),
      ('FX-06','acceptance used as a facet','FACET-BASIS',lambda s:mutate(s,'facet_definitions',3,'projection','decision')),
      ('FX-07','absence of effect from non-significance','NEGATIVE-SCOPE',lambda s:mutate(s,'research_findings',2,'conclusion','EQUIVALENCE')),
      ('FX-08','correctness promoted to prediction','NO-PROMOTION',lambda s:mutate(s,'research_findings',6,'claim_level','C_TRANSFER')),
      ('FX-09','hypothesis creates acceptance','NO-PROMOTION',lambda s:mutate(s,'research_findings',0,'accepted_basis',True)),
      ('FX-10','unknown presentation obligation','PRESENTATION-RELATIONS',lambda s:mutate(s,'presentation_obligations',0,'work_refs',['W99'])),
      ('FX-11','false foreign numerical dependency','IMPACT-EXPECTED',lambda s:s['cat']['foundation_bindings'].append(dict(s['cat']['foundation_bindings'][0],id='FB:FAULT',collection='estimands',field='id',match_value='EST:P-X',depends_on=['RULE:DRIDR-24-1#break_rule']))),
      ('FX-12','future input admitted by an annotation','EDGE-TYPE',lambda s:mutate(s,'foundation_bindings',0,'availability','CASE_FUTURE')),
      ('FX-13','hypothesis presented as measured','NO-PROMOTION',lambda s:mutate(s,'research_findings',0,'grounds','HYPOTHESIS')),
      ('FX-14','legacy numerical input','EDGE-TYPE',lambda s:mutate(s,'foundation_bindings',0,'depends_on',['EST:LEGACY-PLACE-22'])),
    ]
    out=[]
    for cid,tamper,check,change in cases:
        fault=copy.deepcopy(st); change(fault); g,_=graph_builder(fault)
        evidence=next(x for x in checks(fault,g) if x['check']==check)
        out.append(dict(id=cid,tamper=tamper,check=check,detected=evidence['outcome']=='FAIL',violations=evidence['violations']))
    return out

def screen_relations(raw):
    """Verify relationship identity as well as numerical identity; perception remains untested."""
    errors=[]
    context=raw.get('fom',{})
    if context:
        for field in ('now_cut','arrive_cut'):
            cut=context.get(field)
            if cut and cut.get('cut') != context['cut'] and not (field=='now_cut' and context.get('now_status')=='FROZEN_AT_BREAK'):
                errors.append((field,'answer is bound to another closed cut'))
        nc=context.get('now_cut') or {}
        if nc.get('family_id') and nc['family_id']!=context['base']['family_id']:
            errors.append(('now_cut','answer belongs to another family'))
    for i,e in enumerate(raw.get('elements',[])):
        est=e.get('estimand',''); block=e.get('block'); kind=e.get('bound_kind')
        if block=='NOW' and est and not est.startswith('EST:N-'): errors.append((str(i),'foreign estimand in NOW relationship'))
        if block=='ARRIVE' and est!='EST:K-ARRIVE': errors.append((str(i),'foreign estimand in ARRIVE relationship'))
        if kind=='ABSENCE' and e.get('shown') not in ('','—'): errors.append((str(i),'absence rendered as a number'))
        if kind=='UNBOUND': errors.append((str(i),'number without an admitted object'))
    return result('PRESENTATION-RELATION-RUNTIME',len(raw.get('elements',[])),errors)

def report(st,g):
    cq=questions(st,g)
    counts=lambda values: {s:sum(v==s for v in values) for s in ('YES','PARTIAL','NO')}
    ch=checks(st,g)
    return dict(version='FOM-1.2',status='PASS' if all(c['outcome']=='PASS' for c in ch) else 'FAIL',
        sources=st['stamps'],checks=ch,questions=cq,before=counts([q['baseline'] for q in cq]),after=counts([q['status'] for q in cq]),
        holdout_boundary='Prespecified questions not used to select facets; one author, no external independent assessment.',
        inventory=dict(files=len(records(st,'mapped_artifacts')),concepts=len(records(st,'terms')),term_relations=len(records(st,'term_relations')),foundation_edges=len(foundation_edges(st)),presentation_obligations=len(records(st,'presentation_obligations'))),
        G2='LIMIT_TO_DECLARED_AREA',boundaries=['Unextracted research claims remain explicit.', 'Minute tape provenance not replayed (GAP-09).', 'PRE runtime not traced.', 'Candidate SC amendments not semantically ratified.', 'Human perception not established.', 'No C2/C3 or policy authority.'])
