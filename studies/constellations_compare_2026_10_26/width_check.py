"""Discriminating check for the 26.10 comparison: is CN-1's more honest top zone a better geometry, or just a wider zone?
zm3 as on screen; zm3 with every zone widened by one cell ring (0.1 SD, 15 min; rings never cross into another zone);
cn1. Same targets (weekday families, ODR/RDR, NQ/ES/YM, every 2nd target). Area in SD x minutes, clipped to the block.
Aggregates only: width_results.json. python -B studies/constellations_compare_2026_10_26/width_check.py"""
import json
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lab"))
import compare as C  # noqa: E402
import cn1_probe as CN  # noqa: E402

OUT = str(C.HERE / "width_results.json")


def zm3_zones(P, N, b_lo, b_hi, ring):
    m = C.Z.zone_map([(p["k"], p["b"], p["id"]) for p in P], N, b_lo, b_hi)
    base = [set(map(tuple, z["cells"])) for z in m["zones"]]
    if ring:
        grown = []
        for cs in base:
            g = {(k + dk, b + db) for k, b in cs for dk in (-1, 0, 1) for db in (-1, 0, 1) if b_lo <= b + db <= b_hi}
            grown.append(g)
        claim = defaultdict(int)
        for g in grown:
            for c in g: claim[c] += 1
        core = set().union(*base) if base else set()
        base = [cs | {c for c in g if claim[c] == 1 and c not in core} for cs, g in zip(base, grown)]
    pts = defaultdict(set)
    for p in P: pts[(p["k"], p["b"])].add(p["id"])
    out = []
    for cs in base:
        mem = set().union(*(pts.get(c, set()) for c in cs)) if cs else set()
        out.append(dict(cells=cs, members=mem, area=1.5 * len(cs), hit=(lambda cc: lambda t: (t["k"], t["b"]) in cc)(cs)))
    return out


def cn1_zones(P, N, t0, t1):
    pts = [CN.Point(p["id"], p["v"], p["w"], p["t"]) for p in P]
    res = CN.cn(pts, N)
    out = []
    for z in res["zones"]:
        cores = res["all_cores"][z["component"]]
        us = [float(q.u) for q in cores]; ts = [q.t for q in cores]
        u0, ua = min(us) - 0.15, max(us) + 0.15
        a0, a1 = max(min(ts) - 20, t0), min(max(ts) + 20, t1)
        if a1 <= a0: area = 0.0
        else:
            nu, nt = int(round((ua - u0) / 0.01)) + 1, a1 - a0 + 1
            G = np.zeros((nu, nt), dtype=bool)
            for u, t in zip(us, ts):
                i0, i1 = int(round((u - 0.15 - u0) / 0.01)), int(round((u + 0.15 - u0) / 0.01))
                j0, j1 = max(t - 20, a0) - a0, min(t + 20, a1) - a0
                if j1 >= j0: G[i0:i1 + 1, j0:j1 + 1] = True
            area = G.sum() * 0.01 * 1.0
        comp = z["component"]
        out.append(dict(members=set(z["members"]), area=area,
                        hit=(lambda c: lambda t: CN.region_owner(CN.Point("target", t["v"], t["w"], t["t"]), res) == c)(comp)))
    return out


def job(args):
    inst, session = args
    fam, _ = C.families(inst, session)
    _, formed, end = C.S.SESS[session]
    acc = defaultdict(lambda: defaultdict(float))
    for (wd, side, win), ms in fam.items():
        b_lo, b_hi = win, (end - 5 - formed) // 15
        t0, t1 = formed + 15 * b_lo, end
        for j, m in enumerate(ms):
            if m["date"] < C.FROM or j == 0 or j % 2: continue
            c = C.ncls(j)
            if c is None: continue
            for e in C.EVENTS:
                tgt = m[e]
                if tgt is None: continue
                P = [x[e] for x in ms[:j] if x[e] is not None]
                for name, zs in (("zm3", zm3_zones(P, j, b_lo, b_hi, False)), ("zm3ring", zm3_zones(P, j, b_lo, b_hi, True)),
                                 ("cn1", cn1_zones(P, j, t0, t1))):
                    a = acc[f"{name}|{e}|{c}"]
                    a["targets"] += 1
                    mem = set().union(*(z["members"] for z in zs)) if zs else set()
                    a["mass"] += len(mem) / j
                    a["area"] += sum(z["area"] for z in zs)
                    hit_any = any(z["hit"](tgt) for z in zs)
                    a["landed"] += int(hit_any)
                    if zs:
                        top = max(zs, key=lambda z: len(z["members"]))
                        th = bool(top["hit"](tgt))
                        a["top_n"] += 1
                        a["top_mass"] += len(top["members"]) / j
                        a["top_area"] += top["area"]
                        a["top_landed"] += int(th)
                        a["rest_mass"] += (len(mem) - len(top["members"])) / j
                        a["rest_landed"] += int(hit_any and not th)
    return {k: dict(v) for k, v in acc.items()}


if __name__ == "__main__":
    total = defaultdict(lambda: defaultdict(float))
    with ProcessPoolExecutor(max_workers=3) as ex:
        for acc in ex.map(job, [(i, s) for i in C.INSTS for s in C.SESSIONS]):
            for k, v in acc.items():
                for f, x in v.items(): total[k][f] += x
    res = {}
    for k, v in sorted(total.items()):
        n = v["targets"]
        res[k] = dict(targets=int(n), shown=v["mass"] / n, area=v["area"] / n, honesty=v["landed"] / v["mass"],
                      top_shown=v["top_mass"] / v["top_n"], top_area=v["top_area"] / v["top_n"],
                      top_honesty=v["top_landed"] / v["top_mass"],
                      rest_honesty=v["rest_landed"] / v["rest_mass"] if v["rest_mass"] else None)
        r = res[k]
        print(f"{k:18s} n {r['targets']:5d} shown {r['shown']:.3f} area {r['area']:6.1f} honesty {r['honesty']:.2f} | "
              f"top shown {r['top_shown']:.3f} area {r['top_area']:6.1f} honesty {r['top_honesty']:.2f} | rest {r['rest_honesty'] or 0:.2f}", flush=True)
    json.dump(res, open(OUT, "w"), indent=1)
