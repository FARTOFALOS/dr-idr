"""The usage journal of screen 23.5 (spec/DR-LAB-23-5-USAGE-TRACKER.md, operator 23.11.2026).

What the operator does with the screen, never what the market did: actions on named functions, views of named data
under the mouse, how long a pinned detail stayed open, which functions were available, and the trace of the mouse in
the screen's own coordinates (region of the screen, minute of the day, position against the session's IDR/STD grid;
no pixels of the chart, no prices, no page text). Python standard library only (sqlite3).

The page queues finished events and posts them in small packets (POST /api/usage/23-5/events); a packet is written in
one transaction and acknowledged only after the commit; `event_id` is unique, so a resent packet never doubles a row.
The file lives in this working copy's git-ignored lab/.runtime/ and survives restarts; both servers of one working
copy (8735, 8767) write the same file.

    python lab/usage235.py export [--days 7 | --from ISO --to ISO] [--out file.json]   the file for an audit
    python lab/usage235.py summary [--days 7]                                          the summary in the console
"""
import argparse
import json
import re
import sqlite3
import threading
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCHEMA_VERSION = 1
DB_PATH = Path(__file__).resolve().parent / '.runtime' / 'usage-23-5.sqlite3'
# away: the pointer outside the page while the page is visible and focused (a look at another screen, e.g. TradingView)
KINDS = {'visit', 'action', 'dead_click', 'hover_view', 'open_view', 'available', 'trace', 'gap', 'tracker', 'away'}
END_REASONS = {'pointer_left_object', 'pointer_left_page', 'hidden', 'blur', 'idle', 'pagehide', 'replaced', 'closed', 'context', 'returned'}
# a point of the trace where the pointer stayed this long is a rest, not a movement (review 23.11: a parked cursor
# filled 40 % of the first day's map)
REST_MS = 2000
# an interruption that does not close a pinned detail: the next piece of the same object continues the same opening
INTERRUPTS = {'pointer_left_page', 'blur', 'hidden', 'idle'}
ID_RE = re.compile(r'^[A-Za-z0-9_.:+\-|%/<>=]{1,64}$')
UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
TS_RE = re.compile(r'^20\d\d-[01]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d(\.\d{1,3})?Z$')
CONTEXT_KEYS = {'instrument': 8, 'trading_date': 10, 'session': 8, 'mode': 8, 'at': 6, 'status': 12, 'window': 8,
                'event': 2, 'view': 12, 'layers': 160, 'map': 16}
MAX_BODY = 512_000
MAX_EVENTS = 400
MAX_DATA = 16_000
# the regions of the screen in the order of the page's codes (usage235.js U_REG)
REGIONS = ['chart', 'price_axis', 'price_column', 'time_axis', 'strip', 'panel', 'lower_window', 'inspector', 'top', 'menu', 'other']
_lock = threading.Lock()


def _connect(path=None):
    path = Path(path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), timeout=10)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA synchronous=NORMAL')
    con.execute('''CREATE TABLE IF NOT EXISTS events (
        event_id TEXT PRIMARY KEY, schema_version INTEGER NOT NULL, visit_id TEXT NOT NULL, seq INTEGER NOT NULL,
        started_at_utc TEXT NOT NULL, kind TEXT NOT NULL, feature TEXT, object TEXT, duration_ms INTEGER,
        end_reason TEXT, via TEXT, context TEXT, data TEXT, build TEXT, received_at_utc TEXT NOT NULL)''')
    con.execute('CREATE INDEX IF NOT EXISTS events_time ON events(started_at_utc)')
    con.execute('CREATE INDEX IF NOT EXISTS events_visit ON events(visit_id, seq)')
    con.execute('CREATE TABLE IF NOT EXISTS server_gaps (at_utc TEXT NOT NULL, what TEXT NOT NULL)')
    return con


def _short(value, limit, name):
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError(name + ': a string of at most %d characters' % limit)
    return value


def validate(ev):
    """One event of the page, checked field by field; returns the row or raises ValueError."""
    if not isinstance(ev, dict):
        raise ValueError('event: an object')
    if ev.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('schema_version: %d expected' % SCHEMA_VERSION)
    eid, vid = ev.get('event_id'), ev.get('visit_id')
    if not isinstance(eid, str) or not UUID_RE.match(eid) or not isinstance(vid, str) or not UUID_RE.match(vid):
        raise ValueError('event_id, visit_id: uuid')
    seq = ev.get('seq')
    if not isinstance(seq, int) or isinstance(seq, bool) or not 0 <= seq < 10_000_000:
        raise ValueError('seq: an integer')
    ts = ev.get('started_at_utc')
    if not isinstance(ts, str) or not TS_RE.match(ts):
        raise ValueError('started_at_utc: ISO UTC')
    kind = ev.get('kind')
    if kind not in KINDS:
        raise ValueError('kind: unknown')
    feature, obj = ev.get('feature'), ev.get('object')
    for name, v in (('feature', feature), ('object', obj), ('via', ev.get('via'))):
        if v is not None and (not isinstance(v, str) or not ID_RE.match(v)):
            raise ValueError(name + ': an identifier')
    if kind in ('action', 'dead_click', 'hover_view', 'open_view', 'available') and not feature:
        raise ValueError('feature: required for ' + kind)
    dur, why = ev.get('duration_ms'), ev.get('end_reason')
    if kind in ('hover_view', 'open_view', 'away'):
        if not isinstance(dur, int) or isinstance(dur, bool) or not 0 <= dur <= 86_400_000:
            raise ValueError('duration_ms: required for a view')
        if why not in END_REASONS:
            raise ValueError('end_reason: unknown')
    elif dur is not None and (not isinstance(dur, int) or isinstance(dur, bool) or not 0 <= dur <= 86_400_000):
        raise ValueError('duration_ms: an integer')
    ctx = ev.get('context') or {}
    if not isinstance(ctx, dict) or set(ctx) - set(CONTEXT_KEYS):
        raise ValueError('context: unknown key')
    for k, v in ctx.items():
        if v is not None and not isinstance(v, (str, int, float, bool)):
            raise ValueError('context.' + k + ': a scalar')
        if isinstance(v, str) and len(v) > CONTEXT_KEYS[k]:
            raise ValueError('context.' + k + ': too long')
    data = ev.get('data')
    data_txt = None if data is None else json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    if data_txt is not None and len(data_txt) > MAX_DATA:
        raise ValueError('data: too large')
    build = _short(ev.get('build'), 40, 'build')
    return (eid, SCHEMA_VERSION, vid, seq, ts, kind, feature, obj, dur, why, ev.get('via'),
            json.dumps(ctx, ensure_ascii=False, separators=(',', ':')), data_txt, build)


def accept(body, path=None):
    """A packet {schema_version, events:[...]} from the page: every event valid, else nothing is written."""
    if len(body) > MAX_BODY:
        raise ValueError('body too large')
    req = json.loads(body.decode('utf-8') or '{}')
    if not isinstance(req, dict) or req.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('schema_version: %d expected' % SCHEMA_VERSION)
    events = req.get('events')
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        raise ValueError('events: a list of at most %d' % MAX_EVENTS)
    # an invalid event is refused on its own (named with its reason, noted as a gap) so it never blocks the queue;
    # the valid ones of the packet are written together
    rows, rejected = [], []
    for e in events:
        try:
            rows.append(validate(e))
        except ValueError as exc:
            rejected.append(dict(event_id=e.get('event_id') if isinstance(e, dict) else None, error=str(exc)))
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    with _lock:
        con = _connect(path)
        try:
            with con:
                before = con.total_changes
                con.executemany('INSERT OR IGNORE INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                                [r + (now,) for r in rows])
                written = con.total_changes - before
                if rejected:
                    con.execute('INSERT INTO server_gaps VALUES (?,?)',
                                (now, 'rejected %d: %s' % (len(rejected), '; '.join(sorted({r['error'] for r in rejected}))[:400])))
        finally:
            con.close()
    return dict(status='ok', accepted=[r[0] for r in rows], written=written, duplicates=len(rows) - written,
                rejected=rejected)


def _iso(dt):
    return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')


def _parse(ts):
    if not ts:
        return None
    ts = ts.strip()
    if re.fullmatch(r'\d{4}-\d\d-\d\d', ts):
        ts += 'T00:00:00Z'
    return datetime.fromisoformat(ts.replace('Z', '+00:00')).astimezone(timezone.utc)


def rows(t0, t1, path=None):
    con = _connect(path)
    con.row_factory = sqlite3.Row
    try:
        out = []
        for r in con.execute('SELECT * FROM events WHERE started_at_utc >= ? AND started_at_utc < ? ORDER BY started_at_utc, visit_id, seq',
                             (_iso(t0), _iso(t1))):
            e = dict(r)
            e['context'] = json.loads(e['context'] or '{}')
            e['data'] = json.loads(e['data']) if e['data'] else None
            out.append({k: v for k, v in e.items() if v is not None})
        return out
    finally:
        con.close()


def _ctx_key(e):
    c = e.get('context') or {}
    return (c.get('instrument'), c.get('session'), c.get('mode'))


def summary(events):
    """The summary is built only from the events of the same file: every figure can be traced back to rows."""
    visits = sorted({e['visit_id'] for e in events})
    opened = [e for e in events if e['kind'] == 'visit']
    used_in = defaultdict(set)
    actions = Counter()
    calls = Counter()   # by the name of the function and by the name of the control it was called from
    via = defaultdict(Counter)
    for e in events:
        if e['kind'] == 'action':
            actions[e['feature']] += 1
            via[e['feature']][e.get('via') or '?'] += 1
            # an action is named by what changed (instrument) and remembers the control pressed (top.instrument), which
            # is the name the availability is recorded under: the use counts for both (review 23.11: «доступно, 0 раз»
            # beside five switches of the instrument)
            for name in {e['feature'], (e.get('data') or {}).get('from')} - {None}:
                used_in[name].add(e['visit_id'])
                calls[name] += 1
    hovers = defaultdict(lambda: dict(n=0, ms=0, objects=Counter(), returns=0, visits=set()))
    for v in visits:
        seen = set()
        for e in (x for x in events if x['visit_id'] == v and x['kind'] == 'hover_view'):
            h = hovers[e['feature']]
            h['n'] += 1; h['ms'] += e['duration_ms']; h['visits'].add(v)
            key = (e['feature'], e.get('object'))
            h['objects'][e.get('object') or '-'] += 1
            if key in seen:
                h['returns'] += 1
            seen.add(key)
            used_in[e['feature']].add(v)
    # an opening of a detail is one, however many pieces the interruptions cut it into (the pointer on another screen,
    # the window out of focus, idle): a piece continues the previous one of the same object in the visit when that one
    # was interrupted, not closed (review 23.11: one pinned W1 was six records)
    opens = defaultdict(lambda: dict(n=0, pieces=0, ms=0, idle_cut=0))
    for v in visits:
        last = {}
        for e in sorted((x for x in events if x['visit_id'] == v and x['kind'] == 'open_view'), key=lambda x: (x['started_at_utc'], x['seq'])):
            o, key = opens[e['feature']], (e['feature'], e.get('object'))
            o['pieces'] += 1; o['ms'] += e['duration_ms']; o['idle_cut'] += e.get('end_reason') == 'idle'
            if last.get(key) not in INTERRUPTS:
                o['n'] += 1
            last[key] = e.get('end_reason')
    away = [e for e in events if e['kind'] == 'away']
    avail = defaultdict(set)
    for e in events:
        if e['kind'] == 'available':
            avail[e['feature']].add(e['visit_id'])
    availability = []
    # an action whose control is on the availability list is already counted there; it is not a second row
    via_avail = {e['feature'] for e in events if e['kind'] == 'action' and (e.get('data') or {}).get('from') in avail}
    for f in sorted(set(avail) | (set(actions) - via_avail)):
        used = used_in.get(f, set())
        availability.append(dict(feature=f, available_in_visits=len(avail.get(f, ())), used_in_visits=len(used),
                                 calls=calls.get(f, 0),
                                 status='never_seen_available' if f not in avail else 'available_unused' if not used else 'used'))
    dead = Counter((e.get('feature'), e.get('object')) for e in events if e['kind'] == 'dead_click')
    # the order of looking: chains of three named steps (actions and views that passed the threshold) inside one visit,
    # each at the moment it began: a view gets its seq when it ends, so a tooltip opened before a click and closed
    # after it would otherwise follow the click (review 23.11)
    seqs = Counter()
    for v in visits:
        steps = [('A:' if e['kind'] == 'action' else 'V:') + e['feature'] + ('·' + e['object'] if e.get('object') else '')
                 for e in sorted((x for x in events if x['visit_id'] == v and x['kind'] in ('action', 'hover_view')),
                                 key=lambda x: (x['started_at_utc'], x['seq']))]
        steps = [s for i, s in enumerate(steps) if i == 0 or s != steps[i - 1]]
        for i in range(len(steps) - 2):
            seqs[tuple(steps[i:i + 3])] += 1
    # the trace of the mouse: dwell by region of the screen and, over the chart, by minute from the box start × position
    # against the IDR (0 = IDR low, 1 = IDR high, one STD step = 0.5)
    # the maps hold the movement; a rest (a point held REST_MS or longer) is counted apart and has its own screen map
    region_ms = Counter()
    rest_region = Counter()
    screen = Counter()
    rest_screen = Counter()
    chart = Counter()
    near = Counter()
    sweeps = defaultdict(lambda: dict(n=0, ms=0, x0=1.0, x1=0.0, m0=None, m1=None, windows=Counter(), instruments=Counter()))
    for e in events:
        if e['kind'] != 'trace':
            continue
        ps = (e.get('data') or {}).get('p', [])
        for p in ps:
            dt, reg, nx, ny = p[0], p[1], p[2], p[3]
            rn = REGIONS[reg] if isinstance(reg, int) and 0 <= reg < len(REGIONS) else 'other'
            cell = (min(39, int(nx * 40)), min(24, int(ny * 25)))
            if dt >= REST_MS:
                rest_region[rn] += dt
                rest_screen[cell] += dt
                continue
            region_ms[rn] += dt
            screen[cell] += dt
            if len(p) > 5 and p[4] is not None and p[5] is not None:
                chart[(int(p[4] // 5) * 5, round(p[5] * 4) / 4)] += dt
            if len(p) > 7 and p[7]:
                near[p[7]] += dt
        # a sweep along a level: three or more points in a row near the same named line, moving at least 5 % of the
        # width (operator 23.11: «веду мышкой влево по уровню 70 %, где линия не нарисована»)
        i = 0
        while i < len(ps):
            k = ps[i][7] if len(ps[i]) > 7 else None
            j = i
            while j + 1 < len(ps) and len(ps[j + 1]) > 7 and ps[j + 1][7] == k:
                j += 1
            run = ps[i:j + 1]
            xs = [q[2] for q in run]
            if k and len(run) >= 3 and max(xs) - min(xs) >= 0.05:
                w = sweeps[k]
                w['n'] += 1
                w['ms'] += sum(q[0] for q in run if q[0] < REST_MS)
                w['x0'] = min(w['x0'], min(xs))
                w['x1'] = max(w['x1'], max(xs))
                mins = [q[4] for q in run if q[4] is not None]
                if mins:
                    w['m0'] = min(mins) if w['m0'] is None else min(w['m0'], min(mins))
                    w['m1'] = max(mins) if w['m1'] is None else max(w['m1'], max(mins))
                c = e.get('context') or {}
                w['windows'][c.get('window') or '-'] += 1
                w['instruments'][c.get('instrument') or '-'] += 1
            i = j + 1
    gaps = [dict(at=e['started_at_utc'], what=e.get('feature'), data=e.get('data')) for e in events if e['kind'] == 'gap']
    return dict(
        visits=len(visits), openings=len(opened),
        actions=[dict(feature=f, calls=n, visits=len(used_in[f]), via=dict(via[f])) for f, n in actions.most_common()],
        hover_views=[dict(feature=f, views=h['n'], seconds=round(h['ms'] / 1000, 1), returns=h['returns'], visits=len(h['visits']),
                          objects=dict(h['objects'].most_common(12))) for f, h in sorted(hovers.items(), key=lambda kv: -kv[1]['ms'])],
        open_views=[dict(feature=f, opens=o['n'], pieces=o['pieces'], seconds=round(o['ms'] / 1000, 1), ended_by_idle=o['idle_cut'])
                    for f, o in sorted(opens.items(), key=lambda kv: -kv[1]['ms'])],
        away=dict(times=len(away), seconds=round(sum(e['duration_ms'] for e in away) / 1000, 1),
                  ended=dict(Counter(e.get('end_reason') for e in away))),
        availability=availability,
        dead_clicks=[dict(feature=f, object=o, n=n) for (f, o), n in dead.most_common(30)],
        sequences=[dict(steps=list(k), n=n) for k, n in seqs.most_common(30) if n > 1],
        mouse=dict(region_seconds={k: round(v / 1000, 1) for k, v in region_ms.most_common()},
                   rest_ms=REST_MS, rest_region_seconds={k: round(v / 1000, 1) for k, v in rest_region.most_common()},
                   rest_screen_grid=dict(cols=40, rows=25, cells=[[x, y, round(v / 1000, 2)] for (x, y), v in rest_screen.items()]),
                   sweeps=[dict(line=k, n=w['n'], seconds=round(w['ms'] / 1000, 1), x_from=w['x0'], x_to=w['x1'], min_from=w['m0'],
                                min_to=w['m1'], windows=dict(w['windows']), instruments=dict(w['instruments']))
                           for k, w in sorted(sweeps.items(), key=lambda kv: -kv[1]['n'])],
                   near_line_seconds={k: round(v / 1000, 1) for k, v in near.most_common(20)},
                   screen_grid=dict(cols=40, rows=25, cells=[[x, y, round(v / 1000, 2)] for (x, y), v in screen.items()]),
                   chart_grid=dict(minute_step=5, level_step=0.25, cells=[[m, u, round(v / 1000, 2)] for (m, u), v in chart.items()])),
        gaps=gaps)


def export(t0=None, t1=None, path=None, instrument=None, session=None):
    t1 = t1 or datetime.now(timezone.utc) + timedelta(minutes=1)
    t0 = t0 or t1 - timedelta(days=7)
    ev = rows(t0, t1, path)
    # the filters of the report: an instrument and a session (the events of opening and gaps always stay)
    keep = lambda e, k, v: not v or e['kind'] in ('visit', 'gap', 'tracker') or (e.get('context') or {}).get(k) == v
    ev = [e for e in ev if keep(e, 'instrument', instrument) and keep(e, 'session', session)]
    con = _connect(path)
    try:
        server_gaps = [dict(at=a, what=w) for a, w in con.execute('SELECT at_utc, what FROM server_gaps WHERE at_utc >= ? AND at_utc < ?', (_iso(t0), _iso(t1)))]
    finally:
        con.close()
    return dict(
        what='DR Lab 23.5 · журнал использования экрана (spec/DR-LAB-23-5-USAGE-TRACKER.md)',
        schema_version=SCHEMA_VERSION, range_utc=dict(start=_iso(t0), end=_iso(t1)),
        filters=dict(instrument=instrument, session=session),
        generated_utc=_iso(datetime.now(timezone.utc)), events_count=len(ev),
        reading=('Показ данных ≠ прочтение: hover_view подтверждает, что подсказка была видна, не что её прочли. '
                 'Нулевое использование доступной функции — повод спросить оператора, не основание удалять.'),
        trace_format=('trace.p: [мс в этой точке, область (номер в REGIONS), x/ширина окна, y/высота окна, минута от начала коробки, '
                 'положение к IDR (0 = низ IDR, 1 = верх IDR, шаг STD = 0.5), SD семьи от края в игре, линия в пределах 6 px]. '
                 'Точка, где мышь стояла 2 с и дольше, — покой: она не входит в карты движения и считается отдельно. '
                 'Проводка вдоль уровня — три и больше точек подряд у одной линии со сдвигом не меньше 5 % ширины. '
                 'away — курсор вне страницы при видимой и активной странице (взгляд на другой экран). '
                 'Режимы: live — живой рынок, history/replay — разбор.'),
        # the operator 23.11: live trading and the review of history are read apart (decisions about the screen are
        # made first from the live market); every build of the page is named so a change can be compared before/after
        summary=dict(live=summary([e for e in ev if _mode(e) == 'live']),
                     review=summary([e for e in ev if _mode(e) in ('history', 'replay')]),
                     all=summary(ev)),
        regions=REGIONS, builds=_builds(ev), server_gaps=server_gaps, events=ev)


def _mode(e):
    return (e.get('context') or {}).get('mode')


def _builds(ev):
    out = {}
    for e in ev:
        b = out.setdefault(e.get('build') or '?', dict(first_utc=e['started_at_utc'], last_utc=e['started_at_utc'], events=0, visits=set()))
        b['last_utc'] = max(b['last_utc'], e['started_at_utc']); b['first_utc'] = min(b['first_utc'], e['started_at_utc'])
        b['events'] += 1; b['visits'].add(e['visit_id'])
    return [dict(build=k, first_utc=v['first_utc'], last_utc=v['last_utc'], events=v['events'], visits=len(v['visits'])) for k, v in sorted(out.items(), key=lambda kv: kv[1]['first_utc'])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('what', choices=['export', 'summary'])
    ap.add_argument('--days', type=float)
    ap.add_argument('--from', dest='t0')
    ap.add_argument('--to', dest='t1')
    ap.add_argument('--out')
    a = ap.parse_args()
    t1 = _parse(a.t1) if a.t1 else None
    t0 = _parse(a.t0) if a.t0 else (datetime.now(timezone.utc) - timedelta(days=a.days) if a.days else None)
    value = export(t0, t1)
    if a.what == 'summary':
        value = dict(range_utc=value['range_utc'], events=value['events_count'], builds=value['builds'], summary=value['summary'])
    text = json.dumps(value, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).write_text(text, encoding='utf-8')
        print(a.out, len(text) // 1000, 'kB')
    else:
        print(text)


if __name__ == '__main__':
    main()
