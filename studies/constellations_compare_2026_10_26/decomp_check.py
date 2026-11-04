"""Questions 3-5 of the sharpened 27.10 lens: what did the «hits per area» curve hide? For the screen rule (zm3), the same
density with one global threshold at 30 % (hdr30) and CN-1, on the same targets as curve_check.py:
  - which next sessions the zones catch: final R before the session's final X (a pullback before the move) or after
    it (a giveback after the top); for X the same session flag (the top came before / after the deepest point);
  - how wide in TIME and in PRICE the zones are, and how wide the zone was in which a hit landed (a hit inside an
    85-minute window says less about «when» than a hit inside a 30-minute one);
  - how much area goes to zones made mostly of givebacks.
Aggregates only: decomp_results.json. python -B studies/constellations_compare_2026_10_26/decomp_check.py"""
import json
import math
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lab"))
import compare as C  # noqa: E402
import cn1_probe as CN  # noqa: E402

EIGHT = np.ones((3, 3), dtype=int)
HP, HT = Fraction(3, 20), 20


def cell_zone(members, cells):
    ks = [k for k, _ in cells]; bs = [b for _, b in cells]
    return dict(members=members, area=1.5 * len(cells), minutes=15 * (max(bs) - min(bs) + 1), sd=0.1 * (max(ks) - min(ks) + 1),
                hit=(lambda cs: lambda t: (t["k"], t["b"]) in cs)(set(cells)))


def zm3(P, N, b_lo, b_hi):
    m = C.Z.zone_map([(p["k"], p["b"], p["id"]) for p in P], N, b_lo, b_hi)
    return [cell_zone(set(z["members"]), [tuple(c) for c in z["cells"]]) for z in m["zones"]]


def hdr30(P, N, b_lo, b_hi):
    use = [p for p in P if b_lo <= p["b"] <= b_hi]
    if not use: return []
    ks = [p["k"] for p in use]; k_lo, k_hi = min(ks) - 1, max(ks) + 1
    A = np.zeros((k_hi - k_lo + 1, b_hi - b_lo + 1), dtype=np.int64)
    for p in use: A[p["k"] - k_lo, p["b"] - b_lo] += 1
    Dm = ndimage.correlate(A, EIGHT, mode="constant", cval=0)
    own = np.array([Dm[p["k"] - k_lo, p["b"] - b_lo] for p in use])
    goal = math.ceil(0.3 * len(P))
    lam = next((v for v in sorted(set(own.tolist()), reverse=True) if (own >= v).sum() >= goal), 1)
    lab, n = ndimage.label(Dm >= lam, structure=EIGHT)
    out = []
    for L in range(1, n + 1):
        mem = {p["id"] for p in use if lab[p["k"] - k_lo, p["b"] - b_lo] == L}
        if len(mem) < C.need_of(N): continue
        out.append(cell_zone(mem, [(i + k_lo, j + b_lo) for i, j in zip(*np.nonzero(lab == L))]))
    return out


def cn1(P, N, t0, t1):
    pts = [CN.Point(p["id"], p["v"], p["w"], p["t"]) for p in P]
    res = CN.cn(pts, N, HP, HT)
    h, out = float(HP), []
    for z in res["zones"]:
        cores = res["all_cores"][z["component"]]
        us = [float(q.u) for q in cores]; ts = [q.t for q in cores]
        a0, a1 = max(min(ts) - HT, t0), min(max(ts) + HT, t1)
        area = 0.0
        if a1 > a0:
            u0, ua = min(us) - h, max(us) + h
            G = np.zeros((int(round((ua - u0) / 0.01)) + 1, a1 - a0 + 1), dtype=bool)
            for u, t in zip(us, ts):
                i0, i1 = int(round((u - h - u0) / 0.01)), int(round((u + h - u0) / 0.01))
                j0, j1 = max(t - HT, a0) - a0, min(t + HT, a1) - a0
                if j1 >= j0: G[i0:i1 + 1, j0:j1 + 1] = True
            area = G.sum() * 0.01
        c = z["component"]
        out.append(dict(members=set(z["members"]), area=area, minutes=max(0, a1 - a0), sd=max(us) - min(us) + 2 * h,
                        hit=(lambda cc: lambda t: CN.region_owner(CN.Point("target", t["v"], t["w"], t["t"]), res, HP, HT) == cc)(c)))
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
            if c is None or m["post"] is None: continue
            post = {x["id"]: x["post"] for x in ms[:j]}
            script = "after" if m["post"] else "before"
            for e in C.EVENTS:
                tgt = m[e]
                P = [x[e] for x in ms[:j] if x[e] is not None]
                for name, zs in (("zm3", zm3(P, j, b_lo, b_hi)), ("hdr30", hdr30(P, j, b_lo, b_hi)), ("cn1", cn1(P, j, t0, t1))):
                    a = acc[f"{name}|{e}|{c}"]
                    a["n_" + script] += 1
                    hz = next((z for z in zs if z["hit"](tgt)), None)
                    if hz is not None:
                        a["hit_" + script] += 1
                        a["hit_minutes"] += hz["minutes"]; a["hit_sd"] += hz["sd"]; a["hits"] += 1
                    for z in zs:
                        known = [post[s] for s in z["members"] if post.get(s) is not None]
                        giveback = bool(known) and sum(known) / len(known) > 0.5
                        a["area_giveback" if giveback else "area_pullback"] += z["area"]
                        a["zone_n"] += len(z["members"]); a["zone_minutes"] += len(z["members"]) * z["minutes"]
                        a["zone_sd"] += len(z["members"]) * z["sd"]
                    if zs:
                        top = max(zs, key=lambda z: len(z["members"]))
                        a["top_n"] += 1; a["top_minutes"] += top["minutes"]; a["top_sd"] += top["sd"]
                    a["targets"] += 1
    return {k: dict(v) for k, v in acc.items()}


if __name__ == "__main__":
    total = defaultdict(lambda: defaultdict(float))
    with ProcessPoolExecutor(max_workers=6) as ex:
        for acc in ex.map(job, [(i, s) for i in C.INSTS for s in C.SESSIONS]):
            for k, v in acc.items():
                for f, x in v.items(): total[k][f] += x
    res = {}
    for k, v in sorted(total.items()):
        n = v["targets"]
        r = dict(targets=int(n),
                 hits_before=v["hit_before"] / v["n_before"], hits_after=v["hit_after"] / v["n_after"],
                 share_after=v["n_after"] / n,
                 area_pullback=v["area_pullback"] / n, area_giveback=v["area_giveback"] / n,
                 zone_minutes=v["zone_minutes"] / v["zone_n"] if v["zone_n"] else None,
                 zone_sd=v["zone_sd"] / v["zone_n"] if v["zone_n"] else None,
                 top_minutes=v["top_minutes"] / v["top_n"] if v["top_n"] else None,
                 top_sd=v["top_sd"] / v["top_n"] if v["top_n"] else None,
                 hit_minutes=v["hit_minutes"] / v["hits"] if v["hits"] else None,
                 hit_sd=v["hit_sd"] / v["hits"] if v["hits"] else None)
        res[k] = r
        print(f"{k:14s} n {r['targets']:5d} hits before/after X {r['hits_before']:.3f}/{r['hits_after']:.3f} (after {r['share_after']:.2f}) "
              f"area pullback/giveback {r['area_pullback']:5.1f}/{r['area_giveback']:5.1f} | zone {r['zone_minutes'] or 0:5.1f} min "
              f"{r['zone_sd'] or 0:.2f} SD | top {r['top_minutes'] or 0:5.1f} min {r['top_sd'] or 0:.2f} SD | hit zone {r['hit_minutes'] or 0:5.1f} min {r['hit_sd'] or 0:.2f} SD", flush=True)
    json.dump(res, open(C.HERE / "decomp_results.json", "w"), indent=1)
