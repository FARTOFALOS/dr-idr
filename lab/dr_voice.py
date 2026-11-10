"""Local speech for new DR confirmations and SD reaches established by closed M5."""
import json
import queue
import sqlite3
import subprocess
import threading
import time
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / '.runtime' / 'live'
_started = None
_queue = queue.Queue()
_thread = None


def session_events(inst, raw):
    """Find the first DR confirmation and each first SD reach on the known prefix."""
    import scene21
    import pandas as pd
    stamp = pd.Timestamp(raw['fetched_at']).tz_convert('America/New_York')
    day = (stamp + pd.Timedelta(hours=6)).normalize()
    now = (stamp-day).total_seconds()/60
    bars = [[(pd.Timestamp(x[0], unit='s', tz='UTC').tz_convert('America/New_York')-day).total_seconds()/60, *x[1:5]] for x in raw['bars']]
    closed = {b[0]: b for b in bars if b[0] + 5 <= now}
    events = []
    for session, (start, formed, end) in scene21.SESS.items():
        # The M5 closing at block end can be fetched on the next minute poll.
        if not formed <= now <= end + 3: continue
        state = scene21._state(bars, session, int(now), now, True)
        close = state.get('conf')
        if close is None: continue
        if not all(t in closed for t in range(start, int(close), 5)): continue
        key = f'{inst}:{day.date()}:{session}'
        closed_at = (day + pd.Timedelta(minutes=close)).timestamp()
        events.append(dict(id=f'{key}:{close}', instrument=inst,
                           session=session, closed_at=closed_at))
        side = state['side']
        edge = state['idrH'] if side == 1 else state['idrL']
        width = state['idrH'] - state['idrL']
        remaining = [0.5, 1]
        # A target reached on the confirming bar is known when that bar closes.
        for minute in range(int(close) - 5, end, 5):
            bar = closed.get(minute)
            if bar is None or (state['failed'] is not None and minute + 5 >= state['failed']):
                break
            extreme = bar[2] if side == 1 else bar[3]
            distance = side * (extreme - edge)
            while remaining and distance >= remaining[0] * width:
                level = remaining.pop(0)
                events.append(dict(id=f'{key}:sd:{level}', instrument=inst, session=session,
                                   closed_at=(day + pd.Timedelta(minutes=minute + 5)).timestamp(), sd=level))
            if not remaining:
                break
    return events


def observe(inst, raw):
    if _started is None: return
    for event in session_events(inst, raw):
        # Ignore past events at launch/reconnect; never narrate replay or stale cached candles.
        if event['closed_at'] <= _started or not 0 <= time.time()-event['closed_at'] <= 180: continue
        if 'sd' in event and event['closed_at'] - 300 < _started: continue
        RUNTIME.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(RUNTIME/'dr_voice_seen.sqlite3', timeout=5)) as db:
            with db:
                db.execute('CREATE TABLE IF NOT EXISTS spoken (id TEXT PRIMARY KEY)')
                inserted = db.execute('INSERT OR IGNORE INTO spoken VALUES (?)', (event['id'],)).rowcount
        if inserted: _queue.put(event)


def _speak():
    while True:
        event = _queue.get()
        try:
            args = ['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                    '-File', str(ROOT/'dr_speak.ps1'), '-Instrument', event['instrument']]
            if 'sd' in event:
                args.extend(['-StandardDeviation', str(event['sd'])])
            result = subprocess.run(args,
                                    capture_output=True, timeout=30,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            if result.returncode: raise RuntimeError(result.stderr.decode('utf-8', errors='replace')[-500:])
            status = dict(ok=True, event=event)
        except Exception as exc:
            status = dict(ok=False, event=event, error=str(exc))
        RUNTIME.mkdir(parents=True, exist_ok=True)
        (RUNTIME/'dr_voice_status.json').write_text(json.dumps(status), encoding='utf-8')
        _queue.task_done()


def start():
    global _started, _thread
    if _thread and _thread.is_alive(): return
    _started = time.time()
    _thread = threading.Thread(target=_speak, name='female-dr-voice', daemon=True)
    _thread.start()
