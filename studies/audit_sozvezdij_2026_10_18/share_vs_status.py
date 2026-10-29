"""Audit 2026-10-18 (meaning/lens/2026-10-18-audit-sozvezdij/), aggregates only: on screen 24 a constellation's label
is its family share n/N; its status (HOLDS / POSSIBLE / IMPOSSIBLE) is today's reachability. How did the displayed
share compare with what then happened?

Prefix-honest like studies/zone_map_3_2026_10_01/check.py: targets = sessions 2018-2025 with an established
confirmation; the family of a target = its key strictly before its date (weekday scope = the screen's default; the
all-weekdays scope apart, for the whole-map transfer only); zones by lab/zonemap24.zone_map; the target's own final
R / X decides whether a zone was realised; status at 30 / 60 / 120 minutes after the target's confirmation by
lab/zonemap24.status. Exploration: this corpus has been seen by the whole line (meaning/12 §4).

    python -B studies/audit_sozvezdij_2026_10_18/share_vs_status.py --out studies/audit_sozvezdij_2026_10_18/share_vs_status.json   # ~10 min
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "lab"))
import scene24 as S  # noqa: E402
import zonemap24 as Z  # noqa: E402

S.cluster24.of_snapshot = lambda snap, ev: None
SLICES = (30, 60, 120)
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); OUT = ap.parse_args().out


def members_of(snap):
    out = []
    for m in snap["members"]:
        out.append(dict(id=m["id"], date=m["date"], w=m["w"], act=m["act"], order=m["order"],
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


# acc[(N class, ev, minutes, status, zone class)] = [zones, sum of displayed shares, realised]
acc = defaultdict(lambda: [0, 0.0, 0])
mass = defaultdict(lambda: [0, 0.0, 0])          # whole map: targets, sum of zone mass, landed in any zone
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
        nb = (end - formed) // 15
        for (wd, side, win), ms in fam.items():
            b_lo, b_hi = (15 * win + 5) // 15, (end - 5 - formed) // 15
            aw = allw[(side, win)]
            for j, m in enumerate(ms):
                if m["date"] < "2018-01-01" or j == 0: continue
                for e in ("R", "X"):
                    if m[e][0] == "unknown": continue
                    tgt = cell(m, e, formed)
                    for scope, F in (("weekday", ms[:j]), ("all", [x for x in aw if x["date"] < m["date"]])):
                        N = len(F)
                        if N < 20: continue
                        ncls = "N>=60" if N >= 60 else "N20-59"
                        pts = [(c[0], c[1], x["id"]) for x in F for c in [cell(x, e, formed)] if c is not None]
                        zm = Z.zone_map(pts, N, b_lo, b_hi)
                        zs = []
                        for z in zm["zones"]:
                            cs = set(map(tuple, z["cells"]))
                            cls = "early" if z["time"][0] <= win + 1 else "late" if z["time"][1] >= nb else "middle"
                            zs.append((z, cs, cls, int(tgt is not None and tuple(tgt) in cs)))
                        mk = (scope, ncls, session, e)
                        mass[mk][0] += 1; mass[mk][1] += sum(z["n"] for z in zm["zones"]) / N; mass[mk][2] += int(any(h for *_, h in zs))
                        if scope != "weekday": continue
                        for mm in SLICES:
                            q = today(m, e, grid, formed, end, mm)
                            if q is None: continue
                            for z, cs, cls, hit in zs:
                                st = Z.status(z["cells"], e, tuple(q[0]), q[1], m["w"], q[2], formed, end - 5)
                                for c2 in (cls, "any"):
                                    a = acc[(ncls, e, mm, st, c2)]
                                    a[0] += 1; a[1] += z["n"] / N; a[2] += hit
        print(inst, session, "done", flush=True)

res = dict(status={}, transfer={})
for (ncls, e, mm, st, cls), (n, s, h) in sorted(acc.items()):
    res["status"][f"{ncls} {e} {mm}min {st} {cls}"] = dict(zones=n, mean_share=round(s / n, 4), realised=round(h / n, 4))
for (scope, ncls, session, e), (n, s, h) in sorted(mass.items()):
    res["transfer"][f"{scope} {ncls} {session} {e}"] = dict(targets=n, mean_mass=round(s / n, 4), landed=round(h / n, 4), ratio=round(h / s, 3) if s else None)
Path(OUT).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("written", OUT)
