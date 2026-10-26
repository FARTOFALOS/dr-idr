"""The explicit implementation map must reference the existing FOM and the right typed contract, never promote PB."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
read=lambda name:json.loads((ROOT/name).read_text(encoding='utf-8'))
base=read('contract/build/registry.json')['registry']
proposal=read('integration/candidates/build/registry.json')['registry']
mapping=read('integration/profile235-bindings.json')
accepted={e['id']:e for e in base['estimands']}
proposed={e['id']:e for e in proposal['estimands']}
forms={f['estimand']:f for f in proposal['claim_forms']}
facts={f['id'] for f in proposal['fact_forms']}
outcomes={o['id'] for o in proposal['outcomes']}
catalog=read('integration/reference/trace/catalog/60-facets.yaml')
facets={f['id'] for f in catalog['facet_definitions']}
assert set(mapping['facets'])==facets
assert len(accepted)==53 and len(proposed)==72
assert not any(k.startswith(('EST:PB-','EST:TS-')) for k in accepted)
assert mapping['surface']=='/23-5/'
for carrier in mapping['bindings']:
    assert set(carrier['outcomes'])<=outcomes,carrier['carrier']
    for metric in carrier['estimands']:
        e=proposed[metric]
        assert e['profile']==carrier['profile'],(carrier['carrier'],metric)
        assert forms[metric]['claim_class']==carrier['claim_class'],(carrier['carrier'],metric)
        assert carrier['denominators'][metric]==e['q4_denominator']
        assert carrier['case_sets'][metric]==e['q4_case_set']
        assert carrier['claim_class'] in ('DescriptiveClaim','ConditionalDescriptiveClaim')
        if metric.startswith('EST:PB-'):
            assert e['q5_outcome']=='OUT:PB-L-1'
            assert set(e['q4_case_set'])=={'CS:F-CONF-1','CS:F-CONF-ALL-1','CS:F-BREAK-1','CS:F-BREAK-ALL-1'}
            assert e['q4_denominator']=='N_BASE_UNIQUE_MEMBERS'
        if metric.startswith('EST:TS-'):
            assert e['q4_denominator']=='N_BASE_UNIQUE_MEMBERS'
            assert e['q5_outcome']==('OUT:TS-POST-L' if metric=='EST:TS-LINK' else 'OUT:PB-L-1' if metric.endswith('-R') else 'OUT:FINAL-X-1')
    print('PASS',carrier['carrier'],carrier['profile'],carrier['claim_class'])
for binding in mapping['fact_bindings']:
    assert set(binding['facts'])<=facts,binding['carrier']
    assert binding['denominator'] in (None,'N of F for shares only')
    print('PASS fact / presentation boundary:',binding['carrier'])
covered={i for b in mapping['bindings'] for i in b['estimands']}
assert {i for i in covered if i.startswith('EST:TS-')} == {'EST:TS-LINK'} | {'EST:TS-'+k+'-'+e for k in ('CORE','PEAK','REGION','SESSIONS') for e in ('R','X')}
assert (covered & set(accepted)) | set(mapping['accepted_inherited']) == set(accepted)
doc=(ROOT/mapping['source']).read_text(encoding='utf-8')
for facet in facets:assert facet.split(':')[1] in doc
assert (ROOT/'design/sozvezdiya-23-5/src/app.js').is_file()
assert (ROOT/'design/sozvezdiya-24/src/app.js').is_file()
print('ALL GOOD:',len(mapping['bindings']),'statistical carriers,',len(mapping['fact_bindings']),'fact/presentation carriers,',len(facets),'existing facets; accepted 53 unchanged')
