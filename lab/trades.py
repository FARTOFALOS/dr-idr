"""DR Lab — the operator's trade journal: every trading action of his, collected from NinjaTrader 8.

Source: NinjaTrader keeps accounts, orders, every order update and every fill in its local SQLite base
(Documents/NinjaTrader 8/db/NinjaTrader.sqlite). The operator trades on the NinjaTrader screen only; the OneUp prop
account comes through NinjaTrader's Rithmic connection, Sim101 is NinjaTrader's local simulator. No API, no login:
the collector copies the base file, reads the copy and never writes to NinjaTrader.

Journal (private, local only: lab/.runtime/trades/journal.sqlite3, never in git):
  raw layer   nt_* tables  every row seen, kept even if NinjaTrader's base is reset or reinstalled
  bars        M5 bars of NQ/ES/YM archived from DR Lab's live cache (it holds only a few days)
  derived     trades, trade_fills, actions — rebuilt from the raw layer on every run (deterministic)

Run:  python lab/trades.py collect          (the scheduled task runs this every 15 minutes)
      python lab/trades.py summary
      python lab/trades.py sql "select ..."  (read-only)
Spec: spec/DR-LAB-TRADE-JOURNAL.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT / '.runtime'
OUT_DIR = RUNTIME / 'trades'
JOURNAL = OUT_DIR / 'journal.sqlite3'
REPORT = OUT_DIR / 'report.html'
LIVE = RUNTIME / 'live'
NT_DB = Path.home() / 'Documents' / 'NinjaTrader 8' / 'db' / 'NinjaTrader.sqlite'
VERSION = 'dr-lab-trades-1'

# Box hours of the DR/IDR method, minutes of the New York day: (start, box formed, session end). Same numbers as
# engine_market.SESSIONS; copied so the collector runs without numpy/pandas. tests/trades.py checks they agree.
SESSIONS = {'ODR': (180, 240, 510), 'RDR': (570, 630, 960), 'ADR': (1170, 1230, 1560)}

# NinjaTrader 8.1 enums, read from NinjaTrader.Core.dll 8.1.8.4 (23.11.2026).
ORDER_STATE = {0: 'Accepted', 1: 'Cancelled', 2: 'Filled', 3: 'Initialized', 4: 'PartFilled', 5: 'CancelSubmitted',
               6: 'ChangeSubmitted', 7: 'Submitted', 8: 'TriggerPending', 9: 'Rejected', 10: 'Working',
               11: 'CancelPending', 12: 'ChangePending', 13: 'Suspended', 50: 'AcceptedByRisk', 99: 'Unknown'}
ORDER_TYPE = {0: 'Limit', 1: 'Market', 2: 'MIT', 3: 'StopLimit', 4: 'StopMarket', 99: 'Unknown'}
ORDER_ACTION = {0: 'Buy', 1: 'BuyToCover', 2: 'Sell', 3: 'SellShort'}
ACCOUNT_ITEM = {0: 'BuyingPower', 1: 'CashValue', 2: 'Commission', 3: 'ExcessIntradayMargin', 4: 'ExcessInitialMargin',
                5: 'ExcessMaintenanceMargin', 6: 'ExcessPositionMargin', 7: 'Fee', 8: 'GrossRealizedProfitLoss',
                9: 'InitialMargin', 10: 'IntradayMargin', 15: 'NetLiquidation', 18: 'RealizedProfitLoss',
                21: 'SodCashValue', 23: 'UnrealizedProfitLoss', 24: 'TotalCashBalance', 25: 'DailyLossLimit',
                30: 'TrailingMaxDrawdown'}
# OneUp Evaluation commission per contract per side, as the operator's MNQ Protection Panel counts it
# (ProtectionMath.EvaluationFee): micro contracts $1, others $2.50. Sim101 has no commission template, so this
# estimate is applied to both kinds to keep them comparable.
MICROS = {'MNQ', 'MES', 'MYM', 'M2K', 'MCL', 'MGC', 'M6A', 'M6B', 'M6E', 'MCD', 'MSF', 'MJY', 'MNG', 'MHG', 'MBT', 'MET'}
FAMILY = {'NQ': 'NQ', 'MNQ': 'NQ', 'ES': 'ES', 'MES': 'ES', 'YM': 'YM', 'MYM': 'YM'}
EPOCH = dt.datetime(1, 1, 1, tzinfo=dt.timezone.utc)


def fee(master, qty):
    return qty * (1.0 if master.upper() in MICROS else 2.5)


def ticks_to_utc(v):
    """NinjaTrader stores times as .NET ticks (100 ns since 0001-01-01). Checked against NQ bars 23.11.2026: these are
    UTC (132 of 132 fills inside the UTC M5 bar, 3 of 132 under local time)."""
    return EPOCH + dt.timedelta(microseconds=int(v) // 10)


def iso(d):
    return d.strftime('%Y-%m-%dT%H:%M:%S.') + f'{d.microsecond // 1000:03d}Z'


def now_iso():
    return iso(dt.datetime.now(dt.timezone.utc))


# ---- New York clock without a tz database: US DST = second Sunday of March 2:00 .. first Sunday of November 2:00
def _nth_sunday(year, month, n):
    d = dt.date(year, month, 1)
    d += dt.timedelta(days=(6 - d.weekday()) % 7)
    return d + dt.timedelta(days=7 * (n - 1))


def to_et(u):
    """UTC datetime -> naive New York local time."""
    y = u.year
    start = dt.datetime.combine(_nth_sunday(y, 3, 2), dt.time(7), dt.timezone.utc)   # 2:00 EST = 7:00 UTC
    end = dt.datetime.combine(_nth_sunday(y, 11, 1), dt.time(6), dt.timezone.utc)    # 2:00 EDT = 6:00 UTC
    off = -4 if start <= u < end else -5
    return (u + dt.timedelta(hours=off)).replace(tzinfo=None)


def et_to_utc_ts(naive):
    for off in (-4, -5):
        u = (naive - dt.timedelta(hours=off)).replace(tzinfo=dt.timezone.utc)
        if to_et(u) == naive:
            return u.timestamp()
    return (naive + dt.timedelta(hours=5)).replace(tzinfo=dt.timezone.utc).timestamp()


SCHEMA = """
create table if not exists meta(key text primary key, value text);
create table if not exists runs(id integer primary key, started_utc text, finished_utc text, status text, message text,
  source_mtime real, new_executions integer, new_updates integer, new_bars integer, trades integer);
create table if not exists nt_accounts(name text primary key, nt_id integer, provider integer, fcm text,
  initial_cash real, kind text, first_seen_utc text, last_seen_utc text);
create table if not exists instruments(instrument text primary key, master text, expiry text, point_value real,
  tick_size real, family text);
create table if not exists nt_orders(order_id text primary key, account text, nt_id integer, name text, origin text,
  entry_mode text, action text, side text, order_type text, quantity integer, limit_price real, stop_price real,
  state text, oco text, instrument text, t real, time_utc text, first_seen_utc text, last_seen_utc text);
create table if not exists nt_order_updates(order_id text, nr integer, t real, time_utc text, state text,
  limit_price real, stop_price real, quantity integer, filled integer, avg_fill_price real, comment text, error text,
  first_seen_utc text, primary key(order_id, nr));
create table if not exists nt_executions(execution_id text, order_id text, instrument text, account text,
  nt_id integer, t real, time_utc text, side text, price real, quantity integer, position_after integer,
  is_entry integer, is_exit integer, name text, commission real, first_seen_utc text,
  primary key(execution_id, order_id, instrument));
create table if not exists nt_account_values(account text, item text, value real, time_utc text, seen_utc text,
  primary key(account, item, time_utc, value));
create table if not exists bars(family text, t integer, o real, h real, l real, c real, feed text,
  primary key(family, t));
"""

DERIVED = """
drop table if exists trades; drop table if exists trade_fills; drop table if exists actions;
create table trades(trade_id integer primary key, account text, kind text, attempt integer, instrument text,
  master text, family text, direction text, opened_utc text, closed_utc text, opened_et text, closed_et text,
  weekday text, hold_sec real, status text, gap integer, fills integer, entry_fills integer, exit_fills integer,
  max_qty integer, adds integer, avg_entry real, avg_exit real, points real, ticks_per_contract real,
  pnl_gross real, fees_est real, pnl_net_est real, commission_nt real, outcome text, exit_by text, exit_origin text,
  target_set integer, target_first_ticks real, target_last_ticks real, target_moves integer,
  target_moves_closer integer, target_moves_further integer, exit_before_target integer,
  left_to_target_ticks real, stop_set integer, stop_first_ticks real, stop_last_ticks real, stop_moves integer,
  stop_tightened integer, stop_loosened integer, stop_to_breakeven integer, entry_origin text, entry_order_type text,
  entry_session text, entry_box_min real, entry_phase text, entry_state text, entry_sd real, entry_idr_pos real,
  exit_session text, exit_box_min real, exit_state text, exit_sd real, exit_idr_pos real,
  box_day text, dr_high real, dr_low real, idr_high real, idr_low real, bars_ok integer);
create table trade_fills(trade_id integer, execution_id text, order_id text, t real, time_utc text, side text,
  quantity integer, price real, role text, position_after integer, origin text, order_type text);
create table actions(id integer primary key, account text, kind text, attempt integer, instrument text,
  order_id text, trade_id integer, t real, time_utc text, time_et text, action text, origin text, order_type text,
  side text, role text, quantity integer, price real, price_from real, price_to real, ticks_moved real,
  toward text, state text);
create index if not exists ix_actions_trade on actions(trade_id);
create index if not exists ix_fills_trade on trade_fills(trade_id);
"""


def origin_of(name, entry_mode):
    name = name or ''
    if name.startswith('SimAPI'): return 'agent'
    if name.startswith('MNQPanel'): return 'panel'
    if name == 'Close': return 'close_button'
    if name == 'External': return 'external'
    return 'hand' if entry_mode == 1 else 'auto'


def kind_of(name, fcm):
    if name == 'Sim101': return 'sim'
    if (fcm or '').lower().startswith('oneup') or 'OUP' in name: return 'prop'
    return 'other'


# ------------------------------------------------------------------------------------------------ raw layer
def copy_source(src, dst):
    """Copy NinjaTrader's base while it runs and check the copy; one retry if it caught a write half-way."""
    for attempt in range(3):
        shutil.copyfile(src, dst)
        try:
            con = sqlite3.connect(f'file:{dst}?mode=ro', uri=True)
            ok = con.execute('pragma quick_check').fetchone()[0] == 'ok'
            con.close()
        except sqlite3.DatabaseError:
            ok = False
        if ok: return True
        time.sleep(2)
    return False


def import_raw(j, src_path):
    s = sqlite3.connect(f'file:{src_path}?mode=ro', uri=True)
    seen = now_iso()
    n_exec = n_upd = 0
    acc_name = {}
    for aid, name, prov, fcm, cash in s.execute('select Id, Name, Provider, Fcm, SimulatorInitialCash from Accounts'):
        acc_name[aid] = name
        kind = kind_of(name, fcm)
        j.execute("""insert into nt_accounts(name, nt_id, provider, fcm, initial_cash, kind, first_seen_utc, last_seen_utc)
                     values(?,?,?,?,?,?,?,?) on conflict(name) do update set nt_id=excluded.nt_id,
                     initial_cash=excluded.initial_cash, last_seen_utc=excluded.last_seen_utc""",
                  (name, aid, prov, fcm, cash, kind, seen, seen))
    inst = {}
    for iid, master, expiry, pv, tick in s.execute("""select i.Id, m.Name, i.Expiry, m.PointValue, m.TickSize
            from Instruments i join MasterInstruments m on m.Id=i.MasterInstrument
            where i.Id in (select Instrument from Executions union select Instrument from Orders)"""):
        exp = ticks_to_utc(expiry).strftime('%m-%y') if expiry else ''
        key = f'{master} {exp}'.strip()
        inst[iid] = (key, master)
        j.execute('insert or replace into instruments values(?,?,?,?,?,?)', (key, master, exp, pv, tick, FAMILY.get(master)))
    order_key = {}
    for row in s.execute("""select Id, OrderId, Account, Name, OrderEntry, OrderAction, OrderType, Quantity, LimitPrice,
            StopPrice, OrderState, Oco, Instrument, Time from Orders"""):
        nid, oid, aid, name, entry, action, otype, qty, lim, stp, state, oco, iid, tm = row
        order_key[nid] = oid
        act = ORDER_ACTION.get(action, str(action))
        j.execute("""insert into nt_orders values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            on conflict(order_id) do update set quantity=excluded.quantity, limit_price=excluded.limit_price,
            stop_price=excluded.stop_price, state=excluded.state, last_seen_utc=excluded.last_seen_utc""",
                  (oid, acc_name.get(aid, str(aid)), nid, name, origin_of(name, entry), 'manual' if entry == 1 else 'automated',
                   act, 'buy' if action in (0, 1) else 'sell', ORDER_TYPE.get(otype, str(otype)), qty, lim, stp,
                   ORDER_STATE.get(state, str(state)), oco, inst.get(iid, (str(iid),))[0],
                   ticks_to_utc(tm).timestamp(), iso(ticks_to_utc(tm)), seen, seen))
    for oref, nr, avg, comment, err, filled, lim, state, qty, stp, tm in s.execute(
            """select "Order", Nr, AvgFillPrice, Comment, Error, Filled, LimitPrice, OrderState, Quantity, StopPrice, Time
               from OrderUpdates"""):
        oid = order_key.get(oref)
        if oid is None: continue
        u = ticks_to_utc(tm)
        cur = j.execute("""insert or ignore into nt_order_updates values(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (oid, nr, u.timestamp(), iso(u), ORDER_STATE.get(state, str(state)), lim, stp, qty, filled, avg,
                         comment, err, seen))
        n_upd += cur.rowcount
    for row in s.execute("""select Id, ExecutionId, OrderId, Instrument, Account, Time, MarketPosition, Price, Quantity,
            Position, IsEntry, IsExit, Name, Commission from Executions"""):
        nid, eid, oid, iid, aid, tm, mp, px, qty, pos, ie, ix, name, comm = row
        u = ticks_to_utc(tm)
        cur = j.execute('insert or ignore into nt_executions values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                        (eid, oid, inst.get(iid, (str(iid),))[0], acc_name.get(aid, str(aid)), nid, u.timestamp(), iso(u),
                         'buy' if mp == 0 else 'sell', px, qty, pos, ie, ix, name, comm, seen))
        n_exec += cur.rowcount
    for aid, item, val, tm in s.execute('select Account, ItemType, Value, TimeUtc from AccountItems'):
        name = acc_name.get(aid)
        if name is None or kind_of(name, '') == 'other' and not name.startswith('Sim'): continue
        if item not in ACCOUNT_ITEM: continue
        j.execute('insert or ignore into nt_account_values values(?,?,?,?,?)',
                  (name, ACCOUNT_ITEM[item], val, iso(ticks_to_utc(tm)), seen))
    s.close()
    return n_exec, n_upd


def import_bars(j, live_dir):
    n = 0
    for fam in ('NQ', 'ES', 'YM'):
        p = Path(live_dir) / f'{fam.lower()}.json'
        if not p.exists(): continue
        try:
            d = json.loads(p.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            continue
        if d.get('switched'): continue                     # the pane showed another symbol: do not trust these bars
        fetched = dt.datetime.fromisoformat(d['fetched_at']).timestamp()
        for b in d.get('bars', []):
            if int(b[0]) + 300 > fetched: continue          # only closed bars are archived
            cur = j.execute('insert or ignore into bars values(?,?,?,?,?,?,?)', (fam, int(b[0]), *map(float, b[1:5]), d.get('feed')))
            n += cur.rowcount
    return n


# ------------------------------------------------------------------------------------------------ market moment
class Market:
    def __init__(self, j):
        self.j = j
        self.cache = {}

    def _bars(self, fam, lo, hi):
        return self.j.execute('select t, o, h, l, c from bars where family=? and t>=? and t<? order by t', (fam, lo, hi)).fetchall()

    def box(self, fam, session, iday):
        key = (fam, session, iday)
        if key not in self.cache:
            start, formed, end = SESSIONS[session]
            base = dt.datetime.combine(iday, dt.time())
            t0 = et_to_utc_ts(base + dt.timedelta(minutes=start))
            t1 = et_to_utc_ts(base + dt.timedelta(minutes=end))
            self.cache[key] = [(int(t), o, h, l, c, (t - t0) / 60.0 + start) for t, o, h, l, c in self._bars(fam, int(t0), int(t1))]
        return self.cache[key]

    def moment(self, fam, ts, price):
        """Where a fill stands in the method: session, minutes from box start, phase; with bars also the box levels,
        confirmation and position. Formulas mirror live.state(): DR = high/low of the box hour, IDR = body extremes,
        confirmation = first closed M5 beyond DR after the box, position in IDR widths from the confirmed edge."""
        u = dt.datetime.fromtimestamp(ts, dt.timezone.utc)
        et = to_et(u)
        mod = et.hour * 60 + et.minute + et.second / 60.0
        out = dict(session=None, box_min=None, phase='вне сессий', state=None, sd=None, idr_pos=None, day=None,
                   dr_high=None, dr_low=None, idr_high=None, idr_low=None, bars_ok=0)
        sess = iday = None
        for name, (start, formed, end) in SESSIONS.items():
            if start <= mod < end:
                sess, iday, m = name, et.date(), mod
            elif name == 'ADR' and mod < end - 1440:
                sess, iday, m = name, et.date() - dt.timedelta(days=1), mod + 1440
        if sess is None or fam is None: return out
        start, formed, end = SESSIONS[sess]
        out.update(session=sess, box_min=round(m - start, 2), phase='бокс' if m < formed else 'после бокса',
                   day=str(iday + dt.timedelta(days=1) if sess == 'ADR' else iday))
        bars = self.box(fam, sess, iday)
        win = [b for b in bars if b[5] < formed]
        if len(win) < (formed - start) // 5:
            out['state'] = 'нет свечей'
            return out
        out['bars_ok'] = 1
        dr_hi, dr_lo = max(b[2] for b in win), min(b[3] for b in win)
        idr_hi, idr_lo = max(max(b[1], b[4]) for b in win), min(min(b[1], b[4]) for b in win)
        out.update(dr_high=dr_hi, dr_low=dr_lo, idr_high=idr_hi, idr_low=idr_lo)
        width = idr_hi - idr_lo
        if m < formed:
            out['state'] = 'бокс формируется'
            return out
        closed = [b for b in bars if b[5] >= formed and b[5] + 5 <= m + 1e-9]
        side = tau = None
        for b in closed:
            if b[4] > dr_hi: side, tau = 1, b[5] + 5; break
            if b[4] < dr_lo: side, tau = -1, b[5] + 5; break
        if width > 0:
            out['idr_pos'] = round((price - idr_lo) / width, 3)
        if side is None or width <= 0:
            out['state'] = 'ждём подтверждения'
            return out
        edge, opp = (idr_hi, dr_lo) if side == 1 else (idr_lo, dr_hi)
        failed = any(side * (b[4] - opp) < 0 for b in closed if b[5] + 5 > tau)
        out['sd'] = round(side * (price - edge) / width, 3)
        out['state'] = ('подтверждён вверх' if side == 1 else 'подтверждён вниз') + (', сломан' if failed else '')
        return out


# ------------------------------------------------------------------------------------------------ derived layer
def price_at(updates, t, field):
    """Price of an order at time t: last non-zero value among updates up to t (by sequence number)."""
    val = None
    for u in updates:
        if u['t'] > t + 0.5: break
        if u[field]: val = u[field]
    return val


def rebuild(j):
    j.executescript(DERIVED)
    acc = {r[0]: r for r in j.execute('select name, kind from nt_accounts')}
    inst = {r[0]: dict(master=r[1], pv=r[2], tick=r[3], family=r[4]) for r in j.execute(
        'select instrument, master, point_value, tick_size, family from instruments')}
    # attempt = order of first activity among accounts of the same kind (OneUp gives a new number per evaluation)
    attempt = {}
    for kind in ('prop', 'sim'):
        rows = j.execute("""select a.name, min(e.t) from nt_accounts a join nt_executions e on e.account=a.name
                            where a.kind=? group by a.name order by 2""", (kind,)).fetchall()
        for i, (name, _) in enumerate(rows, 1): attempt[name] = i
    orders = {r['order_id']: r for r in map(dict, _rows(j, 'select * from nt_orders'))}
    updates = {}
    for r in _rows(j, 'select * from nt_order_updates order by order_id, nr'):
        updates.setdefault(r['order_id'], []).append(dict(r))
    market = Market(j)
    trades, fills_out = [], []
    groups = {}
    for r in _rows(j, """select * from nt_executions e where exists
                        (select 1 from nt_accounts a where a.name=e.account and a.kind in ('prop','sim'))
                        order by account, instrument, t, nt_id"""):
        groups.setdefault((r['account'], r['instrument']), []).append(dict(r))
    for (account, instrument), fills in groups.items():
        meta = inst.get(instrument, dict(master=instrument.split()[0], pv=1.0, tick=0.25, family=None))
        pos, cur = 0, None

        def close(tr, status):
            tr['status'] = status
            trades.append(tr)

        for f in fills:
            dq = f['quantity'] if f['side'] == 'buy' else -f['quantity']
            nt_after = f['position_after']
            if nt_after is not None and pos + dq != nt_after:
                pre = nt_after - dq                       # what NinjaTrader says the position was before this fill
                if cur is not None:
                    cur['gap'] = 1
                    if pre == 0 or (pre > 0) != (pos > 0):
                        close(cur, 'gap')                 # it was closed by something not in the base
                        cur = None
                pos = pre
                if pos != 0 and cur is None:
                    cur = _new_trade(account, instrument, f, 1 if pos > 0 else -1)
                    cur['gap'] = 1
            if pos == 0 and cur is None:
                cur = _new_trade(account, instrument, f, 1 if dq > 0 else -1)
            o = orders.get(f['order_id'], {})
            new = pos + dq
            if pos != 0 and new != 0 and (new > 0) != (pos > 0):          # flip through zero: split the fill
                part = abs(pos)
                _add_fill(cur, f, -cur['dir'] * part, 'exit', o, fills_out)
                close(cur, 'closed')
                cur = _new_trade(account, instrument, f, 1 if new > 0 else -1)
                _add_fill(cur, f, new, 'entry', o, fills_out)
            else:
                same = dq * cur['dir'] > 0
                role = ('entry' if not cur['fills'] else 'add') if same else ('exit' if new == 0 else 'reduce')
                _add_fill(cur, f, dq, role, o, fills_out)
                if new == 0:
                    close(cur, 'closed')
                    cur = None
            pos = new
            if cur is not None: cur['max_qty'] = max(cur['max_qty'], abs(pos))
        if cur is not None:
            close(cur, 'open')
    trades.sort(key=lambda tr: tr['fills'][0]['t'])
    for tid, tr in enumerate(trades, 1):
        tr['trade_id'] = tid
        for fo in tr['fill_rows']: fo['trade_id'] = tid
    # orders -> trades: same account and instrument, first seen between the trade's first fill (minus 3 s) and its end
    by_ai = {}
    for tr in trades: by_ai.setdefault((tr['account'], tr['instrument']), []).append(tr)
    order_trade = {}
    for oid, o in orders.items():
        ups = updates.get(oid, [])
        t0 = min([u['t'] for u in ups] + [o['t']])
        for tr in by_ai.get((o['account'], o['instrument']), []):
            end = tr['fills'][-1]['t'] if tr['status'] != 'open' else float('inf')
            if tr['fills'][0]['t'] - 3 <= t0 <= end + 0.5 or oid in tr['order_ids']:
                order_trade[oid] = tr['trade_id']
                tr.setdefault('orders', []).append(oid)
                break
    rows = []
    for tr in trades:
        rows.append(_trade_row(tr, meta_of(inst, tr), orders, updates, acc, attempt, market))
    _insert(j, 'trades', rows)
    _insert(j, 'trade_fills', [{k: fo[k] for k in ('trade_id', 'execution_id', 'order_id', 't', 'time_utc', 'side', 'quantity',
                                                    'price', 'role', 'position_after', 'origin', 'order_type')} for fo in fills_out])
    _insert(j, 'actions', _actions(orders, updates, order_trade, {r['trade_id']: r for r in rows}, inst, acc, attempt,
                                   j.execute('select execution_id, order_id, account, instrument, t, time_utc, side, quantity, price from nt_executions').fetchall()))
    return len(rows)


def meta_of(inst, tr):
    return inst.get(tr['instrument'], dict(master=tr['instrument'].split()[0], pv=1.0, tick=0.25, family=None))


def _rows(j, sql, args=()):
    j.row_factory = sqlite3.Row
    try:
        return j.execute(sql, args).fetchall()
    finally:
        j.row_factory = None


def _insert(j, table, rows):
    if not rows: return
    cols = list(dict.fromkeys(k for r in rows for k in r))      # rows of one table may carry different optional fields
    j.executemany(f'insert into {table}({",".join(cols)}) values({",".join("?" * len(cols))})', [tuple(r.get(c) for c in cols) for r in rows])


def _new_trade(account, instrument, f, direction):
    return dict(account=account, instrument=instrument, dir=direction, fills=[], fill_rows=[], max_qty=0, gap=0,
                order_ids=set())


def _add_fill(tr, f, signed_qty, role, o, out):
    q = abs(signed_qty)
    tr['fills'].append(dict(t=f['t'], time_utc=f['time_utc'], price=f['price'], q=q, signed=signed_qty, role=role,
                            order_id=f['order_id'], origin=o.get('origin'), order_type=o.get('order_type'),
                            name=f['name'], commission=f['commission'] or 0))
    tr['order_ids'].add(f['order_id'])
    row = dict(trade_id=None, execution_id=f['execution_id'], order_id=f['order_id'], t=f['t'], time_utc=f['time_utc'],
               side='buy' if signed_qty > 0 else 'sell', quantity=q, price=f['price'], role=role,
               position_after=f['position_after'], origin=o.get('origin'), order_type=o.get('order_type'))
    tr['fill_rows'].append(row)
    out.append(row)


def _trade_row(tr, meta, orders, updates, acc, attempt, market):
    d, pv, tick = tr['dir'], meta['pv'] or 1.0, meta['tick'] or 0.25
    fills = tr['fills']
    ent = [f for f in fills if f['role'] in ('entry', 'add')]
    ext = [f for f in fills if f['role'] in ('exit', 'reduce')]
    first, last = fills[0], fills[-1]
    avg_entry = sum(f['price'] * f['q'] for f in ent) / sum(f['q'] for f in ent) if ent else None
    avg_exit = sum(f['price'] * f['q'] for f in ext) / sum(f['q'] for f in ext) if ext else None
    closed = tr['status'] == 'closed' and not tr['gap']
    gross = sum(-f['signed'] * f['price'] for f in fills) * pv if closed else None
    fees = sum(fee(meta['master'], f['q']) for f in fills)
    entered = sum(f['q'] for f in ent)
    points = (avg_exit - avg_entry) * d if (avg_entry is not None and avg_exit is not None) else None
    tpc = gross / pv / tick / entered if (gross is not None and entered) else None
    outcome = None
    if tpc is not None:
        outcome = 'плюс' if tpc > 2 else ('минус' if tpc < -2 else 'около нуля')
    # exit kind
    exit_kinds, exit_origins = [], []
    for f in ext:
        o = orders.get(f['order_id'], {})
        typ = o.get('order_type') or f['order_type']
        org = o.get('origin') or f['origin'] or 'unknown'
        exit_origins.append(org)
        if typ in ('Limit', 'MIT'):
            better = avg_entry is not None and d * (f['price'] - avg_entry) > 0
            exit_kinds.append('тейк' if better else 'лимит без прибыли')
        elif typ in ('StopMarket', 'StopLimit'):
            sp = o.get('stop_price') or f['price']
            rel = d * (sp - avg_entry) / tick if avg_entry is not None else None
            exit_kinds.append('безубыток' if rel is not None and -1 <= rel <= 6 else ('стоп в плюсе' if rel is not None and rel > 6 else 'стоп'))
        elif typ == 'Market':
            exit_kinds.append('рынок')
        elif typ is None:
            exit_kinds.append('нет заявки в базе')
        else:
            exit_kinds.append('другое')
    uniq = sorted(set(exit_kinds))
    exit_by = uniq[0] if len(uniq) == 1 else ('смешанный' if uniq else None)
    org_u = sorted(set(exit_origins))
    # targets and stops working during the trade: closing-side orders attached to it
    tgt, stp = [], []
    for oid in tr.get('orders', []):
        o = orders[oid]
        closing = (o['side'] == 'sell') == (d == 1)
        if not closing: continue
        ups = updates.get(oid, [])
        if o['order_type'] in ('Limit', 'MIT'):
            tgt.append((o, ups, 'limit_price'))
        elif o['order_type'] in ('StopMarket', 'StopLimit'):
            stp.append((o, ups, 'stop_price'))

    def path(o, ups, field):
        seq = [u[field] for u in ups if u[field]] or ([o[field]] if o[field] else [])
        moves = [(a, b) for a, b in zip(seq, seq[1:]) if abs(b - a) > 1e-9]
        return seq, moves

    def rel(p):
        return round(d * (p - avg_entry) / tick, 2) if (p is not None and avg_entry is not None) else None

    t_first = t_last = None; t_moves = t_closer = t_further = 0
    for o, ups, field in tgt:
        seq, moves = path(o, ups, field)
        if not seq: continue
        if t_first is None: t_first = seq[0]
        t_last = seq[-1]
        t_moves += len(moves)
        t_closer += sum(1 for a, b in moves if d * (b - a) < 0)
        t_further += sum(1 for a, b in moves if d * (b - a) > 0)
    s_first = s_last = None; s_moves = s_tight = s_loose = 0; to_be = 0
    for o, ups, field in stp:
        seq, moves = path(o, ups, field)
        if not seq: continue
        if s_first is None: s_first = seq[0]
        s_last = seq[-1]
        s_moves += len(moves)
        s_tight += sum(1 for a, b in moves if d * (b - a) > 0)
        s_loose += sum(1 for a, b in moves if d * (b - a) < 0)
        if any(rel(b) is not None and -1 <= rel(b) <= 6 for a, b in moves): to_be = 1
    # exit before target: the trade ended by market/stop while a target order was still working
    before, left = 0, None
    if ext and exit_by not in ('тейк', None):
        t_end = last['t']
        for o, ups, field in tgt:
            if o['order_id'] in {f['order_id'] for f in ext}: continue
            placed = min([u['t'] for u in ups] + [o['t']])
            if placed > t_end: continue
            p = price_at(ups, t_end, field) or o[field]
            if p is None: continue
            before = 1
            left = round(d * (p - last['price']) / tick, 2)
    e = market.moment(meta['family'], first['t'], first['price'])
    x = market.moment(meta['family'], last['t'], last['price']) if tr['status'] != 'open' else {}
    o0 = orders.get(first['order_id'], {})
    ou = to_et(dt.datetime.fromtimestamp(first['t'], dt.timezone.utc))
    return dict(trade_id=tr['trade_id'], account=tr['account'], kind=acc.get(tr['account'], (None, None))[1],
                attempt=attempt.get(tr['account']), instrument=tr['instrument'], master=meta['master'], family=meta['family'],
                direction='long' if d == 1 else 'short', opened_utc=first['time_utc'],
                closed_utc=last['time_utc'] if tr['status'] != 'open' else None,
                opened_et=ou.strftime('%Y-%m-%d %H:%M:%S'),
                closed_et=to_et(dt.datetime.fromtimestamp(last['t'], dt.timezone.utc)).strftime('%Y-%m-%d %H:%M:%S') if tr['status'] != 'open' else None,
                weekday=['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс'][ou.weekday()],
                hold_sec=round(last['t'] - first['t'], 3) if tr['status'] != 'open' else None,
                status=tr['status'], gap=tr['gap'], fills=len(fills), entry_fills=len(ent), exit_fills=len(ext),
                max_qty=tr['max_qty'], adds=max(0, len(ent) - 1), avg_entry=avg_entry, avg_exit=avg_exit,
                points=round(points, 4) if points is not None else None, ticks_per_contract=round(tpc, 2) if tpc is not None else None,
                pnl_gross=round(gross, 2) if gross is not None else None, fees_est=round(fees, 2),
                pnl_net_est=round(gross - fees, 2) if gross is not None else None,
                commission_nt=round(sum(f['commission'] for f in fills), 2), outcome=outcome, exit_by=exit_by,
                exit_origin=','.join(org_u) if org_u else None,
                target_set=1 if tgt else 0, target_first_ticks=rel(t_first), target_last_ticks=rel(t_last),
                target_moves=t_moves, target_moves_closer=t_closer, target_moves_further=t_further,
                exit_before_target=before, left_to_target_ticks=left,
                stop_set=1 if stp else 0, stop_first_ticks=rel(s_first), stop_last_ticks=rel(s_last), stop_moves=s_moves,
                stop_tightened=s_tight, stop_loosened=s_loose, stop_to_breakeven=to_be,
                entry_origin=o0.get('origin') or first['origin'], entry_order_type=o0.get('order_type') or first['order_type'],
                entry_session=e['session'], entry_box_min=e['box_min'], entry_phase=e['phase'], entry_state=e['state'],
                entry_sd=e['sd'], entry_idr_pos=e['idr_pos'],
                exit_session=x.get('session'), exit_box_min=x.get('box_min'), exit_state=x.get('state'), exit_sd=x.get('sd'),
                exit_idr_pos=x.get('idr_pos'), box_day=e['day'], dr_high=e['dr_high'], dr_low=e['dr_low'],
                idr_high=e['idr_high'], idr_low=e['idr_low'], bars_ok=e['bars_ok'])


def _actions(orders, updates, order_trade, trades, inst, acc, attempt, executions):
    out = []

    def role_of(o, tid):
        tr = trades.get(tid)
        if tr is None:
            return 'вход без исполнения' if o['order_type'] in ('Limit', 'MIT', 'StopMarket', 'StopLimit') else 'другое'
        d = 1 if tr['direction'] == 'long' else -1
        closing = (o['side'] == 'sell') == (d == 1)
        if not closing: return 'вход'
        return {'Limit': 'тейк', 'MIT': 'тейк', 'StopMarket': 'стоп', 'StopLimit': 'стоп'}.get(o['order_type'], 'выход')

    for oid, o in orders.items():
        if acc.get(o['account'], (None, None))[1] not in ('prop', 'sim'): continue
        tid = order_trade.get(oid)
        role = role_of(o, tid)
        tick = (inst.get(o['instrument']) or {}).get('tick') or 0.25
        field = 'limit_price' if o['order_type'] in ('Limit', 'MIT') else 'stop_price'
        prev_px = prev_q = None
        placed = cancelled = rejected = False
        tr = trades.get(tid)
        d = (1 if tr['direction'] == 'long' else -1) if tr else 0
        for u in updates.get(oid, []) or [dict(t=o['t'], time_utc=o['time_utc'], state=o['state'], limit_price=o['limit_price'],
                                                  stop_price=o['stop_price'], quantity=o['quantity'])]:
            px = u[field] or None
            base = dict(account=o['account'], kind=acc[o['account']][1], attempt=attempt.get(o['account']),
                        instrument=o['instrument'], order_id=oid, trade_id=tid, t=u['t'], time_utc=u['time_utc'],
                        time_et=to_et(dt.datetime.fromtimestamp(u['t'], dt.timezone.utc)).strftime('%Y-%m-%d %H:%M:%S'),
                        origin=o['origin'], order_type=o['order_type'], side=o['side'], role=role, state=u['state'])
            if not placed:
                out.append(dict(base, action='выставил', quantity=u['quantity'], price=px))
                placed = True
            elif px is not None and prev_px is not None and abs(px - prev_px) > 1e-9:
                toward = None
                if d and role == 'тейк': toward = 'ближе' if d * (px - prev_px) < 0 else 'дальше'
                if d and role == 'стоп': toward = 'ближе' if d * (px - prev_px) > 0 else 'дальше'
                out.append(dict(base, action='передвинул', quantity=u['quantity'], price=px, price_from=prev_px, price_to=px,
                                ticks_moved=round((px - prev_px) / tick, 2), toward=toward))
            elif prev_q is not None and u['quantity'] != prev_q:
                out.append(dict(base, action='изменил объём', quantity=u['quantity'], price=px))
            if u['state'] == 'Cancelled' and not cancelled:
                out.append(dict(base, action='отменил', quantity=u['quantity'], price=px)); cancelled = True
            if u['state'] == 'Rejected' and not rejected:
                out.append(dict(base, action='отклонено', quantity=u['quantity'], price=px)); rejected = True
            if px is not None: prev_px = px
            prev_q = u['quantity']
    for eid, oid, account, instrument, t, time_utc, side, qty, price in executions:
        if acc.get(account, (None, None))[1] not in ('prop', 'sim'): continue
        o = orders.get(oid, {})
        tid = order_trade.get(oid)
        out.append(dict(account=account, kind=acc[account][1], attempt=attempt.get(account), instrument=instrument,
                        order_id=oid, trade_id=tid, t=t, time_utc=time_utc,
                        time_et=to_et(dt.datetime.fromtimestamp(t, dt.timezone.utc)).strftime('%Y-%m-%d %H:%M:%S'),
                        action='исполнено', origin=o.get('origin'), order_type=o.get('order_type'), side=side,
                        role=role_of(o, tid) if o else None, quantity=qty, price=price, state='Fill'))
    # a fill's order may be missing (seen in the base); attach such fills to the trade that holds the execution
    out.sort(key=lambda a: (a['t'], a['order_id'] or ''))
    return out


# ------------------------------------------------------------------------------------------------ checks & report
def reconcile(j):
    """Sim101 keeps its cash in NinjaTrader: start cash + all closed trades must equal its CashValue. Prop balances
    live on the Rithmic side and are not in the base, so they cannot be checked here."""
    out = {}
    for name, cash0 in j.execute("select name, initial_cash from nt_accounts where kind='sim'"):
        cv = j.execute("select value from nt_account_values where account=? and item='CashValue' order by time_utc desc, seen_utc desc limit 1", (name,)).fetchone()
        known = j.execute("select coalesce(sum(pnl_gross),0), count(*) from trades where account=? and status='closed' and gap=0", (name,)).fetchone()
        gaps = j.execute("select count(*) from trades where account=? and (gap=1 or status='open')", (name,)).fetchone()[0]
        comm = j.execute("select coalesce(sum(commission_nt),0) from trades where account=?", (name,)).fetchone()[0]
        if cv is None: continue
        nt_change = round(cv[0] - (cash0 or 0), 2)
        holes = [f'{r[0]} ({r[1]} NY)' for r in j.execute(
            "select trade_id, opened_et from trades where account=? and (gap=1 or status='open') order by trade_id", (name,))]
        out[name] = dict(nt_cash_change=nt_change, journal_closed_pnl=round(known[0] - comm, 2), closed_trades=known[1],
                         trades_with_gap_or_open=gaps, unexplained=round(nt_change - (known[0] - comm), 2),
                         unexplained_is_in=holes)
    return out


def summary(j):
    lines = []
    for kind, n, first, last in j.execute("select kind, count(*), min(opened_et), max(opened_et) from trades group by kind"):
        lines.append(f'{kind}: {n} сделок, {first} … {last} (NY)')
    for r in j.execute("""select kind, outcome, count(*), round(avg(hold_sec)/60,1), round(sum(pnl_net_est),2)
                          from trades where status='closed' and gap=0 group by kind, outcome order by kind, outcome"""):
        lines.append(f'  {r[0]} {r[1]}: {r[2]} сделок, держал в среднем {r[3]} мин, итог с комиссией ${r[4]}')
    for r in j.execute("select kind, action, count(*) from actions group by kind, action order by kind, 3 desc"):
        lines.append(f'  действия {r[0]} · {r[1]}: {r[2]}')
    rec = j.execute("select value from meta where key='reconcile'").fetchone()
    if rec: lines.append('сверка Sim101: ' + rec[0])
    last = j.execute('select started_utc, status, message from runs order by id desc limit 1').fetchone()
    if last: lines.append(f'последний сбор: {last[0]} · {last[1]} · {last[2] or ""}')
    return '\n'.join(lines)


def write_report(j, path):
    trades = [dict(r) for r in _rows(j, 'select * from trades order by opened_utc desc')]
    acts = {}
    for r in _rows(j, 'select trade_id, time_et, action, role, origin, order_type, side, quantity, price, price_from, price_to, ticks_moved, toward from actions where trade_id is not null order by t'):
        acts.setdefault(r['trade_id'], []).append(dict(r))
    for tr in trades: tr['acts'] = acts.get(tr['trade_id'], [])
    rec = j.execute("select value from meta where key='reconcile'").fetchone()
    last = j.execute('select finished_utc, status from runs order by id desc limit 1').fetchone()
    data = json.dumps(dict(trades=trades, reconcile=json.loads(rec[0]) if rec else {}, collected=last[0] if last else None),
                      ensure_ascii=False, default=str)
    tpl = (ROOT / 'trades_report.html').read_text(encoding='utf-8')
    path.write_text(tpl.replace('/*DATA*/null', data.replace('</', '<\\/')), encoding='utf-8')


# ------------------------------------------------------------------------------------------------ entry points
def connect(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    j = sqlite3.connect(path)
    j.executescript(SCHEMA)
    return j


def collect(nt_db=NT_DB, journal=JOURNAL, live_dir=LIVE, report=REPORT, force=False):
    journal = Path(journal)
    lock = journal.parent / 'collect.lock'
    journal.parent.mkdir(parents=True, exist_ok=True)
    try:
        if lock.exists() and time.time() - lock.stat().st_mtime < 600: return 'busy'
        lock.write_text(str(os.getpid()), encoding='utf-8')
    except OSError:
        return 'busy'
    j = connect(journal)
    started = now_iso()
    status, msg, n_exec = 'ok', '', 0
    n_upd = n_bars = n_tr = 0
    try:
        src = Path(nt_db)
        mtimes = json.dumps([src.stat().st_mtime if src.exists() else None] +
                            [(Path(live_dir) / f'{x}.json').stat().st_mtime if (Path(live_dir) / f'{x}.json').exists() else None
                             for x in ('nq', 'es', 'ym')])
        prev = j.execute("select value from meta where key='source_mtimes'").fetchone()
        if not force and prev and prev[0] == mtimes and j.execute("select value from meta where key='version'").fetchone() == (VERSION,):
            status = 'unchanged'
        else:
            if src.exists():
                tmp = journal.parent / 'nt-copy.sqlite'
                if copy_source(src, tmp):
                    n_exec, n_upd = import_raw(j, tmp)
                else:
                    status, msg = 'source_inconsistent', 'копия базы NinjaTrader не прошла проверку; повтор через 15 минут'
                try: tmp.unlink()
                except OSError: pass
            else:
                status, msg = 'no_source', f'нет базы NinjaTrader: {src}'
            n_bars = import_bars(j, live_dir)
            n_tr = rebuild(j)
            rec = reconcile(j)
            j.execute("insert or replace into meta values('reconcile', ?)", (json.dumps(rec, ensure_ascii=False),))
            j.execute("insert or replace into meta values('version', ?)", (VERSION,))
            if status == 'ok':
                j.execute("insert or replace into meta values('source_mtimes', ?)", (mtimes,))
            j.commit()
            if report: write_report(j, Path(report))
    except Exception as exc:                                   # a failed run is recorded, never silent
        j.rollback()
        status, msg = 'error', f'{type(exc).__name__}: {exc}'
    finally:
        j.execute('insert into runs(started_utc, finished_utc, status, message, source_mtime, new_executions, new_updates, new_bars, trades) values(?,?,?,?,?,?,?,?,?)',
                  (started, now_iso(), status, msg, Path(nt_db).stat().st_mtime if Path(nt_db).exists() else None, n_exec, n_upd, n_bars, n_tr))
        j.commit()
        j.close()
        try: lock.unlink()
        except OSError: pass
    return status


def main(argv=None):
    ap = argparse.ArgumentParser(description='DR Lab trade journal (NinjaTrader → local journal)')
    ap.add_argument('cmd', choices=['collect', 'summary', 'sql', 'report'])
    ap.add_argument('query', nargs='?')
    ap.add_argument('--nt-db', default=str(NT_DB))
    ap.add_argument('--journal', default=str(JOURNAL))
    ap.add_argument('--live-dir', default=str(LIVE))
    ap.add_argument('--report', default=str(REPORT))
    ap.add_argument('--force', action='store_true', help='rebuild even if nothing changed')
    a = ap.parse_args(argv)
    if a.cmd == 'collect':
        st = collect(a.nt_db, a.journal, a.live_dir, Path(a.report), force=a.force)
        if sys.stdout: print(st)
        return 0 if st in ('ok', 'unchanged', 'busy') else 1
    j = sqlite3.connect(f'file:{Path(a.journal)}?mode=ro', uri=True)
    if a.cmd == 'summary':
        print(summary(j))
    elif a.cmd == 'sql':
        cur = j.execute(a.query)
        print('\t'.join(c[0] for c in cur.description))
        for r in cur: print('\t'.join('' if v is None else str(v) for v in r))
    elif a.cmd == 'report':
        j.close(); j = sqlite3.connect(Path(a.journal)); write_report(j, Path(a.report)); print(a.report)
    return 0


if __name__ == '__main__':
    sys.exit(main())
