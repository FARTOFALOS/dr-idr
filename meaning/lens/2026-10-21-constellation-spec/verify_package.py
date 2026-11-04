"""Check provenance, declared parameters, current/proposed IDs and evidence scope."""
import hashlib
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path, lf=False):
    data = path.read_bytes()
    return hashlib.sha256(data.replace(b'\r\n', b'\n') if lf else data).hexdigest()


def run():
    config = json.loads((HERE/'algorithm.json').read_text())
    result = json.loads((HERE/'probe-results.json').read_text())
    counter = json.loads((HERE/'semantic-counterexamples.json').read_text())
    registry = json.loads((ROOT/'contract/build/registry.json').read_text())['registry']
    spec = json.loads((ROOT/'contract/build/runtime_spec.json').read_text())
    ids = {x['id'] for rows in registry.values() if isinstance(rows, list) for x in rows if isinstance(x, dict) and 'id' in x}
    checks = {}
    checks['protocol_before_run_unchanged'] = result['protocol_sha256'] == sha(HERE/'PROTOCOL.md') == '622f59da24bf195e3d2c2452ad2e379edaddbced7e3dacd95b7345c81c97b3fd'
    checks['exact_probe_source'] = result['source_sha256'] == sha(HERE/'probe.py')
    checks['calculators_unchanged'] = all(sha(ROOT/name, True) == value for name, value in result['calculator_sha256_lf'].items())
    checks['declared_parameters'] = result['price_radius'] == '3/20' and result['time_radius'] == config['time_radius_minutes'] == 20
    checks['not_deployed'] = config['runtime_enabled'] is False and config['standing'] == 'PROPOSED_RESEARCH_ONLY'
    checks['accepted_ids_exist'] = all(x in ids for x in config['preserved_ids'])
    checks['new_ids_not_silently_registered'] = all(x not in ids for x in config['proposed_ids'])
    checks['real_schema_boundary'] = all([
        spec['classes']['DensityAlgorithmSpecification']['slots']['grid']['required'],
        spec['classes']['DensityRegion']['slots']['n_cells']['required'],
        spec['classes']['DensityRegion']['slots']['mask_verified']['required'],
    ])
    checks['synthetic_pass'] = result['synthetic']['outcome'] == 'PASS' and result['synthetic']['assertions'] == 31
    hist = result['historical']
    checks['declared_scope'] = hist['family_event_maps'] == 540 and len(hist['diagnostics']) == 18
    checks['history_closed'] = all(x['history'].endswith('2025-12-31') for x in hist['base_versions'].values())
    checks['source_state_ledgers'] = all(sum(d['source_statuses'].values()) == d['N'] and d['source_statuses'].get('known', 0) == d['known'] for d in hist['diagnostics'])
    checks['semantic_counterexample'] = counter['outcome'] == 'COUNTEREXAMPLES_CONFIRMED' and counter['ccpb_new_high_branch']['high_then_threshold_lower_close_then_higher_close_is_observed'] is True
    keys = ['label','N','known','old','cn1','deletion_recovery_old','deletion_recovery_cn1','scales','ym_zone_aggregates']
    numbers = {'groups': hist['groups'], 'diagnostics': [{k:x[k] for k in keys} for x in hist['diagnostics']]}
    numeric_digest = hashlib.sha256(json.dumps(numbers, sort_keys=True).encode()).hexdigest()
    checks['numeric_results_preserved_after_provenance_and_domain_checks'] = numeric_digest == '25dc061c850eb0d2352754f7844dd4b7a3ac22697b96796975977d190af3ae06'
    means = {}
    for e in ['R','X']:
        rows = [x for x in hist['diagnostics'] if x['label'].split()[2] == e]
        means[e] = {'maps': len(rows), 'old': statistics.mean(x['deletion_recovery_old'] for x in rows),
                    'cn1': statistics.mean(x['deletion_recovery_cn1'] for x in rows),
                    'cn1_higher': sum(x['deletion_recovery_cn1'] > x['deletion_recovery_old'] for x in rows)}
    output = {'outcome': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks,
              'deletion_diagnostics': means, 'numeric_digest': numeric_digest,
              'boundaries': ['research prototype only', 'not walk-forward', 'not operator acceptance', 'no active schema or UI change'],
              'artifact_hashes': {p.name: sha(p) for p in HERE.iterdir() if p.is_file() and p.name != 'validation.json'}}
    (HERE/'validation.json').write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(run())
