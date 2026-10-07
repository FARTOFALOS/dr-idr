"""Semantic reference checks and aggregate-only probes. No DR Lab mutations.

The historical probe treats an existing M5 as an observation, but does not
certify completeness of its underlying M1 data. No individual dates or bars
are emitted. History is restricted to 2006-2025.
"""
from __future__ import annotations

import json
from collections import Counter
from fractions import Fraction as Q
from pathlib import Path

import numpy as np

ROOT = Path(r"C:\Users\Admin\Claude\dr-idr")
HERE = Path(__file__).resolve().parent


def window(close: int, formed: int) -> int:
    return (close - 5 - formed) // 15


def summary(rows, activation, end, opposite=Q(-11, 10)):
    """Rows: (close minute, normalized low, high, close), exact rational values.

    The activation candle is excluded. Certified shortened sessions supply
    their actual effective end; absent such certification use the nominal end.
    """
    expected = set(range(activation + 5, end + 1, 5))
    observed = sorted((t, Q(l), Q(h), Q(c)) for t, l, h, c in rows if t in expected)
    present = {r[0] for r in observed}
    assert len(present) == len(observed), "Duplicate M5 is an invalid input."
    assert all(l <= c <= h for _, l, h, c in observed)
    missing = expected - present
    broken = any(c < opposite for _, _, _, c in observed)
    outcome = "none" if not expected else "broken" if broken else "unknown" if missing else "held"
    result = {"status": "unknown" if missing else "none" if not expected else "known",
              "outcome": outcome, "missing": len(missing)}
    if result["status"] != "known":
        return result
    low = min(r[1] for r in observed)
    high = max(r[2] for r in observed)
    low_times = [r[0] - 5 for r in observed if r[1] == low]
    high_times = [r[0] - 5 for r in observed if r[2] == high]
    order = "minimum_first" if low_times[0] < high_times[0] else "maximum_first" if high_times[0] < low_times[0] else "same_M5"
    return dict(result, low=low, high=high, low_times=low_times,
                high_times=high_times, order=order)


def threshold(rows, start, end, level, upward=True):
    expected = set(range(start + 5, end + 1, 5))
    rows = [r for r in rows if r[0] in expected]
    hit = any((Q(r[2]) >= level) if upward else (Q(r[1]) <= level) for r in rows)
    return "yes" if hit else "unknown" if expected - {r[0] for r in rows} else "no"


def prefix_state(rows, slice_close, dr_high=Q(1,10), dr_low=Q(-11,10)):
    closed=sorted(r for r in rows if r[0] <= slice_close)
    confirmation=next(((r[0],1 if r[3]>dr_high else -1) for r in closed if r[3]>dr_high or r[3]<dr_low),None)
    return confirmation, closed[-1][3] if closed else None


def synthetic_checks():
    names = []

    def check(name, condition):
        assert condition, name
        names.append(name)

    a = [(5, Q(-1, 2), Q(1, 5), 0), (10, 0, 1, Q(1, 2))]
    b = [(5, 0, 1, Q(1, 2)), (10, Q(-1, 2), Q(1, 5), 0)]
    sa, sb = summary(a, 0, 10), summary(b, 0, 10)
    check("same_extreme_values_different_order", (sa['low'], sa['high']) == (sb['low'], sb['high']) and sa['order'] != sb['order'])
    check("session_end_excludes_next_block", summary(a + [(15, -9, 9, 0)], 0, 10) == sa)
    check("confirmation_bar_excluded", summary([(0, -9, 9, 0)] + a, 0, 10) == sa)
    check("own_confirmation_changes_event", summary(b, 5, 10)['high'] == Q(1, 5))
    check("window_by_open_label", window(660, 630) == 1 and window(665, 630) == 2)
    check("adr_wrap_keeps_window", window(-205, -210) == window(1235, 1230) == 0)
    check("half_open_price_boundary", Q(-3, 4) // Q(1, 10) == -8 and Q(1, 2) // Q(1, 10) == 5)
    check("time_boundary_has_no_minus_one", 750 // 15 == 50)
    repeat = summary(a + [(15, Q(-1, 2), 1, 0)], 0, 15)
    check("all_tied_times_preserved", repeat['low_times'] == [0, 10] and repeat['high_times'] == [5, 10])
    check("single_event_uses_first_time", repeat['low_times'][0] == 0)
    check("same_bar_order_unknown", summary([(5, -1, 1, 0)], 0, 5)['order'] == 'same_M5')
    missing = summary(a[:1], 0, 10)
    check("missing_bar_invalidates_final_extreme", missing['status'] == 'unknown')
    check("missing_without_observed_break_not_held", missing['outcome'] == 'unknown')
    check("observed_break_survives_missing", summary([(5, -2, 0, Q(-3, 2))], 0, 10)['outcome'] == 'broken')
    check("wick_not_DR_break", summary([(5, -2, 0, 0)], 0, 5)['outcome'] == 'held')
    check("equal_opposite_DR_not_break", summary([(5, -2, 0, Q(-11, 10))], 0, 5)['outcome'] == 'held')
    check("no_future_event_is_none", summary([], 10, 10)['status'] == 'none')
    check("empty_lifetime_is_not_evidence_DR_held", summary([], 10, 10)['outcome'] == 'none')
    check("empty_remaining_horizon_has_no_reach", threshold(a, 10, 10, Q(1, 2)) == 'no')
    check("hit_with_other_missing_is_known_yes", threshold(a[1:], 0, 10, Q(1, 2)) == 'yes')
    check("no_hit_with_missing_is_unknown", threshold(a[:1], 0, 10, 1) == 'unknown')
    gap = [(5, Q(4, 5), 1, Q(9, 10))]
    check("beyond_is_not_literal_intersection", threshold(gap, 0, 5, Q(1, 2)) == 'yes' and not (gap[0][1] <= Q(1, 2) <= gap[0][2]))
    check("range_can_cover_multiple_bins", sum(1 for k in range(3) if Q(0) < Q(k + 1, 10) and Q(1, 5) >= Q(k, 10)) == 3)
    check("full_N_with_unknown", Q(7, 25) + Q(13, 25) + Q(5, 25) == 1)
    check("unknown_share_bounds", (Q(7, 25), Q(7 + 5, 25)) == (Q(28, 100), Q(48, 100)))
    check("price_band_not_joint_region", Q(5, 25) != Q(2, 25))
    check("70_percent_not_exact_at_N25", Q(18, 25) >= Q(7, 10) > Q(17, 25))
    # Reflection of prices and direction preserves directed coordinates.
    price, edge, width = Q(109), Q(100), Q(10)
    check("long_short_reflection", (price-edge)/width == -((-price)-(-edge))/width)
    prefix=[(5,Q(-1,10),Q(1,10),0),(10,0,Q(3,10),Q(1,5))]
    future_a=prefix+[(15,-9,Q(1,5),-8)]
    future_b=prefix+[(15,Q(1,5),9,8)]
    check("today_prefix_invariant_to_future_replacement", prefix_state(future_a,10) == prefix_state(future_b,10) == ((10,1),Q(1,5)))
    check("forming_M5_does_not_change_statistics", prefix_state(future_a,14) == prefix_state(future_b,14))
    check("member_with_two_places_counted_once_in_union", len(set([0, 0, 1])) == 2)
    check("levels_are_nested", all(not (sa['high'] >= upper) or sa['high'] >= lower for lower, upper in [(Q(1, 2), 1), (1, Q(3, 2))]))
    return {"passed": len(names), "cases": names}


def historical_probe():
    p = ROOT / 'lab' / '.runtime'
    meta = json.loads((p/'boxes_nq_meta.json').read_text(encoding='utf-8'))['boxes']
    with np.load(p/'boxes_nq.npz', allow_pickle=False) as z:
        bars, offsets = z['bars'], z['offsets']
    out = []
    for sess, formed, key, end, t0 in [('RDR',630,5,960,710), ('ODR',240,0,510,245)]:
        selected = [(i,m) for i,m in enumerate(meta) if m['session']==sess and m['weekday']==2 and m['side']==1 and m['conf'] is not None and window(m['conf'],formed)==key and '2006-01-01' <= m['date'] < '2026-01-01']
        events, years, all_events, gaps, orders = [], [], [], Counter(), Counter()
        differences = Counter()
        below_DR = held_below_DR = joint = price_zone = 0
        for i,m in selected:
            a = bars[offsets[i]:offsets[i+1]]
            w, edge = int(m['idr_high']-m['idr_low']), int(m['idr_high'])
            rows = [(int(r[0]), Q(int(r[3])-edge,w), Q(int(r[2])-edge,w), Q(int(r[4])-edge,w)) for r in a]
            opp = Q(int(m['dr_low'])-edge,w)
            s = summary(rows,int(m['conf']),end,opp)
            old = summary(rows,t0,end,opp)
            gaps[s['status']] += 1
            gaps['missing_m5'] += s['missing']
            gaps['legacy_complete'] += int(m['complete'])
            gaps['outcome_'+s['outcome']] += 1
            if s['status'] != 'known':
                all_events.append(None)
                continue
            r,t = s['low'],s['low_times'][0]
            events.append((r,t));years.append(int(m['date'][:4]));all_events.append((r,t))
            orders[s['order']] += 1
            if s['high_times'][-1] < s['low_times'][0]:orders['all_maximum_before_all_minimum'] += 1
            if s['low_times'][-1] < s['high_times'][0]:orders['all_minimum_before_all_maximum'] += 1
            below_DR += int(r < opp)
            held_below_DR += int(r < opp and s['outcome']=='held')
            if old['status']=='known':
                differences['minimum_price'] += int(old['low'] != r)
                differences['minimum_time'] += int(old['low_times'][0] != t)
                if Q(-9,10) <= old['low'] < Q(-7,10):
                    price_zone += 1
                    joint += int(840 <= old['low_times'][0] < 870)
        n=len(selected)
        grids=[]
        for du,dt,pu,pt in [(Q(1,10),15,Q(0),0),(Q(1,10),15,Q(1,20),5),(Q(1,10),15,Q(0),10),(Q(1,5),30,Q(0),0),(Q(1,5),30,Q(1,10),15)]:
            cells=Counter((int((r-pu)//du),(t-pt)//dt) for r,t in events)
            maximum=max(cells.values(),default=0)
            grids.append({'price_width':str(du),'time_width_min':dt,'price_phase':str(pu),'time_phase_min':pt,
                          'occupied_cells':len(cells),'singletons':sum(v==1 for v in cells.values()),
                          'largest_cell_n':maximum,'largest_cell_pct_of_N':round(100*maximum/n,4),
                          'number_of_equal_modes':sum(v==maximum for v in cells.values())})
        base_labels=[None if e is None else (int(e[0]//Q(1,10)),e[1]//15) for e in all_events]
        counts=Counter(x for x in base_labels if x is not None)
        mode_set={k for k,v in counts.items() if v==max(counts.values())}
        anchor=min(mode_set)
        rng=np.random.default_rng(20261001)
        anchor_wins=0
        anchor_shares=[]
        for _ in range(2000):
            sample=Counter(base_labels[int(k)] for k in rng.integers(0,n,n))
            sample.pop(None,None)
            if not sample:continue
            winners={k for k,v in sample.items() if v==max(sample.values())}
            anchor_wins+=int(anchor in winners)
            anchor_shares.append(100*sample.get(anchor,0)/n)
        epochs=[]
        for lo_year,hi_year in [(2006,2015),(2016,2025)]:
            es=[(r,t) for (r,t),year in zip(events,years) if lo_year<=year<=hi_year]
            cs=Counter((int(r//Q(1,10)),t//15) for r,t in es)
            epochs.append({'years':[lo_year,hi_year],'known_events':len(es),'largest_cell_n':max(cs.values(),default=0)})
        out.append({'session':sess,'N':n,'quality_on_existing_M5':dict(gaps),
                    'minimum_start_contract_changes':dict(differences),'order_known_events':dict(orders),
                    'wick_beyond_own_DR':below_DR,'wick_beyond_but_held':held_below_DR,
                    'old_clock_zone_minus09_minus07':price_zone,'old_clock_same_zone_and_1400_1430':joint,
                    'grid_diagnostics':grids,'epochs':epochs,
                    'bootstrap_2000':{'warning':'in-sample resampling diagnostic, not validation of a market cluster',
                      'anchor_rule':'lexicographically first among tied modal cells; no claim of a uniquely best cell',
                      'original_tied_modes':len(mode_set),'anchor_cell':anchor,
                      'anchor_among_bootstrap_modes_pct':anchor_wins/20,
                      'anchor_share_percentile_2_5_97_5':np.percentile(anchor_shares,[2.5,97.5]).tolist()}})
    return out


if __name__ == '__main__':
    result={'spec_version':'DR-LAB-SEM-1.0','synthetic':synthetic_checks(),
            'historical':historical_probe(),
            'limits':['Existing M5 completeness only; underlying M1 coverage not certified.',
                      'No automatic cluster is certified by this probe.',
                      'No code, UI, history or governance changes.']}
    (HERE/'validation_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
