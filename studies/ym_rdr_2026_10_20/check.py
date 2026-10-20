"""YM · RDR · 20.10.2026: why the constellation map of this family has one R zone — the density field and every
candidate region of the zone-map-3 rule, recomputed from a saved family snapshot with the production functions.

Input: a snapshot saved from the local server, `/api/d24/family?instrument=YM&session=RDR&at=<min>&view=conf`
(the family is fixed at the confirmation, so `at` does not change it). The snapshot holds per-session records and
stays local (lab/.runtime, hard rule 1). This script writes ONLY aggregates: results.json and the density figure.

    python -B studies/ym_rdr_2026_10_20/check.py <snapshot.json> [--lab lab] [--out studies/ym_rdr_2026_10_20]

Nothing on the screen, in the contract or in the algorithm is changed by this study.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import ndimage

ap = argparse.ArgumentParser()
ap.add_argument("snapshot")
ap.add_argument("--lab", default=str(Path(__file__).resolve().parents[2] / "lab"))
ap.add_argument("--out", default=str(Path(__file__).resolve().parent))
args = ap.parse_args()
sys.path.insert(0, args.lab)
import zonemap24 as zm  # noqa: E402  the production rule, unchanged

S = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
N, formed, end = S["N"], S["schedule"]["formed"], S["schedule"]["end"]
key = S["key"]
assert key["instrument"] == "YM" and key["session"] == "RDR" and S["family_id"] == "94ff135d851522ab", "another family"
assert max(m["date"] for m in S["members"]) <= "2025-12-31", "the history base must stop in 2025"
win = (key["window"][0] - formed) // 15
ids = [m["id"] for m in S["members"]]
hm = lambda t: f"{t // 60:02d}:{t % 60:02d}"
need = max(zm.MIN_ABS, math.ceil(zm.MIN_FRAC * N))
t_first, t_last = formed + 15 * win + 5, end - 5
b_lo, b_hi = (t_first - formed) // 15, (t_last - formed) // 15


def zone_rows(m, dk=0, dt=0):
    return [dict(n=z["n"], share=round(z["n"] / N, 4),
                 price_sd=[round(z["price"][0] / 10 + dk * 0.05, 2), round(z["price"][1] / 10 + dk * 0.05, 2)],
                 time_et=[hm(formed + dt + 15 * z["time"][0]), hm(formed + dt + 15 * z["time"][1])]) for z in m["zones"]]


def field(ev):
    """A(k,b), D(k,b) and the cell -> sessions index of one event, exactly as zonemap24.regions builds them."""
    pts = []
    for m in S["members"]:
        x = m[ev]
        if x["s"] == "known":
            k, b = zm.cell_of(x["v"], m["w"], x["t"], formed)
            pts.append((k, b, m["id"]))
    ks = [p[0] for p in pts]
    k_lo, k_hi = min(ks) - 1, max(ks) + 1
    A = np.zeros((k_hi - k_lo + 1, b_hi - b_lo + 1), dtype=np.int64)
    where = defaultdict(set)
    for k, b, s in pts:
        if b_lo <= b <= b_hi:
            A[k - k_lo, b - b_lo] += 1
            where[(k, b)].add(s)
    D = ndimage.correlate(A, zm.EIGHT, mode="constant", cval=0)
    return pts, A, D, where, k_lo


def components(ev):
    """Every local peak's half-height component and why the rule accepts or rejects it (no per-session output)."""
    pts, A, D, where, k_lo = field(ev)
    peak = (D == ndimage.maximum_filter(D, size=3, mode="constant", cval=0)) & (D > 0)
    out, seen = [], set()
    for i, j in sorted(zip(*np.nonzero(peak)), key=lambda c: (-D[c], c[1], c[0])):
        lam = D[i, j] / 2
        lab, _ = ndimage.label(D >= lam, structure=zm.EIGHT)
        L = lab[i, j]
        if (lam, L) in seen:
            continue
        seen.add((lam, L))
        mask = lab == L
        cells = sorted((int(a) + k_lo, int(c) + b_lo) for a, c in zip(*np.nonzero(mask)))
        n = len(set().union(*(where.get(c, set()) for c in cells)))
        verdict = "joins_higher_peak" if D[mask].max() > D[i, j] else ("below_support" if n < need else "zone")
        ks, bs = [c[0] for c in cells], [c[1] for c in cells]
        out.append(dict(apex_D=int(D[i, j]), apex=[round((i + k_lo) / 10, 1), hm(formed + 15 * (j + b_lo))],
                        level=float(lam), n_sessions_in_component=n, verdict=verdict,
                        price_sd=[min(ks) / 10, (max(ks) + 1) / 10],
                        time_et=[hm(formed + 15 * min(bs)), hm(formed + 15 * (max(bs) + 1))], cells=cells))
    return out


def quantiles(ev):
    vals = sorted(m[ev]["v"] / m["w"] for m in S["members"] if m[ev]["s"] == "known")
    tms = sorted(m[ev]["t"] for m in S["members"] if m[ev]["s"] == "known")
    n = len(vals)
    q = lambda xs, p: xs[min(n - 1, int(p * n))]
    return dict(price_sd={f"q{int(p * 100)}": round(q(vals, p), 2) for p in (.1, .3, .5, .7, .9)},
                time_et={f"q{int(p * 100)}": hm(q(tms, p)) for p in (.1, .3, .5, .7, .9)})


res = dict(study="ym_rdr_2026_10_20", algorithm=zm.VERSION, family_id=S["family_id"], snapshot_id=S["snapshot_id"],
           family=dict(instrument="YM", session="RDR", weekday="Tue", direction=key["direction"],
                       window=[hm(key["window"][0]), hm(key["window"][1])], years="2006-2025", N=N),
           min_support=need, grid=dict(price_sd=0.1, time_min=15, smoothing="3x3 cells (0.3 SD x 45 min)"),
           events={})
for ev in ("R", "X"):
    published = S["zones"][ev]
    base = zm.map_of(S["members"], ev, formed, end, win, ids)
    assert [z["n"] for z in base["zones"]] == [z["n_zone"] for z in published["zones"]], "recomputed != published"
    comps = components(ev)
    res["events"][ev] = dict(
        known=sum(m[ev]["s"] == "known" for m in S["members"]), unknown=published["unknown_count"],
        no_event=published["no_event_count"], residual_share=round(published["residual_share"], 4),
        zones=[dict(label=z["label"], n=z["n_zone"], share=round(z["p_snapshot"], 4),
                    price_sd=[z["price_low"] / 10, z["price_high"] / 10],
                    time_et=[hm(z["time_start"]), hm(z["time_end"])],
                    grid_jaccard=z["grid_member_jaccard"], bootstrap=z["bootstrap_recovery"],
                    null=dict(status=z["null_status"], excess=z.get("null_excess"), interval=z.get("null_interval")))
               for z in published["zones"]],
        shifted_grids=[dict(price_shift_sd=dk * 0.05, time_shift_min=dt, zones=zone_rows(
            zm.map_of(S["members"], ev, formed, end, win, ids, dk, dt), dk, dt)) for dk, dt in zm.SHIFTS],
        components=[{k: v for k, v in c.items() if k != "cells"} for c in comps],
        quantiles_all_known=quantiles(ev))
out = Path(args.out)
(out / "results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

# ---------- figure: the density D of each event and the rule's regions (no stars: only aggregated counts) ----------
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

INK, INK2, MUTED, GRID, SURF, SHIFT = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb", "#2a78d6"
plt.rcParams.update({"font.family": "Segoe UI", "font.size": 9, "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2,
                     "xtick.color": MUTED, "ytick.color": MUTED})


def outline(ax, cells, dk=0.0, dt=0, **kw):
    s = set(map(tuple, cells))
    for k, b in s:
        x0, x1 = formed + dt + 15 * b, formed + dt + 15 * b + 15
        y0, y1 = k / 10 + dk, (k + 1) / 10 + dk
        for nb, seg in (((k + 1, b), ((x0, x1), (y1, y1))), ((k - 1, b), ((x0, x1), (y0, y0))),
                        ((k, b - 1), ((x0, x0), (y0, y1))), ((k, b + 1), ((x1, x1), (y0, y1)))):
            if nb not in s:
                ax.plot(seg[0], seg[1], solid_capstyle="butt", **kw)


def panel(ax, ev, cmap_name, ylim):
    pts, A, D, where, k_lo = field(ev)
    base = plt.get_cmap(cmap_name)
    cmap = ListedColormap(base(np.linspace(0.12, 0.95, 256)))
    cmap.set_bad(SURF)
    Dm = np.ma.masked_where(D == 0, D).astype(float)
    ext = [formed + 15 * b_lo, formed + 15 * (b_hi + 1), k_lo / 10, (k_lo + D.shape[0]) / 10]
    im = ax.imshow(Dm, origin="lower", aspect="auto", cmap=cmap, extent=ext, interpolation="nearest", vmin=1)
    for y in ((0, -0.5, -1.0) if ev == "R" else (0, 0.5, 1.0, 1.5)):
        ax.axhline(y, color=GRID, lw=0.8, zorder=0.5)
    comps = components(ev)
    for z in S["zones"][ev]["zones"]:
        outline(ax, z["cell_mask"], color=INK, lw=2.0, zorder=4)
        ax.text(z["time_end"] + 3, z["price_high"] / 10 + 0.02, f"{z['label']} · зона · {z['n_zone']} сесс.",
                color=INK, fontsize=8.5, fontweight="bold", va="bottom", zorder=5,
                bbox=dict(fc=SURF, ec="none", alpha=0.85, pad=1.2))
    if ev == "R":
        pick = {(9, "below_support"): ("ядро D=9: 5 сесс. < порога 8", (0, (4, 2)), 1.6),
                (8, "joins_higher_peak"): ("контур D=8: 15 сесс., снят как «плечо»", (0, (1.2, 1.6)), 1.6),
                (6, "joins_higher_peak"): ("контур D=6: 28 сесс., снят как «плечо»", (0, (6, 2, 1, 2)), 1.2)}
        used = set()
        for c in comps:
            tag = (c["apex_D"], c["verdict"])
            if tag in pick and tag not in used and (tag[0] != 8 or c["n_sessions_in_component"] == 15):
                used.add(tag)
                text, ls, lw = pick[tag]
                outline(ax, c["cells"], color=INK2, lw=lw, linestyle=ls, zorder=4)
        sh = zm.map_of(S["members"], "R", formed, end, win, ids, 1, 0)
        for z in sh["zones"]:
            outline(ax, z["cells"], dk=0.05, color=SHIFT, lw=1.6, linestyle=(0, (8, 3)), zorder=3)
        handles = [Line2D([], [], color=INK, lw=2, label="зона правила = созвездие на экране"),
                   Line2D([], [], color=INK2, lw=1.6, ls=(0, (4, 2)), label=pick[(9, "below_support")][0]),
                   Line2D([], [], color=INK2, lw=1.6, ls=(0, (1.2, 1.6)), label=pick[(8, "joins_higher_peak")][0]),
                   Line2D([], [], color=INK2, lw=1.2, ls=(0, (6, 2, 1, 2)), label=pick[(6, "joins_higher_peak")][0]),
                   Line2D([], [], color=SHIFT, lw=1.6, ls=(0, (8, 3)),
                          label="та же семья, сетка цены сдвинута на +0,05 SD: зоны 23 и 24 сесс.")]
        ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.0, -0.13), ncol=2, fontsize=7.8,
                  frameon=False)
    ax.set_ylim(*ylim)
    ax.set_xlim(formed, end + 70)
    ticks = list(range(formed, end + 1, 60))
    ax.set_xticks(ticks)
    ax.set_xticklabels([hm(t) for t in ticks])
    ax.set_xlabel("время ET (окно клетки — 15 минут)")
    ax.set_ylabel("цена в ширинах IDR от края IDR (SD); 0 — край по подтверждению, −1 — противоположный")
    ax.set_facecolor(SURF)
    outside = sum(1 for k, b, _ in pts if not (ylim[0] <= k / 10 < ylim[1]))
    ttl = "R — окончательный откат" if ev == "R" else "X — окончательное расширение"
    ax.set_title(f"{ttl}: плотность D и области правила\n(вне кадра по цене: {outside} из {len(pts)} известных)",
                 fontsize=9.5, color=INK, loc="left")
    cb = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.01)
    cb.set_label("D — число окончательных событий в окне 3×3 клетки", color=INK2, fontsize=8)
    cb.outline.set_edgecolor(GRID)


fig, axs = plt.subplots(1, 2, figsize=(15.5, 7.4), facecolor=SURF)
panel(axs[0], "R", "Oranges", (-3.0, 0.8))
panel(axs[1], "X", "Blues", (-0.4, 3.2))
fig.suptitle("YM · RDR · вторник · лонг · подтверждение 10:30–10:45 · семья N = 157 (2006–2025) · zone-map-3, порог поддержки 8",
             x=0.01, ha="left", fontsize=11, color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.95))
(out / "img").mkdir(exist_ok=True)
fig.savefig(out / "img" / "density-rx.png", dpi=130, facecolor=SURF)
print(json.dumps({ev: dict(zones=[(z["label"], z["n"]) for z in r["zones"]], residual=r["residual_share"])
                  for ev, r in res["events"].items()}, ensure_ascii=False))
