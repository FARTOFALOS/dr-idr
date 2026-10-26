"""POS_GEO against a distance-and-time control on the questions of 15.10. Protocol: sibling README.md.

Reuses the population, questions and labels of studies/dynamic_field_2026_10_15/checks.py unchanged.
Rows stay in lab/.runtime/pos-geo-vs-distance-2026-10-19 (not in git); aggregates go to results.json.
"""
from __future__ import annotations
import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "lab"))
_spec = importlib.util.spec_from_file_location("dyn1015", ROOT / "studies/dynamic_field_2026_10_15/checks.py")
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)
N = C.N

VERSION = "POS-GEO-VS-DISTANCE-1"
RT = ROOT / "lab/.runtime/pos-geo-vs-distance-2026-10-19"
METHODS = ("POS_GEO", "DIST_GEO", "CLOCK_GEO")
PAIRS = (("POS_GEO", "DIST_GEO"), ("POS_GEO", "CLOCK_GEO"), ("DIST_GEO", "CLOCK_GEO"))
PRIMARY = ("WINDOW_VISIT", "POS_GEO - DIST_GEO")


def stamp():
    files = (HERE / "README.md", HERE / "run.py", ROOT / "studies/dynamic_field_2026_10_15/checks.py",
             ROOT / "studies/dynamic_field_2026_10_15/README.md", ROOT / "lab/now24.py", ROOT / "lab/now24_validate.py")
    return {str(p.relative_to(ROOT)).replace("\\", "/"): C.hfile(p) for p in files}


def keys_at(d, c, ids):
    return np.floor(10 * d["cl"][ids, c] / d["w"][ids]).astype(np.int64)


def shifted_labels(d, c, ids, cache):
    """DIST_GEO: every case's band is placed at the same offset from ITS OWN current cell (distance and time only)."""
    out = None
    keys = keys_at(d, c, ids)
    for k in np.unique(keys):
        k = int(k)
        if k not in cache:
            cache[k] = C.labels(d, c, k)
        y, specs = cache[k]
        if out is None:
            out = np.full((len(d["w"]), y.shape[1]), -1, np.int8)
        rows = ids[keys == k]
        out[rows] = y[rows]
    return out


def sets_at(d, i, c):
    """The parent (alive at the common clock, same instrument/block, earlier dates) and POS_GEO, as in 15.10."""
    prior = int(np.searchsorted(d["dates"], d["dates"][i], side="left"))
    geo = np.flatnonzero(d["valid"][:prior, c])
    pg = geo[N._near(d["cl"][geo, c], d["w"][geo], d["cl"][i, c], int(d["w"][i]), (1, 4))]
    return geo, pg


def counts(y, ids):
    if not len(ids):
        z = np.zeros(y.shape[1], np.uint16)
        return z, z
    a = y[ids]
    return (a >= 0).sum(0).astype(np.uint16), (a == 1).sum(0).astype(np.uint16)


def collect(inst, block, dry=False):
    begin = time.time()
    d = C.load(inst, block)
    targets = d["targets"][:4] if dry else d["targets"]
    L = len(d["grid"])
    recs, cuts = [], 0
    for c in range(L - 3):
        chosen = targets[d["valid"][targets, c]]
        if not len(chosen):
            continue
        cache = {}
        alive = np.flatnonzero(d["valid"][:, c])
        Ys = shifted_labels(d, c, alive, cache)
        for i in chosen:
            i = int(i)
            ki = int(keys_at(d, c, np.array([i]))[0])
            if ki not in cache:
                cache[ki] = C.labels(d, c, ki)
            ys, specs = cache[ki]
            assert np.array_equal(Ys[i], ys[i]), "own band = shifted band for the target itself"
            geo, pg = sets_at(d, i, c)
            q = ys.shape[1]
            row = dict(target=np.full(q, i, np.uint16), week=np.full(q, d["week"][i], np.int32),
                       year=np.full(q, d["year"][i], np.int16), cut=np.full(q, c, np.uint8),
                       window=specs[:, 0], kind=specs[:, 1], offset=specs[:, 2], y=ys[i].astype(np.int8))
            n = np.zeros((3, q), np.uint16); known = np.zeros((3, q), np.uint16); yes = np.zeros((3, q), np.uint16)
            for mi, (lab, ids) in enumerate(((ys, pg), (Ys, geo), (ys, geo))):
                n[mi] = len(ids)
                known[mi], yes[mi] = counts(lab, ids)
            row.update(n=n, known=known, yes=yes)
            recs.append(row)
            cuts += 1
        if c % 12 == 0:
            print(f"  {inst}/{block} M5={c}/{L} cuts={cuts} {time.time() - begin:.0f}s", flush=True)
    rec = {k: np.concatenate([r[k] for r in recs], axis=-1) for k in recs[0]}
    meta = dict(version=VERSION, source_hashes=stamp(), instrument=inst, block=block, methods=METHODS,
                source_cases=len(d["cases"]), target_weeks=len(targets), target_cuts=cuts, rows=int(rec["y"].shape[0]),
                input_digest=d["input_digest"], maximum_source_date=str(max(d["dates"])), dry=dry,
                elapsed_seconds=round(time.time() - begin, 1))
    assert meta["maximum_source_date"] <= "2025-12-31", "2026 stays closed"
    if not dry:
        RT.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(RT / f"{inst}_{block}.npz", **rec, meta=np.array(json.dumps(meta)))
    print(f"COMPLETE {inst}/{block}: {meta['rows']} rows, {cuts} cuts, {meta['elapsed_seconds']}s", flush=True)
    return meta


def semantic_checks():
    base = C.semantic_checks()
    # A synthetic corpus: every case moves exactly +0.5 SD from its own close in the first future M5.
    grid = list(range(5, 101, 5)); c = 4; cases = []
    for i in range(30):
        u0 = 30 if i % 2 else 0               # half the analogs stand at +0.3 SD, half at 0
        p = np.full((20, 3), float(u0)); p[0] = np.nan
        p[c + 1] = [u0 + 45, u0 + 55, u0 + 50]   # +0.45..+0.55 SD from its own close, then back
        date = (dt.date(2010, 1, 1) + dt.timedelta(days=i)).isoformat()
        cases.append(dict(id=str(i), date=date, weekday=0, side=1, win=0, a=0, w=100, oppv=-200, P=p))
    z = C.pack(cases, grid); i = 29                     # the target stands at +0.3 SD (u0 = 30)
    geo, pg = sets_at(z, i, c)
    cache = {}
    Ys = shifted_labels(z, c, np.flatnonzero(z["valid"][:, c]), cache)
    ki = int(keys_at(z, c, np.array([i]))[0])
    ys, specs = C.labels(z, c, ki)
    col = int(np.flatnonzero((specs[:, 0] == 0) & (specs[:, 1] == 0) & (C.OFFSETS[specs[:, 2]] == 5))[0])
    dist = Ys[geo, col]; clock = ys[geo, col]; pos = ys[pg, col]
    assert (dist == 1).all(), "DIST: every analog moved +0.5 from its own price, so every one visited its own +0.5 band"
    assert (pos == 1).all(), "POS: the analogs standing where the target stands visited the same absolute band"
    assert (clock == 0).any() and (clock == 1).any(), "CLOCK: the absolute band is missed by the analogs standing elsewhere"
    # All analogs in the target's own cell: the shifted and the absolute question are the same question.
    same = [ix for ix in geo if keys_at(z, c, np.array([ix]))[0] == ki]
    assert np.array_equal(Ys[same], ys[same])
    # The target's future changes neither the sets nor the analogs' labels.
    z2 = copy.deepcopy(z); z2["P"][i, c + 1:] = 900
    st = N.series(z2["P"][i], 0, -200)
    for name in ("cl", "r", "x", "valid"):
        z2[name][i] = st[name]
    g2, p2 = sets_at(z2, i, c)
    assert np.array_equal(g2, geo) and np.array_equal(p2, pg)
    Y2 = shifted_labels(z2, c, np.flatnonzero(z2["valid"][:, c]), {})
    assert np.array_equal(Y2[geo], Ys[geo])
    # An analog's future changes its label, not the sets.
    j = int(geo[0]); z3 = copy.deepcopy(z); z3["P"][j, c + 1] = [0, 1, 0]
    assert all(np.array_equal(a, b) for a, b in zip(sets_at(z3, i, c), (geo, pg)))
    Y3 = shifted_labels(z3, c, np.flatnonzero(z3["valid"][:, c]), {})
    assert Y3[j, col] != Ys[j, col]
    return dict(status="PASS", inherited=base["checks"],
                checks=["DIST places the band at the same offset from each analog's own cell",
                        "POS and DIST agree when the analogs stand where the target stands",
                        "CLOCK misses an absolute band the moved analogs reached elsewhere",
                        "target future changes neither sets nor analog labels",
                        "analog future changes its label only"])


def report():
    stats, pairs, cal, unk, meta = {}, {}, {}, {}, []
    for inst, block in C.CELLS:
        f = RT / f"{inst}_{block}.npz"
        if not f.exists():
            raise RuntimeError("missing cell " + str(f))
        with np.load(f, allow_pickle=False) as a:
            m = json.loads(str(a["meta"]))
            assert not m["dry"] and m["source_hashes"] == stamp(), "rows from another protocol or code"
            meta.append(m)
            y, target, wk, yr = a["y"], a["target"], a["week"], a["year"]
            kind, win, off = a["kind"], a["window"], a["offset"]
            nt, nk, ny = a["n"].astype(np.int64), a["known"].astype(np.int64), a["yes"].astype(np.int64)
            p = np.divide(ny, nk, out=np.full(ny.shape, np.nan), where=nk > 0)
            ok = (nt >= C.SUPPORT) & (nk >= C.SUPPORT) & (y[None, :] >= 0)
            yy = np.maximum(y, 0)
            err = (p - yy[None, :]) ** 2
            groups = [("overall", np.ones(len(y), bool)), ("cell:" + inst + "/" + block, np.ones(len(y), bool)),
                      ("epoch:2016-19", yr <= 2019), ("epoch:2020-25", yr >= 2020)]
            groups += [("window:" + str(j), win == j) for j in range(3)]
            groups += [("distance:" + str(v), np.abs(C.OFFSETS[off]) == v) for v in (2, 5, 10)]
            groups += [("side:below", C.OFFSETS[off] < 0), ("side:above", C.OFFSETS[off] > 0)]
            for ki, kn in enumerate(C.KINDS):
                for gn, gm in groups:
                    base = gm & (kind == ki)
                    for mi, mn in enumerate(METHODS):
                        stats.setdefault((kn, mn, gn), C.Acc()).add(err[mi], ok[mi] & base, target, wk, base, y < 0,
                                                                 nt[mi] if gn == "overall" else None)
                    for x, z in PAIRS:
                        ia, ib = METHODS.index(x), METHODS.index(z)
                        pairs.setdefault((kn, x + " - " + z, gn), C.Acc()).add(err[ia] - err[ib], base & ok[ia] & ok[ib],
                                                                             target, wk, base, y < 0)
                base = kind == ki
                for mi, mn in enumerate(METHODS):
                    mask = base & ok[mi]
                    u = unk.setdefault((kn, mn), [0, 0, 0.])
                    u[0] += int(mask.sum()); u[1] += int((mask & (nk[mi] < nt[mi])).sum())
                    u[2] += float(((nt[mi] - nk[mi]) / np.maximum(nt[mi], 1))[mask].sum())
                    bins = np.minimum((np.nan_to_num(p[mi]) * 10).astype(np.int16), 9)
                    for bi in range(10):
                        take = mask & (bins == bi)
                        if not take.any():
                            continue
                        r = cal.setdefault((kn, mn, bi), dict(n=0, p=0., y=0, weeks={}))
                        r["n"] += int(take.sum()); r["p"] += float(p[mi, take].sum()); r["y"] += int(yy[take].sum())
                        for w in np.unique(wk[take]):
                            mm = take & (wk == w); v = r["weeks"].setdefault(int(w), [0, 0])
                            v[0] += int(yy[mm].sum()); v[1] += int(mm.sum())
        print("aggregated " + inst + "/" + block, flush=True)
    proto = C.hfile(HERE / "README.md")
    out = dict(version=VERSION, protocol_sha256_lf=proto, source_hashes=stamp(), primary=list(PRIMARY),
               scope="seen-history exploration 2016-2025 (analogs 2006-2025); weekly targets; all closed M5; NQ/ES/YM ODR/RDR; no 2026",
               cells=meta, semantic_checks=semantic_checks(), methods=[], comparisons=[], calibration=[], unknown=[])
    for (k, m, g), acc in stats.items():
        out["methods"].append(dict(kind=k, method=m, group=g, **acc.result(ci=g == "overall")))
    for (k, pr, g), acc in pairs.items():
        out["comparisons"].append(dict(kind=k, pair=pr, group=g, negative_is_better_for_first=True,
                                       **acc.result(ci=g == "overall" or g.startswith(("cell:", "epoch:")))))
    for (k, m, b), a in cal.items():
        sums, cnt = np.array(list(a["weeks"].values()), float).T
        rng = np.random.default_rng(C.SEED); bs = []
        for _ in range(C.REPS // 100):
            ix = rng.integers(0, len(sums), (100, len(sums))); bs.extend(sums[ix].sum(1) / cnt[ix].sum(1))
        out["calibration"].append(dict(kind=k, method=m, bin=[b / 10, (b + 1) / 10], n=a["n"], predicted=a["p"] / a["n"],
                                       observed=a["y"] / a["n"], ci95=[float(v) for v in np.quantile(bs, [.025, .975])]))
    for (k, m), (n, w, s) in unk.items():
        out["unknown"].append(dict(kind=k, method=m, answered_rows=n, rows_with_unknown_in_support=w / n if n else None,
                                   mean_unknown_share_of_support=s / n if n else None))
    (HERE / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for k in C.KINDS:
        print("\n" + k)
        for r in out["methods"]:
            if r["kind"] == k and r["group"] == "overall":
                print(" ", r["method"], "coverage", round(r["coverage"], 4), "brier", r["mean"], r.get("ci95"), "support", r.get("support_median"))
        for r in out["comparisons"]:
            if r["kind"] == k and (r["group"] == "overall" or r["group"].startswith("epoch")):
                print(" ", r["pair"], r["group"], r["mean"], r.get("ci95"), "coverage", round(r["coverage"], 4))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true"); ap.add_argument("--dry", action="store_true")
    ap.add_argument("--run", action="store_true"); ap.add_argument("--report", action="store_true")
    ap.add_argument("--cell")
    a = ap.parse_args()
    if a.check:
        print(json.dumps(semantic_checks(), ensure_ascii=False, indent=1))
    if a.dry:
        semantic_checks(); collect("NQ", "RDR", dry=True)
    if a.run:
        semantic_checks()
        for inst, block in ([tuple(a.cell.split("/"))] if a.cell else C.CELLS):
            collect(inst, block)
        if not a.cell:
            report()
    if a.report:
        report()
    if not any((a.check, a.dry, a.run, a.report)):
        ap.error("choose --check, --dry, --run or --report")


if __name__ == "__main__":
    main()
