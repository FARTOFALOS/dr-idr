"""Representation check of `zone-map-3` (lab/zonemap24.py) on 2018-2025, exploratory: this corpus has been seen by the
whole line (meaning/12 §5). Aggregates only.

Targets: every session of 2018-2025 with an established confirmation; its family = its key strictly before its date,
weekday scope and, apart, the explicit all-weekdays scope. Per target and event: the zones of the family, where the
target's own final event fell, today's status of every zone 30 / 60 / 120 minutes after the target's confirmation,
and the simpler displays the frozen acceptance compares against: a fixed early block (the most frequent first-hour
position of 2006-2017, fixed in studies/cluster_synthesis_audit_2026_10_01), the first hour at any price (time only),
the family's modal 0.5-wide band over the whole session (price only). The null diagnostic: the same zone map on
sign-flipped copies of the families of 60+ as of the end of the base.

    python -B studies/zone_map_3_2026_10_01/check.py --out studies/zone_map_3_2026_10_01/check_results.json
"""
import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "lab"))
import scene24 as S  # noqa: E402
import zonemap24 as Z  # noqa: E402

S.cluster24.of_snapshot = lambda snap, ev: None
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--nullreps", type=int, default=20)
a = ap.parse_args()
TEMPLATE = json.loads((ROOT / "studies/cluster_synthesis_audit_2026_10_01/audit_results.json").read_text(encoding="utf-8"))["template"]
SLICES = (30, 60, 120)


def members_of(snap):
    out = []
    for m in snap["members"]:
        out.append(dict(id=m["id"], date=m["date"], w=m["w"], act=m["act"],
                        path=np.array([q if q is not None else [np.nan] * 3 for q in m["path"]], dtype=float),
                        R=(m["R"]["s"], m["R"].get("v"), m["R"].get("t")), X=(m["X"]["s"], m["X"].get("v"), m["X"].get("t"))))
    return out


def cell(m, e, formed):
    s, v, t = m[e]
    return Z.cell_of(v, m["w"], t, formed) if s == "known" else None


def today(m, e, grid, formed, end, minutes):
    T = m["act"] + minutes
    if T > end: return None
    sel = (grid > m["act"]) & (grid <= T)
    rows = m["path"][sel]
    if not len(rows) or np.isnan(rows).any(): return None
    col = rows[:, 0] if e == "R" else rows[:, 1]
    j = int(col.argmin()) if e == "R" else int(col.argmax())
    v = int(col[j]); t_open = int(grid[sel][j]) - 5
    return Z.cell_of(v, m["w"], t_open, formed), 10 * v, T


t0 = time.time()
recs, nulls = [], []
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
            snap = S._snapshot(inst, B, session, key[0], key[1], "conf", key[2], "9999-12-31")
            S._SNAP.clear()
            grid = np.array(snap["grid"]); fam[key] = members_of(snap)
        allw = defaultdict(list)
        for (wd, side, win), ms in fam.items(): allw[(side, win)] += ms
        for k in allw: allw[k].sort(key=lambda m: m["date"])
        for (wd, side, win), ms in fam.items():
            b_lo, b_hi = (15 * win + 5) // 15, (end - 5 - formed) // 15
            aw = allw[(side, win)]
            for j, m in enumerate(ms):
                if m["date"] < "2018-01-01" or j == 0: continue
                for e in ("R", "X"):
                    if m[e][0] == "unknown": continue
                    tgt = cell(m, e, formed)
                    row = dict(inst=inst, s=session, ev=e, win=win, date=m["date"])
                    for scope, F in (("wd", ms[:j]), ("aw", [x for x in aw if x["date"] < m["date"]])):
                        pts = [(c[0], c[1], x["id"]) for x in F for c in [cell(x, e, formed)] if c is not None]
                        zm = Z.zone_map(pts, len(F), b_lo, b_hi)
                        N = len(F)
                        zs = [dict(n=z["n"], early=z["time"][0] - b_lo < 4, cells=len(z["cells"]), hit=int(tgt is not None and tuple(tgt) in set(map(tuple, z["cells"])))) for z in zm["zones"]]
                        # the background: the cells of the family's own range (its events' prices +-1 cell x its time) outside the zones
                        ks = [p[0] for p in pts]
                        dom = (max(ks) - min(ks) + 3) * (b_hi - b_lo + 1) if ks else 0
                        inz = set(c for z in zm["zones"] for c in map(tuple, z["cells"]))
                        in_dom = tgt is not None and ks and min(ks) - 1 <= tgt[0] <= max(ks) + 1 and b_lo <= tgt[1] <= b_hi
                        row[scope] = dict(N=N, zones=zs, resid=len(zm["residual"]), bg_cells=max(1, dom - len(inz)),
                                          bg_hit=int(bool(in_dom) and tuple(tgt) not in inz and not any(z["hit"] for z in zs)))
                        if scope == "wd":
                            tk, tb = TEMPLATE[f"{session} {e}"]
                            T0 = [(k, b) for k in range(tk, tk + 5) for b in range(b_lo + tb, b_lo + tb + 4)]
                            T0s = set(T0)
                            row["tpl"] = dict(mass=sum(1 for p in pts if (p[0], p[1]) in T0s) / N, hit=int(tgt is not None and tuple(tgt) in T0s))
                            row["time_only"] = dict(mass=sum(1 for p in pts if b_lo <= p[1] < b_lo + 4) / N, hit=int(tgt is not None and b_lo <= tgt[1] < b_lo + 4))
                            if pts:
                                # the same area as the zones, chosen from the two histograms alone (price x time, no joint structure)
                                kc, tcn = Counter(p[0] for p in pts), Counter(p[1] for p in pts)
                                area = len(inz)
                                cand = [(kc[k] * tcn[b], k, b) for k in range(min(kc) - 1, max(kc) + 2) for b in range(b_lo, b_hi + 1) if kc[k] * tcn[b] > 0]
                                cand.sort(key=lambda x: (-x[0], x[2], abs(2 * x[1] + 1), x[1]))
                                top = {(k, b) for _, k, b in cand[:area]}
                                row["marg"] = dict(area=area, hit_zone=int(any(z["hit"] for z in zs)), hit_marg=int(tgt is not None and tuple(tgt) in top))
                                best = max(range(min(kc) - 4, max(kc) + 1), key=lambda q: (sum(kc.get(x, 0) for x in range(q, q + 5)), -abs(2 * q + 5)))
                                row["price_only"] = dict(mass=sum(kc.get(x, 0) for x in range(best, best + 5)) / N, hit=int(tgt is not None and best <= tgt[0] < best + 5))
                            st = {}
                            for mm in SLICES:
                                q = today(m, e, grid, formed, end, mm)
                                if q is None: continue
                                st[str(mm)] = [Z.status(z["cells"], e, tuple(q[0]), q[1], m["w"], q[2], formed, end - 5) for z in zm["zones"]]
                            row["status"] = st
                    recs.append(row)
        for key, ms in fam.items():                             # §33.2 on the families of 60+ as of the end of the base
            if len(ms) < 60: continue
            b_lo, b_hi = (15 * key[2] + 5) // 15, (end - 5 - formed) // 15
            for e in ("R", "X"):
                real = Z.zone_map([(c[0], c[1], x["id"]) for x in ms for c in [cell(x, e, formed)] if c is not None], len(ms), b_lo, b_hi)
                rng = np.random.default_rng(Z.seed("check-null", inst, session, key, e))
                nz, mass, late = [], [], []
                for _ in range(a.nullreps):
                    pts = []
                    for x in ms:
                        if x[e][0] != "known": continue
                        ai = int(np.searchsorted(grid, x["act"]))
                        vals, idx = Z._flip(x["path"], ai, rng, 1, e)
                        pts.append((*Z.cell_of(int(vals[0]), x["w"], int(grid[ai + 1 + idx[0]]) - 5, formed), x["id"]))
                    zz = Z.zone_map(pts, len(ms), b_lo, b_hi)
                    nz.append(len(zz["zones"])); mass.append(sum(z["n"] for z in zz["zones"]) / len(ms)); late.append(sum(1 for z in zz["zones"] if z["time"][0] - b_lo >= 4))
                nulls.append(dict(s=session, ev=e, real_n=len(real["zones"]), real_mass=sum(z["n"] for z in real["zones"]) / len(ms),
                                  real_late=sum(1 for z in real["zones"] if z["time"][0] - b_lo >= 4), null_n=float(np.mean(nz)), null_mass=float(np.mean(mass)), null_late=float(np.mean(late))))
        print(inst, session, len(recs), "%.0fs" % (time.time() - t0), flush=True)


def yb(rows, f, g=None):
    yrs = np.array([int(r["date"][:4]) for r in rows]); uy = np.unique(yrs)
    fv = np.array([f(r) for r in rows], float); gv = np.array([g(r) for r in rows], float) if g else None
    val = fv.mean() / gv.mean() if g else fv.mean()
    rng = np.random.default_rng(1); bs = []
    for _ in range(300):
        idx = np.concatenate([np.flatnonzero(yrs == y) for y in rng.choice(uy, len(uy))])
        bs.append(fv[idx].mean() / gv[idx].mean() if g else fv[idx].mean())
    return [round(float(val), 4), [round(float(x), 4) for x in np.percentile(bs, [5, 95])]]


res = dict(version=Z.VERSION, targets=len(recs), by={}, comparators={}, status={}, null={})
grp = defaultdict(list)
for r in recs: grp[(r["s"], r["ev"])].append(r)
for (s, e), rows in sorted(grp.items()):
    for scope in ("wd", "aw"):
        for lab, sub in (("all", rows), ("N60+", [r for r in rows if r[scope]["N"] >= 60])):
            if len(sub) < 30: continue
            o = dict(n=len(sub), medianN=int(np.median([r[scope]["N"] for r in sub])),
                     zones_per_family={str(k): round(v / len(sub), 4) for k, v in sorted(Counter(min(len(r[scope]["zones"]), 4) for r in sub).items())},
                     mass=yb(sub, lambda r: sum(z["n"] for z in r[scope]["zones"]) / r[scope]["N"]),
                     landed=yb(sub, lambda r: sum(z["hit"] for z in r[scope]["zones"])),
                     ratio=yb(sub, lambda r: sum(z["hit"] for z in r[scope]["zones"]), lambda r: sum(z["n"] for z in r[scope]["zones"]) / r[scope]["N"]),
                     # forward density inside zones against the family's own background (per cell)
                     lift=yb(sub, lambda r: sum(z["hit"] for z in r[scope]["zones"]) / max(1, sum(z["cells"] for z in r[scope]["zones"])),
                             lambda r: r[scope]["bg_hit"] / r[scope]["bg_cells"]))
            for pos, test in (("early", lambda z: z["early"]), ("late", lambda z: not z["early"])):
                zr = [r for r in sub if any(test(z) for z in r[scope]["zones"])]
                if len(zr) >= 30:
                    o[pos] = dict(families=len(zr), mass=yb(zr, lambda r: sum(z["n"] for z in r[scope]["zones"] if test(z)) / r[scope]["N"]),
                                  landed=yb(zr, lambda r: sum(z["hit"] for z in r[scope]["zones"] if test(z))),
                                  ratio=yb(zr, lambda r: sum(z["hit"] for z in r[scope]["zones"] if test(z)), lambda r: sum(z["n"] for z in r[scope]["zones"] if test(z)) / r[scope]["N"]))
            res["by"][f"{s} {e} {scope} {lab}"] = o
    sub = [r for r in rows if r["wd"]["N"] >= 60]
    if len(sub) >= 30:
        c = {}
        for nm in ("tpl", "time_only", "price_only"):
            ss = [r for r in sub if nm in r]
            c[nm] = dict(mass=yb(ss, lambda r: r[nm]["mass"]), landed=yb(ss, lambda r: r[nm]["hit"]), ratio=yb(ss, lambda r: r[nm]["hit"], lambda r: r[nm]["mass"]))
        mg = [r for r in sub if "marg" in r and r["marg"]["area"]]
        c["equal_area_histograms"] = dict(zones_landed=yb(mg, lambda r: r["marg"]["hit_zone"]), histograms_landed=yb(mg, lambda r: r["marg"]["hit_marg"]),
                                          zones_minus_histograms=yb(mg, lambda r: r["marg"]["hit_zone"] - r["marg"]["hit_marg"]))
        early = [r for r in sub if any(z["early"] for z in r["wd"]["zones"])]
        c["early_zone_minus_template_landed"] = yb(early, lambda r: sum(z["hit"] for z in r["wd"]["zones"] if z["early"]) - r["tpl"]["hit"])
        res["comparators"][f"{s} {e} N60+"] = c
    st = {}
    for mm in SLICES:
        cnt, hit = Counter(), Counter()
        for r in rows:
            ss = r["status"].get(str(mm))
            if not ss: continue
            for z, x in zip(r["wd"]["zones"], ss): cnt[x] += 1; hit[x] += z["hit"]
        tot = sum(cnt.values())
        if tot: st[str(mm)] = {x: [round(cnt[x] / tot, 4), round(hit[x] / cnt[x], 4) if cnt[x] else None] for x in ("HOLDS", "POSSIBLE", "IMPOSSIBLE")}
    res["status"][f"{s} {e}"] = st
ng = defaultdict(list)
for r in nulls: ng[(r["s"], r["ev"])].append(r)
for (s, e), rows in sorted(ng.items()):
    m = lambda k: round(float(np.mean([r[k] for r in rows])), 3)
    res["null"][f"{s} {e}"] = dict(families=len(rows), zones_real=m("real_n"), zones_null=m("null_n"), mass_real=m("real_mass"),
                                   mass_null=m("null_mass"), late_real=m("real_late"), late_null=m("null_late"))
Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("done %.0fs" % (time.time() - t0))
