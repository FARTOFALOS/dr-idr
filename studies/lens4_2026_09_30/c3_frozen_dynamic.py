"""Check 3 of lens 4: a map frozen at the anchor against the screen's map rebuilt at every closed M5.

Anchor = the confirmation (the M5 close beyond DR). At the anchor the screen's similar sessions C0 are taken once
(same rules as lab/scene21.py at that minute). Then, every 15 minutes while today's DR holds, for each place ahead of
today's price (edges as the screen draws them) three forecasts of «price comes there after this minute»:
  dyn  - the screen: similar sessions rebuilt at this minute (price matched now), their paths after this minute;
  frz  - the frozen sessions C0, their paths after this minute (the same films, read further);
  map  - the frozen map as drawn at the anchor: share of C0 that came there after the anchor (never changes).
Outcome: today's price came there after the minute. Walk-forward cohorts (years before the test year), 2016-2025.
Also the «weather»: how much the rebuilt map moves between two checks 15 minutes apart for the same level.
python -B c3_frozen_dynamic.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from lenscommon import INST, RT, TEST_YEARS, Screen, bss, dense, edges_conf, near_edge, paired_brier, reliability, slot

OUT = RT / "lens4_frozen_dynamic.json"


def run(inst, sess):
    d = dense(inst, sess)
    S = Screen(d)
    formed, end = d["formed"], d["end"]
    grid = np.arange(formed + 15, end - 14, 15)
    conf, fail, year = d["conf"], d["fail"], d["year"]
    rec = []
    for Y in TEST_YEARS:
        ok_years = year < Y
        test = np.flatnonzero((year == Y) & d["complete"] & (conf >= 0) & (d["side"] != 0))
        for i in test:
            ta = int(conf[i])
            sa = slot(d, ta)
            if ta > end - 30 or not S.avail(sa)[i]: continue
            C0, band0, _ = S.cohort(i, ta, ok_years.copy())
            if len(C0) == 0: continue
            for t in grid[grid > ta]:
                if 0 <= fail[i] <= t: break
                s = slot(d, t)
                if not S.avail(s)[i]: continue
                sel, band, u0 = S.cohort(i, t, ok_years.copy())
                if len(sel) == 0: continue
                for role, lo, hi in edges_conf(u0):
                    e = near_edge(role, lo, hi)
                    if role == "cont":
                        y = S.SU[i, s] >= e
                        pd_, pf, pm = (S.SU[sel, s] >= e).mean(), (S.SU[C0, s] >= e).mean(), (S.SU[C0, sa] >= e).mean()
                    else:
                        y = S.SD[i, s] <= e
                        pd_, pf, pm = (S.SD[sel, s] <= e).mean(), (S.SD[C0, s] <= e).mean(), (S.SD[C0, sa] <= e).mean()
                    rec.append(dict(sid=f"{inst}-{sess}-{d['date'][i]}", t=int(t), dt=int(t - ta), role=role, edge=float(e),
                                    y=bool(y), dyn=float(pd_), frz=float(pf), map=float(pm), band=band, band0=band0,
                                    n=int(len(sel)), n0=int(len(C0))))
    return rec


def report(out):
    L = []
    allR = [r for rec in out.values() for r in rec]
    for key, R in list(out.items()) + [("ALL", allR)]:
        R = [r for r in R if r["band"] in (0.25, 0.5)]          # the screen shows numbers only at ● and ◐
        if len(R) < 500: continue
        sid = [r["sid"] for r in R]; y = [r["y"] for r in R]
        sc = {m: bss([r[m] for r in R], y, sid) for m in ("dyn", "frz", "map")}
        L.append(f"{key:7s} states {len(R):7d} | BSS dyn {100 * sc['dyn'][0]:5.1f}% [{100 * sc['dyn'][1][0]:.1f}; {100 * sc['dyn'][1][1]:.1f}]"
                 f"  frozen-films {100 * sc['frz'][0]:5.1f}% [{100 * sc['frz'][1][0]:.1f}; {100 * sc['frz'][1][1]:.1f}]"
                 f"  frozen-map {100 * sc['map'][0]:5.1f}% [{100 * sc['map'][1][0]:.1f}; {100 * sc['map'][1][1]:.1f}]")
        for lo_, hi_ in ((0, 30), (30, 90), (90, 180), (180, 999)):
            Q = [r for r in R if lo_ < r["dt"] <= hi_]
            if len(Q) < 300: continue
            dq, ci = paired_brier([r["frz"] for r in Q], [r["dyn"] for r in Q], [r["y"] for r in Q], [r["sid"] for r in Q])
            b = {m: bss([r[m] for r in Q], [r["y"] for r in Q], [r["sid"] for r in Q], B=100)[0] for m in ("dyn", "frz", "map")}
            L.append(f"{'':9s} {lo_:3d}-{hi_:3d} min after the confirmation: states {len(Q):6d}  BSS dyn {100 * b['dyn']:5.1f}%  frozen-films "
                     f"{100 * b['frz']:5.1f}%  frozen-map {100 * b['map']:5.1f}%  | Brier frozen-films minus dyn {1e3 * dq:+.1f}e-3 [{1e3 * ci[0]:+.1f}; {1e3 * ci[1]:+.1f}]")
        if key == "ALL":
            L.append(f"{'':9s} reliability dyn: {reliability([r['dyn'] for r in R], y)}")
            L.append(f"{'':9s} reliability frozen-films: {reliability([r['frz'] for r in R], y)}")
            # the weather: change of the same level's number between two checks 15 minutes apart
            by = {}
            for r in R: by.setdefault((r["sid"], r["role"], round(r["edge"], 2)), []).append(r)
            dd, df = [], []
            for v in by.values():
                v.sort(key=lambda r: r["t"])
                for a, b2 in zip(v, v[1:]):
                    if b2["t"] - a["t"] == 15:
                        dd.append(abs(b2["dyn"] - a["dyn"])); df.append(abs(b2["frz"] - a["frz"]))
            dd, df = np.array(dd), np.array(df)
            L.append(f"{'':9s} weather (same level, 15 min apart): dyn moves {100 * dd.mean():.1f} pp on average, "
                     f"> 10 pp in {100 * (dd > 0.10).mean():.0f}% of steps; frozen films {100 * df.mean():.1f} pp, > 10 pp in {100 * (df > 0.10).mean():.0f}%")
    return "\n".join(L)


if __name__ == "__main__":
    out, t0 = {}, time.time()
    for inst in INST:
        for sess in ("RDR", "ODR"):
            out[f"{inst}-{sess}"] = run(inst, sess)
            print(inst, sess, len(out[f"{inst}-{sess}"]), f"{time.time() - t0:.0f}s", flush=True)
    OUT.write_text(json.dumps(out), encoding="utf-8")
    print(report(out))
