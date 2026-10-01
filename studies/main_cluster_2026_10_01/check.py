"""Check of the main-cluster rule (lab/cluster24.py) on sessions the rule was not tuned on: meaning/11-glavnyj-klaster.md.

Every session of the period with an established first confirmation is a target of its own family: the key's sessions
strictly before its date, exactly the snapshot the screen shows on that day (lab/scene24.py). The rule runs on that
family; the target's own event says whether the place held. Per-target rows are derived from the tape and stay local
(--rows, outside the repository); only the aggregates below are kept.

    python -B studies/main_cluster_2026_10_01/check.py --lo 2018-01-01 --hi 2025-12-31 --out <aggregates.json>
    python -B studies/main_cluster_2026_10_01/check.py ... --after 4      # the inside of the session (M4)
"""
import argparse
import json
import os
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "lab"))
import cluster24 as C  # noqa: E402
import scene24 as S  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--lo", required=True)
ap.add_argument("--hi", required=True)
ap.add_argument("--after", type=int, default=0, help="the candidate only from this many 15-minute cells after the family's first block")
ap.add_argument("--inst", default="NQ,ES,YM")
ap.add_argument("--sess", default="ADR,ODR,RDR")
ap.add_argument("--rows", default=os.path.join(tempfile.gettempdir(), "dr_main_cluster_rows.json"))
ap.add_argument("--out", required=True)
a = ap.parse_args()

BOOT_Y, SEED = 300, 1
MIN_N = 2 * C.MIN_NEW


def keys(inst, session, B):
    formed, shift = S.SESS[session][1], S.SHIFT[session]
    miss = S._missing(inst, B, session)
    out = set()
    for i, m in enumerate(B["boxes"]):
        if m["session"] != session or m["conf"] is None: continue
        conf = int(m["conf"]) - shift
        if any(T < conf for T in miss.get(i, [])): continue          # first confirmation not established: no family
        out.add((m["weekday"], m["side"], S.window_of(conf, formed)))
    return sorted(out)


def inside(c, k0, b0):
    return c is not None and k0 <= c[0] < k0 + C.KB and b0 <= c[1] < b0 + C.TB


def run():
    rows, t0 = [], time.time()
    for inst in a.inst.split(","):
        B = S._base(inst)
        for session in a.sess.split(","):
            _, formed, end = S.SESS[session]
            for wd, side, win in keys(inst, session, B):
                snap = S._snapshot(inst, B, session, wd, side, "conf", win, "9999-12-31")   # every date of the key
                S._SNAP.clear()
                mem, grid = snap["members"], snap["grid"]                                  # in date order
                b_min, b_max = C._span(formed, end, win, 0)
                for ev in ("R", "X"):
                    pts = C.compact(mem, ev, grid)
                    for j in range(1, len(mem)):
                        if not (a.lo <= mem[j]["date"] <= a.hi): continue
                        r = C.main_cluster(pts[:j], ev, formed, end, win, full=False, after=a.after)
                        tg = pts[j]
                        if "block" not in r or tg[0] == "u": continue                       # no candidate / unknown target
                        k0, b0 = r["block"]["k0"], r["block"]["b0"]
                        c = None if tg[0] == "n" else ((10 * tg[1]) // tg[2], (tg[3] - formed) // C.WINDOW)
                        nbs = [(k0 - C.KB, b0), (k0 + C.KB, b0)] + [(k0, b0 + s) for s in (-C.TB, C.TB) if b_min <= b0 + s <= b_max]
                        rows.append(dict(inst=inst, s=session, ev=ev, key=[wd, side, win], date=mem[j]["date"], N=j,
                                         st=r["status"], failed=r["failed"], yes=r["yes"], k0=k0, b0=b0, first=b0 == b_min,
                                         hit=int(inside(c, k0, b0)), nb=len(nbs), nbhit=sum(int(inside(c, *q)) for q in nbs)))
            print(inst, session, len(rows), "rows", "%.0fs" % (time.time() - t0), flush=True)
    return rows


def _div(x, y):
    return x / y if y > 0 else (np.inf if x > 0 else np.nan)


def _num(x, d=3):
    return None if np.isnan(x) else "∞" if np.isinf(x) else round(float(x), d)


def stats(rs):
    """Family share, landing share, their ratio and the contrast against a neighbouring block, with 5-95 % intervals
    from resampling whole years (the interval ends are resampled values, no interpolation)."""
    if not rs: return dict(n=0), None
    st = np.array([r["yes"] / r["N"] for r in rs]); hit = np.array([r["hit"] for r in rs], float)
    nb = np.array([r["nbhit"] / r["nb"] for r in rs])
    yrs = np.array([int(r["date"][:4]) for r in rs]); uy = np.unique(yrs)
    rng = np.random.default_rng(SEED); ratio, contrast = [], []
    for _ in range(BOOT_Y):
        idx = np.concatenate([np.flatnonzero(yrs == y) for y in rng.choice(uy, len(uy))])
        ratio.append(hit[idx].mean() / st[idx].mean())
        contrast.append(_div(hit[idx].mean(), nb[idx].mean()))
    contrast = np.nan_to_num(np.array(contrast), nan=0.0, posinf=np.inf)
    q = lambda v: [_num(x) for x in np.percentile(v, [5, 95], method="lower")]
    c = _div(hit.mean(), nb.mean())
    raw = dict(contrast=c, contrast_lo=float(np.percentile(contrast, 5, method="lower")))
    return dict(n=len(rs), families=len({(r["inst"], r["s"], r["ev"], tuple(r["key"])) for r in rs}),
                family_share=_num(st.mean(), 4), landed=_num(hit.mean(), 4),
                ratio=_num(hit.mean() / st.mean()), ratio_5_95=q(ratio),
                neighbour=_num(nb.mean(), 4), contrast=_num(c), contrast_5_95=q(contrast),
                first_block=_num(np.mean([r["first"] for r in rs]))), raw


def aggregate(rows):
    out = dict(period=[a.lo, a.hi], after=a.after, rule=C.RULE, block=[C.KB, C.TB], targets={}, earned={}, not_earned_60={}, M1={})
    by = defaultdict(list)
    for r in rows: by[(r["s"], r["ev"])].append(r)
    for (s, ev), rs in sorted(by.items()):
        k = f"{s} {ev}"
        e = [r for r in rs if r["st"] == "earned"]
        out["targets"][k] = dict(n=len(rs), earned=len(e), n60=sum(r["N"] >= MIN_N for r in rs), earned_share=round(len(e) / len(rs), 4))
        out["earned"][k] = stats(e)[0]
        out["not_earned_60"][k] = stats([r for r in rs if r["st"] != "earned" and r["N"] >= MIN_N])[0]
    for s in sorted({r["s"] for r in rows}):
        m, raw = stats([r for r in rows if r["s"] == s and r["st"] == "earned"])
        verdict = "не проверено" if m["n"] < 100 else ("выдержано" if raw["contrast"] >= 1.5 and raw["contrast_lo"] > 1.0 else "не выдержано")
        out["M1"][s] = dict(verdict=verdict, **m)
    return out


rows = run()
with open(a.rows, "w", encoding="utf-8") as f: json.dump(rows, f)
res = aggregate(rows)
with open(a.out, "w", encoding="utf-8") as f: json.dump(res, f, ensure_ascii=False, indent=1)
for s, m in res["M1"].items():
    print(s, m["verdict"], "n", m["n"], "contrast", m.get("contrast"), m.get("contrast_5_95"), "ratio", m.get("ratio"), m.get("ratio_5_95"))
