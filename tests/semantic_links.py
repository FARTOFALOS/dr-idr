"""Links between what the registry says and what the executable computes (review of 2026-10-19).

The review of Codex's direction (meaning/lens/2026-10-19-sborka/01-recenziya.md) found places where a registry text
described another question than the one computed. An agent who trusts the text would «fix» the computation into
another question and change the numbers. Each check pins one link from both sides: a discriminating synthetic case
for the executable and the words of the compiled registry. Stdlib + numpy; no market data, no server.

    python -B tests/semantic_links.py
"""
import copy
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lab'))
import contract as C  # noqa: E402
import continuity24 as E  # noqa: E402


def check(ok, name):
    if not ok:
        raise AssertionError(name)
    print('  ok  ' + name, flush=True)


def registry(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))['registry']


def by_id(reg, coll, ident):
    return next(x for x in reg[coll] if x['id'] == ident)


def rest_horizon():
    """B-LEVEL-REST / B-VISIT-REST. «После среза» is the common remainder (t, H] for every member: SC-1.1 §12.4
    «общий остаток после t», the typed outcome COMMON_CUT_EXCLUSIVE, the 07.10 node of meaning/07, the page
    (reachCount / visitCount) and the reference. A member that activates after t contributes its M5 between t and its own
    activation. The case discriminates: its only touch of +1.0 is the M5 closing at 10:45, after t = 10:40 and before its
    own activation at 10:50; the other reading, (max(t, own activation), H], says NO."""
    grid = list(range(635, 961, 5))
    w, cut = 100, 640
    path = [[-10, 10, 0] for _ in grid]
    path[grid.index(645)] = [0, 110, 40]            # a wick to +1.1 SD, the close inside the box: not its activation
    member = dict(id='m', act=650, w=w, path=path, R=dict(s='none'), X=dict(s='none'))
    fam = dict(grid=grid, schedule=dict(formed=630, end=960), N=1, members=[member])
    end = fam['schedule']['end']
    check(C.ref_reach(path, grid, cut, end, 1, 1, w, True) == 'yes'
          and C.ref_reach(path, grid, max(cut, member['act']), end, 1, 1, w, True) == 'no',
          'REST: the synthetic member discriminates the common cut from max(t, own activation)')
    check(C.ref_visit(path, grid, cut, end, 10, 11, w) == 'yes'
          and C.ref_visit(path, grid, max(cut, member['act']), end, 10, 11, w) == 'no',
          'REST: the same member discriminates the two readings for a band visit')
    passports = [dict(id='lvl', estimand='EST:B-LEVEL-REST', params=dict(a=1, b=1, up=True, cut=cut),
                      yes_count=1, unknown_count=0, no_event_count=0, N=1),
                 dict(id='band', estimand='EST:B-VISIT-REST', params=dict(k0=10, k1=11, cut=cut),
                      yes_count=1, unknown_count=0, no_event_count=0, N=1),
                 dict(id='full', estimand='EST:B-LEVEL-FULL', params=dict(a=1, b=1, up=True),
                      yes_count=0, unknown_count=0, no_event_count=1, N=1)]
    check(C.verify_passports(fam, [], 0.25, passports) == [],
          'REST: the reference counts the member from the common cut; FULL from its own activation')
    reg = registry('contract/build/registry.json')
    for est in ('EST:B-LEVEL-REST', 'EST:B-VISIT-REST'):
        x = by_id(reg, 'estimands', est)
        o = by_id(reg, 'outcomes', x['q5_outcome'])
        text = x['q6_time_ru']
        check(o['horizon_start'] == 'COMMON_CUT_EXCLUSIVE' and 'max(' not in text and 'общий остаток' in text
              and 'собственной активацией' in text,
              est + ': the registry words say the common remainder, as its outcome and the reference do')


def fixture():
    """Continuations: a fixed band [0.4, 0.6) SD, window of M5 closing 10:25-10:40, today never in it."""
    grid = list(range(605, 666, 5))
    frame = E.Frame('NQ', '2025-12-17', 'RDR', 1, '100', '10', 605, 665)
    today = dict(id='today', date=frame.date, instrument='NQ', block='RDR', side=1, tick='0.1', edge='100',
                 a=0, w=100, oppv=-200, P=np.tile([-5., 5., 0.], (len(grid), 1)))
    cases = []
    for i in range(25):
        c = copy.deepcopy(today)
        c.update(id=str(i), date='2020-12-17')
        cases.append(c)
    cases[1]['P'][grid.index(615)] = [40, 60, 0]     # at the place BEFORE the window, the close back at today's 0
    cases[2]['P'][grid.index(625)] = [40, 60, 0]     # at the place in the window's first M5
    target = E.pin(frame, '.4', '.6', 625, 640, 610)
    original = dict(family_id='F', snapshot_id='FS', N=1, ids=['0'], members=[dict(id='0')])
    return cases, today, grid, target, original


def pos_geo():
    """CMP:C-POS / CF:C-WINDOW. POS_GEO compares the position of the close on the common clock; an earlier visit of the
    place does not exclude a case (lens 15.10 scene continuity §2, DELIVERY «посещение цены до закреплённого окна не
    доказывает посещения внутри него»). Inside the window the residual question adds its own condition: no visit in the
    elapsed part of the window (CS:C-RISK). The set G is not the family F."""
    cases, today, grid, target, original = fixture()
    before = E.release(cases, today, grid, target, 620, original)
    check('1' in before['selection']['M'] and '1' in before['risk_set']['ids'],
          'POS_GEO: a case that was at the place before the window stays in the set and in the support')
    check(len(set(before['selection']['M']) - set(original['ids'])) > 0,
          'POS_GEO: the set G/M reaches beyond the original family F')
    inside = E.release(cases, today, grid, target, 630, original)
    check(inside['question']['conditions'][0]['kind'] == 'WINDOW_NO_VISIT'
          and '1' in inside['risk_set']['ids']
          and inside['risk_set']['exclusions'].get('2') == 'WINDOW_ALREADY_VISITED_OR_UNKNOWN',
          'residual: only a visit inside the elapsed part of the window excludes a case')
    reg = registry('integration/candidates/build/registry.json')
    cmp_ = by_id(reg, 'comparisons', 'CMP:C-POS')
    words = ' '.join([cmp_['title_ru'], *cmp_['features']])
    check('not yet at the place' not in words and 'ещё не были у места' not in words
          and 'earlier visits of the place do not exclude' in words,
          'CMP:C-POS: the registry words say what continuity24.select compares (prior visits allowed)')
    subject = by_id(reg, 'claim_forms', 'CF:C-WINDOW')['subject_ru']
    check('сессии семьи' not in subject and 'исторические случаи' in subject and 'не только семья F' in subject,
          'CF:C-WINDOW: the subject is the historical cases of POS_GEO, not the family F')


def pullback_words_side_neutral():
    """The candidate words of the «Сейчас» pullback line (operator 08.10, trial «nowmarks») are read for a long and a
    short alike; R is the pullback against the confirmation, so in a short it goes UP. «ниже сегодняшнего дна» was
    true for a long only (found 19.10 on the live NQ ODR short)."""
    page = json.loads((ROOT / 'integration/candidates/build/page_registry.json').read_text(encoding='utf-8'))
    words = [t for est in ('EST:N-NEW-R', 'EST:N-IF-NEW-R', 'EST:N-TIME-R')
             for key, v in page['forms'][est]['labels'].items() if key.endswith('_mark') for t in v.values()]
    side = [w for w in words if any(s in w.lower() for s in ('дно', 'дна', 'ниже', 'выше', 'минимум', 'максимум'))]
    check(len(words) >= 4 and not side, 'NOW pullback marks: the candidate words name no side (' + str(len(words)) + ' labels)')


def claim_classes():
    """The share of a constellation is C0 (DescriptiveClaim, an unconditional share of F), «Сейчас» is C1
    (ConditionalDescriptiveClaim); the audit of 18.10 called the zone share C1 (review of 19.10, point 5)."""
    reg = registry('contract/build/registry.json')
    form = {f['estimand']: f['claim_class'] for f in reg['claim_forms']}
    check(form['EST:B-ZONE-R'] == form['EST:B-ZONE-X'] == 'DescriptiveClaim'
          and form['EST:N-NEW-R'] == 'ConditionalDescriptiveClaim',
          'claim classes: the zone share is C0, the NOW share is C1')


if __name__ == '__main__':
    print('Semantic links: registry words = executable definitions')
    failed = []
    for fn in (rest_horizon, pos_geo, pullback_words_side_neutral, claim_classes):
        try:
            fn()
        except AssertionError as exc:
            failed.append(str(exc))
            print('  FAIL ' + str(exc), flush=True)
    print('\nALL GOOD' if not failed else '\nFAILED: ' + '; '.join(failed))
    sys.exit(1 if failed else 0)
