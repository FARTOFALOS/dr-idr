"""Question 5 of the 27.10 lens: does the weekday make a family more comparable to today, or does a bigger family only
give steadier statistics? The same targets, the rule of the screen (zone-map-3), three families of each target:
  W  its weekday family (as on screen), N = n;
  S  the same size n drawn at random from the earlier sessions of the other weekdays (same side and window): another
     composition, the same size;
  A  all earlier sessions of the side and window (all weekdays): the bigger family.
W against S separates comparability from size (equal N, the same targets); S against A is the effect of size alone.
Targets 2018-2025, NQ / ES / YM, ADR / ODR / RDR, every target whose weekday family has N >= 20 and whose other
weekdays hold at least n sessions. Aggregates only: family_results.json.
python -B studies/constellations_compare_2026_10_26/family_check.py"""
import json
import random
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lab"))
import compare as C  # noqa: E402

SESSIONS = ("ADR", "ODR", "RDR")


def zm3(P, N, b_lo, b_hi):
    m = C.Z.zone_map([(p["k"], p["b"], p["id"]) for p in P], N, b_lo, b_hi)
    cells = set()
    mem = set()
    zs = []
    for z in m["zones"]:
        cs = set(map(tuple, z["cells"]))
        cells |= cs; mem |= set(z["members"]); zs.append((cs, set(z["members"])))
    return cells, mem, len(m["zones"]), zs


def job(args):
    inst, session = args
    fam, allw = C.families(inst, session)
    _, formed, end = C.S.SESS[session]
    wd_of = {x["id"]: wd for (wd, _, _), ms in fam.items() for x in ms}
    acc = defaultdict(lambda: defaultdict(float))
    for (wd, side, win), ms in fam.items():
        b_lo, b_hi = win, (end - 5 - formed) // 15
        pool = allw[(side, win)]
        for j, m in enumerate(ms):
            if m["date"] < C.FROM: continue
            c = C.ncls(j)
            if c is None: continue
            earlier = [x for x in pool if x["date"] < m["date"]]
            others = [x for x in earlier if wd_of[x["id"]] != wd]
            if len(others) < j:
                acc[f"skip|{c}"]["n"] += 1
                continue
            S = random.Random(m["id"]).sample(others, j)
            for e in C.EVENTS:
                tgt = m[e]
                if tgt is None: continue
                for name, X in (("W", ms[:j]), ("S", S), ("A", earlier)):
                    P = [x[e] for x in X if x[e] is not None]
                    cells, mem, nz, zs = zm3(P, len(X), b_lo, b_hi)
                    a = acc[f"{name}|{e}|{c}"]
                    a["targets"] += 1
                    a["N"] += len(X)
                    a["shown"] += len(mem) / len(X)
                    hit = int((tgt["k"], tgt["b"]) in cells)
                    a["hits"] += hit
                    a["area"] += 1.5 * len(cells)
                    a["zones"] += nz
                    # the sharpened lens (27.10): which scenario the hits and the area serve — the target's final R
                    # before its final X (a pullback before the move) or after it (a giveback after the top)
                    if m["post"] is not None:
                        sc = "after" if m["post"] else "before"
                        a["n_" + sc] += 1; a["hit_" + sc] += hit
                    post = {x["id"]: x["post"] for x in X}
                    for cs, members in zs:
                        known = [post[s] for s in members if post.get(s) is not None]
                        a["area_giveback" if known and sum(known) / len(known) > 0.5 else "area_pullback"] += 1.5 * len(cs)
    return {k: dict(v) for k, v in acc.items()}


if __name__ == "__main__":
    total = defaultdict(lambda: defaultdict(float))
    with ProcessPoolExecutor(max_workers=6) as ex:
        for acc in ex.map(job, [(i, s) for i in C.INSTS for s in SESSIONS]):
            for k, v in acc.items():
                for f, x in v.items(): total[k][f] += x
    res = {}
    for k, v in sorted(total.items()):
        if k.startswith("skip"): res[k] = dict(v); print(k, int(v["n"])); continue
        n = v["targets"]
        res[k] = dict(targets=int(n), N=v["N"] / n, shown=v["shown"] / n, hits=v["hits"] / n, area=v["area"] / n,
                      honesty=v["hits"] / v["shown"] if v["shown"] else None, zones=v["zones"] / n,
                      hits_before=v["hit_before"] / v["n_before"] if v["n_before"] else None,
                      hits_after=v["hit_after"] / v["n_after"] if v["n_after"] else None,
                      area_pullback=v["area_pullback"] / n, area_giveback=v["area_giveback"] / n)
        r = res[k]
        print(f"{k:12s} n {r['targets']:5d} N {r['N']:6.1f} shown {r['shown']:.3f} hits {r['hits']:.3f} honesty {r['honesty']:.2f} "
              f"area {r['area']:6.1f} zones {r['zones']:.2f} | before/after X {r['hits_before']:.3f}/{r['hits_after']:.3f} "
              f"area pullback/giveback {r['area_pullback']:.1f}/{r['area_giveback']:.1f}", flush=True)
    json.dump(res, open(C.HERE / "family_results.json", "w"), indent=1)
