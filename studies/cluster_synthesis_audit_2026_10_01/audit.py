"""Independent audit of DR-LAB-CLUSTER-SYNTHESIS-1.0: the calculations that decide some of its lenses (aggregates only).

E1 path-null. The synthesis' sign-flip null (§11-12) on the stable areas of main-cluster-1 (its 2018-2025 check):
   the older half picks the block, the newer half is validated; each validation session's M5 after its own activation
   are reflected at random (1000 replicates), R / X measured by the same rule; q_obs against the null, Holm over R and X.
E2 simpler objects on the next session (2018-2025 targets): the family's L1 block against a fixed template block of the
   same size (taken from 2006-2017 only), the first hour at any price and the family's modal 0.5-wide band.
E3 coverage: how many targets can reach L2 at all (N >= 60), by session and confirmation window.
E4 prefix: when the area's hour has passed, what today's own path already says about it, against the snapshot's n / N.

    python -B studies/cluster_synthesis_audit_2026_10_01/audit.py --v1rows <rows of the main-cluster-1 check> --out <json>
"""
import argparse
import hashlib
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "lab"))
import cluster24 as C  # noqa: E402  (main-cluster-1: L1 pick and the block geometry)
import scene24 as S  # noqa: E402

S.cluster24.of_snapshot = lambda snap, ev: None          # the audit does not need the whole-key clusters
ap = argparse.ArgumentParser()
ap.add_argument("--v1rows", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--reps", type=int, default=1000)
a = ap.parse_args()
KB, TB, W15 = C.KB, C.TB, C.WINDOW


def seed(*parts):
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:15], 16)


def key_data(snap, formed):
    """Per member: date, width, activation, R / X (status, value, open), the directed path as an array (NaN = no M5)."""
    grid = np.array(snap["grid"])
    out = dict(grid=grid, dates=[], years=[], w=[], act=[], path=[], ev={"R": [], "X": []})
    for m in snap["members"]:
        out["dates"].append(m["date"]); out["years"].append(int(m["date"][:4])); out["w"].append(m["w"]); out["act"].append(m["act"])
        out["path"].append(np.array([q if q is not None else [np.nan] * 3 for q in m["path"]], dtype=float))
        for e in ("R", "X"):
            x = m[e]
            out["ev"][e].append((x["s"], x.get("v"), x.get("t")))
    return out


def cells(K, e, idx, formed):
    """(k, b) of the known events among members idx; None for unknown / none."""
    res = []
    for i in idx:
        s, v, t = K["ev"][e][i]
        res.append(((10 * v) // K["w"][i], (t - formed) // W15) if s == "known" else None)
    return res


def pick(cs, b_min, b_max):
    kn = [c for c in cs if c is not None]
    if not kn: return None
    k = np.array([c[0] for c in kn]); b = np.array([c[1] for c in kn])
    return C._Field(k, b, b_min, b_max).pick()


inside = lambda c, k0, b0: c is not None and k0 <= c[0] < k0 + KB and b0 <= c[1] < b0 + TB


def null_hits(K, i, e, blk, formed, rng, reps):
    """Sign-flip null of one session (synthesis §11): its own M5 after its activation, each reflected with p = 1/2 about
    the previous synthetic close; R / X = min of lows / max of highs, first time. True where the synthetic event falls in
    the block."""
    P, grid, act = K["path"][i], K["grid"], K["act"][i]
    ja = int(np.searchsorted(grid, act))
    seg = P[ja + 1:]
    if np.isnan(seg).any() or not len(seg): return None          # unknown events stay unknown
    c0 = P[ja, 2]
    prev = np.concatenate([[c0], seg[:-1, 2]])
    dL, dH, dC = seg[:, 0] - prev, seg[:, 1] - prev, seg[:, 2] - prev
    eps = rng.choice((-1.0, 1.0), size=(reps, len(seg)))
    cl = c0 + np.cumsum(eps * dC, axis=1)
    pv = np.concatenate([np.full((reps, 1), c0), cl[:, :-1]], axis=1)
    lo = pv + np.where(eps > 0, dL, -dH)
    hi = pv + np.where(eps > 0, dH, -dL)
    vals, j = (lo.min(1), lo.argmin(1)) if e == "R" else (hi.max(1), hi.argmax(1))
    t = grid[ja + 1 + j] - 5
    k = np.floor_divide(10 * vals.astype(np.int64), K["w"][i])
    b = (t - formed) // W15
    k0, b0 = blk
    return (k >= k0) & (k < k0 + KB) & (b >= b0) & (b < b0 + TB)


def prefix_state(K, i, e, blk, t_end):
    """Today's own extreme so far (M5 closing after the activation up to t_end) against the block's band: 'in' (the block
    is still possible: it holds if no farther extreme comes later), 'out' (impossible already) or None (no M5)."""
    P, grid, act = K["path"][i], K["grid"], K["act"][i]
    sel = (grid > act) & (grid <= t_end)
    col = P[sel, 0 if e == "R" else 1]
    if not len(col) or np.isnan(col).all(): return None
    v = np.nanmin(col) if e == "R" else np.nanmax(col)
    k = int((10 * int(v)) // K["w"][i])
    return "in" if blk[0] <= k < blk[0] + KB else "out"


v1 = {}
for r in json.load(open(a.v1rows, encoding="utf-8")):
    v1[(r["inst"], r["s"], r["ev"], tuple(r["key"]), r["date"])] = r

t0 = time.time()
dev_pos = defaultdict(Counter)            # E2: L1 positions of 2006-2017 families of 60+ (the template)
recs = []                                 # per 2018-2025 target-event
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
        for wd, side, win in sorted(keys):
            snap = S._snapshot(inst, B, session, wd, side, "conf", win, "9999-12-31")
            S._SNAP.clear()
            K = key_data(snap, formed)
            b_min, b_max = C._span(formed, end, win, 0)
            n = len(K["dates"])
            for e in ("R", "X"):
                allc = cells(K, e, range(n), formed)
                for j in range(1, n):
                    d = K["dates"][j]
                    if d <= "2017-12-31":
                        if j >= 60:
                            p = pick(allc[:j], b_min, b_max)
                            if p: dev_pos[(session, e)][(p[0], p[1] - b_min)] += 1
                        continue
                    r1 = v1.get((inst, session, e, (wd, side, win), d))
                    if r1 is None: continue                                   # unknown target or no candidate
                    fam = allc[:j]
                    tg = allc[j]
                    rec = dict(inst=inst, s=session, ev=e, key=(wd, side, win), date=d, N=j, st=r1["st"], yes=r1["yes"],
                               k0=r1["k0"], b0=r1["b0"], hit=r1["hit"], first=r1["first"], b_min=b_min, tg=tg,
                               fam_first=sum(1 for c in fam if c is not None and b_min <= c[1] < b_min + TB),
                               tg_first=int(tg is not None and b_min <= tg[1] < b_min + TB))
                    # the family's modal 0.5-wide band over the whole session (price only)
                    ks = Counter(c[0] for c in fam if c is not None)
                    if ks:
                        lo_k, hi_k = min(ks), max(ks)
                        best = max(range(lo_k - KB + 1, hi_k + 1), key=lambda q: (sum(ks.get(x, 0) for x in range(q, q + KB)), -abs(2 * q + KB)))
                        rec["band_share"] = sum(ks.get(x, 0) for x in range(best, best + KB)) / j
                        rec["band_hit"] = int(tg is not None and best <= tg[0] < best + KB)
                    rec["_cells"] = fam                                        # dropped before writing
                    if r1["st"] == "earned":
                        h = j // 2
                        po = pick(allc[:h], b_min, b_max)                       # the discovery block, frozen
                        val = [i for i in range(h, j) if allc[i] is not None]
                        rng = np.random.default_rng(seed("audit-null", inst, session, wd, side, win, d, e))
                        Hn = [null_hits(K, i, e, (po[0], po[1]), formed, rng, a.reps) for i in val]
                        ok = [q is not None for q in Hn]
                        val = [i for i, o in zip(val, ok) if o]
                        Hn = np.array([q for q in Hn if q is not None])
                        real = np.array([inside(allc[i], po[0], po[1]) for i in val], dtype=float)
                        if len(val) >= 10:
                            q_obs, q_null = real.mean(), Hn.mean(0)
                            G = q_obs - np.median(q_null)
                            p = (1 + np.sum(q_null >= q_obs)) / (len(q_null) + 1)
                            yrs = np.array([K["years"][i] for i in val]); uy = np.unique(yrs)
                            brng = np.random.default_rng(seed("audit-years", inst, session, wd, side, win, d, e))
                            Gs = []
                            for _ in range(300):
                                wts = np.zeros(len(val))
                                for y in brng.choice(uy, len(uy)): wts += yrs == y
                                Gs.append((wts @ real) / wts.sum() - np.median((wts @ Hn) / wts.sum()))
                            rec["null"] = dict(n=len(val), q_obs=float(q_obs), q_null=float(np.median(q_null)), G=float(G), p=float(p),
                                               G_lo=float(np.percentile(Gs, 5)))
                        # E4: at the end of the area's hour, today's own extreme so far
                        t_end = formed + W15 * (r1["b0"] + TB)
                        blk = (r1["k0"], r1["b0"])
                        stt = prefix_state(K, j, e, blk, t_end)
                        if stt is not None and r1["b0"] == b_min:
                            same = [i for i in range(j) if allc[i] is not None and prefix_state(K, i, e, blk, t_end) == "in"]
                            rec["prefix"] = dict(state=stt, cond=(sum(inside(allc[i], *blk) for i in same) / len(same)) if same else None)
                    recs.append(rec)
        print(inst, session, len(recs), "%.0fs" % (time.time() - t0), flush=True)

# Holm over R and X of the same target (synthesis §12.3)
byt = defaultdict(list)
for r in recs:
    if "null" in r: byt[(r["inst"], r["s"], r["key"], r["date"])].append(r)
for rs in byt.values():
    ps = sorted(rs, key=lambda r: r["null"]["p"])
    m, prev = len(ps), 0.0
    for i, r in enumerate(ps):
        prev = max(prev, min(1.0, (m - i) * r["null"]["p"]))
        r["null"]["p_holm"] = prev
for r in recs:
    if "null" in r:
        x = r["null"]
        x["structural"] = x["G"] > 0 and x["p_holm"] <= 0.05 and x["G_lo"] > 0

# the fixed template of each session and event: the most frequent L1 position of 2006-2017 families of 60+
template = {f"{s} {e}": list(c.most_common(1)[0][0]) for (s, e), c in dev_pos.items()}
for r in recs:
    tk, tb = template[f"{r['s']} {r['ev']}"]
    r["tpl_share"] = sum(1 for c in r["_cells"] if c is not None and tk <= c[0] < tk + KB and r["b_min"] + tb <= c[1] < r["b_min"] + tb + TB) / r["N"]
    r["tpl_hit"] = int(r["tg"] is not None and tk <= r["tg"][0] < tk + KB and r["b_min"] + tb <= r["tg"][1] < r["b_min"] + tb + TB)
    del r["_cells"]


def yb(rs, f, reps=300):
    """Mean of f over targets with a 5-95 % interval from resampling whole years."""
    yrs = np.array([int(r["date"][:4]) for r in rs]); uy = np.unique(yrs); v = np.array([f(r) for r in rs], float)
    rng = np.random.default_rng(1); bs = []
    for _ in range(reps):
        idx = np.concatenate([np.flatnonzero(yrs == y) for y in rng.choice(uy, len(uy))]); bs.append(v[idx].mean())
    return [round(float(v.mean()), 4), [round(float(x), 4) for x in np.percentile(bs, [5, 95])]]


res = dict(template=template, E1={}, E2={}, E3={}, E4={}, F1={})
groups = defaultdict(list)
for r in recs: groups[(r["s"], r["ev"])].append(r)
for (s, e), rs in sorted(groups.items()):
    g = f"{s} {e}"
    st = [r for r in rs if r["st"] == "earned" and "null" in r]
    if st:
        res["E1"][g] = dict(n=len(st), families=len({(r["inst"], r["key"]) for r in st}),
                            structural=round(sum(r["null"]["structural"] for r in st) / len(st), 4),
                            q_obs=round(float(np.mean([r["null"]["q_obs"] for r in st])), 4),
                            q_null=round(float(np.mean([r["null"]["q_null"] for r in st])), 4),
                            null_over_obs=round(float(np.mean([r["null"]["q_null"] for r in st]) / np.mean([r["null"]["q_obs"] for r in st])), 3),
                            p_holm_median=round(float(np.median([r["null"]["p_holm"] for r in st])), 4))
    for lab, sub in (("N60+", [r for r in rs if r["N"] >= 60]), ("all", rs)):
        if not sub: continue
        res["E2"][f"{g} {lab}"] = dict(
            n=len(sub), L1_share=yb(sub, lambda r: r["yes"] / r["N"]), L1_hit=yb(sub, lambda r: r["hit"]),
            template_share=yb(sub, lambda r: r["tpl_share"]), template_hit=yb(sub, lambda r: r["tpl_hit"]),
            L1_minus_template_hit=yb(sub, lambda r: r["hit"] - r["tpl_hit"]),
            first_hour_share=yb(sub, lambda r: r["fam_first"] / r["N"]), first_hour_hit=yb(sub, lambda r: r["tg_first"]),
            band_share=yb([r for r in sub if "band_share" in r], lambda r: r["band_share"]), band_hit=yb([r for r in sub if "band_share" in r], lambda r: r["band_hit"]),
            L1_in_first_block=round(float(np.mean([r["first"] for r in sub])), 4))
    stp = [r for r in rs if r["st"] == "earned" and "prefix" in r]
    if stp:
        inn = [r for r in stp if r["prefix"]["state"] == "in"]
        res["E4"][g] = dict(n=len(stp), out_already=round(1 - len(inn) / len(stp), 4), snapshot_share=round(float(np.mean([r["yes"] / r["N"] for r in stp])), 4),
                            in_cond_family=round(float(np.mean([r["prefix"]["cond"] for r in inn if r["prefix"]["cond"] is not None])), 4) if inn else None,
                            in_landed=round(float(np.mean([r["hit"] for r in inn])), 4) if inn else None,
                            out_landed=round(float(np.mean([r["hit"] for r in stp if r["prefix"]["state"] == "out"])), 4) if len(inn) < len(stp) else None)
# E3: who can reach L2 at all
cov = defaultdict(lambda: [0, 0])
for r in recs:
    if r["ev"] != "R": continue
    c = cov[(r["s"], r["key"][2])]; c[0] += 1; c[1] += r["N"] >= 60
for s in ("ADR", "ODR", "RDR"):
    rows = sorted((w, c) for (ss, w), c in cov.items() if ss == s)
    tot = sum(c[0] for _, c in rows)
    res["E3"][s] = dict(targets=tot, n60=round(sum(c[1] for _, c in rows) / tot, 4),
                        by_window={str(w): [c[0], round(c[1] / c[0], 3)] for w, c in rows if c[0] >= 30})
Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print("done %.0fs" % (time.time() - t0))
