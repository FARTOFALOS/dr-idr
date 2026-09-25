"""M7DR claims on our tape: which statements of the DR/IDR author hold on NQ / ES / YM 2006-2025.

Written before counting (2026-09-25). Tape: the G3 minute spine read through lab/build_market.py (same session
instances, same clock M5 buckets, same 2026 cut). Aggregates only are written; no bars leave lab/.runtime/.
Unit: one session instance (ADR 19:30-20:30/02:00, ODR 03:00-04:00/08:30, RDR 09:30-10:30/16:00 ET).
Instruments are reported separately and never pooled (same day, same market). Epochs 2006-12 / 2013-19 / 2020-25.
Prices in ticks; coordinates in IDR widths from the confirmation-side IDR edge (0 = that edge, -1 = opposite IDR
edge, +0.5 = the first Pine STD level), shorts mirrored. IDR = M5 body extremes (Pine V1 / V1.5); the close-only
IDR the author names since 2024 is measured alongside (C0).

Claims (the author's number, source video in docs/STRATEGY.md) and how each is read:
 C0  IDR by bodies vs by closes: how often and by how much they differ (definition question, no claim).
 C1  DR true after a confirmation ~80% ("88%" in 2022); per session, instrument, epoch.
 C2  Box colour: green (close of the hour > open) -> ~70% long confirmation (2025-26; 60-65% in 2023).
 C3  Retracement back into the DR after confirmation ~80-90%, into the IDR ~66-80% (QuantX numbers are on DR-true
     sessions; both the unconditional and the DR-true rate are shown).
 C4  +0.5 STD after confirmation "almost certain", mean extension ~0.7 STD (DRlens 2023).
 C5  Session ends (last close) outside the DR in the confirmation direction ~62-70%.
 C6  Retirement setup (confirmation, return to <= -0.75 inside the IDR before the last hour, entry there, stop 2 ticks
     beyond the opposite DR) "85%": trade outcomes in R for three targets (DR edge, new session extreme, +0.5).
 C7  Session models at the RDR box close (10:30): upside / downside intact (no M5 close beyond the previous session's
     low / high: ODR vs ADR from 03:00, RDR vs ODR from 09:30), range expansion (IDR width ADR < ODR < RDR),
     ODR took both sides of the ADR, range contraction (ADR DR inside the previous day's RDR DR).
     a) the intact model predicts the RDR confirmation direction; b) a confirmation with the model holds (DR true)
     more often than against it; c) range expansion -> +1.0 reached more often; d) contraction "squeeze then explosive
     move to the other side of the previous RDR": after a pre-09:30 take of one previous-RDR extreme only, RDR confirms
     the other way / reaches the other extreme more often than on non-contraction days with the same event;
     e) counter-model ODR confirmation (downside intact, long confirmation, or mirror) extends less than an aligned one.
 C8  10:00 reversal window: session highs / lows of the RDR (09:30-16:00) fall in 09:50-10:10 more often than a
     volatility-clock arcsine baseline says.
 C9  Time split "max retracement before 12:00 -> DR true 95%, after -> 61%" (CL example; here NQ/ES/YM RDR long and
     short, confirmation 10:30-11:00). This conditions on the future; the honest counterpart is shown:
     P(DR true | DR still intact at 12:00).
 C10 Weekdays: Monday and Friday highest DR true, Wednesday lowest (2022).
 C11 Earlier confirmation holds more often (DR true by 30-minute confirmation bucket).
 C12 ADR judged until 01:00 instead of 02:00 gains ~4-7 pp DR true (less time to fail).
 C13 The author's time-and-price procedure, walk-forward by year (test years 2011-2025, parameters from all earlier
     years): key = instrument, session, direction, weekday, confirmation bucket (first / second 30 minutes after the
     box); fallback without weekday if the key has < 30 training sessions. Parameters: T = median time of the max
     retracement; L(p) = level p% of max retracements stay above; X = extension reached by 70%. Bullet 1: limit at
     the IDR edge (0), stop 2 ticks beyond min(L(50), -0.1); bullet 2 only after bullet 1 is stopped: limit at
     L(50) - 0.1, stop 2 ticks beyond min(L(70), entry - 0.1). Target X for both. Entries only until T; no trade if X
     is touched before the first fill; exit at the session end otherwise; R:R >= 3 required (reported also without).
     Two training cohorts: "author" = DR-true sessions only (as QuantX), "honest" = all confirmed sessions.
     Fills: a limit fills when price trades 1 tick through; stop at its price; within one M1 bar the adverse order
     is assumed (stop before target; a bar that fills and hits the stop is a loss). Costs 2 ticks per round trip
     (4 ticks as a stress case), subtracted once.

Decision rule (fixed now). A comparative claim (C2, C7, C8, C10, C11) is SUPPORTED when the difference has the
claimed sign in each instrument with |z| >= 3 and the same sign in all three epochs; PARTIAL when the sign holds in
all instruments but not the z / epoch condition; otherwise NOT SUPPORTED. A level claim (C1, C3-C5) is read as the
measured rate with a 95% Wilson interval and compared to the stated number (within +-5 pp = matches). C6 and C13
count as a tradable edge only if the net mean R (2 ticks) is > 0 with the 95% interval above zero in each instrument
and positive in each epoch; the author's numbers do not enter that judgement.

Run from the repository root: python -B studies/m7_claims.py        (builds a cache in lab/.runtime/ first)
"""
from __future__ import annotations

import json
import math
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "lab"))
from build_market import CLOSED_GAP_NS, SESSIONS, TICKS, load_minutes  # noqa: E402

RUNTIME = ROOT / "lab" / ".runtime"
INST = ("NQ", "ES", "YM")
SESS = ("ADR", "ODR", "RDR")
EPOCHS = (("2006-12", 2006, 2012), ("2013-19", 2013, 2019), ("2020-25", 2020, 2025))
CACHE_V = "m7-claims-1"


# ----------------------------------------------------------------------------------------------------------- tape

class Tape:
    """Global M1 and clock-M5 arrays of one instrument in absolute ET minutes (days since epoch * 1440 + minute)."""

    def __init__(self, inst):
        df = load_minutes(inst)
        tick = TICKS[inst]
        day = pd.to_datetime(df["date"].astype(str)).to_numpy().astype("datetime64[D]").astype(np.int64)
        self.inst, self.tick = inst, tick
        self.t_open = day * 1440 + df["mod"].to_numpy().astype(np.int64)      # bar open minute, ET absolute
        self.t_close = self.t_open + 1
        self.ts = df["ts"].to_numpy()
        self.o, self.h, self.l, self.c = (np.rint(df[k].to_numpy() / tick).astype(np.int64) for k in ("o", "h", "l", "c"))
        k5 = self.t_open // 5
        first = np.r_[0, np.flatnonzero(k5[1:] != k5[:-1]) + 1]
        last = np.r_[first[1:], len(k5)] - 1
        self.m5_start = k5[first] * 5
        self.m5_o = self.o[first]
        self.m5_h = np.maximum.reduceat(self.h, first)
        self.m5_l = np.minimum.reduceat(self.l, first)
        self.m5_c = self.c[last]
        self.m5_last = last

    def m1(self, a, b):
        """Row slice of M1 bars whose close minute is in (a, b]."""
        return slice(np.searchsorted(self.t_close, a, "right"), np.searchsorted(self.t_close, b, "right"))

    def m5(self, a, b):
        """Slice of M5 buckets that close in (a, b] (bucket close = start + 5)."""
        return slice(np.searchsorted(self.m5_start + 5, a, "right"), np.searchsorted(self.m5_start + 5, b, "right"))


def instances(tape):
    """One row per session instance with a complete 12-bucket window, weekend trade days skipped."""
    rows = []
    day0 = int(tape.t_open.min() // 1440) - 1
    day1 = int(tape.t_open.max() // 1440) + 1
    for name, (start, formed, end) in SESSIONS.items():
        for d in range(day0, day1):
            a, f, e = d * 1440 + start, d * 1440 + formed, d * 1440 + end
            w = tape.m5(a, f)
            if w.stop - w.start != 12 or tape.m5_start[w.start] != a:
                continue
            tday = d + (1 if name == "ADR" else 0)
            wd = int(pd.Timestamp(np.datetime64(tday, "D")).weekday())
            if wd > 4:
                continue
            wo, wh, wl, wc = tape.m5_o[w], tape.m5_h[w], tape.m5_l[w], tape.m5_c[w]
            obs = tape.m1(f, e)
            if obs.stop == obs.start:
                continue
            last_row = obs.stop - 1
            closed_early = last_row + 1 >= len(tape.ts) or tape.ts[last_row + 1] - tape.ts[last_row] >= CLOSED_GAP_NS
            complete = bool(tape.t_close[last_row] == e or closed_early)
            rows.append(dict(session=name, day=d, tday=tday, wd=wd, year=int(str(np.datetime64(tday, "D"))[:4]),
                             a=a, f=f, e=e, dr_hi=int(wh.max()), dr_lo=int(wl.min()),
                             idr_hi=int(np.maximum(wo, wc).max()), idr_lo=int(np.minimum(wo, wc).min()),
                             idrc_hi=int(wc.max()), idrc_lo=int(wc.min()), open=int(wo[0]), close=int(wc[-1]),
                             complete=complete))
    S = pd.DataFrame(rows)
    S["box"] = np.sign(S.close - S.open).astype(int)
    S["w"] = S.idr_hi - S.idr_lo
    S = S[S.w > 0].reset_index(drop=True)
    # confirmation and outcomes
    out = {k: [] for k in ("dir", "conf", "fail", "dr_true", "retr", "retr_t", "ext", "ext_t", "into_dr", "into_idr",
                           "last_close_out", "last3_out", "fail_0100")}
    for r in S.itertuples():
        m = tape.m5(r.f, r.e)
        cl = tape.m5_c[m]; st = tape.m5_start[m]
        up = np.flatnonzero(cl > r.dr_hi); dn = np.flatnonzero(cl < r.dr_lo)
        if not len(up) and not len(dn):
            for k in out: out[k].append(np.nan if k != "dir" else 0)
            continue
        side = 1 if (len(up) and (not len(dn) or up[0] < dn[0])) else -1
        k = up[0] if side == 1 else dn[0]
        conf = int(st[k] + 5)
        later = np.arange(len(cl)) > k
        fail_i = np.flatnonzero(later & ((cl < r.dr_lo) if side == 1 else (cl > r.dr_hi)))
        fail = int(st[fail_i[0]] + 5) if len(fail_i) else np.nan
        dr_true = 0.0 if len(fail_i) else (1.0 if r.complete else np.nan)
        edge = r.idr_hi if side == 1 else r.idr_lo
        after = tape.m1(conf, r.e)
        fromc = tape.m1(conf - 5, r.e)
        if after.stop == after.start:
            lows = np.array([edge]); highs = np.array([edge]); tt = np.array([conf])
        else:
            lows = tape.l[after] if side == 1 else tape.h[after]
            tt = tape.t_close[after]
        highs_c = tape.h[fromc] if side == 1 else tape.l[fromc]
        tt_c = tape.t_close[fromc]
        rc = side * (lows - edge) / r.w
        ec = side * (highs_c - edge) / r.w
        ir, ie = int(np.argmin(rc)), int(np.argmax(ec))
        dr_edge = r.dr_hi if side == 1 else r.dr_lo
        into_dr = float(np.any(side * (lows - dr_edge) <= 0)) if after.stop > after.start else 0.0
        into_idr = float(np.any(side * (lows - edge) <= 0)) if after.stop > after.start else 0.0
        lc = tape.c[after.stop - 1] if after.stop > after.start else r.close
        last3 = cl[-3:]
        out["dir"].append(side); out["conf"].append(conf); out["fail"].append(fail); out["dr_true"].append(dr_true)
        out["retr"].append(float(rc[ir])); out["retr_t"].append(int(tt[ir])); out["ext"].append(float(ec[ie]))
        out["ext_t"].append(int(tt_c[ie])); out["into_dr"].append(into_dr); out["into_idr"].append(into_idr)
        out["last_close_out"].append(float(side * (lc - dr_edge) > 0))
        out["last3_out"].append(float(np.any(side * (last3 - dr_edge) > 0)))
        if r.session == "ADR":
            f01 = np.flatnonzero(later & (st + 5 <= r.day * 1440 + 1500) & ((cl < r.dr_lo) if side == 1 else (cl > r.dr_hi)))
            out["fail_0100"].append(0.0 if len(f01) else 1.0)
        else:
            out["fail_0100"].append(np.nan)
    for k, v in out.items():
        S[k] = v
    S["dir"] = S["dir"].astype(int)
    return S


def load(inst):
    p = RUNTIME / f"study_m7_{inst.lower()}.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            blob = pickle.load(fh)
        if blob.get("v") == CACHE_V:
            return blob["tape"], blob["S"]
    tape = Tape(inst)
    S = instances(tape)
    with open(p, "wb") as fh:
        pickle.dump(dict(v=CACHE_V, tape=tape, S=S), fh, protocol=4)
    return tape, S


# ----------------------------------------------------------------------------------------------------------- stats

def wilson(k, n):
    if not n: return None
    z = 1.96; p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(100 * (c - h), 1), round(100 * (c + h), 1)]


def rate(mask):
    m = pd.Series(mask).dropna()
    k, n = int(m.sum()), int(len(m))
    return dict(pct=round(100 * k / n, 1) if n else None, k=k, n=n, ci=wilson(k, n))


def ztest(k1, n1, k2, n2):
    if not n1 or not n2: return None
    p = (k1 + k2) / (n1 + n2); se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return round((k1 / n1 - k2 / n2) / se, 2) if se > 0 else None


def compare(a, b):
    """Two rates (boolean series, NaN dropped): difference in pp and z."""
    a, b = pd.Series(a).dropna(), pd.Series(b).dropna()
    ka, na, kb, nb = int(a.sum()), len(a), int(b.sum()), len(b)
    d = round(100 * (ka / na - kb / nb), 1) if na and nb else None
    return dict(a=rate(a), b=rate(b), diff_pp=d, z=ztest(ka, na, kb, nb))


def by_epoch(S, fn):
    return {name: fn(S[(S.year >= y0) & (S.year <= y1)]) for name, y0, y1 in EPOCHS}


def verdict(per_inst, sign=+1):
    """per_inst: {inst: {'all': compare(), epochs...}} -> SUPPORTED / PARTIAL / NOT SUPPORTED."""
    signs_ok = all((v["all"]["diff_pp"] or 0) * sign > 0 for v in per_inst.values())
    z_ok = all((v["all"]["z"] or 0) * sign >= 3 for v in per_inst.values())
    ep_ok = all(all((v[e]["diff_pp"] or 0) * sign > 0 for e, _, _ in EPOCHS) for v in per_inst.values())
    if signs_ok and z_ok and ep_ok: return "SUPPORTED"
    if signs_ok: return "PARTIAL"
    return "NOT SUPPORTED"


def cmp_epochs(S, cond_a, cond_b, outcome):
    res = {"all": compare(S.loc[cond_a(S), outcome], S.loc[cond_b(S), outcome])}
    for name, y0, y1 in EPOCHS:
        E = S[(S.year >= y0) & (S.year <= y1)]
        res[name] = compare(E.loc[cond_a(E), outcome], E.loc[cond_b(E), outcome])
    return res


# ----------------------------------------------------------------------------------------------------------- claims

def c0(S):
    m = S.copy()
    diff_hi = (m.idr_hi - m.idrc_hi) / m.w
    diff_lo = (m.idrc_lo - m.idr_lo) / m.w
    any_diff = (m.idr_hi != m.idrc_hi) | (m.idr_lo != m.idrc_lo)
    wc = (m.idrc_hi - m.idrc_lo).clip(lower=1)
    return dict(share_sessions_differ_pct=round(100 * any_diff.mean(), 1),
                median_edge_shift_when_differs_idr=round(float(pd.concat([diff_hi[diff_hi > 0], diff_lo[diff_lo > 0]]).median()), 3),
                median_width_ratio_close_over_body=round(float((wc / m.w).median()), 3))


def c1(S):
    C = S[S.dir != 0]
    return {s: dict(all=rate(C[C.session == s].dr_true), **by_epoch(C[C.session == s], lambda E: rate(E.dr_true)))
            for s in SESS}


def c2(S):
    res = {}
    for s in SESS:
        X = S[(S.session == s) & (S.box != 0) & ((S.dir != 0) | S.complete)]
        same = (X.dir == X.box).astype(float)
        conf = X[X.dir != 0]
        res[s] = dict(same_dir_all_sessions=rate(same), same_dir_confirmed=rate((conf.dir == conf.box).astype(float)),
                      green_long=rate((X[X.box == 1].dir == 1).astype(float)), red_short=rate((X[X.box == -1].dir == -1).astype(float)),
                      epochs=by_epoch(X, lambda E: rate((E.dir == E.box).astype(float))))
    return res


def c3_c4_c5(S):
    res = {}
    for s in SESS:
        C = S[(S.session == s) & (S.dir != 0) & S.complete]
        T = C[C.dr_true == 1]
        res[s] = dict(into_dr_all=rate(C.into_dr), into_idr_all=rate(C.into_idr),
                      into_dr_true=rate(T.into_dr), into_idr_true=rate(T.into_idr),
                      ext_ge_05_all=rate((C.ext >= 0.5).astype(float)), ext_ge_10_all=rate((C.ext >= 1.0).astype(float)),
                      ext_ge_05_true=rate((T.ext >= 0.5).astype(float)), ext_median_all=round(float(C.ext.median()), 2),
                      ext_mean_all=round(float(C.ext.mean()), 2), ext_median_true=round(float(T.ext.median()), 2),
                      retr_median_all=round(float(C.retr.median()), 2), retr_median_true=round(float(T.retr.median()), 2),
                      last_close_outside=rate(C.last_close_out), last3_close_outside=rate(C.last3_out))
    return res


def c10_c11(S):
    res = {}
    for s in SESS:
        C = S[(S.session == s) & (S.dir != 0)]
        f = SESSIONS[s][1]
        wd = {int(k): rate(g.dr_true) for k, g in C.groupby("wd")}
        rel = C.conf - (C.day * 1440 + f)
        b = (rel // 30).clip(upper=8)
        buckets = {f"+{int(k) * 30}..{int(k) * 30 + 30}m" if k < 8 else "+240m..": rate(g.dr_true) for k, g in C.groupby(b)}
        res[s] = dict(weekday=wd, conf_bucket=buckets)
    return res


def c12(S):
    A = S[(S.session == "ADR") & (S.dir != 0) & (S.conf <= S.day * 1440 + 1500)]
    return dict(until_0200=rate(A.dr_true), until_0100=rate(A.fail_0100))


def c9(S, tape):
    res = {}
    R = S[(S.session == "RDR") & (S.dir != 0) & S.complete]
    rel = R.conf - (R.day * 1440 + 630)
    R = R[(rel > 0) & (rel <= 30)]
    noon = R.day * 1440 + 720
    early = R.retr_t <= noon
    intact_noon = ~(R.fail <= noon)
    res["look_ahead_split"] = dict(max_retr_before_12=rate(R.loc[early, "dr_true"]), max_retr_after_12=rate(R.loc[~early, "dr_true"]),
                                   share_max_retr_before_12=round(100 * early.mean(), 1))
    res["honest_at_12"] = dict(all_confirmed=rate(R.dr_true), dr_intact_at_12=rate(R.loc[intact_noon, "dr_true"]))
    # Friday long only, the author's cut
    F = R[(R.wd == 4) & (R.dir == 1)]
    fe = F.retr_t <= F.day * 1440 + 720
    res["friday_long"] = dict(n=len(F), before_12=rate(F.loc[fe, "dr_true"]), after_12=rate(F.loc[~fe, "dr_true"]),
                              all=rate(F.dr_true), intact_at_12=rate(F.loc[~(F.fail <= F.day * 1440 + 720), "dr_true"]))
    return res


def c8(S, tape):
    """Time of the RDR session high and low (09:30-16:00) vs a volatility-clock arcsine baseline."""
    R = S[(S.session == "RDR") & S.complete]
    mins = np.arange(570, 960)
    var = np.zeros(len(mins)); cnt = np.zeros(len(mins))
    hi_t, lo_t, yrs = [], [], []
    for r in R.itertuples():
        sl = tape.m1(r.a, r.e)
        if sl.stop - sl.start < 300: continue
        yrs.append(r.year)
        t = tape.t_open[sl] - r.day * 1440
        c = tape.c[sl].astype(float)
        hi_t.append(int(t[np.argmax(tape.h[sl])])); lo_t.append(int(t[np.argmin(tape.l[sl])]))
        dr = np.diff(np.log(np.maximum(c, 1)))
        idx = t[1:] - 570
        ok = (idx >= 0) & (idx < len(mins))
        np.add.at(var, idx[ok], dr[ok] ** 2); np.add.at(cnt, idx[ok], 1)
    v = var / np.maximum(cnt, 1)
    F = np.r_[0, np.cumsum(v)] / v.sum()                 # F[i] = variance share before minute 570+i

    def expected(a, b):
        fa, fb = F[a - 570], F[b - 570]
        return (2 / math.pi) * (math.asin(math.sqrt(fb)) - math.asin(math.sqrt(fa)))

    res = dict(n_days=len(hi_t), bins={})
    ext = np.array(hi_t + lo_t)
    for a in range(570, 700, 10):
        b = a + 10
        obs = float(np.mean((ext >= a) & (ext < b)))
        res["bins"][f"{a // 60:02d}:{a % 60:02d}"] = dict(observed_pct=round(100 * obs, 2), baseline_pct=round(100 * expected(a, b), 2))
    obs = float(np.mean((ext >= 590) & (ext < 610))); exp = expected(590, 610)
    n = len(ext)
    z = (obs - exp) / math.sqrt(exp * (1 - exp) / n)
    res["window_0950_1010"] = dict(observed_pct=round(100 * obs, 2), baseline_pct=round(100 * exp, 2), z=round(z, 2))
    for name, y0, y1 in EPOCHS:
        ya = np.array(yrs)
        m = (ya >= y0) & (ya <= y1)
        e2 = np.r_[np.array(hi_t)[m], np.array(lo_t)[m]]
        res[name] = round(100 * float(np.mean((e2 >= 590) & (e2 < 610))), 2)
    return res


# ------------------------------------------------------------------------------------------------ C7 session models

def day_table(S, tape):
    """One row per trade day with ADR, ODR, RDR of that day and the previous trade day's RDR."""
    piv = {s: S[S.session == s].set_index("tday") for s in SESS}
    days = sorted(set(piv["ADR"].index) & set(piv["ODR"].index) & set(piv["RDR"].index))
    rdr_days = sorted(piv["RDR"].index)
    prev = {d: p for p, d in zip(rdr_days[:-1], rdr_days[1:])}
    rows = []
    for d in days:
        if d not in prev: continue
        A, O, R, P = piv["ADR"].loc[d], piv["ODR"].loc[d], piv["RDR"].loc[d], piv["RDR"].loc[prev[d]]
        if isinstance(A, pd.DataFrame) or isinstance(O, pd.DataFrame) or isinstance(R, pd.DataFrame): continue
        t0300, t0930, t1030 = d * 1440 + 180, d * 1440 + 570, d * 1440 + 630
        m_o = tape.m5(t0300, t1030); m_r = tape.m5(t0930, t1030)
        up = bool(tape.m5_c[m_o].min() >= A.dr_lo and tape.m5_c[m_r].min() >= O.dr_lo)
        dn = bool(tape.m5_c[m_o].max() <= A.dr_hi and tape.m5_c[m_r].max() <= O.dr_hi)
        # model at the ODR box close (04:00) for the counter-model test
        m4 = tape.m5(t0300, d * 1440 + 240)
        up4 = bool(tape.m5_c[m4].min() >= A.dr_lo); dn4 = bool(tape.m5_c[m4].max() <= A.dr_hi)
        o_sl = tape.m1(t0300, t0930)
        odr_both = bool(tape.h[o_sl].max() > A.dr_hi and tape.l[o_sl].min() < A.dr_lo) if o_sl.stop > o_sl.start else False
        rexp = bool(A.w < O.w < R.w)
        contr = bool(A.dr_hi <= P.dr_hi and A.dr_lo >= P.dr_lo)
        pre = tape.m1(P.e, t0930)                                  # previous RDR end -> today 09:30
        took_hi = bool(tape.h[pre].max() > P.dr_hi) if pre.stop > pre.start else False
        took_lo = bool(tape.l[pre].min() < P.dr_lo) if pre.stop > pre.start else False
        rs = tape.m1(t0930, d * 1440 + 960)
        r_hi = tape.h[rs].max() if rs.stop > rs.start else np.nan
        r_lo = tape.l[rs].min() if rs.stop > rs.start else np.nan
        rows.append(dict(tday=d, year=int(R.year), up=up, dn=dn, up4=up4, dn4=dn4, odr_both=odr_both, rexp=rexp, contr=contr,
                         took_hi=took_hi, took_lo=took_lo, r_dir=int(R.dir), r_true=R.dr_true, r_ext=R.ext, r_complete=bool(R.complete),
                         o_dir=int(O.dir), o_true=O.dr_true, o_ext=O.ext, o_complete=bool(O.complete),
                         r_reach_prev_hi=float(r_hi > P.dr_hi) if R.complete else np.nan,
                         r_reach_prev_lo=float(r_lo < P.dr_lo) if R.complete else np.nan))
    return pd.DataFrame(rows)


def c7(D):
    res = {}
    only_up = D.up & ~D.dn; only_dn = D.dn & ~D.up
    X = D[D.r_dir != 0].copy()
    X["long"] = (X.r_dir == 1).astype(float)
    res["a_model_predicts_direction"] = dict(
        share_only_up=round(100 * only_up.mean(), 1), share_only_dn=round(100 * only_dn.mean(), 1),
        share_both=round(100 * (D.up & D.dn).mean(), 1), share_neither=round(100 * (~D.up & ~D.dn).mean(), 1),
        cmp=cmp_epochs(X, lambda E: E.up & ~E.dn, lambda E: E.dn & ~E.up, "long"))
    X["with_model"] = ((X.up & ~X.dn & (X.r_dir == 1)) | (X.dn & ~X.up & (X.r_dir == -1)))
    X["against_model"] = ((X.up & ~X.dn & (X.r_dir == -1)) | (X.dn & ~X.up & (X.r_dir == 1)))
    res["b_with_vs_against_dr_true"] = cmp_epochs(X, lambda E: E.with_model, lambda E: E.against_model, "r_true")
    X["ext1"] = np.where(X.r_complete | (X.r_ext >= 1), (X.r_ext >= 1).astype(float), np.nan)
    res["c_range_expansion_ext1"] = dict(share_rexp=round(100 * D.rexp.mean(), 1),
                                         cmp=cmp_epochs(X, lambda E: E.rexp, lambda E: ~E.rexp, "ext1"))
    # d) contraction: only the previous RDR high was taken before 09:30 -> RDR short confirmation / reach prev low
    Y = D.copy()
    Y["squeeze_up"] = Y.took_hi & ~Y.took_lo
    Y["squeeze_dn"] = Y.took_lo & ~Y.took_hi
    Y["opp_conf"] = np.where(Y.r_dir == 0, 0.0, np.where(Y.squeeze_up, (Y.r_dir == -1).astype(float), (Y.r_dir == 1).astype(float)))
    Y["opp_reach"] = np.where(Y.squeeze_up, Y.r_reach_prev_lo, Y.r_reach_prev_hi)
    Z = Y[Y.squeeze_up | Y.squeeze_dn]
    res["d_contraction"] = dict(share_contraction=round(100 * D.contr.mean(), 1),
                                n_squeeze_events=int(len(Z)), contraction_share_of_events=round(100 * Z.contr.mean(), 1),
                                opposite_confirmation=cmp_epochs(Z, lambda E: E.contr, lambda E: ~E.contr, "opp_conf"),
                                reach_other_prev_rdr_extreme=cmp_epochs(Z, lambda E: E.contr, lambda E: ~E.contr, "opp_reach"))
    # e) counter-model ODR confirmation extends less (ext >= 1.0)
    W = D[(D.o_dir != 0)].copy()
    W["aligned"] = (W.up4 & ~W.dn4 & (W.o_dir == 1)) | (W.dn4 & ~W.up4 & (W.o_dir == -1))
    W["counter"] = (W.dn4 & ~W.up4 & (W.o_dir == 1)) | (W.up4 & ~W.dn4 & (W.o_dir == -1))
    W["ext1"] = np.where(W.o_complete | (W.o_ext >= 1), (W.o_ext >= 1).astype(float), np.nan)
    res["e_odr_counter_vs_aligned_ext1"] = cmp_epochs(W, lambda E: E.aligned, lambda E: E.counter, "ext1")
    res["e_odr_counter_vs_aligned_dr_true"] = cmp_epochs(W, lambda E: E.aligned, lambda E: E.counter, "o_true")
    res["e_median_ext"] = dict(aligned=round(float(W.loc[W.aligned, "o_ext"].median()), 2),
                               counter=round(float(W.loc[W.counter, "o_ext"].median()), 2))
    # f) ODR took both ADR sides -> RDR DR true / both sides of RDR
    res["f_odr_both_sides_rdr_true"] = cmp_epochs(X, lambda E: ~E.odr_both, lambda E: E.odr_both, "r_true")
    return res


# ------------------------------------------------------------------------------------------------ trade simulation

def simulate(tape, r, side, entry, stop, target, t_from, t_last_entry, t_end, preempt=True):
    """One limit order. Returns None (no fill) or dict(R, exit, fill_t). Levels in ticks. Adverse intrabar order.
    preempt=True: no trade if the target is touched before the fill (the author's S3 rule)."""
    sl = tape.m1(t_from, t_end)
    if sl.stop == sl.start: return None
    H, L, T = tape.h[sl], tape.l[sl], tape.t_close[sl]
    fav = H if side == 1 else -L
    adv = L if side == 1 else -H
    e, s, x = side * entry, side * stop, side * target
    fill = np.flatnonzero((adv <= e - 1) & (T <= t_last_entry))
    if not len(fill): return None
    i = fill[0]
    if preempt and np.any(fav[:i] >= x): return None           # target touched before the fill -> no trade
    risk = e - s
    if adv[i] <= s: return dict(R=-1.0, exit="stop", fill_t=int(T[i]), risk=risk)
    rest_adv, rest_fav = adv[i + 1:], fav[i + 1:]
    hit_s = np.flatnonzero(rest_adv <= s); hit_x = np.flatnonzero(rest_fav >= x)
    js = hit_s[0] if len(hit_s) else 10**9; jx = hit_x[0] if len(hit_x) else 10**9
    if js == 10**9 and jx == 10**9:
        last = (tape.c[sl][-1]) * side
        return dict(R=(last - e) / risk, exit="time", fill_t=int(T[i]), risk=risk)
    if js <= jx: return dict(R=-1.0, exit="stop", fill_t=int(T[i]), risk=risk)
    return dict(R=(x - e) / risk, exit="target", fill_t=int(T[i]), risk=risk)


def summarize(trades, cost_ticks=(2, 4)):
    if not trades: return dict(n=0)
    R = np.array([t["R"] for t in trades]); risk = np.array([t["risk"] for t in trades], float)
    out = dict(n=len(R), win_pct=round(100 * float(np.mean([t["exit"] == "target" for t in trades])), 1),
               stop_pct=round(100 * float(np.mean([t["exit"] == "stop" for t in trades])), 1),
               gross_R=round(float(R.mean()), 3))
    for c in cost_ticks:
        net = R - c / risk
        se = float(net.std(ddof=1) / math.sqrt(len(net))) if len(net) > 1 else float("nan")
        out[f"net{c}_R"] = round(float(net.mean()), 3)
        out[f"net{c}_ci"] = [round(float(net.mean()) - 1.96 * se, 3), round(float(net.mean()) + 1.96 * se, 3)]
    out["median_risk_ticks"] = float(np.median(risk))
    return out


def c6(S, tape):
    res = {}
    cut = {"RDR": 900, "ODR": 450, "ADR": 1500}
    for s in SESS:
        C = S[(S.session == s) & (S.dir != 0)]
        trades = {k: [] for k in ("dr_edge", "new_extreme", "plus05")}
        entered_true = []
        for r in C.itertuples():
            side = r.dir
            edge = r.idr_hi if side == 1 else r.idr_lo
            entry = int(round(edge - side * 0.75 * r.w))
            stop = (r.dr_lo - 2) if side == 1 else (r.dr_hi + 2)
            if side * (entry - stop) < 2: continue
            t_last = r.day * 1440 + cut[s]
            seg = tape.m1(r.conf, r.e)
            if seg.stop == seg.start: continue
            adv = tape.l[seg] if side == 1 else -tape.h[seg]
            fi = np.flatnonzero((adv <= side * entry - 1) & (tape.t_close[seg] <= t_last))
            if not len(fi): continue
            ext_so_far = (tape.h[seg][:fi[0]].max() if side == 1 else tape.l[seg][:fi[0]].min()) if fi[0] > 0 else (r.dr_hi if side == 1 else r.dr_lo)
            targets = dict(dr_edge=r.dr_hi if side == 1 else r.dr_lo,
                           new_extreme=int(ext_so_far + side),
                           plus05=int(round(edge + side * 0.5 * r.w)))
            for k, tgt in targets.items():
                if side * (tgt - entry) <= 0: continue
                t = simulate(tape, r, side, entry, stop, tgt, r.conf, t_last, r.e, preempt=False)
                if t: t["year"] = r.year; trades[k].append(t)
            entered_true.append(r.dr_true)
        res[s] = dict(entered=len(entered_true), dr_true_when_entered=rate(pd.Series(entered_true)),
                      **{k: dict(all=summarize(v), **{n: summarize([t for t in v if y0 <= t["year"] <= y1]) for n, y0, y1 in EPOCHS})
                         for k, v in trades.items()})
    return res


def c13(S, tape):
    """Walk-forward time-and-price procedure (see the module docstring)."""
    res = {}
    for s in SESS:
        f = SESSIONS[s][1]
        C = S[(S.session == s) & (S.dir != 0)].copy()
        C["rel"] = C.conf - (C.day * 1440 + f)
        C = C[(C.rel > 0) & (C.rel <= 60)]
        C["bucket"] = (C.rel > 30).astype(int)
        C["rt_clock"] = C.retr_t - C.day * 1440
        for cohort in ("author", "honest"):
            for rr_filter in (True, False):
                trades, used = [], dict(key=0, fallback=0, skipped=0)
                for Y in range(2011, 2026):
                    train = C[(C.year < Y) & C.complete]
                    if cohort == "author": train = train[train.dr_true == 1]
                    test = C[C.year == Y]
                    params = {}
                    for r in test.itertuples():
                        key = (r.dir, r.wd, r.bucket)
                        if key not in params:
                            g = train[(train.dir == r.dir) & (train.wd == r.wd) & (train.bucket == r.bucket)]
                            kind = "key"
                            if len(g) < 30:
                                g = train[(train.dir == r.dir) & (train.bucket == r.bucket)]; kind = "fallback"
                            if len(g) < 30: params[key] = None; continue
                            params[key] = dict(kind=kind, T=float(g.rt_clock.median()), L50=float(g.retr.quantile(0.5)),
                                               L70=float(g.retr.quantile(0.3)), X=float(g.ext.quantile(0.3)))
                        p = params[key]
                        if p is None: used["skipped"] += 1; continue
                        used[p["kind"]] += 1
                        side = r.dir
                        edge = r.idr_hi if side == 1 else r.idr_lo
                        lvl = lambda c: int(round(edge + side * c * r.w))  # noqa: E731
                        tgt = lvl(p["X"])
                        e1 = lvl(0.0); s1 = lvl(min(p["L50"], -0.1)) - 2 * side
                        e2c = min(p["L50"], -0.1) - 0.1
                        e2 = lvl(e2c); s2 = lvl(min(p["L70"], e2c - 0.1)) - 2 * side
                        t_last = r.day * 1440 + int(p["T"])
                        if t_last <= r.conf: continue
                        if rr_filter and side * (tgt - e1) < 3 * side * (e1 - s1): continue
                        t1 = simulate(tape, r, side, e1, s1, tgt, r.conf, t_last, r.e)
                        if t1 is None: continue
                        t1.update(year=Y, bullet=1); trades.append(t1)
                        if t1["exit"] == "stop":
                            if rr_filter and side * (tgt - e2) < 3 * side * (e2 - s2): continue
                            t2 = simulate(tape, r, side, e2, s2, tgt, t1["fill_t"], t_last, r.e, preempt=False)
                            if t2: t2.update(year=Y, bullet=2); trades.append(t2)
                name = f"{cohort}{'_rr3' if rr_filter else ''}"
                res.setdefault(s, {})[name] = dict(params_used=used, all=summarize(trades),
                                                   bullet1=summarize([t for t in trades if t["bullet"] == 1]),
                                                   bullet2=summarize([t for t in trades if t["bullet"] == 2]),
                                                   **{n: summarize([t for t in trades if y0 <= t["year"] <= y1]) for n, y0, y1 in
                                                      (("2011-15", 2011, 2015), ("2016-20", 2016, 2020), ("2021-25", 2021, 2025))},
                                                   by_year={int(y): summarize([t for t in trades if t["year"] == y]).get("net2_R") for y in range(2011, 2026)})
    return res


# ----------------------------------------------------------------------------------------------------------- main

def main():
    only = [a.upper() for a in sys.argv[1:]] or list(INST)
    out = dict(version=CACHE_V, tape="G3 minute spine NQ/ES/YM 2006-2025 ET (2026 hidden)", instruments={})
    for inst in only:
        tape, S = load(inst)
        print(inst, "instances", len(S), flush=True)
        D = day_table(S, tape)
        R = dict(C0=c0(S), C1=c1(S), C2=c2(S), C3_C4_C5=c3_c4_c5(S), C10_C11=c10_c11(S), C12=c12(S), C9=c9(S, tape),
                 C8=c8(S, tape), C7=c7(D))
        print(inst, "descriptive done", flush=True)
        R["C6"] = c6(S, tape)
        print(inst, "C6 done", flush=True)
        R["C13"] = c13(S, tape)
        print(inst, "C13 done", flush=True)
        out["instruments"][inst] = R
    # verdicts across instruments for comparative claims
    if len(out["instruments"]) == len(INST):
        I = out["instruments"]
        out["verdicts"] = dict(
            C7a_model_direction=verdict({i: I[i]["C7"]["a_model_predicts_direction"]["cmp"] for i in INST}),
            C7b_with_model_dr_true=verdict({i: I[i]["C7"]["b_with_vs_against_dr_true"] for i in INST}),
            C7c_range_expansion_ext1=verdict({i: I[i]["C7"]["c_range_expansion_ext1"]["cmp"] for i in INST}),
            C7d_contraction_opposite_conf=verdict({i: I[i]["C7"]["d_contraction"]["opposite_confirmation"] for i in INST}),
            C7d_contraction_reach_other=verdict({i: I[i]["C7"]["d_contraction"]["reach_other_prev_rdr_extreme"] for i in INST}),
            C7e_counter_model_ext1=verdict({i: I[i]["C7"]["e_odr_counter_vs_aligned_ext1"] for i in INST}),
            C7f_odr_both_sides=verdict({i: I[i]["C7"]["f_odr_both_sides_rdr_true"] for i in INST}))
    name = "m7_claims" if len(only) == len(INST) else f"m7_claims_{'_'.join(only).lower()}"
    (HERE / f"{name}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print("written", name, flush=True)


if __name__ == "__main__":
    main()
