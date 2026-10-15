"""Integrity/coverage of the handoff artifacts; this cannot certify their semantic conclusions."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
PACKAGE=ROOT/'meaning/lens/2026-10-14-integration'

def main():
    failures=[]; checked_links=0
    docs=list(PACKAGE.rglob('*.md'))+[ROOT/'spec/DR-LAB-INTEGRATION-1.0.md']
    for p in docs:
        if p.name=='input-deep-research.md': continue
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if target.startswith(('http:','https:','#','app:')): continue
            target=target.split('#',1)[0].strip('<>')
            if not (p.parent/target).resolve().exists(): failures.append('broken local link: '+str(p.relative_to(ROOT))+': '+target)
            checked_links+=1
    src=json.loads((PACKAGE/'sources.json').read_text(encoding='utf-8'))
    assert [x['pr'] for x in src['layers']]==list(range(1,14))
    assert src['refs']['accepted']!=src['refs']['pr1']!=src['refs']['pr1_merge']
    assert src['layers'][1]['head']==src['layers'][10]['head']
    digest=hashlib.sha256((PACKAGE/'input-deep-research.md').read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    assert digest==src['input_sha256_lf']
    census=json.loads((PACKAGE/'ontology-sources.json').read_text(encoding='utf-8'))
    assert len(census['baseline_definitions']['estimands'])==53 and len(census['candidate_definitions']['estimands'])==59
    assert set(range(1,14))<={pr for f in census['files'] for pr in f['prs']}
    comparison=json.loads((PACKAGE/'comparison/report.json').read_text(encoding='utf-8'))
    assert comparison['pairs']==20 and comparison['rendered_screens']==40
    for scene in comparison['scenes']:
        assert all(scene['checks'].values())
        for variant,p in scene['images'].items():
            assert hashlib.sha256((PACKAGE/'comparison'/p).read_bytes()).hexdigest()==scene['image_sha256'][variant]
    assert json.loads((PACKAGE/'comparison/gallery-check.json').read_text())==dict(checked=60,problems=[])
    assert json.loads((PACKAGE/'relation-checks.json').read_text())['status']=='PASS'
    main_ref=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','refs/heads/main']).decode().strip()
    assert main_ref==src['baseline']
    # The only executable change to the research checkout is the shared collector export/argument interface.
    for folder in ('lab','contract','design'):
        diff=subprocess.check_output(['git','-C',str(ROOT),'diff','--name-only','f954046','--',folder]).decode().strip()
        assert not diff, 'product sources changed: '+diff
    forbidden=[p for p in PACKAGE.rglob('*') if p.is_file() and (p.name.endswith('.local.json') or p.suffix=='.npz')]
    assert not forbidden, 'private records inside the public handoff'
    out=dict(status='PASS' if not failures else 'FAIL',checked_local_links=checked_links,failures=failures,
             pr_sources=13,baseline_unchanged=True,product_sources_unchanged=True,
             comparison_image_hashes='PASS',scope='artifact integrity and declared coverage; not independent semantic or human acceptance')
    (PACKAGE/'package-check.json').write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False)); return bool(failures)

if __name__=='__main__': raise SystemExit(main())
