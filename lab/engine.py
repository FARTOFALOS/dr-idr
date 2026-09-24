"""DR Lab. Deterministic synthetic fixtures and explicit cohort statistics.

No market tape is read. All bars and all dates in this database are synthetic.
Prices are integer NQ ticks; normalized coordinates use the IDR width.
"""
from __future__ import annotations

import datetime as dt
import json
import math
from pathlib import Path
import random
import sqlite3

VERSION = "dr-lab-demo-1"
SEED = 91724
SESSIONS = {"RDR": (570, 630, 960), "ODR": (180, 240, 510), "ADR": (1170, 1230, 1560)}
ROOT = Path(__file__).resolve().parent
DB = ROOT / ".runtime" / "demo.sqlite3"


def clock(minute):
    if minute is None:
        return None
    m = int(minute)
    return f"{m // 60 % 24:02d}:{m % 60:02d}" + (" +1" if m >= 1440 else "")


def percentile(values, q):
    a = sorted(values)
    if not a:
        return None
    p = (len(a) - 1) * q
    lo, hi = math.floor(p), math.ceil(p)
    return a[lo] + (a[hi] - a[lo]) * (p - lo)


def interval(k, n):
    """Wilson interval, descriptive demo only; not a dependence correction."""
    if not n:
        return None
    z = 1.959963984540054
    p = k / n
    center = (p + z*z/(2*n)) / (1 + z*z/n)
    radius = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1 + z*z/n)
    return [round(100 * (center-radius), 1), round(100 * (center+radius), 1)]


def coord(price, edge, width, side):
    return side * (price - edge) / width


def metrics(bars, edge, width, side, opposite, complete=True):
    """bars contain closed minutes strictly AFTER confirmation; first tie wins."""
    if width <= 0 or not bars:
        raise ValueError("A positive IDR width and post-confirmation bars are required")
    lows = [(coord(b[3] if side == 1 else b[2], edge, width, side), b[0]) for b in bars]
    highs = [(coord(b[2] if side == 1 else b[3], edge, width, side), b[0]) for b in bars]
    low = min(lows, key=lambda x: (x[0], x[1]))
    high = max(highs, key=lambda x: (x[0], -x[1]))
    failed = any(b[0] % 5 == 0 and side * (b[4] - opposite) < 0 for b in bars)
    return {"retracement": round(low[0], 6), "retracement_time": low[1],
            "extension": round(high[0], 6), "extension_time": high[1],
            "dr_true": False if failed else (True if complete else None)}


def _fixtures():
    rng = random.Random(SEED)
    date = dt.date(2020, 1, 6)
    for day in range(720):
        while date.weekday() > 4:
            date += dt.timedelta(days=1)
        for session, (start, formed, end) in SESSIONS.items():
            side = 1 if rng.random() < .52 else -1
            tau = formed + rng.choice([5, 10, 15, 15, 20, 25, 30, 35, 40, 45, 55, 65, 80])
            width = rng.randrange(100, 321, 4)
            edge = rng.randrange(76000, 85000, 4)
            far_idr = edge - side * width
            dr_near, dr_far = edge + side * round(.08*width), far_idr - side * round(.10*width)
            late = rng.random() < .30
            false = rng.random() < .19
            # These deliberately manufactured regimes are UI fixtures, not a market model.
            retr = (-1.18 - rng.random()*.25) if false else rng.choice([.05, -.12, -.18, -.31, -.55, -.72]) + rng.gauss(0, .07)
            rt = min(end-45, tau + (rng.randrange(90, 176) if late else rng.randrange(6, 61)))
            ext = max(.22, rng.gauss(1.42 if not late else .78, .49) + (.22 if retr < -.6 and not false else 0))
            et = min(end-2, rt + rng.randrange(20, max(21, end-rt)))
            pivots = [(tau, .17), (tau+3, .25), (rt, retr), (et, ext), (end, ext*rng.uniform(.15, .9))]
            pivots = sorted(dict(pivots).items())
            complete = rng.random() > .025
            observed_end = end if complete else min(end-1, tau + rng.randrange(35, 120))
            last = edge + side*round(.17*width)
            bars = []
            for minute in range(tau+1, observed_end+1):
                j = next(j for j in range(1, len(pivots)) if pivots[j][0] >= minute)
                ta, a = pivots[j-1]
                tb, b = pivots[j]
                value = a + (b-a)*(minute-ta)/(tb-ta) + rng.gauss(0, .022)
                close = edge + side*round(value*width)
                wick = rng.randrange(1, max(2, round(width*.025)))
                high, low = max(last, close)+wick, min(last, close)-wick
                bars.append([minute, last, high, low, close])
                last = close
            m = metrics(bars, edge, width, side, dr_far, complete)
            yield {"id": f"DEMO-{day+1:04d}-{session}", "date": date.isoformat(), "weekday": date.weekday(),
                   "session": session, "direction": "long" if side == 1 else "short", "confirmation": tau,
                   "formed": formed, "end": end, "edge": edge, "width": width,
                   "dr_high": max(dr_near, dr_far), "dr_low": min(dr_near, dr_far),
                   "idr_high": max(edge, far_idr), "idr_low": min(edge, far_idr),
                   "complete": complete, "bars": bars, **m}
        date += dt.timedelta(days=1)


def initialize():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as db:
        db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        version = db.execute("SELECT value FROM metadata WHERE key='version'").fetchone()
        if version and version[0] == VERSION:
            return
        if version:
            raise RuntimeError("Demo database version differs; preserve it and use a new runtime directory")
        db.execute("""CREATE TABLE episodes (
          id TEXT PRIMARY KEY, date TEXT NOT NULL, weekday INTEGER NOT NULL,
          session TEXT NOT NULL, direction TEXT NOT NULL, confirmation INTEGER NOT NULL,
          complete INTEGER NOT NULL, payload TEXT NOT NULL)""")
        db.executemany("INSERT INTO episodes VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       ((e['id'], e['date'], e['weekday'], e['session'], e['direction'], e['confirmation'],
                         int(e['complete']), json.dumps(e, separators=(',', ':'))) for e in _fixtures()))
        db.execute("CREATE INDEX idx_episodes_cohort ON episodes(session, direction, confirmation, weekday)")
        db.execute("INSERT INTO metadata VALUES ('version', ?)", (VERSION,))
        db.execute("INSERT INTO metadata VALUES ('provenance', 'SYNTHETIC; no market data; seed 91724')")
        db.execute("PRAGMA optimize")


def scene(scene_id):
    with sqlite3.connect(DB) as db:
        row = db.execute("SELECT payload FROM episodes WHERE id=?", (scene_id,)).fetchone()
    return json.loads(row[0]) if row else None


def get_base(p):
    session = p.get('session', 'RDR')
    if session not in SESSIONS:
        raise ValueError('Unknown session')
    start = float(p.get('from', SESSIONS[session][1]))
    stop = float(p.get('to', SESSIONS[session][1]+90))
    if not math.isfinite(start) or not math.isfinite(stop) or start >= stop:
        raise ValueError('Начало окна должно быть раньше конца')
    sql = 'SELECT payload FROM episodes WHERE session=? AND confirmation>=? AND confirmation<?'
    args = [session, start, stop]
    if p.get('direction', 'long') != 'all':
        if p.get('direction', 'long') not in ('long', 'short'):
            raise ValueError('Unknown direction')
        sql += ' AND direction=?'
        args.append(p.get('direction', 'long'))
    if p.get('weekday', 'all') != 'all':
        if int(p['weekday']) not in range(5):
            raise ValueError('День недели должен быть от понедельника до пятницы')
        sql += ' AND weekday=?'
        args.append(int(p['weekday']))
    with sqlite3.connect(DB) as db:
        rows = db.execute(sql+' ORDER BY date, id', args).fetchall()
    return [json.loads(r[0]) for r in rows]


def bucket(v, step=.1):
    return math.floor((v + 1e-9) / step)


def hist(rows, field, lo, hi, step):
    bins = [{"lo": round(lo+i*step, 6), "hi": round(lo+(i+1)*step, 6), "n": 0}
            for i in range(round((hi-lo)/step))]
    under, over = 0, 0
    for e in rows:
        v = e[field]
        idx = math.floor((v-lo+1e-9)/step)
        if idx < 0:
            under += 1
        elif idx >= len(bins):
            over += 1
        else:
            bins[idx]['n'] += 1
    return {"bins": bins, "n": len(rows), "underflow": under, "overflow": over}


def query(p):
    base = get_base(p)
    rows = base
    mode = p.get('mode', 'history')
    if mode not in ('history', 'prefix'):
        raise ValueError('Unknown observation mode')
    if p.get('status', 'all') not in ('all', 'true', 'false'):
        raise ValueError('Unknown final session status')
    future_filters = [x for x in ('retr', 'rtime', 'ext', 'etime', 'retr_hi', 'rtime_hi', 'ext_hi', 'etime_hi') if p.get(x) not in (None, '')]
    if mode == 'prefix' and (future_filters or p.get('status', 'all') != 'all'):
        raise ValueError('Фильтры итогового исхода доступны только в исследовании полной истории')
    formed, end = SESSIONS[p.get('session', 'RDR')][1:]
    observed = int(p.get('observed', formed+60))
    if not formed < observed < end:
        raise ValueError('Срез должен быть после формирования DR и до конца сессии')
    target = float(p.get('target', .8))
    if not .1 <= target <= 4:
        raise ValueError('Цель должна быть от 0.1 до 4 IDR')
    prefix_excluded = 0
    if mode == 'prefix':
        alive = []
        for e in rows:
            side = 1 if e['direction'] == 'long' else -1
            past = [b for b in e['bars'] if b[0] <= observed]
            if not past or e['confirmation'] >= observed or past[-1][0] != observed:
                continue
            opposite = e['dr_low'] if side == 1 else e['dr_high']
            failed = any(b[0] % 5 == 0 and side*(b[4]-opposite)<0 for b in past)
            reached = max(coord(b[2] if side == 1 else b[3], e['edge'], e['width'], side) for b in past) >= target
            if not failed and not reached:
                alive.append(e)
        prefix_excluded = len(rows)-len(alive)
        rows = alive
    else:
        if p.get('status', 'all') != 'all':
            wanted = p['status'] == 'true'
            rows = [e for e in rows if e['dr_true'] is wanted]
        for field, param, step in [('retracement', 'retr', .1), ('extension', 'ext', .1),
                                   ('retracement_time', 'rtime', 15), ('extension_time', 'etime', 15)]:
            if p.get(param) not in (None, ''):
                lo = float(p[param])
                hi = float(p.get(param+'_hi', lo+step))
                if not math.isfinite(lo) or not math.isfinite(hi) or lo >= hi:
                    raise ValueError('Некорректный диапазон выделения')
                rows = [e for e in rows if e['complete'] and lo-1e-9 <= e[field] < hi-1e-9]
    # Final-extremum charts have only fully observed sessions in their denominator.
    known = [e for e in rows if e['complete']]
    base_known = [e for e in base if e['complete']]
    measured = known
    if mode == 'prefix':
        measured = []
        for e in known:
            side = 1 if e['direction']=='long' else -1
            after = [b for b in e['bars'] if b[0] > observed]
            opposite = e['dr_low'] if side == 1 else e['dr_high']
            measured.append({**e, **metrics(after, e['edge'], e['width'], side, opposite)})
    hits = sum(e['extension'] >= target for e in measured)
    failures = len(measured)-hits
    unknown_target = 0
    for e in rows:
        if e['complete']:
            continue
        side = 1 if e['direction']=='long' else -1
        available = [b for b in e['bars'] if mode=='history' or b[0]>observed]
        reached = any(coord(b[2] if side==1 else b[3], e['edge'], e['width'], side)>=target for b in available)
        if reached:
            hits += 1
        else:
            unknown_target += 1
    target_known = hits+failures
    true_k = sum(e['dr_true'] is True for e in rows)
    true_n = sum(e['dr_true'] is not None for e in rows)
    time_lo = formed if mode == 'history' else (observed//15)*15
    defs = {'retr': ('retracement', -1.6, .5, .1), 'ext': ('extension', 0, 3.6, .1),
            'rtime': ('retracement_time', time_lo, end, 15), 'etime': ('extension_time', time_lo, end, 15)}
    charts = {name: hist(measured, *definition) for name, definition in defs.items()}
    for name, definition in defs.items():
        charts[name]['reference'] = hist(base_known, *definition)['bins']
    heat = []
    for e in measured:
        r, t = bucket(e['retracement']), int(e['retracement_time']//15)*15
        heat.append((r, t))
    counts = {}
    for r,t in heat:
        counts[(r,t)] = counts.get((r,t), 0)+1
    # Display includes out-of-view counts explicitly; no renormalization of visible cells.
    cells = [{"r": r/10, "t": t, "n": n} for (r,t),n in sorted(counts.items())]
    curve = []
    for t in range(formed+5, end+1, 5):
        values = []
        for e in known:
            index = t-e['confirmation']-1
            if 0 <= index < len(e['bars']):
                values.append(coord(e['bars'][index][4], e['edge'], e['width'], 1 if e['direction']=='long' else -1))
        if values:
            curve.append({"t": t, "n": len(values), "low": percentile(values,.2), "mid": percentile(values,.5), "high": percentile(values,.8)})
    return {"data_kind": "SYNTHETIC", "version": VERSION, "seed": SEED, "total": 2160,
            "query": p, "base_n": len(base), "n": len(rows), "complete_n": len(known),
            "unknown_n": len(rows)-len(known), "prefix_excluded": prefix_excluded,
            "true": {"k": true_k, "n": true_n, "pct": 100*true_k/true_n if true_n else None, "interval": interval(true_k,true_n)},
            "target": {"k": hits, "n": target_known, "failures": failures, "unknown": unknown_target,
                       "pct": 100*hits/target_known if target_known else None, "interval": interval(hits,target_known),
                       "bounds": [100*hits/len(rows),100*(hits+unknown_target)/len(rows)] if rows else None},
            "median_retr": percentile([e['retracement'] for e in measured],.5),
            "median_ext": percentile([e['extension'] for e in measured],.5),
            "median_rtime": clock(percentile([e['retracement_time'] for e in measured],.5)),
            "charts": charts, "heat": cells, "curve": curve, "end": end, "formed": formed,
            "scenes": [{k:e[k] for k in ('id','date','direction','confirmation','complete','dr_true','retracement','retracement_time','extension')} for e in rows[:80]]}
