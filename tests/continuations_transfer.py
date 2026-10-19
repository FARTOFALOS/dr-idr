"""«Продолжения»: the transfer of meaning across one real scene, checked independently of the engine (lens 19.10,
«две системы доказательства», result 1). NQ · RDR · 17.12.2025, the target +1.7…+1.9 SD in the window 11:25–11:40,
releases on the closed M5 11:10 … 11:40. Each relation is recomputed here from the published witnesses and ids:

  Φ  the pinned band moves into every historical case's OWN directed frame (its edge, width, direction), not by price;
  S  the transition between two releases names exactly who entered and who left the position set;
  H  before the window the question stays the same; inside it a new residual question with its own risk set, whose
     every exclusion is a visit (or an unknown) in the elapsed part of the window, or a later activation;
  O  a known visit becomes a fact that later releases keep, with no new percentage.

Needs the local history base (lab/.runtime); writes nothing.   python -B tests/continuations_transfer.py
"""
from fractions import Fraction as Q
import copy
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lab'))
import continuations24 as W  # noqa: E402
import scene24 as S  # noqa: E402


def check(ok, name):
    if not ok:
        raise AssertionError(name)
    print('PASS ' + name, flush=True)


def visit(path, grid, lo, hi, w, first, last):
    """YES / NO / UNKNOWN of one witness on the M5 closing in [first, last], written here from the definition."""
    gap = False
    for T, p in zip(grid, path):
        if not first <= T <= last:
            continue
        if p is None or any(v is None or not math.isfinite(v) for v in p):
            gap = True
            continue
        if Q(p[0]) < hi * w and Q(p[1]) >= lo * w:
            return 'YES'
    return 'UNKNOWN' if gap else 'NO'


def main():
    lo, hi = Q(17, 10), Q(19, 10)
    req = dict(instrument='NQ', session='RDR', date='2025-12-17', scope='all',
               target=dict(low=[17, 10], high=[19, 10], first_close=690, last_close=700, created_at=670))
    rel, prev = {}, None
    for cut in (670, 675, 680, 685, 690, 695, 700):
        r = W.response(dict(req, at=cut, previous=prev))
        rel[cut] = r
        prev = r.get('release_id') or prev
    a = rel[670]['proof']
    grid = a['grid']

    # Φ — one physical band, every case read in its own frame
    phys = {cut: r['proof']['target']['physical_edges'] for cut, r in rel.items()}
    check(len({str(v) for v in phys.values()}) == 1, 'Φ: the pinned physical band is the same in all seven releases')
    t = a['target']['frame']
    edge, width, d = Q(t['edge']), Q(t['width']), t['direction']
    want = [edge + d * width * lo, edge + d * width * hi]
    check([Q(*x) for x in a['target']['physical_edges']] == want,
          "Φ: today's band = today's IDR edge + direction × width × [1.7, 1.9) (a short counts down from IDR low)")
    sides = {x['direction'] for x in a['witnesses']}
    bad = [x['id'] for x in a['witnesses']
           if visit(x['path'], grid, lo, hi, Q(x['w']), 690, 700) != x['outcome']]
    check(not bad and sides == {1, -1},
          f'Φ: every one of {len(a["witnesses"])} witnesses, longs and shorts, gets its outcome from the band in its own '
          'directed ticks (edge, width), recounted here')
    widths = {x['w'] for x in a['witnesses']}
    check(len(widths) > 10, 'Φ: the band is carried by proportion of each own IDR width, not by points of price')

    # S — transitions between releases
    for x, y in ((670, 675), (675, 680), (680, 685), (685, 690)):
        A, B = set(rel[x]['proof']['position_ids']), set(rel[y]['proof']['position_ids'])
        cmp = rel[y].get('comparison') or {}
        check(cmp.get('entered') == len(B - A) and cmp.get('left') == len(A - B),
              f'S: {x // 60:02d}:{x % 60:02d}→{y // 60:02d}:{y % 60:02d} names exactly who entered ({len(B - A)}) and left ({len(A - B)}) the position set')
    check(any(set(rel[y]['proof']['position_ids']) - set(rel[x]['proof']['position_ids'])
              for x, y in ((670, 675), (675, 680), (680, 685), (685, 690))),
          'S: a later set is not a subset of the earlier one (a new M5 is new knowledge, not a narrowing)')

    # H — the same question before the window, a residual question inside it
    qid = {cut: rel[cut]['proof']['question']['id'] for cut in (670, 675, 680, 685, 690)}
    check(qid[670] == qid[675] == qid[680] == qid[685], 'H: before the window every release answers the same question')
    q690 = rel[690]['proof']['question']
    check(qid[690] != qid[685] and q690['conditions'] and q690['conditions'][0]['kind'] == 'WINDOW_NO_VISIT'
          and q690['conditions'][0]['last_close'] == 690 and q690['first_close'] == 695,
          'H: inside the window a new residual question: no visit in the elapsed part (to 11:30), remaining M5 from 11:35')
    p690 = rel[690]['proof']
    pos, risk = set(p690['position_ids']), set(p690['risk_ids'])
    check(risk < pos and (rel[690].get('comparison') or {}).get('same_question') is False,
          'H: its risk set is a named part of the position set, and the transition says the question changed')
    raw = W._releases[rel[690]['release_id']]
    reasons = raw['risk_set']['exclusions']
    cases, source_grid = W.corpus('NQ', 'RDR')
    expected = {}
    for case in cases:
        if case['id'] not in pos:
            continue
        elapsed = visit(case['P'], source_grid, lo, hi, int(case['w']), 690, 690)
        if case['a'] >= 0 and source_grid[case['a']] >= 690:
            expected[case['id']] = 'NOT_ACTIVE_AT_WINDOW_START'
        elif elapsed != 'NO':
            expected[case['id']] = 'WINDOW_ALREADY_VISITED' if elapsed == 'YES' else 'WINDOW_VISIT_UNKNOWN'
    check(reasons == expected and set(expected) == pos - risk and p690['risk_exclusions'] == expected,
          'H: every exclusion and its cause independently follow from source activation and actual elapsed M5 ranges')
    check(sum(p690['exclusion_counts'].values()) == len(pos) - len(risk),
          'H: displayed reasons partition exactly the cases excluded from the residual support')
    fam, _, day = S._family('NQ', 'RDR', 690, '2025-12-17', 'conf:all')
    today = W.rows_today(fam, day, source_grid, 690)
    bad = copy.deepcopy(raw)
    for cid in bad['risk_set']['exclusions']:
        bad['risk_set']['exclusions'][cid] = ('NOT_ACTIVE_AT_WINDOW_START'
            if expected[cid] == 'WINDOW_ALREADY_VISITED' else 'WINDOW_ALREADY_VISITED')
    rejected = W.publish(bad, p690['witnesses'], cases, today, source_grid, dict(day, _F_ids=fam['ids']))
    check(rejected['status'] == 'WITNESS_MISMATCH' and not rejected['contract'].get('bundles'),
          'H counterexample: correct membership/count with false exclusion causes cannot publish')
    s = p690['support']
    check(s['n_total'] == len(risk) and s['yes'] + s['no'] + s['unknown'] == s['n_total'],
          'H: the residual share is counted on the risk set only (yes + no + unknown = its n)')

    # O — the fact
    f = rel[695]['proof']
    check(rel[695]['status'] == 'FACT_YES' and f['observed']['available_at'] == 695 and not f['witnesses'],
          'O: the visit at the M5 closing 11:35 becomes a fact; the conditional paths are withdrawn')
    check(rel[700]['status'] == 'FACT_YES' and rel[700]['proof']['observed'] == f['observed']
          and not rel[700]['contract'].get('bundles'), 'O: the next release keeps the same fact and issues no percentage')
    print('ALL GOOD')


if __name__ == '__main__':
    main()
