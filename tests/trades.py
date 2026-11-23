"""The trade journal (lab/trades.py, spec/DR-LAB-TRADE-JOURNAL.md), offline on a synthetic NinjaTrader base.

    python -B tests/trades.py

Builds a small base with NinjaTrader's table layout in a temporary folder (never the operator's base or
lab/.runtime): Sim101 and a OneUp-style prop account, orders with every update, fills (one repeated), a flip through
zero, a stop moved to breakeven, a market exit while a target was working, a missing fill and an entry that never
filled. Checks the trades, the actions, the market moment against hand-computed box levels, the Sim101 balance check,
that the raw layer survives a reset of the source, and the report. Exit code 0 = every check passed.
"""
import json
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'lab'))
import trades as T  # noqa: E402

bad = 0


def check(ok, what):
    global bad
    bad += not ok
    print(('  ok   ' if ok else '  FAIL ') + what)


def ticks(d):
    return int((d - datetime(1, 1, 1, tzinfo=timezone.utc)) / timedelta(microseconds=1)) * 10


DAY = datetime(2026, 11, 18, tzinfo=timezone.utc)          # Wednesday, New York on EST (UTC-5)


def at(hh, mm, ss=0):
    return DAY + timedelta(hours=hh, minutes=mm, seconds=ss)


class Base:
    def __init__(self, path):
        self.c = sqlite3.connect(path)
        self.c.executescript("""
        create table Accounts(Id, Name, Provider, Fcm, SimulatorInitialCash);
        create table MasterInstruments(Id, Name, PointValue, TickSize);
        create table Instruments(Id, MasterInstrument, Expiry);
        create table Orders(Id, OrderId, Account, Name, OrderEntry, OrderAction, OrderType, Quantity, LimitPrice,
                            StopPrice, OrderState, Oco, Instrument, Time);
        create table OrderUpdates("Order", Nr, AvgFillPrice, Comment, Error, Filled, LimitPrice, OrderState, Quantity,
                                  StopPrice, Time);
        create table Executions(Id, ExecutionId, OrderId, Instrument, Account, Time, MarketPosition, Price, Quantity,
                                Position, IsEntry, IsExit, Name, Commission);
        create table AccountItems(Account, Currency, ItemType, Value, TimeUtc);
        insert into Accounts values(0, 'Backtest', 15, '', 100000), (2, 'Sim101', 15, '', 100000),
                                   (5, 'testOUP00000000001', 38, 'OneUpTrader', 100000);
        insert into MasterInstruments values(1, 'MNQ', 2.0, 0.25);
        insert into Instruments values(10, 1, 639316800000000000);
        """)
        self.n_order = self.n_exec = 0

    def order(self, acc, name, entry, action, otype, qty, updates):
        """updates: list of (time, state, limit, stop). Returns the order id."""
        self.n_order += 1
        oid = f'O{acc}-{updates[0][0]:%H%M%S}-{action}-{otype}'   # stable across rebuilt bases, like NinjaTrader ids
        last = updates[-1]
        self.c.execute('insert into Orders values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                       (self.n_order, oid, acc, name, entry, action, otype, qty, last[2], last[3], last[1], '', 10, ticks(updates[0][0])))
        for nr, (tm, state, lim, stp) in enumerate(updates):
            self.c.execute('insert into OrderUpdates values(?,?,?,?,?,?,?,?,?,?,?)',
                           (self.n_order, nr, 0, '', '', 0, lim, state, qty, stp, ticks(tm)))
        return oid

    def fill(self, acc, oid, tm, side, price, qty, pos, name='', repeat=False):
        self.n_exec += 1
        eid = f'E{acc}-{tm:%H%M%S}-{side}'
        for k in range(2 if repeat else 1):
            self.c.execute('insert into Executions values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                           (self.n_exec * 10 + k, eid, oid, 10, acc, ticks(tm), 0 if side == 'buy' else 1, price, qty, pos, 0, 0, name, 0))


BUY, SELL = 0, 2
LIMIT, MARKET, STOP = 0, 1, 4
ACC, CXL, FILL, WORK, INIT, CHG = 0, 1, 2, 10, 3, 12


def build(path, with_first=True):
    b = Base(path)
    S, P = 2, 5
    if with_first:
        # A (Sim101): long 1 + add 1, target placed at 20040, moved further to 20050, filled there (fill repeated)
        a1 = b.order(S, '', 1, BUY, MARKET, 1, [(at(9, 30), FILL, 0, 0)])
        b.fill(S, a1, at(9, 30), 'buy', 20020, 1, 1)
        a2 = b.order(S, '', 1, BUY, MARKET, 1, [(at(9, 30, 10), FILL, 0, 0)])
        b.fill(S, a2, at(9, 30, 10), 'buy', 20022, 1, 2)
        a3 = b.order(S, 'MNQPanel.Target', 0, SELL, LIMIT, 2, [(at(9, 30, 20), INIT, 20040, 0), (at(9, 30, 21), WORK, 20040, 0),
                                                              (at(9, 35), CHG, 20050, 0), (at(9, 35, 1), WORK, 20050, 0),
                                                              (at(9, 40), FILL, 20050, 0)])
        b.fill(S, a3, at(9, 40), 'sell', 20050, 2, 0, repeat=True)
    # B (Sim101): long 1, then a sell 2 flips to short 1, then the Close button buys 1
    b1 = b.order(S, '', 1, BUY, MARKET, 1, [(at(10, 0), FILL, 0, 0)])
    b.fill(S, b1, at(10, 0), 'buy', 20030, 1, 1)
    b2 = b.order(S, '', 1, SELL, MARKET, 2, [(at(10, 1), FILL, 0, 0)])
    b.fill(S, b2, at(10, 1), 'sell', 20025, 2, -1)
    b3 = b.order(S, 'Close', 1, BUY, MARKET, 1, [(at(10, 2), FILL, 0, 0)])
    b.fill(S, b3, at(10, 2), 'buy', 20020, 1, 0, name='Close')
    # C (prop): short 1, panel stop 20040 moved to breakeven 20029, stopped there
    c1 = b.order(P, '', 1, SELL, MARKET, 1, [(at(9, 50), FILL, 0, 0)])
    b.fill(P, c1, at(9, 50), 'sell', 20030, 1, -1)
    c2 = b.order(P, 'MNQPanel.Stop', 0, BUY, STOP, 1, [(at(9, 50, 1), INIT, 0, 20040), (at(9, 50, 2), ACC, 0, 20040),
                                                       (at(9, 52), CHG, 0, 20029), (at(9, 52, 1), ACC, 0, 20029),
                                                       (at(9, 55), FILL, 0, 20029)])
    b.fill(P, c2, at(9, 55), 'buy', 20029, 1, 0)
    # D (prop): long 1, target 20060 working, closed by hand at market 20035, target then cancelled
    d1 = b.order(P, '', 1, BUY, MARKET, 1, [(at(11, 0), FILL, 0, 0)])
    b.fill(P, d1, at(11, 0), 'buy', 20030, 1, 1)
    b.order(P, '', 1, SELL, LIMIT, 1, [(at(11, 0, 5), INIT, 20060, 0), (at(11, 0, 6), WORK, 20060, 0), (at(11, 5, 1), CXL, 20060, 0)])
    d3 = b.order(P, '', 1, SELL, MARKET, 1, [(at(11, 5), FILL, 0, 0)])
    b.fill(P, d3, at(11, 5), 'sell', 20035, 1, 0)
    # E (prop): long 1; the next fill says the position was flat before it -> the first trade lost its closing fill
    e1 = b.order(P, '', 1, BUY, MARKET, 1, [(at(12, 0), FILL, 0, 0)])
    b.fill(P, e1, at(12, 0), 'buy', 20000, 1, 1)
    e2 = b.order(P, '', 1, BUY, MARKET, 1, [(at(12, 30), FILL, 0, 0)])
    b.fill(P, e2, at(12, 30), 'buy', 20010, 1, 1)
    e3 = b.order(P, '', 1, SELL, MARKET, 1, [(at(12, 40), FILL, 0, 0)])
    b.fill(P, e3, at(12, 40), 'sell', 20015, 1, 0)
    # F (prop): a limit entry placed while flat and cancelled
    b.order(P, '', 1, BUY, LIMIT, 1, [(at(13, 0), INIT, 19990, 0), (at(13, 0, 1), WORK, 19990, 0), (at(13, 5), CXL, 19990, 0)])
    cash = 100000 + (116 if with_first else 0) - 10 + 10
    b.c.execute('insert into AccountItems values(2, 7, 1, ?, ?)', (cash, ticks(at(13, 10))))
    b.c.commit(); b.c.close()


def bars_file(d):
    """NQ M5 bars for the ODR box of 18.11 (03:00-04:00 ET = 08:00-09:00 UTC): IDR 20000-20010, DR 19995-20015;
    the 04:00 bar closes 20020 above DR -> confirmed up at 04:05; then flat bars at 20020 until 05:00."""
    bars = []
    for k in range(12):
        t = int(at(8, 0).timestamp()) + 300 * k
        o, c = (20000, 20010) if k % 2 == 0 else (20010, 20000)
        bars.append([t, o, 20015 if k == 3 else 20011, 19995 if k == 7 else 19999, c])
    for k in range(12):
        t = int(at(9, 0).timestamp()) + 300 * k
        bars.append([t, 20012, 20022, 20011, 20020])
    (d / 'nq.json').write_text(json.dumps(dict(instrument='NQ', feed='TEST', switched=False,
                                                fetched_at=at(14, 0).isoformat(), bars=bars)), encoding='utf-8')


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    src, live, jr, rep = tmp / 'nt.sqlite', tmp / 'live', tmp / 'journal.sqlite3', tmp / 'report.html'
    live.mkdir()
    build(src)
    bars_file(live)
    check(T.collect(src, jr, live, rep) == 'ok', 'collect runs on the synthetic base')
    j = sqlite3.connect(jr); j.row_factory = sqlite3.Row
    tr = [dict(r) for r in j.execute('select * from trades order by trade_id')]
    by = lambda acc, t0: next(x for x in tr if x['account'] == acc and x['opened_utc'].startswith(t0))
    check(len(tr) == 7, f'7 trades from 6 scenarios with a flip (got {len(tr)})')
    check(j.execute("select count(*) from nt_accounts where name='Backtest' and kind='other'").fetchone()[0] == 1, 'Backtest is kept raw but is no kind')

    A = by('Sim101', '2026-11-18T09:30:00')
    check(A['kind'] == 'sim' and A['direction'] == 'long' and A['status'] == 'closed', 'A: sim long closed')
    check(A['fills'] == 3, 'A: the repeated fill counted once')
    check(A['max_qty'] == 2 and A['adds'] == 1, 'A: two contracts, one add')
    check(A['pnl_gross'] == 116.0 and A['fees_est'] == 4.0 and A['pnl_net_est'] == 112.0, f'A: $116 gross, $4 OneUp fees (got {A["pnl_gross"]}, {A["fees_est"]})')
    check(A['hold_sec'] == 600, 'A: held 10 minutes')
    check(A['exit_by'] == 'тейк' and A['exit_origin'] == 'panel', 'A: closed by the panel target')
    check(A['target_moves'] == 1 and A['target_moves_further'] == 1 and A['target_first_ticks'] == 76.0 and A['target_last_ticks'] == 116.0,
          'A: target moved once further, 76 -> 116 ticks from the average entry')
    check(A['entry_session'] == 'ODR' and A['entry_box_min'] == 90 and A['entry_phase'] == 'после бокса', 'A: ODR, 90 min from box start')
    check(A['entry_state'] == 'подтверждён вверх' and A['entry_sd'] == 1.0 and A['dr_high'] == 20015 and A['idr_low'] == 20000,
          f'A: confirmed up, 1.0 IDR beyond the edge (got {A["entry_state"]}, {A["entry_sd"]})')
    check(A['opened_et'] == '2026-11-18 04:30:00' and A['weekday'] == 'ср', 'A: New York clock and weekday')

    B = [x for x in tr if x['account'] == 'Sim101' and x['opened_utc'] >= '2026-11-18T10']
    check(len(B) == 2 and B[0]['direction'] == 'long' and B[1]['direction'] == 'short', 'B: the flip splits into long then short')
    check(B[0]['pnl_gross'] == -10.0 and B[1]['pnl_gross'] == 10.0, 'B: -$10 then +$10')
    check(B[1]['exit_origin'] == 'close_button', 'B: the short was closed by the Close button')

    C = by('testOUP00000000001', '2026-11-18T09:50')
    check(C['kind'] == 'prop' and C['attempt'] == 1, 'C: prop, attempt 1')
    check(C['exit_by'] == 'безубыток' and C['stop_to_breakeven'] == 1 and C['stop_moves'] == 1 and C['stop_tightened'] == 1,
          'C: stop moved to breakeven and hit there')
    check(C['stop_first_ticks'] == -40.0 and C['stop_last_ticks'] == 4.0, 'C: stop -40 ticks, then +4 ticks (entry plus fee)')
    check(C['entry_session'] == 'ODR' and C['entry_box_min'] == 110, 'C: 04:50 ET = ODR, 110 min')

    D = by('testOUP00000000001', '2026-11-18T11:00')
    check(D['exit_by'] == 'рынок' and D['exit_before_target'] == 1 and D['left_to_target_ticks'] == 100.0,
          'D: closed at market 100 ticks before a working target')

    E = [x for x in tr if x['account'] == 'testOUP00000000001' and x['opened_utc'] >= '2026-11-18T12']
    check(len(E) == 2 and E[0]['status'] == 'gap' and E[0]['pnl_gross'] is None, 'E: the trade without its closing fill is marked, no invented result')
    check(E[1]['status'] == 'closed' and E[1]['gap'] == 0 and E[1]['pnl_gross'] == 10.0, 'E: the next trade is whole (+$10)')

    acts = [dict(r) for r in j.execute('select * from actions')]
    f_act = [a for a in acts if a['price'] == 19990]
    check(f_act and all(a['trade_id'] is None and a['role'] == 'вход без исполнения' for a in f_act), 'F: unfilled entry kept as actions, no trade')
    check({a['action'] for a in f_act} == {'выставил', 'отменил'}, 'F: placed and cancelled')
    mv = [a for a in acts if a['action'] == 'передвинул']
    check(len(mv) == 2 and {(a['role'], a['toward']) for a in mv} == {('тейк', 'дальше'), ('стоп', 'ближе')}, f'moves: target further, stop closer {[(a["role"], a["toward"], a["price_from"], a["price_to"]) for a in mv]}')
    check(sum(a['action'] == 'исполнено' for a in acts) == 13, 'every fill is an action, repeats removed')

    rec = json.loads(j.execute("select value from meta where key='reconcile'").fetchone()[0])
    check(rec['Sim101']['unexplained'] == 0 and rec['Sim101']['nt_cash_change'] == 116, 'Sim101 balance = sum of its trades')
    check(rep.exists() and '/*DATA*/null' not in rep.read_text(encoding='utf-8'), 'report written with data')
    j.close()

    check(T.collect(src, jr, live, rep) == 'unchanged', 'a second run without changes does nothing')
    src.unlink()
    build(src, with_first=False)                        # NinjaTrader base reset: trade A is gone from the source
    check(T.collect(src, jr, live, rep, force=True) == 'ok', 'collect after a reset of the source')
    j = sqlite3.connect(jr)
    check(j.execute('select count(*) from trades').fetchone()[0] == 7, 'the journal keeps trade A after the reset')
    check(j.execute("select count(*) from runs").fetchone()[0] == 3, 'every run is recorded')
    j.close()

# the copy of the box hours agrees with the engine, and the New York clock agrees with pandas across DST changes
import engine_market  # noqa: E402
check(T.SESSIONS == engine_market.SESSIONS, 'box hours equal engine_market.SESSIONS')
import pandas as pd  # noqa: E402
ok = True
for s in ('2026-03-08 06:59', '2026-03-08 07:00', '2026-11-01 05:59', '2026-11-01 06:00', '2026-07-01 12:00', '2026-12-31 23:30'):
    u = pd.Timestamp(s, tz='UTC')
    ok &= T.to_et(u.to_pydatetime()) == u.tz_convert('America/New_York').tz_localize(None).to_pydatetime()
check(ok, 'New York clock matches pandas around both DST changes')

print('ALL GOOD' if not bad else f'{bad} FAILED')
sys.exit(1 if bad else 0)
