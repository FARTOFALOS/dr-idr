"""Lens 8, parts C and D: the frozen contract (dogovor.md, version 1.1) on the tape. NQ RDR only, no optimisation, no trading claim.

Test states fixed before counting: the ones the audit and lens 4 already used (studies/audit_2026_09_29/place_arrivals.py,
studies/lens4_2026_09_30/*): every complete NQ RDR session of 2016-2025, every 15 minutes 10:45-15:45 (M5 closes),
confirmed and DR not broken by then; similar sessions = the screen's rules (lab/scene21.py, conf mode) from the years
before the test year (lens4 lenscommon.Screen, checked identical to replay_core and scene21). For 8.2 the same states
two and four minutes after the M5 close (lens 4, c5_minute_alignment.py).

Areas (DR Lab places, design 22 zoneDefs, conf mode): A «от центра» [-0.75; -0.25], B «retirement» at or below -0.75;
for 8.1 also the two continuation places ahead of the price (next half-step s1 not closer than 0.25, and s2 = s1+0.5).
L = +1.0. The trader card (part D) is fixed before counting: t = 11:00, today's price in [0; +0.5), today's L not reached.

Only aggregates are printed (tape_diagnostic.log). Per-state records stay in the git-ignored lab/.runtime/lens8_states.json.gz.
python -B tape_diagnostic.py
"""
from __future__ import annotations

import gzip
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lens4_2026_09_30"))
from lenscommon import RT, TEST_YEARS, Screen, dense, slot  # noqa: E402
from c5_minute_alignment import conf_coords, minute_arrays  # noqa: E402
from build_market import load_minutes  # noqa: E402  (c5 put lab/ on the path)
from contract import classify  # noqa: E402

INST, SESS = "NQ", "RDR"
L = 1.0
AREAS = {"A": (-0.75, -0.25), "B": (-np.inf, -0.75)}
BIG = 10 ** 6
CARD = dict(t=660, u_lo=0.0, u_hi=0.5)
OUT = RT / "lens8_states.json.gz"


def next_true(C):
    """out[:, s] = the first slot k > s where C is True (BIG if none)."""
    n, S_ = C.shape
    idx = np.where(C, np.arange(S_)[None, :], BIG)
    m = np.minimum.accumulate(idx[:, ::-1], axis=1)[:, ::-1]
    out = np.full((n, S_), BIG, dtype=np.int64)
    out[:, :-1] = m[:, 1:]
    return out


class Tape:
    def __init__(self):
        d = self.d = dense(INST, SESS)
        self.Sc = Screen(d)
        self.up, self.dn, self.X = self.Sc.up, self.Sc.dn, self.Sc.X
        n, NS = self.X.shape
        self.NS, self.start, self.end = NS, d["start"], d["end"]
        side = d["side"].astype(float)
        w = d["idrh"] - d["idrl"]; w = np.where(w > 0, w, np.nan)
        e = np.where(side == 1, d["idrh"], d["idrl"])
        opp = np.where(side == 1, d["drl"], d["drh"])
        self.ou = side * (opp - e) / w
        self.O = side[:, None] * (d["O"] - e[:, None]) / w[:, None]
        valid = ~np.isnan(self.X)
        cols = np.arange(NS)
        self.last = np.where(valid.any(1), NS - 1 - np.argmax(valid[:, ::-1], axis=1), -1)
        gap = ~valid & (cols[None, :] <= self.last[:, None])
        with np.errstate(invalid="ignore"):
            self.nL = next_true(self.up >= L)
            self.nI = next_true(self.X < self.ou[:, None])
            self.nK = {k: next_true(self.dn <= hi) for k, (lo, hi) in AREAS.items()}
            self.nKs = {k: next_true(self.dn < hi) for k, (lo, hi) in AREAS.items()}
        self.nG = next_true(gap)
        self.RM = np.maximum.accumulate(np.where(np.isnan(self.up), -np.inf, self.up), axis=1)
        t0 = time.time()
        df = load_minutes(INST)
        Hm, Lm, Cm = minute_arrays(df, d)
        del df
        self.upm, self.dnm, self.Xm = conf_coords(d, Hm, Lm, Cm)
        print(f"minute bars loaded {time.time() - t0:.0f}s", flush=True)
        self.ties = dict(n=0, K=0, L=0, same=0, none=0)

    # ---------- the contract, vectorised ----------
    def tie_order(self, j, tau, hi):
        c = np.arange(5 * tau, 5 * tau + 5)
        up, dn = self.upm[j, c], self.dnm[j, c]
        if np.isnan(up).any() or np.isnan(dn).any(): return None, "none"      # a missing minute may hide the order
        kK = np.flatnonzero(dn <= hi); kL = np.flatnonzero(up >= L)
        if not len(kK) or not len(kL): return None, "none"
        if kK[0] == kL[0]: return None, "same"
        return ("K", "K") if kK[0] < kL[0] else ("L", "L")

    def evaluate(self, js, s, key, count=True):
        """Codes per similar session: status 0 before / 1 inside / 2 beyond / 3 unknown; new, adm 1 / 0 / -1 unknown;
        outcome 1 success / 2 invalidated / 3 neither / -1 unknown / 0 no admissible arrival; eligible; tie; tau."""
        lo, hi = AREAS[key]
        k = len(js)
        x = self.X[js, s]
        ok = ~np.isnan(x)
        st = np.full(k, 3)
        st[ok & (x > hi)] = 0
        st[ok & (x <= hi) & (x >= lo)] = 1
        st[ok & (x < lo)] = 2
        tau, g = self.nK[key][js, s], self.nG[js, s]
        hit = tau < BIG
        new = np.full(k, -1)
        new[(st == 1) | (st == 2)] = 0
        b = st == 0
        new[b & hit] = 1
        new[((st == 0) | (st == 3)) & ~hit & (g >= BIG)] = 0          # no touch after t: no arrival whatever the status
        el = self.RM[js, s] < L
        kL1, kI1 = self.nL[js, s], self.nI[js, s]
        lim = np.minimum(tau, g)
        adm = np.full(k, -1)
        adm[new == 0] = 0
        m = new == 1
        no = m & ((kL1 < lim) | (kI1 < lim))
        adm[no] = 0
        rest = m & ~no
        gb = g < tau
        tie = rest & ~gb & (kL1 == tau)
        adm[rest & ~gb & ~tie] = 1
        tieK = np.zeros(k, bool)
        for q in np.flatnonzero(tie & el):
            o, why = self.tie_order(js[q], tau[q], hi)
            if count: self.ties["n"] += 1; self.ties[why] += 1
            if o == "K": adm[q] = 1; tieK[q] = True
            elif o == "L": adm[q] = 0
        a = (adm == 1) & el
        kLa = np.where(tieK, tau, kL1)
        gA = self.nG[js, np.minimum(tau, self.NS - 1)]
        dec = np.minimum(kLa, kI1)
        unk = a & (gA < dec)
        succ = a & ~unk & (kLa < BIG) & (kLa <= kI1)
        inv = a & ~unk & ~succ & (kI1 < BIG)
        out = np.zeros(k, int)
        out[unk] = -1; out[succ] = 1; out[inv] = 2; out[a & ~unk & ~succ & ~inv] = 3
        return dict(st=st, new=new, adm=adm, out=out, el=el, tie=tie, tau=tau)

    def path(self, j, s, tie_tau=None, complete=True):
        """One session as a path for contract.classify (the check of the vectorised code)."""
        start = self.start
        bars = [(start + 5 * (k + 1), self.O[j, k], self.up[j, k], self.dn[j, k], self.X[j, k])
                for k in range(self.NS) if not np.isnan(self.X[j, k])]
        minutes = {}
        if tie_tau is not None and tie_tau < BIG:
            c = range(5 * tie_tau, 5 * tie_tau + 5)
            minutes[start + 5 * (tie_tau + 1)] = [(start + cc, self.upm[j, cc], self.dnm[j, cc]) for cc in c if not np.isnan(self.upm[j, cc])]
        return dict(bars=bars, t=start + 5 * (s + 1), ou=self.ou[j], H=self.end, complete=complete, minutes=minutes)


def mean(v):
    v = [x for x in v if x is not None and not (isinstance(x, float) and math.isnan(x))]
    return float(np.mean(v)) if v else float("nan")


def pc(x):
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.1f}%"


def run():
    T = Tape()
    d, Sc = T.d, T.Sc
    start, formed, end = d["start"], d["formed"], d["end"]
    conf, fail, year, side = d["conf"], d["fail"], d["year"], d["side"]
    grid = list(range(formed + 15, end - 14, 15))
    recs, eq, excl, rng = [], dict(n=0, bad=0, fail_slot_bad=0), [], np.random.default_rng(8)
    t0 = time.time()
    for Y in TEST_YEARS:
        ok_years = year < Y
        test = np.flatnonzero((year == Y) & d["complete"] & (conf >= 0) & (side != 0))
        for t in grid:
            s = slot(d, t)
            av = Sc.avail(s)
            for i in test:
                if conf[i] > t or (0 <= fail[i] <= t) or not av[i]: continue
                sel, band, u0 = Sc.cohort(i, t, ok_years.copy())
                if len(sel) == 0: continue
                r = dict(sid=f"{INST}-{SESS}-{d['date'][i]}", t=int(t), u0=float(u0), band=band, N=int(len(sel)),
                         el_today=bool(T.RM[i, s] < L), stale_today=bool(np.isnan(T.X[i, s])))
                el = T.RM[sel, s] < L
                r["Nsc"] = int(el.sum())
                # the first failure after t must be the session's recorded DR break
                fs = np.where(fail[sel] >= 0, (fail[sel] - start) // 5 - 1, BIG)
                eq["fail_slot_bad"] += int((T.nI[sel, s] != fs).sum())
                for key, (lo, hi) in AREAS.items():
                    if not u0 > hi: continue
                    E = T.evaluate(sel, s, key)
                    st, new, adm, out = E["st"], E["new"], E["adm"], E["out"]
                    e_ = E["el"]
                    tt = T.evaluate(np.array([i]), s, key, count=False)
                    r[key] = dict(
                        st=[int((st == c).sum()) for c in range(4)],
                        old=int((T.nKs[key][sel, s] < BIG).sum()), old_le=int((T.nK[key][sel, s] < BIG).sum()),
                        new_base=int((new == 1).sum()),
                        sc_st=[int(((st == c) & e_).sum()) for c in range(4)],
                        new=int(((new == 1) & e_).sum()), new_unk=int(((new == -1) & e_).sum()),
                        adm=int(((adm == 1) & e_).sum()), adm_unk=int(((adm == -1) & e_).sum()), st_unk=int(((st == 3) & e_).sum()),
                        succ=int((out == 1).sum()), inv=int((out == 2).sum()), nei=int((out == 3).sum()), out_unk=int((out == -1).sum()),
                        ties=int((E["tie"] & e_).sum()),
                        t_adm=[int(T.start + 5 * (tau + 1) - t) for tau in E["tau"][(adm == 1) & e_]] if t == CARD["t"] else [],
                        today=dict(st=int(tt["st"][0]), new=int(tt["new"][0]), adm=int(tt["adm"][0]), out=int(tt["out"][0])))
                    # check the vectorised codes against contract.classify on a sample
                    if rng.random() < 0.02:
                        for q in range(len(sel)):
                            j = sel[q]
                            P = T.path(j, s, tie_tau=E["tau"][q] if E["tie"][q] else None)
                            c = classify(P, (lo, hi), L)
                            code_st = {"before": 0, "inside": 1, "beyond": 2, "unknown": 3}[c["status"]]
                            code_new = {True: 1, False: 0, None: -1}[c["new"]]
                            same = code_st == st[q] and code_new == new[q]
                            if c["eligible"] != bool(e_[q]): same = False
                            if c["eligible"]:
                                code_adm = {True: 1, False: 0, None: -1}[c["adm"]]
                                code_out = {"success": 1, "invalidated": 2, "neither": 3, None: -1 if c["adm"] else 0}[c["outcome"]]
                                same &= code_adm == adm[q] and code_out == out[q]
                            eq["n"] += 1; eq["bad"] += int(not same)
                # 8.1: the two continuation places ahead of the price (the screen's s1, s2)
                s1 = math.ceil((u0 + 0.25) / 0.5) * 0.5
                x = T.X[sel, s]
                SU = Sc.SU[sel, s]
                for nm, edge, far in (("s1", s1, s1 + 0.5), ("s2", s1 + 0.5, np.inf)):
                    stc = np.where(np.isnan(x), 3, np.where(x < edge, 0, np.where(x <= far, 1, 2)))
                    r[nm] = dict(st=[int((stc == c).sum()) for c in range(4)], old=int((SU >= edge).sum()),
                                 new_base=int(((stc == 0) & (SU >= edge)).sum()))
                # 8.4: sessions left out only because they are not complete
                inc = ~d["complete"] & ok_years & av & (side == side[i]) & (conf >= 0) & (conf <= t) & (np.abs(conf - conf[i]) <= 15)
                inc &= ~((fail >= 0) & (fail <= t))
                if band is not None: inc &= np.abs(Sc.pos(s) - u0) <= band
                for j in np.flatnonzero(inc):
                    row = dict(sid=r["sid"], t=int(t), j=int(j), last=int(start + 5 * (T.last[j] + 1)))
                    for key in AREAS:
                        c = classify(T.path(j, s, complete=False), AREAS[key], L)
                        row[key] = dict(new=c["new"], adm=c["adm"], outcome=c["outcome"], eligible=c["eligible"])
                    excl.append(row)
                # 8.4: holiday sessions (ended before 16:00) and sessions with a missing bar after t among the similar ones
                r["early"] = int((T.last[sel] < T.NS - 1).sum())
                r["gap"] = int((T.nG[sel, s] < BIG).sum())
                recs.append(r)
        print(Y, len(recs), f"{time.time() - t0:.0f}s", flush=True)
    return T, recs, eq, excl


def minute_states(T):
    """8.2: the live screen between two M5 closes. How many of its arrivals happened in minutes that today has already
    lived (the similar sessions are measured from their last M5 close)?"""
    d, Sc = T.d, T.Sc
    start, formed, end = d["start"], d["formed"], d["end"]
    conf, fail, year, side = d["conf"], d["fail"], d["year"], d["side"]
    agg = {}
    for Y in TEST_YEARS:
        ok_years = year < Y
        test = np.flatnonzero((year == Y) & d["complete"] & (conf >= 0) & (side != 0))
        for t5 in range(formed + 15, end - 14, 15):
            s = slot(d, t5)
            av = Sc.avail(s)
            c0 = 5 * (s + 1)
            for i in test:
                if conf[i] > t5 or (0 <= fail[i] <= t5) or not av[i]: continue
                pool, _, _ = Sc.cohort(i, t5, ok_years.copy(), band_on=False)
                if len(pool) == 0: continue
                pos5 = Sc.pos(s)[pool]
                for dl in (2, 4):
                    um = T.Xm[i, c0 + dl - 1]
                    if np.isnan(um): continue
                    sel, band = pool, None
                    for bw in (0.25, 0.5):
                        cc = pool[np.abs(pos5 - um) <= bw]
                        if len(cc) >= 40: sel, band = cc, bw; break
                    s1 = math.ceil((um + 0.25) / 0.5) * 0.5
                    places = [("A", "pull", -0.25), ("B", "pull", -0.75), ("s1", "cont", s1), ("s2", "cont", s1 + 0.5)]
                    for nm, role, edge in places:
                        if role == "pull" and not edge <= um: continue
                        if role == "pull":
                            old = T.nKs[nm][sel, s] < BIG
                            first = old & (T.nKs[nm][sel, s] == s + 1)
                        else:
                            old = Sc.SU[sel, s] >= edge
                            first = T.up[sel, s + 1] >= edge
                        A_ = [agg.setdefault((dl, nm, bk), dict(states=0, N=0, old=0, first=0, past=0, pure=0, unk=0, inside_at_m=0, share=[]))
                              for bk in ("all", band)]
                        for a in A_: a["states"] += 1; a["N"] += len(sel); a["old"] += int(old.sum()); a["first"] += int(first.sum())
                        c_ = dict(past=0, pure=0, unk=0, inside_at_m=0)
                        for j in sel[first]:
                            cols = np.arange(c0, c0 + 5)
                            hitm = (T.dnm[j, cols] < edge) if role == "pull" else (T.upm[j, cols] >= edge)
                            if not hitm.any(): c_["unk"] += 1; continue
                            rel = int(np.argmax(hitm))
                            if rel >= dl: continue
                            c_["past"] += 1
                            later = hitm[dl:].any() or ((T.nKs[nm][j, s + 1] < BIG) if role == "pull" else (Sc.SU[j, s + 1] >= edge))
                            if not later: c_["pure"] += 1
                            xm = T.Xm[j, c0 + dl - 1]
                            if not np.isnan(xm) and ((xm <= edge) if role == "pull" else (xm >= edge)): c_["inside_at_m"] += 1
                        for a in A_:
                            for k_, v_ in c_.items(): a[k_] += v_
                            a["share"].append(c_["past"] / len(sel))
        print("minutes", Y, flush=True)
    return agg


def report(T, recs, eq, excl, agg):
    L_ = []
    P = L_.append
    tb = lambda t: "10:45-11:30" if t <= 690 else ("11:45-13:00" if t <= 780 else "13:15-15:45")
    P(f"NQ RDR, test states (M5 closes, confirmed, DR intact): {len(recs)}; sessions {len({r['sid'] for r in recs})}")
    P(f"check: vectorised codes = contract.classify on {eq['n']} sampled (state, similar session, area): mismatches {eq['bad']}; "
      f"first close beyond DR after t = the recorded DR break: mismatches {eq['fail_slot_bad']}")
    t_ = T.ties
    P(f"K and L touched inside one M5 bar (eligible similar sessions): {t_['n']}; by minutes K first {t_['K']}, L first {t_['L']}, "
      f"same minute {t_['same']}, no minutes {t_['none']}")
    P("")
    P("8.1 Initial state against each place ahead of today's price (mean over states of shares of N_base)")
    P("    place  band   states | before inside beyond unknown | old screen | old with <= | new arrival (from before) on N_base | old - new")
    for nm in ("A", "B", "s1", "s2"):
        for bd in ("all", 0.25, 0.5, None):
            R = [r for r in recs if nm in r and (bd == "all" or r["band"] == bd)]
            if len(R) < 50: continue
            sh = lambda f: mean([f(r) / r["N"] for r in R])
            st = [sh(lambda r, c=c: r[nm]["st"][c]) for c in range(4)]
            old = sh(lambda r: r[nm]["old"]); new = sh(lambda r: r[nm]["new_base"])
            ole = sh(lambda r: r[nm]["old_le"]) if nm in AREAS else float("nan")
            bn = {"all": "all", 0.25: "±0.25", 0.5: "±0.5", None: "none"}[bd]
            P(f"    {nm:5s}  {bn:5s} {len(R):7d} | {pc(st[0]):>6s} {pc(st[1]):>6s} {pc(st[2]):>6s} {pc(st[3]):>6s} | {pc(old):>9s} | "
              f"{pc(ole):>9s} | {pc(new):>9s} | {100 * (old - new):+.1f} pt")
    P("")
    P("8.2 Minute cut inside an M5 (the live screen): arrivals whose first touch was in minutes today has already lived")
    P("    At an M5 close the similar sessions are measured from the same close: nothing is in the past by construction.")
    for dl in (2, 4):
        for nm in ("A", "B", "s1", "s2"):
          for bk in ("all", 0.25, 0.5, None):
            a = agg.get((dl, nm, bk))
            if not a: continue
            bn = {"all": "all", 0.25: "±0.25", 0.5: "±0.5", None: "none"}[bk]
            P(f"    +{dl} min {nm:3s} {bn:5s} states {a['states']:6d} | arrivals {a['old']:7d}, in the first bar {a['first']:6d}, "
              f"first touch in the lived minutes {a['past']:6d} ({pc(a['past'] / max(1, a['old']))} of arrivals; "
              f"{100 * mean(a['share']):.1f} pt of the place's share on average) | no touch after the cut at all {a['pure']}, "
              f"at the cut already at/over the edge {a['inside_at_m']}, minute order unknown {a['unk']}")
    P("")
    P("8.3 L = +1.0 already reached by t")
    for grp, R in (("all states", recs), ("today L not reached", [r for r in recs if r["el_today"]]),
                   ("today L reached", [r for r in recs if not r["el_today"]])):
        P(f"    {grp:20s} states {len(R):6d} | similar sessions with L reached by t {pc(mean([1 - r['Nsc'] / r['N'] for r in R]))} | "
          f"N_base mean {mean([r['N'] for r in R]):.0f} median {np.median([r['N'] for r in R]):.0f} | "
          f"N_scenario mean {mean([r['Nsc'] for r in R]):.0f} median {np.median([r['Nsc'] for r in R]):.0f}")
    for b in ("10:45-11:30", "11:45-13:00", "13:15-15:45"):
        R = [r for r in recs if tb(r["t"]) == b]
        Rt = [r for r in R if r["el_today"]]
        P(f"    {b}: states {len(R):6d}, today L reached {pc(1 - len(Rt) / len(R))}; where today not: similar with L reached "
          f"{pc(mean([1 - r['Nsc'] / r['N'] for r in Rt]))}")
    P("")
    P("8.4 Incomplete observations")
    nx = len(excl)
    res = lambda k: sum(1 for x in excl if x[k]["outcome"] is not None or x[k]["new"] is False or x[k]["adm"] is False)
    P(f"    similar sessions left out only because the session is not complete: {nx} (session, state) pairs over "
      f"{len({x['j'] for x in excl})} sessions; ends of data {sorted({x['last'] for x in excl})}; the event already decided "
      f"before the cut: A {res('A')} of {nx}, B {res('B')} of {nx}")
    P(f"    holiday sessions (market closed before 16:00) inside the similar sessions: {pc(mean([r['early'] / r['N'] for r in recs]))} "
      f"of N_base on average (counted as complete; after their close nothing can happen)")
    P(f"    similar sessions with a missing M5 bar after t: {pc(mean([r['gap'] / r['N'] for r in recs]))} of N_base on average "
      f"({sum(r['gap'] for r in recs)} pairs)")
    P("")
    P("Part D and context: the scenario 'new arrival in K -> L=+1.0 before the DR break' where today's L is not reached and today is before K")
    P("    each number on its known cases; unknown = share of N_scenario (new / adm / seq); today = what the test session itself did")
    P("    group                         states | N_base N_sc | area | p_new  p_adm  q      p_seq | unknown new/adm/seq | today (realised): new adm q seq")

    def line(R, nm, key):
        """Each number on its known cases (dogovor.md 1.1): p = count / (N_scenario - unknown), averaged over states; the
        card's q = mean p_seq / mean p_adm, so that p_seq = p_adm x q holds on the card; unknown shares of N_scenario."""
        R = [r for r in R if key in r and r["el_today"] and r["Nsc"] > 0]
        if not R: return
        kv = lambda num, unk: mean([r[key][num] / (r["Nsc"] - r[key][unk]) if r["Nsc"] > r[key][unk] else None for r in R])
        for r in R: r[key]["seq_unk"] = r[key]["adm_unk"] + r[key]["out_unk"]
        pn, pa, ps = kv("new", "new_unk"), kv("adm", "adm_unk"), kv("succ", "seq_unk")
        q = ps / pa if pa else float("nan")
        qp = sum(r[key]["succ"] for r in R) / max(1, sum(r[key]["adm"] - r[key]["out_unk"] for r in R))
        un = (mean([r[key]["new_unk"] / r["Nsc"] for r in R]), mean([r[key]["adm_unk"] / r["Nsc"] for r in R]),
              mean([r[key]["seq_unk"] / r["Nsc"] for r in R]))
        td = [r[key]["today"] for r in R]
        tn = [x for x in td if x["new"] >= 0]; ta = [x for x in td if x["adm"] >= 0]
        tq = [x for x in td if x["adm"] == 1 and x["out"] > 0]
        ts = [x for x in ta if x["adm"] == 0 or x["out"] != -1]
        real = (mean([x["new"] == 1 for x in tn]), mean([x["adm"] == 1 for x in ta]),
                mean([x["out"] == 1 for x in tq]) if tq else float("nan"), mean([x["adm"] == 1 and x["out"] == 1 for x in ts]))
        P(f"    {nm:28s} {len(R):6d} | {mean([r['N'] for r in R]):5.0f} {mean([r['Nsc'] for r in R]):5.0f} | {key}    | "
          f"{pc(pn):>6s} {pc(pa):>6s} {pc(q):>6s} {pc(ps):>6s} | {pc(un[0])}/{pc(un[1])}/{pc(un[2])} | "
          f"{pc(real[0])} {pc(real[1])} {pc(real[2])} {pc(real[3])} | pooled q {pc(qp)}")

    card = [r for r in recs if r["t"] == CARD["t"] and CARD["u_lo"] <= r["u0"] < CARD["u_hi"]]
    for key in AREAS: line(card, "CARD 11:00, price 0..+0.5", key)
    for key in AREAS: line(recs, "all states", key)
    for b in ("10:45-11:30", "11:45-13:00", "13:15-15:45"):
        for key in AREAS: line([r for r in recs if tb(r["t"]) == b], b, key)
    P("")
    P("Time of the admissible arrival (card states): two different numbers")
    for key in AREAS:
        R = [r for r in card if key in r and r["el_today"] and r["Nsc"] > 0]
        allt = np.array([x for r in R for x in r[key]["t_adm"]])
        if not len(allt): continue
        for lo, hi in ((0, 30), (30, 90), (90, 400)):
            share_all = mean([sum(1 for x in r[key]["t_adm"] if lo < x <= hi) / r["Nsc"] for r in R])
            share_arr = float(((allt > lo) & (allt <= hi)).mean())
            P(f"    {key}: arrival {lo:3d}-{hi:3d} min after t | of all N_scenario {pc(share_all):>6s} | among admissible arrivals {pc(share_arr):>6s}")
        P(f"    {key}: median time from t to the admissible arrival {np.median(allt):.0f} min")
    return "\n".join(L_)


if __name__ == "__main__":
    T, recs, eq, excl = run()
    agg = minute_states(T)
    with gzip.open(OUT, "wt", encoding="utf-8") as fh: json.dump(dict(recs=recs, excl=excl), fh, default=str)
    text = report(T, recs, eq, excl, agg)
    (HERE / "tape_diagnostic.log").write_text(text + "\n", encoding="utf-8")
    print(text)
