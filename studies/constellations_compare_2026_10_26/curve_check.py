"""Questions 8-9 of the 27.10 lens: is a rule better, or only at another point of the same trade-off?
Out of sample, per target: hits (the target's own final event fell in the zones), the area the zones cover (SD x
minutes inside the block) and the shown share. The reference curve is the level sets of zone-map-3's own density
(3 x 3 cell counts) at fixed masses 20-70 % (hdr); a rule above that curve localises the next session better at the
same area, a rule on it is only another operating point. Cost side for R: how much a zone mixes the two scripts
(final R before the session's final X = a pullback before the move; after it = a fade after the top), 0 = pure,
0.5 = half and half, weighted by the zone's sessions. Same targets as width_check.py (weekday families, ODR / RDR,
NQ / ES / YM, every 2nd target). Aggregates only: curve_results.json.
python -B studies/constellations_compare_2026_10_26/curve_check.py"""
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

MASSES = (0.2, 0.3, 0.4, 0.5, 0.7)
CN_SCALES = ((Fraction(1, 10), 15), (Fraction(3, 20), 20))
EIGHT = np.ones((3, 3), dtype=int)


def hdr(P, N, b_lo, b_hi, mass):
    use = [p for p in P if b_lo <= p["b"] <= b_hi]
    if not use: return []
    ks = [p["k"] for p in use]; k_lo, k_hi = min(ks) - 1, max(ks) + 1
    A = np.zeros((k_hi - k_lo + 1, b_hi - b_lo + 1), dtype=np.int64)
    for p in use: A[p["k"] - k_lo, p["b"] - b_lo] += 1
    Dm = ndimage.correlate(A, EIGHT, mode="constant", cval=0)
    own = np.array([Dm[p["k"] - k_lo, p["b"] - b_lo] for p in use])
    goal = math.ceil(mass * len(P))
    lam = next((v for v in sorted(set(own.tolist()), reverse=True) if (own >= v).sum() >= goal), 1)
    lab, n = ndimage.label(Dm >= lam, structure=EIGHT)
    out, need = [], C.need_of(N)
    for L in range(1, n + 1):
        mem = {p["id"] for p in use if lab[p["k"] - k_lo, p["b"] - b_lo] == L}
        if len(mem) < need: continue
        cells = {(i + k_lo, j + b_lo) for i, j in zip(*np.nonzero(lab == L))}
        out.append(dict(members=mem, area=1.5 * len(cells), hit=(lambda cs: lambda t: (t["k"], t["b"]) in cs)(cells)))
    return out


def zm3(P, N, b_lo, b_hi):
    m = C.Z.zone_map([(p["k"], p["b"], p["id"]) for p in P], N, b_lo, b_hi)
    out = []
    for z in m["zones"]:
        cs = set(map(tuple, z["cells"]))
        out.append(dict(members=set(z["members"]), area=1.5 * len(cs), hit=(lambda cc: lambda t: (t["k"], t["b"]) in cc)(cs)))
    return out


def cn1(P, N, t0, t1, hp, ht):
    pts = [CN.Point(p["id"], p["v"], p["w"], p["t"]) for p in P]
    res = CN.cn(pts, N, hp, ht)
    h, out = float(hp), []
    for z in res["zones"]:
        cores = res["all_cores"][z["component"]]
        us = [float(q.u) for q in cores]; ts = [q.t for q in cores]
        u0, ua = min(us) - h, max(us) + h
        a0, a1 = max(min(ts) - ht, t0), min(max(ts) + ht, t1)
        area = 0.0
        if a1 > a0:
            G = np.zeros((int(round((ua - u0) / 0.01)) + 1, a1 - a0 + 1), dtype=bool)
            for u, t in zip(us, ts):
                i0, i1 = int(round((u - h - u0) / 0.01)), int(round((u + h - u0) / 0.01))
                j0, j1 = max(t - ht, a0) - a0, min(t + ht, a1) - a0
                if j1 >= j0: G[i0:i1 + 1, j0:j1 + 1] = True
            area = G.sum() * 0.01
        c = z["component"]
        out.append(dict(members=set(z["members"]), area=area,
                        hit=(lambda cc: lambda t: CN.region_owner(CN.Point("target", t["v"], t["w"], t["t"]), res, hp, ht) == cc)(c)))
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
            post = {x["id"]: x["post"] for x in ms[:j]}
            for e in C.EVENTS:
                tgt = m[e]
                if tgt is None: continue
                P = [x[e] for x in ms[:j] if x[e] is not None]
                variants = [("zm3", zm3(P, j, b_lo, b_hi))]
                variants += [(f"hdr{int(100 * q)}", hdr(P, j, b_lo, b_hi, q)) for q in MASSES]
                variants += [(f"cn1_{float(hp):.2f}_{ht}", cn1(P, j, t0, t1, hp, ht)) for hp, ht in CN_SCALES]
                for name, zs in variants:
                    a = acc[f"{name}|{e}|{c}"]
                    mem = set().union(*(z["members"] for z in zs)) if zs else set()
                    a["targets"] += 1
                    a["shown"] += len(mem) / j
                    a["area"] += sum(z["area"] for z in zs)
                    a["hits"] += int(any(z["hit"](tgt) for z in zs))
                    a["zones"] += len(zs)
                    a["empty"] += int(not zs)
                    if e == "R":
                        for z in zs:
                            known = [post[s] for s in z["members"] if post.get(s) is not None]
                            if known:
                                p = sum(known) / len(known)
                                a["mix_w"] += len(known); a["mix"] += len(known) * min(p, 1 - p)
    return {k: dict(v) for k, v in acc.items()}


if __name__ == "__main__":
    total = defaultdict(lambda: defaultdict(float))
    with ProcessPoolExecutor(max_workers=4) as ex:
        for acc in ex.map(job, [(i, s) for i in C.INSTS for s in C.SESSIONS]):
            for k, v in acc.items():
                for f, x in v.items(): total[k][f] += x
    res = {}
    for k, v in sorted(total.items()):
        n = v["targets"]
        res[k] = dict(targets=int(n), shown=v["shown"] / n, area=v["area"] / n, hits=v["hits"] / n,
                      honesty=v["hits"] / v["shown"] if v["shown"] else None, zones=v["zones"] / n, empty=v["empty"] / n,
                      mix=v["mix"] / v["mix_w"] if v.get("mix_w") else None)
        r = res[k]
        print(f"{k:22s} n {r['targets']:5d} area {r['area']:6.1f} hits {r['hits']:.3f} shown {r['shown']:.3f} "
              f"honesty {r['honesty'] or 0:.2f} zones {r['zones']:.2f} empty {r['empty']:.2f} mix {r['mix'] if r['mix'] is None else round(r['mix'], 3)}", flush=True)
    json.dump(res, open(C.HERE / "curve_results.json", "w"), indent=1)
