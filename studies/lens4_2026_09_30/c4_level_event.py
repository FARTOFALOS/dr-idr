"""Check 4 of lens 4: the screen's state matcher against a level-activation matcher.

A level activation = an M5 close that crosses a half-step of the IDR scale (…, -0.5, 0 = the confirmation-side IDR edge,
+0.5, +1.0, …) after the confirmation while DR holds; key = (level, direction). At every activation of a test session
(2016-2025) the similar sessions are taken two ways:
  state - the screen (lab/scene21.py): same side, confirmation ±15 min, DR intact, price matched ±0.25 / ±0.5 IDR at
          the same clock minute; their paths after that minute;
  event - sessions with the same side, confirmation ±15 min and an activation of the same level in the same direction
          within ±15 min of today's (the nearest one), DR intact then; their paths after THEIR activation;
  event+band - the same, then the screen's price band on the close at the activation.
Forecast for each place ahead of today's price (edges as the screen draws them); outcome = today came there after.
Walk-forward cohorts (years before the test year).
python -B c4_level_event.py
"""
from __future__ import annotations

import json
import time

import numpy as np

from lenscommon import INST, RT, TEST_YEARS, Screen, bss, dense, edges_conf, near_edge, paired_brier, reliability

OUT = RT / "lens4_level_event.json"


def activations(d, X):
    """All half-step crossings by M5 closes after the confirmation and before a DR break: arrays j, k, t, level, dir."""
    start = d["start"]
    a, b = np.floor(X[:, :-1] / 0.5), np.floor(X[:, 1:] / 0.5)
    ok = ~np.isnan(a) & ~np.isnan(b) & (a != b)
    j, kk = np.nonzero(ok)
    k = kk + 1
    t = start + 5 * (k + 1)
    up = b[j, kk] > a[j, kk]
    lev = np.where(up, b[j, kk] * 0.5, (b[j, kk] + 1) * 0.5)
    conf, fail = d["conf"][j], d["fail"][j]
    keep = (conf >= 0) & (t >= conf) & ((fail < 0) | (t < fail)) & (lev >= -1.0) & (lev <= 3.0)
    return j[keep], k[keep], t[keep], lev[keep], np.where(up, 1, -1)[keep]


def run(inst, sess):
    d = dense(inst, sess)
    S = Screen(d)
    end = d["end"]
    conf, year, side = d["conf"], d["year"], d["side"]
    J, K, T, LV, DR = activations(d, S.X)
    idx = {}
    for n_, key in enumerate(zip(LV, DR)): idx.setdefault(key, []).append(n_)
    idx = {k: np.array(v) for k, v in idx.items()}
    rec = []
    for Y in TEST_YEARS:
        ok_years = year < Y
        for n_ in np.flatnonzero(year[J] == Y):
            i, k, t = J[n_], K[n_], int(T[n_])
            if t > end - 15 or not d["complete"][i] or not S.avail(k)[i]: continue
            sel, band, _ = S.cohort(i, t, ok_years.copy())
            u0 = S.X[i, k]
            c = idx[(LV[n_], DR[n_])]
            jj = J[c]
            m = (ok_years[jj] & d["complete"][jj] & (side[jj] == side[i]) & (jj != i) & (np.abs(T[c] - t) <= 15)
                 & (np.abs(conf[jj] - conf[i]) <= 15) & S.fut_ok[jj, np.minimum(K[c] + 1, S.X.shape[1] - 1)] & (K[c] + 1 < S.X.shape[1]))
            c = c[m]
            if len(c) == 0: continue
            order = np.lexsort((T[c], np.abs(T[c] - t)))
            c = c[order]
            _, first = np.unique(J[c], return_index=True)
            c = c[first]
            ej, ek = J[c], K[c]
            xe = S.X[ej, ek]
            eb = np.arange(len(c))
            for bw in (0.25, 0.5):
                cc = np.flatnonzero(np.abs(xe - u0) <= bw)
                if len(cc) >= 40: eb = cc; break
            jac = len(np.intersect1d(sel, ej)) / max(1, len(np.union1d(sel, ej)))
            for role, lo, hi in edges_conf(u0):
                e = near_edge(role, lo, hi)
                if role == "cont":
                    y = S.SU[i, k] >= e; ps = (S.SU[sel, k] >= e).mean() if len(sel) else np.nan; pe_ = S.SU[ej, ek] >= e
                else:
                    y = S.SD[i, k] <= e; ps = (S.SD[sel, k] <= e).mean() if len(sel) else np.nan; pe_ = S.SD[ej, ek] <= e
                rec.append(dict(sid=f"{inst}-{sess}-{d['date'][i]}", t=t, lev=float(LV[n_]), dir=int(DR[n_]), role=role, y=bool(y),
                                state=float(ps), event=float(pe_.mean()), eventb=float(pe_[eb].mean()), band=band,
                                n=int(len(sel)), ne=int(len(c)), neb=int(len(eb)), jac=float(jac)))
    return rec


def report(out):
    L = []
    allR = [r for rec in out.values() for r in rec]
    for key, R0 in list(out.items()) + [("ALL", allR)]:
        R = [r for r in R0 if r["band"] in (0.25, 0.5) and r["ne"] >= 20]
        if len(R) < 500: continue
        sid = [r["sid"] for r in R]; y = [r["y"] for r in R]
        sc = {m: bss([r[m] for r in R], y, sid) for m in ("state", "event", "eventb")}
        d1, c1 = paired_brier([r["event"] for r in R], [r["state"] for r in R], y, sid)
        d2, c2 = paired_brier([r["eventb"] for r in R], [r["state"] for r in R], y, sid)
        thin = np.mean([r["ne"] < 20 for r in R0 if r["band"] in (0.25, 0.5)])
        L.append(f"{key:7s} activations x places {len(R):7d} | BSS state {100 * sc['state'][0]:5.1f}% [{100 * sc['state'][1][0]:.1f}; {100 * sc['state'][1][1]:.1f}]"
                 f"  event {100 * sc['event'][0]:5.1f}% [{100 * sc['event'][1][0]:.1f}; {100 * sc['event'][1][1]:.1f}]"
                 f"  event+band {100 * sc['eventb'][0]:5.1f}% [{100 * sc['eventb'][1][0]:.1f}; {100 * sc['eventb'][1][1]:.1f}]")
        L.append(f"{'':9s} Brier event minus state {1e3 * d1:+.1f}e-3 [{1e3 * c1[0]:+.1f}; {1e3 * c1[1]:+.1f}], event+band minus state {1e3 * d2:+.1f}e-3 "
                 f"[{1e3 * c2[0]:+.1f}; {1e3 * c2[1]:+.1f}] | similar sessions: state median {np.median([r['n'] for r in R]):.0f}, event {np.median([r['ne'] for r in R]):.0f}; "
                 f"shared sessions (Jaccard) median {np.median([r['jac'] for r in R]):.2f}; activations with < 20 event analogs {100 * thin:.0f}%")
        if key == "ALL":
            for m in ("state", "event", "eventb"):
                L.append(f"{'':9s} reliability {m}: {reliability([r[m] for r in R], y)}")
    return "\n".join(L)


if __name__ == "__main__":
    out, t0 = {}, time.time()
    for inst in INST:
        for sess in ("RDR", "ODR"):
            out[f"{inst}-{sess}"] = run(inst, sess)
            print(inst, sess, len(out[f"{inst}-{sess}"]), f"{time.time() - t0:.0f}s", flush=True)
    OUT.write_text(json.dumps(out), encoding="utf-8")
    print(report(out))
