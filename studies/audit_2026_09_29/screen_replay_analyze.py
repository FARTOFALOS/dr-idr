"""Aggregates of screen_replay.py (lab/.runtime/audit_screen_replay.json) with session-clustered bootstrap intervals.
The printed report is kept as screen_replay.log next to this file (aggregates only).

Metric names, precisely:
- BSS = 1 - Brier(forecast) / Brier(constant), the constant being the realised frequency of the same states
  (an optimistic constant: it knows the test-period base rate). Multi-class: summed over classes.
- calibration-in-the-large = mean forecast - realised frequency, percentage points.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np

R = json.loads((Path(__file__).resolve().parents[2] / "lab" / ".runtime" / "audit_screen_replay.json").read_text(encoding="utf-8"))
rng = np.random.default_rng(9)
B = 300


def pooled(filter_fn, keys=None):
    rows = []
    for k, recs in R.items():
        if keys and k.split("-")[1] not in keys: continue
        rows.extend(r for r in recs if filter_fn(r))
    return rows


def sid_groups(rows):
    g = defaultdict(list)
    for j, r in enumerate(rows): g[r["sid"]].append(j)
    return list(g.values())


def boot_bss(rows, pkey, ykey):
    p = np.array([r[pkey] for r in rows], float); y = np.array([r[ykey] for r in rows], float)
    groups = sid_groups(rows)
    agg = np.array([[len(ix), y[ix].sum(), ((p[ix] - y[ix]) ** 2).sum(), p[ix].sum()] for ix in groups])
    def bss(a):
        n, sy, se, sp = a.sum(0); yb = sy / n; bc = yb - yb * yb
        return 1 - (se / n) / bc, 100 * (sp / n - yb)
    est = bss(agg)
    bs = np.array([bss(agg[rng.integers(0, len(agg), len(agg))]) for _ in range(B)])
    return dict(states=len(rows), sessions=len(groups), bss=round(100 * est[0], 1), bss_ci=[round(100 * np.percentile(bs[:, 0], 2.5), 1), round(100 * np.percentile(bs[:, 0], 97.5), 1)],
                citl_pp=round(est[1], 1), citl_ci=[round(np.percentile(bs[:, 1], 2.5), 1), round(np.percentile(bs[:, 1], 97.5), 1)])


def boot_bins(rows, pkey, ykey, edges=(0, .5, .7, .8, .9, 1.0001)):
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        sub = [r for r in rows if a <= r[pkey] < b]
        if len(sub) < 100: continue
        groups = sid_groups(sub)
        y = np.array([r[ykey] for r in sub], float); p = np.array([r[pkey] for r in sub], float)
        agg = np.array([[len(ix), y[ix].sum()] for ix in groups])
        est = 100 * agg[:, 1].sum() / agg[:, 0].sum()
        bs = [100 * s[:, 1].sum() / s[:, 0].sum() for s in (agg[rng.integers(0, len(agg), len(agg))] for _ in range(B))]
        out.append(f"{a:.1f}-{min(b, 1):.1f}: pred {100 * p.mean():.0f} real {est:.0f} [{np.percentile(bs, 2.5):.0f}; {np.percentile(bs, 97.5):.0f}] ({len(sub)} states, {len(groups)} sessions)")
    return out


def boot_multi(rows):
    P = np.array([r["p_pull"] for r in rows]); Y = np.eye(4)[[r["y_pull"] for r in rows]]
    groups = sid_groups(rows)
    agg = np.array([np.r_[len(ix), Y[ix].sum(0), ((P[ix] - Y[ix]) ** 2).sum()] for ix in groups])
    def bss(a):
        s = a.sum(0); n = s[0]; f = s[1:5] / n; bc = (f - f * f).sum()
        return 1 - (s[5] / n) / bc
    est = bss(agg); bs = [bss(agg[rng.integers(0, len(agg), len(agg))]) for _ in range(B)]
    return dict(states=len(rows), sessions=len(groups), bss=round(100 * est, 1), ci=[round(100 * np.percentile(bs, 2.5), 1), round(100 * np.percentile(bs, 97.5), 1)],
                pred=[round(100 * x, 1) for x in P.mean(0)], real=[round(100 * x, 1) for x in Y.mean(0)])


for sess in (("RDR",), ("ODR",)):
    S = sess[0]
    print("=" * 30, S, "(NQ, ES, YM pooled; walk-forward 2016-2025)")
    c = pooled(lambda r: r["mode"] == "conf" and "p_held" in r, sess)
    print("DR удержится:", boot_bss(c, "p_held", "y_held"))
    for lab_, f in (("band 0.25", lambda r: r["band"] == 0.25), ("band 0.5", lambda r: r["band"] == 0.5), ("no band", lambda r: r["band"] is None)):
        sub = [r for r in c if f(r)]
        print(f"first STD target (panel «Цели») {lab_}: share of states {100 * len(sub) / len(c):.1f}%", boot_bss(sub, "p_tgt", "y_tgt"))
        for line in boot_bins(sub, "p_tgt", "y_tgt"): print("     ", line)
    print("pullback places (first minutes + 3 bands):", boot_multi(c))
    w = pooled(lambda r: r["mode"] == "wait" and "p_up" in r, sess)
    print("before confirmation, first later confirmation up:", boot_bss(w, "p_up", "y_up"))
    print("   «до DR high» mapped:", boot_bss(w, "p_drh_mapped", "y_drh"), "| own-DR frame:", boot_bss(w, "p_drh_own", "y_drh"))
    contra = np.mean([r["p_drh_mapped"] < r["p_up"] for r in w])
    contra_own = np.mean([r["p_drh_own"] < r["p_up"] for r in w])
    print(f"   states where «до DR high» < «↑»: mapped {100 * contra:.1f}%, own-DR frame {100 * contra_own:.2f}%")
    e = [r for r in c if "arc_far" in r]
    for role in ("pull", "cont"):
        L = [r[f"late_{role}"] for r in e if f"late_{role}" in r]; LA = [r[f"late_all_{role}"] for r in e]
        Y_ = [r[f"y_late_{role}"] for r in e if r.get(f"y_late_{role}") is not None]
        print(f"late 30 min, {role}, early states {len(e)}: cohort {100 * np.mean(L):.1f}% | today {100 * np.mean(Y_):.1f}% | "
              f"arcsine on the tape's variance clock {100 * np.mean([r['arc_far'] for r in e]):.1f}% | arcsine flat clock {100 * np.mean([r['arc_flat'] for r in e]):.1f}% | uniform {100 * np.mean([r['unif'] for r in e]):.1f}%"
              f"  || incl. first minutes: cohort {100 * np.mean(LA):.1f}% vs arcsine {100 * np.mean([r['arc_all'] for r in e]):.1f}%")
    fc = [r["fan_cov"] for r in c if "fan_cov" in r]; fy = [r["fan_y"] for r in c if r.get("fan_y") is not None]
    print(f"fan 20-80: similar sessions whose whole path stays inside {100 * np.mean(fc):.1f}% (median state {100 * np.median(fc):.1f}%); today's path stays inside {100 * np.mean(fy):.1f}%")

# ---- sample sizes behind the percentages (cohorts from every other year = the size a 20-year base gives) and what
# happens to the numbers when today's price cannot be matched
print("=" * 30, "sample sizes (all instruments, both sessions)")
for mode in ("conf", "brk", "wait"):
    rs = [r for recs in R.values() for r in recs if r["mode"] == mode and "nL" in r]
    nL = np.array([r["nL"] for r in rs])
    print(f"{mode}: states {len(rs)}, median n {np.median(nL):.0f}, n<40 {100 * (nL < 40).mean():.1f}%, n<10 {100 * (nL < 10).mean():.1f}%, "
          f"no price band {100 * np.mean([r['bandL'] is None for r in rs]):.1f}%")
    if mode != "wait":
        sc = np.array([r["since_conf"] for r in rs])
        for lab, m in (("0-60 min after the confirmation", sc <= 60), ("60-180", (sc > 60) & (sc <= 180)), ("180+", sc > 180)):
            if m.any(): print(f"   {lab}: states {m.sum()}, n<40 {100 * (nL[m] < 40).mean():.1f}%, n<10 {100 * (nL[m] < 10).mean():.1f}%")
for S in ("RDR", "ODR"):
    c = pooled(lambda r: r["mode"] == "conf" and "p_held" in r, (S,))
    for lab, f in (("price matched", lambda r: r["band"] is not None), ("price NOT matched", lambda r: r["band"] is None)):
        sub = [r for r in c if f(r)]
        print(S, lab, "· DR удержится:", boot_bss(sub, "p_held", "y_held"), "· pullback places:", boot_multi(sub))
