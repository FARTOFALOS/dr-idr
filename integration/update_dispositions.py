"""Build the current disposition index without rewriting the frozen pre-main review."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'integration'


def main():
    restored=json.loads((HERE/'restored-sources.json').read_text(encoding='utf-8'))
    for item in restored:
        if item['path']=='studies/q1_pilot_2026_10_12/reading_check.md':
            item.update(destination='integration/reference/proposals/pr6-reading-check.md',
                        standing='ARCHIVED_PROPOSAL_READING_CHECK_DECLINED_IN_PR8_NOT_REACTIVATED')
    (HERE/'restored-sources.json').write_text(json.dumps(restored,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    before=json.loads((HERE/'pr-review-2026-10-15/units.json').read_text(encoding='utf-8'))
    units=before['units']
    updates={
        'U10':('PRESERVED_RESEARCH','studies/kadr_2026_10_12/README.md','Original A-E evidence restored with source hashes; no new method admission.'),
        'U13':('ADAPTED_FIXED_PREFIX_IDENTITY','lab/q1/engine.py','Future complete/fail metadata removed from prefix identity; known frame changes still change identity; old issues untouched.'),
        'U15':('ADAPTED_REVEAL_SOURCE_AND_ASYNC_GUARDS','lab/q1/server.py','Saved outcome basis must match the revealed full source; stale client replies discarded. Standalone pilot remains separate.'),
        'U20':('ADAPTED_TO_OWN_CONTINUATION_SUPPORT','design/sozvezdiya-24/src/continuations.js','Actual per-case paths include M outside F; their revision, outcome and number share one release. No new default family-path layout.'),
        'U22':('ADAPTED_FIXED_TARGET_CONTINUITY','design/sozvezdiya-24/src/continuations.js','Fixed target survives new cuts and representation changes. Residual question is explicit; historical proposal text restored.'),
        'U26':('PRESERVED_DESIGN_SOURCE','meaning/19-svodka-kandidat.md','Source text retained; proposed permanent summary composition not adopted.'),
        'U28':('CURRENT_ENTRY_AND_PROVENANCE_INDEX','integration/DELIVERY.md','Chain, exact source heads, 30 dispositions, sources and tests available from main entry; old proposals retain standing.'),
        'U29':('PRESERVED_REPRODUCTION_EVIDENCE','studies/q1_pilot_2026_10_12/README.md','Research package restored. The declined reading check is archival only, not reactivated.'),
        'U30':('ADAPTED_LOADED_SOURCE_AND_DATA_GUARD','start-dr-lab.ps1','Launcher compares loaded source/data versions and workspace; current process and one local port are verified.')
    }
    for unit in units:
        unit['pre_main_status']=unit.pop('current_status')
        unit['pre_main_destination']=unit.pop('current_destination')
        state,destination,note=updates.get(unit['id'],(unit['pre_main_status'],unit['pre_main_destination'],unit['recommendation']))
        unit.update(status=state,destination=destination,implementation_note=note,
                    standing='IMPLEMENTATION_OR_PRESERVED_SOURCE_NOT_BLANKET_PRODUCT_ACCEPTANCE')
    result=dict(version='PR-DISPOSITIONS-IMPLEMENTATION-1',source_review='pr-review-2026-10-15/units.json',
                source_heads='pr-review-2026-10-15/sources.json',units=units,
                completion_rule='Close old PRs as individually integrated/preserved/deferred only after the tested integrated result reaches main; retain original branches and PR history.')
    (HERE/'pr-dispositions.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('30 current dispositions; 11 restored source witnesses; declined check kept archival')


if __name__=='__main__':main()
