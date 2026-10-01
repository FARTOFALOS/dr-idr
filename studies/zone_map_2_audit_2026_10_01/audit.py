"""The representation check of DR-LAB-ZONE-MAP-2.0 (§43) for its independent audit; aggregates only.

Targets: every session of 2018-2025 with an established confirmation; its family = the sessions of its key strictly
before its date (weekday scope, §2.1) and, apart, the explicit all-weekdays scope (§2.2). For R and X: the zone map of
the family (zonemap.py), where the target's own final event fell (a zone, the residual, unknown), the zones' order in
time, and today's status of every zone (§22-24) at 30, 60 and 120 minutes after the target's own confirmation. A null
diagnostic (§33.2): the same algorithm on families whose sessions were re-signed M5 by M5 (the synthesis' path-null).

    python -B studies/zone_map_2_audit_2026_10_01/audit.py --out studies/zone_map_2_audit_2026_10_01/audit_results.json
"""
import argparse
import hashlib
import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "lab")); sys.path.insert(0, str(HERE))
import scene24 as S  # noqa: E402
import zonemap as Z  # noqa: E402

S.cluster24.of_snapshot = lambda snap, ev: None           # not needed here
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--nullreps", type=int, default=20)
a = ap.parse_args()
SLICES = (30, 60, 120)


def seed(*parts):
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:15], 16)


def members_of(snap):
    out = []
    for m in snap["members"]:
        out.append(dict(id=m["id"], date=m["date"], w=m["w"], act=m["act"],
                        path=np.array([q if q is not None else [np.nan] * 3 for q in m["path"]], dtype=float),
                        R=(m["R"]["s"], m["R"].get("v"), m["R"].get("t")), X=(m["X"]["s"], m["X"].get("v"), m["X"].get("t"))))
    return out


def cell(m, e, formed):
    s, v, t = m[e]
    return ((10 * v) // m["w"], (t - formed) // 15) if s == "known" else None


def flip_cell(m, e, grid, formed, rng):
    """One sign-flip path of a session (each M5 after its activation reflected with p = 1/2), its R or X cell."""
    ja = int(np.searchsorted(grid, m["act"]))
    seg = m["path"][ja + 1:]
    if not len(seg) or np.isnan(seg).any(): return None
    c0 = m["path"][ja, 2]
    prev = np.concatenate([[c0], seg[:-1, 2]])
    dL, dH, dC = seg[:, 0] - prev, seg[:, 1] - prev, seg[:, 2] - prev
    eps = rng.choice((-1.0, 1.0), size=len(seg))
    cl = c0 + np.cumsum(eps * dC)
    pv = np.concatenate([[c0], cl[:-1]])
    lo = pv + np.where(eps > 0, dL, -dH); hi = pv + np.where(eps > 0, dH, -dL)
    j = int(lo.argmin()) if e == "R" else int(hi.argmax())
    v = int(lo[j]) if e == "R" else int(hi[j])
    return ((10 * v) // m["w"], (int(grid[ja + 1 + j]) - 5 - formed) // 15)


def today_status(zm, m, e, grid, formed, end, minutes):
    """Statuses of the zones at the slice = the close act + minutes (§22-24); None when today's horizon has a gap."""
    T = m["act"] + minutes
    if T > end: return None
    sel = (grid > m["act"]) & (grid <= T)
    rows = m["path"][sel]
    if not len(rows) or np.isnan(rows).any(): return None
    col = rows[:, 0] if e == "R" else rows[:, 1]
    j = int(col.argmin()) if e == "R" else int(col.argmax())
    v = int(col[j]); t_open = int(grid[sel][j]) - 5
    q = ((10 * v) // m["w"], (t_open - formed) // 15)
    return [Z.status(z["mask"], q, 10 * v, m["w"], T, formed, end - 5, e) for z in zm["zones"]]


t0 = time.time()
recs, null_rows = [], []
for inst in ("NQ", "ES", "YM"):
    B = S._base(inst)
    for session in ("ADR", "ODR", "RDR"):
        _, formed, end = S.SESS[session]
        miss, shift = S._missing(inst, B, session), S.SHIFT[session]
        keys = set()
        for i, m in enumerate(B["boxes"]):
            if m["session"] != session or m["conf"] is None: continue
            conf = int(m["conf"]) - shift
            if any(T < conf for T in miss.get(i, [])): continue
            keys.add((m["weekday"], m["side"], S.window_of(conf, formed)))
        fam, grid = {}, None
        for key in sorted(keys):
            snap = S._snapshot(inst, B, session, *key[:2], "conf", key[2], "9999-12-31")
            S._SNAP.clear()
            grid = np.array(snap["grid"])
            fam[key] = members_of(snap)
        allw = defaultdict(list)                        # the explicit all-weekdays scope: same side and window
        for (wd, side, win), ms in fam.items(): allw[(side, win)] += ms
        for k in allw: allw[k].sort(key=lambda m: m["date"])
        for (wd, side, win), ms in fam.items():
            aw = allw[(side, win)]
            for j, m in enumerate(ms):
                if m["date"] < "2018-01-01" or j == 0: continue
                fam_wd = ms[:j]
                fam_aw = [x for x in aw if x["date"] < m["date"]]
                for e in ("R", "X"):
                    tgt = cell(m, e, formed)
                    if m[e][0] == "unknown": continue
                    row = dict(inst=inst, s=session, ev=e, win=win, date=m["date"])
                    for scope, F in (("wd", fam_wd), ("aw", fam_aw)):
                        pts = [(c[0], c[1], x["id"]) for x in F for c in [cell(x, e, formed)] if c is not None]
                        zm = Z.zone_map(pts, len(F))
                        zs = [dict(n=z["n"], rel=z["b0"] - (win), cells=len(z["mask"]), pieces=z["pieces"],
                                   hit=int(tgt is not None and tgt in z["mask"])) for z in zm["zones"]]
                        row[scope] = dict(N=len(F), zones=zs, resid=len(zm["residual"]))
                        if scope == "wd":
                            row["status"] = {str(mm): today_status(zm, m, e, grid, formed, end, mm) for mm in SLICES}
                    recs.append(row)
        # §33.2: the algorithm on a path-null corpus, families of 60+ as of the end of the base (weekday scope)
        for key, ms in fam.items():
            if len(ms) < 60: continue
            for e in ("R", "X"):
                real = Z.zone_map([(c[0], c[1], x["id"]) for x in ms for c in [cell(x, e, formed)] if c is not None], len(ms))
                rng = np.random.default_rng(seed("zm2-null", inst, session, key, e))
                nz, mass, late = [], [], []
                for _ in range(a.nullreps):
                    pts = [(c[0], c[1], x["id"]) for x in ms for c in [flip_cell(x, e, grid, formed, rng) if x[e][0] == "known" else None] if c is not None]
                    zz = Z.zone_map(pts, len(ms))
                    nz.append(len(zz["zones"])); mass.append(sum(z["n"] for z in zz["zones"]) / len(ms))
                    late.append(sum(1 for z in zz["zones"] if z["b0"] - key[2] >= 4))
                null_rows.append(dict(s=session, ev=e, N=len(ms), real_n=len(real["zones"]), real_mass=sum(z["n"] for z in real["zones"]) / len(ms),
                                      real_late=sum(1 for z in real["zones"] if z["b0"] - key[2] >= 4),
                                      null_n=float(np.mean(nz)), null_mass=float(np.mean(mass)), null_late=float(np.mean(late))))
        print(inst, session, len(recs), "%.0fs" % (time.time() - t0), flush=True)


def yb(rows, f, g=None):
    """Mean of f over rows (optionally a ratio of means f / g), 5-95 % by resampling whole years."""
    yrs = np.array([int(r["date"][:4]) for r in rows]); uy = np.unique(yrs)
    fv = np.array([f(r) for r in rows], float); gv = np.array([g(r) for r in rows], float) if g else None
    val = fv.mean() / gv.mean() if g else fv.mean()
    rng = np.random.default_rng(1); bs = []
    for _ in range(300):
        idx = np.concatenate([np.flatnonzero(yrs == y) for y in rng.choice(uy, len(uy))])
        bs.append(fv[idx].mean() / gv[idx].mean() if g else fv[idx].mean())
    return [round(float(val), 4), [round(float(x), 4) for x in np.percentile(bs, [5, 95])]]


res = dict(targets=len(recs), by={}, status={}, null={}, pieces=None)
grp = defaultdict(list)
for r in recs: grp[(r["s"], r["ev"])].append(r)
for (s, e), rows in sorted(grp.items()):
    for scope in ("wd", "aw"):
        for lab, sub in (("all", rows), ("N60+", [r for r in rows if r[scope]["N"] >= 60])):
            if len(sub) < 30: continue
            out = dict(n=len(sub), medianN=int(np.median([r[scope]["N"] for r in sub])))
            out["zones_per_family"] = {str(k): round(v / len(sub), 4) for k, v in sorted(Counter(min(len(r[scope]["zones"]), 4) for r in sub).items())}
            out["zone_mass"] = yb(sub, lambda r: sum(z["n"] for z in r[scope]["zones"]) / r[scope]["N"])
            out["landed_in_a_zone"] = yb(sub, lambda r: sum(z["hit"] for z in r[scope]["zones"]))
            out["coverage_ratio"] = yb(sub, lambda r: sum(z["hit"] for z in r[scope]["zones"]), lambda r: sum(z["n"] for z in r[scope]["zones"]) / r[scope]["N"])
            # by position in time: zones starting in the family's first hour against later ones
            for pos, test in (("first_hour", lambda z: z["rel"] < 4), ("later", lambda z: z["rel"] >= 4)):
                zs_rows = [r for r in sub if any(test(z) for z in r[scope]["zones"])]
                if len(zs_rows) >= 30:
                    out[pos] = dict(families=len(zs_rows), mass=yb(zs_rows, lambda r: sum(z["n"] for z in r[scope]["zones"] if test(z)) / r[scope]["N"]),
                                    landed=yb(zs_rows, lambda r: sum(z["hit"] for z in r[scope]["zones"] if test(z))),
                                    ratio=yb(zs_rows, lambda r: sum(z["hit"] for z in r[scope]["zones"] if test(z)), lambda r: sum(z["n"] for z in r[scope]["zones"] if test(z)) / r[scope]["N"]))
            res["by"][f"{s} {e} {scope} {lab}"] = out
    # today's status (weekday scope): how often, and how often each later realised (a study figure, not a screen number)
    st = {}
    for mm in SLICES:
        c = Counter(); hit = Counter()
        for r in rows:
            ss = r["status"].get(str(mm))
            if not ss: continue
            for z, x in zip(r["wd"]["zones"], ss): c[x] += 1; hit[x] += z["hit"]
        tot = sum(c.values())
        if tot: st[str(mm)] = {x: [round(c[x] / tot, 4), round(hit[x] / c[x], 4) if c[x] else None] for x in ("HOLDS", "POSSIBLE", "IMPOSSIBLE")}
    res["status"][f"{s} {e}"] = st
allz = [z for r in recs for z in r["wd"]["zones"]]
res["pieces"] = dict(zones=len(allz), split=round(sum(z["pieces"] > 1 for z in allz) / max(1, len(allz)), 4))
ng = defaultdict(list)
for r in null_rows: ng[(r["s"], r["ev"])].append(r)
for (s, e), rows in sorted(ng.items()):
    m = lambda k: round(float(np.mean([r[k] for r in rows])), 3)
    res["null"][f"{s} {e}"] = dict(families=len(rows), medianN=int(np.median([r["N"] for r in rows])),
                                   zones_real=m("real_n"), zones_null=m("null_n"), mass_real=m("real_mass"), mass_null=m("null_mass"),
                                   later_zones_real=m("real_late"), later_zones_null=m("null_late"))
Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("done %.0fs" % (time.time() - t0))
