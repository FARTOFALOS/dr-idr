"""Check 5 (lens 4, «alignment»): the live screen between two M5 closes.

Live, lab/scene21.py takes today's price from the forming M5 (the minute now), but places the similar sessions at their
last CLOSED M5 and measures their paths from that close (so their paths include minutes that today has already lived).
At minutes m = an M5 close + 2 or + 4 minutes (every 15 minutes, confirmed states, 2016-2025, walk-forward cohorts):
  A (the live screen)  today's price at m; similar sessions matched on their M5 close before m; paths after that close;
  B (minutes aligned)  today's price at m; similar sessions matched on their price at m (M1); paths after m (M1);
  C (closed M5 only)   today's price at the last M5 close; similar sessions as the 15-minute replay; paths after it.
The places are the ones ahead of today's price at m for all three; outcome = today's price came there after m (M1).
python -B c5_minute_alignment.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from lenscommon import INST, RT, TEST_YEARS, Screen, bss, dense, edges_conf, near_edge, paired_brier, slot

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lab"))
from build_market import load_minutes  # noqa: E402

OUT = RT / "lens4_minute_alignment.json"
DELTAS = (2, 4)


def minute_arrays(df, d):
    """(n, end-start) arrays of M1 open-minute bars in ticks for the sessions of d; column c = bar opening at start+c."""
    start, end = d["start"], d["end"]
    rowof = {int(x.replace("-", "")): r for r, x in enumerate(d["date"])}
    mod = df["mod"].to_numpy(); dat = df["date"].to_numpy()
    m = (mod >= start) & (mod < end)
    r = np.array([rowof.get(int(x), -1) for x in dat[m]])
    ok = r >= 0
    rows, cols = r[ok], (mod[m] - start)[ok]
    out = {}
    for k in ("h", "l", "c"):
        A = np.full((len(d["date"]), end - start), np.nan)
        A[rows, cols] = df[k].to_numpy()[m][ok] / d["tick"]
        out[k] = A
    return out["h"], out["l"], out["c"]


def conf_coords(d, Hm, Lm, Cm):
    side = d["side"].astype(float)[:, None]
    w = (d["idrh"] - d["idrl"]); w = np.where(w > 0, w, np.nan)[:, None]
    e = np.where(side[:, 0] == 1, d["idrh"], d["idrl"])[:, None]
    up = side * (np.where(side == 1, Hm, Lm) - e) / w
    dn = side * (np.where(side == 1, Lm, Hm) - e) / w
    X = side * (Cm - e) / w
    return up, dn, X


def from_max(A):
    """out[:, c] = max of A[:, c:] (the bars opening at or after column c)."""
    B = np.where(np.isnan(A), -np.inf, A)
    return np.maximum.accumulate(B[:, ::-1], axis=1)[:, ::-1]


def run(inst, sess, df):
    d = dense(inst, sess)
    S = Screen(d)
    start, formed, end = d["start"], d["formed"], d["end"]
    Hm, Lm, Cm = minute_arrays(df, d)
    # the M1 bars must rebuild the M5 base
    H5 = np.nanmax(Hm.reshape(len(Hm), -1, 5), axis=2)
    both = ~np.isnan(H5) & ~np.isnan(d["H"])
    agree = np.isclose(H5[both], d["H"][both], atol=1e-6).mean()
    upm, dnm, Xm = conf_coords(d, Hm, Lm, Cm)
    SUm, SDm = from_max(upm), -from_max(-dnm)
    conf, fail, year = d["conf"], d["fail"], d["year"]
    rec = []
    for Y in TEST_YEARS:
        ok_years = year < Y
        test = np.flatnonzero((year == Y) & d["complete"] & (conf >= 0) & (d["side"] != 0))
        for t5 in range(formed + 15, end - 14, 15):
            s = slot(d, t5)
            av = S.avail(s)
            for i in test:
                if conf[i] > t5 or (0 <= fail[i] <= t5) or not av[i]: continue
                pool, _, u5 = S.cohort(i, t5, ok_years.copy(), band_on=False)
                if len(pool) == 0: continue
                pos5 = S.pos(s)[pool]
                for dl in DELTAS:
                    m = t5 + dl; c = m - start                     # today's live price = close of the minute opened at m-1
                    um = Xm[i, c - 1]
                    if np.isnan(um) or c >= Xm.shape[1]: continue
                    posm = Xm[pool, c - 1]
                    def band_sel(pos, u):
                        for bw in (0.25, 0.5):
                            cc = pool[np.abs(pos - u) <= bw]
                            if len(cc) >= 40: return cc, bw
                        return pool, None
                    sA, bA = band_sel(pos5, um)
                    okm = ~np.isnan(posm)
                    sB, bB = band_sel(np.where(okm, posm, np.inf), um)
                    sC, bC = band_sel(pos5, u5)
                    for role, lo, hi in edges_conf(um):
                        e = near_edge(role, lo, hi)
                        if role == "cont":
                            y = SUm[i, c] >= e
                            pA, pB, pC = (S.SU[sA, s] >= e).mean(), (SUm[sB, c] >= e).mean(), (S.SU[sC, s] >= e).mean()
                        else:
                            y = SDm[i, c] <= e
                            pA, pB, pC = (S.SD[sA, s] <= e).mean(), (SDm[sB, c] <= e).mean(), (S.SD[sC, s] <= e).mean()
                        rec.append(dict(sid=f"{inst}-{sess}-{d['date'][i]}", m=int(m), dl=dl, role=role, y=bool(y), A=float(pA), B=float(pB),
                                        C=float(pC), bA=bA, bB=bB, bC=bC, gap=float(e - um) if role == "cont" else float(um - e)))
    return rec, agree


def report(out):
    L = []
    allR = [r for rec in out.values() for r in rec]
    for key, R0 in list(out.items()) + [("ALL", allR)]:
        R = [r for r in R0 if r["bA"] in (0.25, 0.5)]
        if len(R) < 500: continue
        sid = [r["sid"] for r in R]; y = [r["y"] for r in R]
        sc = {v: bss([r[v] for r in R], y, sid) for v in "ABC"}
        dAB, cAB = paired_brier([r["A"] for r in R], [r["B"] for r in R], y, sid)
        dAC, cAC = paired_brier([r["A"] for r in R], [r["C"] for r in R], y, sid)
        L.append(f"{key:7s} states {len(R):7d} | BSS A (live now) {100 * sc['A'][0]:5.1f}% [{100 * sc['A'][1][0]:.1f}; {100 * sc['A'][1][1]:.1f}]  "
                 f"B (minutes) {100 * sc['B'][0]:5.1f}% [{100 * sc['B'][1][0]:.1f}; {100 * sc['B'][1][1]:.1f}]  C (closed M5) {100 * sc['C'][0]:5.1f}% "
                 f"[{100 * sc['C'][1][0]:.1f}; {100 * sc['C'][1][1]:.1f}]")
        L.append(f"{'':9s} Brier A minus B {1e3 * dAB:+.2f}e-3 [{1e3 * cAB[0]:+.2f}; {1e3 * cAB[1]:+.2f}]  A minus C {1e3 * dAC:+.2f}e-3 [{1e3 * cAC[0]:+.2f}; "
                 f"{1e3 * cAC[1]:+.2f}] | mean forecast A {100 * np.mean([r['A'] for r in R]):.1f}% B {100 * np.mean([r['B'] for r in R]):.1f}% "
                 f"C {100 * np.mean([r['C'] for r in R]):.1f}% real {100 * np.mean(y):.1f}%")
        near = [r for r in R if r["gap"] <= 0.25]
        if len(near) >= 300:
            L.append(f"{'':9s} places within 0.25 IDR of the price: mean forecast A {100 * np.mean([r['A'] for r in near]):.1f}% "
                     f"B {100 * np.mean([r['B'] for r in near]):.1f}% C {100 * np.mean([r['C'] for r in near]):.1f}% real {100 * np.mean([r['y'] for r in near]):.1f}%")
    return "\n".join(L)


if __name__ == "__main__":
    out, t0, agr = {}, time.time(), {}
    for inst in INST:
        df = load_minutes(inst)
        for sess in ("RDR", "ODR"):
            out[f"{inst}-{sess}"], agr[f"{inst}-{sess}"] = run(inst, sess, df)
            print(inst, sess, len(out[f"{inst}-{sess}"]), f"M1 rebuilds M5 highs in {100 * agr[f'{inst}-{sess}']:.2f}% of bars", f"{time.time() - t0:.0f}s", flush=True)
        del df
    OUT.write_text(json.dumps(out), encoding="utf-8")
    print(report(out))
