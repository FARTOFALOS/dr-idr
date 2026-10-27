"""Which rule should form the constellations of the main map (final R / X of every session)? 26.10.2026, exploratory.

One harness, the same families and targets for every rule (studies/r_pre_x_2026_10_21/run.py's construction):
targets 2018-2025, NQ / ES / YM, ODR and RDR; each target's family = the earlier sessions of its key (weekday, or all
weekdays for the «all» scope); the target's own final R / X is checked against the zones built without it.

Rules (the map of final events, one point per session):
  zm3   zone-map-3, the rule of screens 24 and 23.5 (lab/zonemap24.py), unchanged
  cn1   CN-1 of 21.10 (grid-free neighbourhoods +-0.15 SD / +-20 min; meaning/lens/2026-10-21-constellation-spec, probe.py)
  tsd   the 23.10 time x SD cores (0.3 SD x one 15-minute window, local maxima of unique sessions, lab/time_sd235.py rule)
  hdr   NEW for this comparison: the same density D as zm3, one level for the whole map chosen so that its upper set holds
        70 % of the known events (a highest-density region of fixed mass); its connected parts are the zones
  band  NEW: the author's Time & Price way (docs/STRATEGY.md §6.3 p.5), price only: the 0.1-SD bands of highest
        3-cell density that hold 70 % of the events; time is not part of the zone
Measured per target: zones, the mass the map shows (sessions in zones / N), whether the target landed in a zone, and
for R the share of the zones' sessions whose final R came after their final X (a fall after the top, not a pullback
before the move). transfer = landed / mass: how honest the printed percentage is for the next session.

Aggregates only. python -B studies/constellations_compare_2026_10_26/compare.py
"""
from __future__ import annotations
import bisect
import json
import math
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "lab"))
sys.path.insert(0, str(HERE))
import scene24 as S  # noqa: E402
import zonemap24 as Z  # noqa: E402
import cn1_probe as CN  # noqa: E402

FROM, INSTS, SESSIONS = "2018-01-01", ("NQ", "ES", "YM"), ("ODR", "RDR")
EVENTS = ("R", "X")
EIGHT = np.ones((3, 3), dtype=int)
MASS = 0.70


def need_of(N):
    return max(4, math.ceil(N / 20))


# ---------------------------------------------------------------- the rules: (zones, lands(target)) ----------------
def r_zm3(P, N, b_lo, b_hi):
    m = Z.zone_map([(p["k"], p["b"], p["id"]) for p in P], N, b_lo, b_hi)
    zs = [dict(cells=set(map(tuple, z["cells"])), members=set(z["members"])) for z in m["zones"]]
    for z in zs: z["hit"] = (lambda cs: lambda t: (t["k"], t["b"]) in cs)(z["cells"])
    cells = set().union(*(z["cells"] for z in zs)) if zs else set()
    return zs, lambda t: (t["k"], t["b"]) in cells


def r_cn1(P, N, b_lo, b_hi):
    pts = [CN.Point(p["id"], p["v"], p["w"], p["t"]) for p in P]
    res = CN.cn(pts, N)
    comp = {z["component"] for z in res["zones"]}
    owner = lambda t: CN.region_owner(CN.Point("target", t["v"], t["w"], t["t"]), res)
    zs = [dict(members=set(z["members"]), hit=(lambda c: lambda t: owner(t) == c)(z["component"])) for z in res["zones"]]
    return zs, lambda t: owner(t) in comp


def r_tsd(P, N, b_lo, b_hi):
    cells = defaultdict(set)
    for p in P:
        if b_lo <= p["b"] <= b_hi: cells[(p["k"], p["b"])].add(p["id"])
    memo = {}
    def D(k, b):
        if not b_lo <= b <= b_hi: return 0
        if (k, b) not in memo: memo[(k, b)] = len(set().union(*(cells.get((k + d, b), set()) for d in (-1, 0, 1))))
        return memo[(k, b)]
    need = need_of(N)
    cand = {(k + d, b) for k, b in cells for d in (-1, 0, 1)}
    peaks = {q for q in cand if D(*q) >= need and all(D(*q) >= D(q[0] + dk, q[1] + db) for dk in (-1, 0, 1) for db in (-1, 0, 1))}
    zs = []
    while peaks:
        k, b = min(peaks, key=lambda q: (q[1], q[0])); v = D(k, b)
        run = [(k, b)]; peaks.discard((k, b)); j = k + 1
        while (j, b) in peaks and D(j, b) == v: run.append((j, b)); peaks.discard((j, b)); j += 1
        a = min(run, key=lambda q: (abs(2 * q[0] + 1), q[0]))
        cs = {(a[0] + d, a[1]) for d in (-1, 0, 1)}
        zs.append(dict(cells=cs, members=set().union(*(cells.get(c, set()) for c in cs)), hit=(lambda cc: lambda t: (t["k"], t["b"]) in cc)(cs)))
    allc = set().union(*(z["cells"] for z in zs)) if zs else set()
    return zs, lambda t: (t["k"], t["b"]) in allc


def r_hdr(P, N, b_lo, b_hi):
    use = [p for p in P if b_lo <= p["b"] <= b_hi]
    if not use: return [], lambda t: False
    ks = [p["k"] for p in use]; k_lo, k_hi = min(ks) - 1, max(ks) + 1
    A = np.zeros((k_hi - k_lo + 1, b_hi - b_lo + 1), dtype=np.int64)
    for p in use: A[p["k"] - k_lo, p["b"] - b_lo] += 1
    Dm = ndimage.correlate(A, EIGHT, mode="constant", cval=0)
    own = np.array([Dm[p["k"] - k_lo, p["b"] - b_lo] for p in use])
    goal = math.ceil(MASS * len(P))
    lam = next((v for v in sorted(set(own.tolist()), reverse=True) if (own >= v).sum() >= goal), 1)
    lab, n = ndimage.label(Dm >= lam, structure=EIGHT)
    need, zs, keep = need_of(N), [], set()
    def at(t):
        i, j = t["k"] - k_lo, t["b"] - b_lo
        return lab[i, j] if 0 <= i < lab.shape[0] and 0 <= j < lab.shape[1] else 0
    for L in range(1, n + 1):
        mem = {p["id"] for p, d in zip(use, own) if lab[p["k"] - k_lo, p["b"] - b_lo] == L}
        if len(mem) >= need:
            cells = int((lab == L).sum())       # its area in 0.1-SD x 15-minute cells
            zs.append(dict(members=mem, area=cells, hit=(lambda LL: lambda t: at(t) == LL)(L))); keep.add(L)
    return zs, lambda t: at(t) in keep


def r_band(P, N, b_lo, b_hi):
    use = [p for p in P if b_lo <= p["b"] <= b_hi]
    if not use: return [], lambda t: False
    cnt = defaultdict(int)
    for p in use: cnt[p["k"]] += 1
    D1 = lambda k: cnt.get(k - 1, 0) + cnt.get(k, 0) + cnt.get(k + 1, 0)
    own = [D1(p["k"]) for p in use]
    goal = math.ceil(MASS * len(P))
    lam = next((v for v in sorted(set(own), reverse=True) if sum(o >= v for o in own) >= goal), 1)
    ks = sorted(k for k in range(min(cnt) - 1, max(cnt) + 2) if D1(k) >= lam)
    runs, cur = [], []
    for k in ks:
        if cur and k != cur[-1] + 1: runs.append(cur); cur = []
        cur.append(k)
    if cur: runs.append(cur)
    need, zs, inband = need_of(N), [], set()
    for r in runs:
        mem = {p["id"] for p in use if r[0] <= p["k"] <= r[-1]}
        if len(mem) >= need: zs.append(dict(members=mem, hit=(lambda rr: lambda t: b_lo <= t["b"] <= b_hi and rr[0] <= t["k"] <= rr[-1])(r))); inband |= set(r)
    return zs, lambda t: b_lo <= t["b"] <= b_hi and t["k"] in inband


RULES = dict(zm3=r_zm3, cn1=r_cn1, tsd=r_tsd, hdr=r_hdr, band=r_band)
SCOPE_RULES = dict(weekday=tuple(RULES), all=("zm3", "tsd", "hdr", "band"))      # CN-1 is O(N^2) in exact fractions


# ---------------------------------------------------------------- families ----------------------------------------
def shifted(P, formed, dk, dt):
    out = []
    for p in P:
        k, b = Z.cell_of(p["v"], p["w"], p["t"], formed, dk, dt)
        out.append({**p, "k": k, "b": b})
    return out


SHIFTS = ((1, 0), (0, 5), (0, 10))           # half a price cell, 5 and 10 minutes (zone-map-3's own stability shifts)
CN_SCALES = ((CN.Fraction(13, 100), 20), (CN.Fraction(17, 100), 20), (CN.Fraction(3, 20), 15), (CN.Fraction(3, 20), 25))


def record(m, formed):
    out = dict(id=m["id"], date=m["date"], w=m["w"], post=None)
    for e in EVENTS:
        x = m[e]
        out[e] = None if x["s"] != "known" else dict(id=m["id"], v=int(x["v"]), w=int(m["w"]), t=int(x["t"]),
                                                    k=Z.cell_of(int(x["v"]), int(m["w"]), int(x["t"]), formed)[0],
                                                    b=Z.cell_of(int(x["v"]), int(m["w"]), int(x["t"]), formed)[1])
    if out["R"] and out["X"]: out["post"] = out["R"]["t"] > out["X"]["t"]
    return out


def families(inst, session):
    B = S._base(inst)
    assert max(b["date"] for b in B["boxes"]) <= "2025-12-31", "2026 stays closed"
    _, formed, end = S.SESS[session]
    shift, miss, keys = S.SHIFT[session], S._missing(inst, B, session), set()
    for i, m in enumerate(B["boxes"]):
        if m["session"] != session or m["conf"] is None: continue
        conf = int(m["conf"]) - shift
        if any(T < conf for T in miss.get(i, [])): continue
        keys.add((m["weekday"], m["side"], S.window_of(conf, formed)))
    fam = {}
    for key in sorted(keys):
        snap = S._snapshot(inst, B, session, key[0], key[1], "conf", key[2], "9999-12-31")
        S._SNAP.clear()
        fam[key] = sorted((record(m, formed) for m in snap["members"]), key=lambda x: x["date"])
    allw = defaultdict(list)
    for (wd, side, win), ms in fam.items(): allw[(side, win)] += ms
    for k in allw: allw[k].sort(key=lambda x: x["date"])
    return fam, allw


def ncls(N):
    return None if N < 20 else "N20-59" if N < 60 else "N60+"


def job(args):
    inst, session = args
    t0 = time.time()
    fam, allw = families(inst, session)
    _, formed, end = S.SESS[session]
    acc = defaultdict(lambda: defaultdict(float))
    dates_a = {k: [x["date"] for x in L] for k, L in allw.items()}
    for (wd, side, win), ms in fam.items():
        b_lo, b_hi = win, (end - 5 - formed) // 15
        for j, m in enumerate(ms):
            if m["date"] < FROM or j == 0: continue
            pa = bisect.bisect_left(dates_a[(side, win)], m["date"])
            for scope, L, p in (("weekday", ms, j), ("all", allw[(side, win)], pa)):
                c = ncls(p)
                if c is None: continue
                for e in EVENTS:
                    tgt = m[e]
                    if tgt is None: continue
                    P = [x[e] for x in L[:p] if x[e] is not None]
                    post = {x["id"]: x["post"] for x in L[:p]}
                    for name in SCOPE_RULES[scope]:
                        zs, lands = RULES[name](P, p, b_lo, b_hi)
                        a = acc[f"{name}|{e}|{scope}|{c}"]
                        land0 = bool(lands(tgt))
                        mem = set().union(*(z["members"] for z in zs)) if zs else set()
                        if zs:
                            top = max(zs, key=lambda z: len(z["members"]))
                            a["top_has"] += 1
                            a["top_mass"] += len(top["members"]) / p
                            a["top_landed"] += int(bool(top["hit"](tgt)))
                            a["rest_mass"] += (len(mem) - len(top["members"])) / p
                            a["rest_landed"] += int(land0 and not top["hit"](tgt))
                        if scope == "weekday":
                            flips = 0
                            if name == "cn1":
                                for hp, ht in CN_SCALES:
                                    res = CN.cn([CN.Point(q["id"], q["v"], q["w"], q["t"]) for q in P], p, hp, ht)
                                    comp = {z["component"] for z in res["zones"]}
                                    flips += int((CN.region_owner(CN.Point("target", tgt["v"], tgt["w"], tgt["t"]), res, hp, ht) in comp) != land0)
                                a["flip_any"] += int(flips > 0); a["flip_n"] += 1
                            else:
                                for dk, dt in (SHIFTS if name != "band" else ((1, 0),)):
                                    Ps, ts = shifted(P, formed, dk, dt), shifted([tgt], formed, dk, dt)[0]
                                    bl, bh = (15 * win + 5 - dt) // 15, (end - 5 - formed - dt) // 15
                                    _, ls = RULES[name](Ps, p, bl, bh)
                                    flips += int(bool(ls(ts)) != land0)
                                a["flip_any"] += int(flips > 0); a["flip_n"] += 1
                        sizes = sorted((len(z["members"]) for z in zs), reverse=True)
                        a["targets"] += 1
                        a["zones"] += len(zs)
                        a["empty"] += int(not zs)
                        a["mass"] += len(mem) / p
                        a["landed"] += int(lands(tgt))
                        if len(sizes) >= 2: a["two"] += 1; a["top_over_rest"] += sizes[0] / max(1, sizes[-1])
                        if sizes: a["top_share"] += sizes[0] / p
                        if e == "R" and mem:
                            a["post_n"] += 1
                            a["post_share"] += sum(1 for s in mem if post.get(s)) / len(mem)
    return inst, session, {k: dict(v) for k, v in acc.items()}, round(time.time() - t0)


def example(inst="NQ", weekday=0):
    """A family on screen with every rule's zones: NQ RDR Monday long 10:30-10:45 (26.10) and YM RDR Tuesday long
    10:30-10:45 (the operator's case of 20.10: no constellation below price)."""
    fam, _ = families(inst, "RDR")
    _, formed, end = S.SESS["RDR"]
    key = next(k for k in fam if k[0] == weekday and k[1] == 1 and k[2] == 0)
    L = fam[key]
    out = {}
    for e in EVENTS:
        P = [x[e] for x in L if x[e] is not None]
        byid = {p["id"]: p for p in P}
        for name in RULES:
            zs, _ = RULES[name](P, len(L), key[2], (end - 5 - formed) // 15)
            rows = []
            for z in zs:
                ps = [byid[s] for s in z["members"]]
                clk = lambda t: f"{t // 60:02d}:{t % 60:02d}"
                rows.append(dict(n=len(z["members"]), share=round(100 * len(z["members"]) / len(L), 1),
                                 time=clk(min(p["t"] for p in ps)) + "-" + clk(max(p["t"] for p in ps) + 5),
                                 sd=[round(min(p["v"] / p["w"] for p in ps), 2), round(max(p["v"] / p["w"] for p in ps), 2)]))
            out[f"{name}|{e}"] = sorted(rows, key=lambda r: r["time"])
    return dict(N=len(L), key=list(key), zones=out)


if __name__ == "__main__":
    t0 = time.time()
    total = defaultdict(lambda: defaultdict(float))
    with ProcessPoolExecutor(max_workers=6) as ex:
        for inst, session, acc, sec in ex.map(job, [(i, s) for i in INSTS for s in SESSIONS]):
            print(inst, session, sec, "s", flush=True)
            for k, v in acc.items():                       # rule|event|scope|class, per session and over both sessions
                for kk in (k + "|" + session, k + "|ALL"):
                    for f, x in v.items(): total[kk][f] += x
    res = {}
    for k, v in total.items():
        n = v["targets"]
        res[k] = dict(targets=int(n), zones=v["zones"] / n, empty=v["empty"] / n, mass=v["mass"] / n, landed=v["landed"] / n,
                      transfer=v["landed"] / v["mass"] if v["mass"] else None, top_share=v["top_share"] / n,
                      top_over_rest=v["top_over_rest"] / v["two"] if v["two"] else None,
                      post_share=v["post_share"] / v["post_n"] if v["post_n"] else None,
                      top_transfer=v["top_landed"] / v["top_mass"] if v["top_mass"] else None,
                      rest_transfer=v["rest_landed"] / v["rest_mass"] if v["rest_mass"] else None,
                      grid_flip=v["flip_any"] / v["flip_n"] if v["flip_n"] else None)
    ex_ = dict(nq_rdr_mon=example("NQ", 0), ym_rdr_tue=example("YM", 1))
    json.dump(dict(results=res, example=ex_), open(HERE / "results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("done", round(time.time() - t0), "s")
