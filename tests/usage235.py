"""The usage journal of 23.5 (lab/usage235.py, spec/DR-LAB-23-5-USAGE-TRACKER.md): the store, offline.

    python -B tests/usage235.py

A temporary database only (never lab/.runtime): an event is validated field by field; a packet is written in one
transaction; a resent event_id is ignored; an invalid event is refused on its own and noted as a gap; the export keeps
live and review apart, names the build, counts availability against use, and filters by instrument and session; the
journal never stores a price or text (the trace has only the semantic coordinates). Exit code 0 = every check passed.
"""
import json
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'lab'))
import usage235 as U  # noqa: E402

bad = 0


def check(ok, what):
    global bad
    bad += not ok
    print(('  ok   ' if ok else '  FAIL ') + what)


VISIT = str(uuid.uuid4())
NOW = datetime.now(timezone.utc)
seq = 0


def ev(kind, **f):
    global seq
    seq += 1
    e = dict(schema_version=1, event_id=str(uuid.uuid4()), visit_id=f.pop('visit', VISIT), seq=seq,
             started_at_utc=(NOW - timedelta(minutes=30) + timedelta(seconds=seq)).strftime('%Y-%m-%dT%H:%M:%S.000Z'), kind=kind,
             context=f.pop('context', dict(instrument='NQ', trading_date='2026-11-23', session='RDR', mode='live', at=640, status='confirmed')),
             build='test0001')
    e.update(f)
    return e


def post(events, db):
    return U.accept(json.dumps(dict(schema_version=1, events=events)).encode('utf-8'), db)


with tempfile.TemporaryDirectory() as tmp:
    db = Path(tmp) / 'u.sqlite3'
    batch = [ev('visit', feature='page.open', via='navigate'),
             ev('available', feature='top.instrument'), ev('available', feature='top.antb'), ev('available', feature='chart.tpwin'),
             ev('action', feature='instrument', object='ES', via='mouse', data=dict(**{'from': 'top.instrument'})),
             ev('hover_view', feature='chart.tpwin', object='W1', duration_ms=3400, end_reason='pointer_left_object'),
             ev('hover_view', feature='chart.zone', object='X1', duration_ms=1200, end_reason='replaced'),
             ev('hover_view', feature='chart.tpwin', object='W1', duration_ms=900, end_reason='idle'),
             ev('open_view', feature='open.tp_window', object='W1', duration_ms=30000, end_reason='idle'),
             ev('dead_click', feature='click.chart', object='empty', via='mouse', data=dict(min=-40, idr=1.9, near='reach70')),
             ev('trace', feature='pointer', duration_ms=900, data=dict(p=[[300, 0, 0.4, 0.3, -40, 1.9, 0.7, 'reach70'], [600, 5, 0.9, 0.5]])),
             ev('action', feature='view.time', object='more_past', via='drag', data=dict(left_min=-60),
                context=dict(instrument='ES', trading_date='2025-12-17', session='RDR', mode='history'))]
    r = post(batch, db)
    check(r['written'] == len(batch) and not r['rejected'], f"a valid packet is written whole ({r['written']}/{len(batch)})")
    r2 = post(batch[:5], db)
    check(r2['written'] == 0 and r2['duplicates'] == 5 and len(r2['accepted']) == 5, 'a resent packet writes nothing and is acknowledged (idempotent event_id)')
    wrong = [ev('hover_view', feature='chart.tpwin', object='W2', end_reason='idle'),                  # no duration
             ev('action', feature='bad feature!', via='mouse'),                                          # not an identifier
             ev('action', feature='instrument', context=dict(price=21500.25)),                            # a key outside the context
             ev('bogus', feature='x'),
             ev('action', feature='session', object='ODR', via='key')]
    r3 = post(wrong, db)
    check(r3['written'] == 1 and len(r3['rejected']) == 4, f"invalid events are refused one by one, the valid one is written ({r3['written']} written, {len(r3['rejected'])} refused)")
    for body, what in ((b'{"schema_version":2,"events":[]}', 'another schema version'), (b'x' * (U.MAX_BODY + 1), 'an oversized body'),
                       (json.dumps(dict(schema_version=1, events=[ev('visit')] * (U.MAX_EVENTS + 1))).encode(), 'too many events')):
        try:
            U.accept(body, db); check(False, what + ' is refused as a packet')
        except ValueError:
            check(True, what + ' is refused as a packet')
    X = U.export(NOW - timedelta(days=1), NOW + timedelta(minutes=1), db)
    L, R, A = X['summary']['live'], X['summary']['review'], X['summary']['all']
    check(X['events_count'] == len(batch) + 1, f"the export holds every stored event once ({X['events_count']})")
    check([a['feature'] for a in R['actions']] == ['view.time'] and 'view.time' not in [a['feature'] for a in L['actions']], 'live and review are apart (the history pan only in review)')
    hv = {h['feature']: h for h in L['hover_views']}
    check(hv['chart.tpwin']['views'] == 2 and hv['chart.tpwin']['returns'] == 1 and abs(hv['chart.tpwin']['seconds'] - 4.3) < 1e-6, 'views: two of W1, one return, 4.3 s')
    st = {a['feature']: a['status'] for a in L['availability']}
    check(st.get('top.antb') == 'available_unused' and st.get('session') == 'never_seen_available', 'availability: «available, 0 uses» differs from «availability not confirmed»')
    check(st.get('top.instrument') == 'used' and 'instrument' not in st, 'availability: a switch through the instrument control counts as its use, no second row (review 23.11)')
    check(st.get('chart.tpwin') == 'used', 'availability: a view of a window counts as the use of the windows on the chart (review 23.11)')
    check(L['dead_clicks'] and L['dead_clicks'][0]['n'] == 1, 'a click without an answer is counted')
    check(L['mouse']['near_line_seconds'].get('reach70') == 0.3 and L['mouse']['region_seconds'].get('panel') == 0.6, 'the trace: time near the 70 % line and in the panel')
    check(X['builds'] and X['builds'][0]['build'] == 'test0001', 'the build of the page is named')
    check(any('rejected 4' in g['what'] for g in X['server_gaps']), 'the refused events are a known gap of the period')
    F = U.export(NOW - timedelta(days=1), NOW + timedelta(minutes=1), db, instrument='ES')
    check({(e.get('context') or {}).get('instrument') for e in F['events'] if e['kind'] not in ('visit', 'gap', 'tracker')} == {'ES'}, 'the instrument filter')
    txt = json.dumps(X, ensure_ascii=False)
    check('21500' not in txt, 'no price reaches the journal')
    check(A['visits'] == 1, 'one visit')
    # the order: a tooltip opened before a click and closed after it gets its seq when it ends; the chain follows the
    # moments the steps began (review 23.11)
    V2 = str(uuid.uuid4())
    t = lambda s: (NOW - timedelta(minutes=10) + timedelta(seconds=s)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    chain = lambda o: [ev('action', visit=V2, feature='instrument', object='ES', via='mouse', started_at_utc=t(o)),
                       ev('action', visit=V2, feature='area.select', object='a', via='mouse', started_at_utc=t(o + 5)),
                       ev('hover_view', visit=V2, feature='chart.pcell', object='c', duration_ms=2000, end_reason='replaced', started_at_utc=t(o + 3)),
                       ev('action', visit=V2, feature='tp.window_pin', object='LATE', via='mouse', started_at_utc=t(o + 8))]
    post(chain(0) + chain(20), db)
    S = U.export(NOW - timedelta(minutes=11), NOW - timedelta(minutes=9), db)['summary']['live']['sequences']
    first = S[0]['steps'] if S else []
    check(first[:3] == ['A:instrument·ES', 'V:chart.pcell·c', 'A:area.select·a'], f'sequences follow the start of each step ({first[:3]})')

    # review 23.11, second round: a rest is apart from the movement; a sweep along a level is named; an opening cut by
    # the pointer leaving the page stays one opening; the pointer on another screen is its own record
    V3 = str(uuid.uuid4())
    t3 = lambda s: (NOW - timedelta(minutes=20) + timedelta(seconds=s)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    c3 = dict(instrument='YM', trading_date='2026-11-23', session='RDR', mode='live', window='LATE')
    sweep = [[200, 0, x / 100, 0.4, 100 + x, 1.7, 0.7, 'reach70'] for x in (23, 30, 38, 47)]
    third = [ev('trace', visit=V3, feature='pointer', duration_ms=30800, started_at_utc=t3(0), context=c3,
                data=dict(p=[[30000, 8, 0.93, 0.02]] + sweep)),
             ev('open_view', visit=V3, feature='open.tp_window', object='W1', duration_ms=5000, end_reason='pointer_left_page', started_at_utc=t3(40), context=c3),
             ev('open_view', visit=V3, feature='open.tp_window', object='W1', duration_ms=7000, end_reason='blur', started_at_utc=t3(50), context=c3),
             ev('open_view', visit=V3, feature='open.tp_window', object='W1', duration_ms=3000, end_reason='closed', started_at_utc=t3(70), context=c3),
             ev('open_view', visit=V3, feature='open.tp_window', object='W1', duration_ms=2000, end_reason='closed', started_at_utc=t3(90), context=c3),
             ev('away', visit=V3, feature='pointer.away', duration_ms=4200, end_reason='returned', started_at_utc=t3(45), context=c3)]
    r4 = post(third, db)
    check(r4['written'] == len(third) and not r4['rejected'], f'the away record is accepted ({r4["written"]}/{len(third)}, {r4["rejected"]})')
    M3 = U.export(NOW - timedelta(minutes=21), NOW - timedelta(minutes=18), db)['summary']['live']
    mo = M3['mouse']
    check(mo['rest_region_seconds'].get('top') == 30.0 and 'top' not in mo['region_seconds'], 'a parked cursor is a rest, not movement on the map')
    sw = {s['line']: s for s in mo['sweeps']}
    check('reach70' in sw and sw['reach70']['n'] == 1 and sw['reach70']['x_from'] == 0.23 and sw['reach70']['windows'] == {'LATE': 1}, f'a sweep along the 70 % level is named with its width and window ({mo["sweeps"]})')
    ov = {o['feature']: o for o in M3['open_views']}['open.tp_window']
    check(ov['opens'] == 2 and ov['pieces'] == 4 and ov['seconds'] == 17.0, f'pieces cut by interruptions stay one opening ({ov})')
    check(M3['away'] == dict(times=1, seconds=4.2, ended={'returned': 1}), f'the pointer on another screen is counted ({M3["away"]})')

print('ALL GOOD' if not bad else f'{bad} FAILED')
sys.exit(1 if bad else 0)
