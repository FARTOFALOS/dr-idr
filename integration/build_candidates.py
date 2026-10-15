"""Build the existing PRE/ARRIVE proposals separately, with PROPOSED standing. Does not edit accepted products."""
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
HERE=Path(__file__).resolve().parent/'candidates'
EDITION='DR-LAB-CANDIDATES-1'

def dump(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

def main():
    module=importlib.util.spec_from_file_location('contract_builder',ROOT/'contract/tools/build.py')
    builder=importlib.util.module_from_spec(module); module.loader.exec_module(builder)
    src=HERE/'registry/00-editions.yaml'
    candidate=yaml.safe_load(src.read_text(encoding='utf-8'))
    accepted=yaml.safe_load((ROOT/'contract/registry/00-editions.yaml').read_text(encoding='utf-8'))
    extra_profiles=[p for p in candidate['profiles'] if p['id'] not in {x['id'] for x in accepted['profiles']}]
    for p in extra_profiles:
        p['edition']=EDITION
        if not p['note'].startswith('CANDIDATE FOR LOCAL REVIEW;'):
            p['note']='CANDIDATE FOR LOCAL REVIEW; NOT PRODUCT ACCEPTED. '+p['note']
    extras=[s for s in candidate['source_references'] if s['id']!='SRC:CANDIDATES-1' and s['id'] not in {x['id'] for x in accepted['source_references']}]
    proposal='integration/candidates/SC11-proposal.md'
    digest=hashlib.sha256((ROOT/proposal).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    accepted['editions'].append(dict(id=EDITION,version='1',sc_ref=['§12.5','§12.6'],grounds='PROPOSAL',
        title_ru='PRE/ARRIVE: отдельные кандидаты для локального испытания',document_path=proposal,
        document_sha256_lf=digest,edition_status='PROPOSED',supersedes='DR-LAB-SC-1.1',source_refs=['SRC:CANDIDATES-1'],
        note='Imported source proposal, not a replacement or ratification of accepted SC-1.1. No C2/C3.'))
    accepted['profiles']+=extra_profiles
    accepted['source_references']+=extras+[dict(id='SRC:CANDIDATES-1',sc_ref=['§12.5','§12.6'],grounds='PROPOSAL',role='DEFINITION',document=proposal,note='Frozen source from PR7 1412567, kept separately from the accepted normative document.')]
    # Idempotent: an already prepared edition remains the same, not another acceptance record.
    dump(src,accepted)
    spec=yaml.safe_load((ROOT/'contract/schema/dr_lab_sc.yaml').read_text(encoding='utf-8'))
    proposal_schema=yaml.safe_load(subprocess.check_output(['git','-C',str(ROOT),'show','1412567:contract/schema/dr_lab_sc.yaml']).decode('utf-8'))
    changed_enums={k:v for k,v in proposal_schema['enums'].items() if v!=spec['enums'].get(k)}
    changed_enums['SurfaceProfile']['permissible_values']['SC11_CONTINUATIONS_0_1']={'description':'separate fixed-window continuation candidate, C1 only'}
    dump(HERE/'schema.yaml',dict(id='https://dr-lab.local/candidates',name='dr_lab_candidates',
        imports=['../../contract/schema/dr_lab_sc'],enums=changed_enums))
    builder.SCHEMA=HERE/'schema.yaml'; builder.REG_DIR=HERE/'registry'; builder.OUT=HERE/'build'
    builder.DOC=proposal; builder.EDITION=EDITION
    builder.EXTRA_SOURCES=[ROOT/'contract/schema/dr_lab_sc.yaml',ROOT/'spec/DR-LAB-Semantic-Contract-1.1-(patched).md']
    builder.build()

if __name__=='__main__': main()
