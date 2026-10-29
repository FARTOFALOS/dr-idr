"""Independent recheck of the CN-1 package by Claude, 21.10.2026 (aggregates only).

Does not rewrite Codex's files: validation.json, probe-results.json and the receipt stay as they were. It checks
that they are intact, reproduces the stored numbers, then tests three claims the recommendation leans on:
  B  the deletion stability of CN-1 is not only an effect of bigger zones (recovery by zone size);
  C  how often the SHARED_BORDER and SMALL_COMPONENT rules actually act (540 maps);
  D  stability under a stronger perturbation (half of the family removed, 20 times, the same 18 maps);
  E  YM RDR Tuesday long window 0, R: is the late deep mass a density below support or no density at all.
Writes recheck-results.json and img/cn1-ym-rdr.png. The picture has no stars: background = number of known final
events in the CN-1 neighbourhood of each 0.1 SD x 15 min cell centre; outlines = regions (display raster, float).
Every count in the JSON comes from the exact rational rule in probe.py.

    %LOCALAPPDATA%\\Python\\bin\\python.exe -B -X utf8 meaning/lens/2026-10-21-constellation-spec/recheck.py
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import statistics
import sys
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("probe", HERE / "probe.py")
P = importlib.util.module_from_spec(spec)
sys.modules["probe"] = P
spec.loader.exec_module(P)
sys.path.insert(0, str(ROOT / "lab"))
import scene24 as S  # noqa: E402
import zonemap24 as Z  # noqa: E402

DIGEST = "25dc061c850eb0d2352754f7844dd4b7a3ac22697b96796975977d190af3ae06"
out = dict(author="Claude (Opus 5.5), independent recheck of Codex CN-1", scope="aggregates only; history < 2026-01-01")

# 0. Codex's package is intact (its own receipt is not rewritten)
stored = json.loads((HERE / "validation.json").read_text(encoding="utf-8"))["artifact_hashes"]
out["codex_files_intact"] = {n: hashlib.sha256((HERE / n).read_bytes()).hexdigest() == h for n, h in stored.items()}
out["checkpoint_json_present"] = (HERE / "CHECKPOINT.json").exists()

# A. the stored historical numbers reproduce exactly
hist = P.historical()
keys = ["label", "N", "known", "old", "cn1", "deletion_recovery_old", "deletion_recovery_cn1", "scales", "ym_zone_aggregates"]
numbers = {"groups": hist["groups"], "diagnostics": [{k: x[k] for k in keys} for x in hist["diagnostics"]]}
out["A_numeric_digest_reproduced"] = hashlib.sha256(json.dumps(numbers, sort_keys=True).encode()).hexdigest() == DIGEST
out["A_scale_recovery_min_max"] = {
    f"{s['price_radius']}/{s['time_radius']}": [min(d["scales"][i]["recovery"] or 0 for d in hist["diagnostics"]),
                                               max(d["scales"][i]["recovery"] or 0 for d in hist["diagnostics"])]
    for i, s in enumerate(hist["diagnostics"][0]["scales"])}
out["A_scale_maps_below_0_5"] = sum((s["recovery"] or 0) < 0.5 for d in hist["diagnostics"] for s in d["scales"])

# C. the border rules over all 540 maps; collect the 18 diagnostic families
c = dict(maps=0, maps_with_shared=0, shared_cases=0, maps_with_small_component=0, small_component_cases=0,
         maps_one_zone=0, maps_no_zone=0, cases=0)
selected = []
for inst in ("NQ", "ES", "YM"):
    B = S._base(inst)
    for block in ("ADR", "ODR", "RDR"):
        for wd in range(5):
            for side in (1, -1):
                for win in (0, 1, 2):
                    snap = S._snapshot(inst, B, block, wd, side, "conf", win, "2026-01-01")
                    for ev in ("R", "X"):
                        pts = P.points_of(snap["members"], ev)
                        dom = (snap["schedule"]["formed"] + 15 * win + 5, snap["schedule"]["end"] - 5)
                        r = P.cn(pts, snap["N"], time_domain=dom)
                        c["maps"] += 1
                        c["cases"] += snap["N"]
                        c["maps_with_shared"] += bool(r["shared"])
                        c["shared_cases"] += len(r["shared"])
                        c["maps_with_small_component"] += bool(r["rejected"])
                        c["small_component_cases"] += sum(len(z["members"]) for z in r["rejected"])
                        c["maps_one_zone"] += len(r["zones"]) == 1
                        c["maps_no_zone"] += not r["zones"]
                        if wd == 1 and side == 1 and win == 0:
                            selected.append((inst, block, ev, snap, pts, dom))
out["C_border_rules"] = c


# B + D. recovery by zone size (10 % deletion) and under half samples
def per_zone(original, changed, retained):
    rows = []
    for z in original["zones"]:
        a = z["members"] & retained
        if a:
            rows.append((len(z["members"]), max((len(a & b["members"]) / len(a | b["members"]) for b in changed["zones"]), default=0)))
    return rows


by_size = {"zone-map-3": [], "CN-1": []}
half = []
for inst, block, ev, snap, pts, dom in selected:
    label, members = f"{inst} {block} {ev}", snap["members"]
    old, new = P.old_map(members, ev, snap, Z), P.cn(pts, snap["N"], time_domain=dom)
    for mode, frac in (("del10", 0.10), ("half", 0.50)):
        rng = random.Random(int(hashlib.sha256((label + mode).encode()).hexdigest()[:16], 16))
        ro, rn = [], []
        for _ in range(20):
            discard = set(rng.sample(range(len(members)), max(1, int(len(members) * frac))))
            kept = [m for i, m in enumerate(members) if i not in discard]
            ids = {m["id"] for m in kept}
            zo = per_zone(old, P.old_map(kept, ev, snap, Z), ids)
            zn = per_zone(new, P.cn(P.points_of(kept, ev), len(kept), time_domain=dom), ids)
            if mode == "del10":
                by_size["zone-map-3"] += zo
                by_size["CN-1"] += zn
            ro += [x for _, x in zo]
            rn += [x for _, x in zn]
        if mode == "half":
            half.append(dict(label=label, zone_map_3=statistics.mean(ro) if ro else 0, cn1=statistics.mean(rn) if rn else 0,
                             zones_zone_map_3=len(old["zones"]), zones_cn1=len(new["zones"])))


def binned(rows):
    bins = defaultdict(list)
    for size, rec in rows:
        bins["a <15" if size < 15 else "b 15-29" if size < 30 else "c >=30"].append(rec)
    return {k[2:]: dict(zone_draws=len(v), mean_recovery=statistics.mean(v)) for k, v in sorted(bins.items())}


out["B_deletion10_recovery_by_original_zone_size"] = {k: binned(v) for k, v in by_size.items()}
out["D_half_sample_maps"] = half
for ev in ("R", "X"):
    rows = [h for h in half if h["label"].endswith(ev)]
    out[f"D_half_sample_{ev}"] = dict(maps=len(rows), zone_map_3=statistics.mean(h["zone_map_3"] for h in rows),
                                      cn1=statistics.mean(h["cn1"] for h in rows),
                                      cn1_higher=sum(h["cn1"] > h["zone_map_3"] for h in rows))

# E. YM RDR R: the late deep mass under the declared and neighbouring scales (exploratory beyond the protocol)
ym = {ev: (snap, pts, dom) for inst, block, ev, snap, pts, dom in selected if (inst, block) == ("YM", "RDR")}
snap, pts, dom = ym["R"]
N, m = snap["N"], max(4, (snap["N"] + 19) // 20)
late = [p for p in pts if p.t >= 13 * 60 + 30 and p.u <= Fraction(-2, 5)]
e = dict(N=N, support_m=m, late_deep_known=len(late), late_deep_share=len(late) / N, scales={})
for hp, ht, declared in [(Fraction(3, 20), 20, "CN-1"), (Fraction(1, 10), 20, "protocol"), (Fraction(1, 5), 20, "protocol"),
                         (Fraction(3, 20), 15, "protocol"), (Fraction(3, 20), 25, "protocol"),
                         (Fraction(1, 4), 30, "exploratory"), (Fraction(3, 10), 45, "exploratory")]:
    r = P.cn(pts, N, hp, ht, time_domain=dom)
    e["scales"][f"{hp}/{ht}"] = dict(
        declared_in=declared, best_late_neighbourhood=max(sum(P.near(p, q, hp, ht) for q in pts) for p in late),
        zones=[dict(n=len(z["members"]), core_time_et=[min(q.t for q in z["cores"]), max(q.t for q in z["cores"])])
               for z in r["zones"]])
out["E_ym_rdr_late_R"] = e

(HERE / "recheck-results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

# Picture: YM RDR Tuesday long window 0, R and X; no stars
import numpy as np  # noqa: E402
import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"
plt.rcParams.update({"font.family": "Segoe UI", "font.size": 9, "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK2,
                     "xtick.color": MUTED, "ytick.color": MUTED})
formed, end = snap["schedule"]["formed"], snap["schedule"]["end"]
hm = lambda t: f"{t // 60:02d}:{t % 60:02d}"
HPF, HTF = float(P.HP), float(P.HT)


def panel(ax, ev, cmap_name, ylim):
    s, pts, dom = ym[ev]
    U = np.array([float(p.u) for p in pts])
    T = np.array([p.t for p in pts], dtype=float)
    # background: CN-1 neighbourhood count at 0.1 SD x 15 min cell centres (coarse on purpose)
    ks = np.arange(int(np.floor(ylim[0] * 10)), int(np.ceil(ylim[1] * 10)))
    bs = np.arange(0, (end - formed) // 15)
    D = np.zeros((len(ks), len(bs)))
    for i, k in enumerate(ks):
        for j, b in enumerate(bs):
            uq, tq = (k + 0.5) / 10, formed + 15 * b + 7.5
            D[i, j] = np.sum((np.abs(U - uq) <= HPF) & (np.abs(T - tq) <= HTF))
    cmap = ListedColormap(plt.get_cmap(cmap_name)(np.linspace(0.12, 0.95, 256)))
    cmap.set_bad(SURF)
    im = ax.imshow(np.ma.masked_where(D == 0, D), origin="lower", aspect="auto", cmap=cmap, interpolation="nearest",
                   extent=[formed, formed + 15 * len(bs), ks[0] / 10, (ks[-1] + 1) / 10], vmin=1)
    for y in ((0, -0.5, -1.0, -1.5, -2.0, -2.5) if ev == "R" else (0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0)):
        ax.axhline(y, color=GRID, lw=0.8, zorder=0.5)
    # CN-1 regions: unique nearest core component within distance 1, inside the outcome's time domain
    r = P.cn(pts, s["N"], time_domain=dom)
    tg = np.arange(formed, end + 1, 1.0)
    ug = np.arange(ylim[0], ylim[1], 0.005)
    TT, UU = np.meshgrid(tg, ug)
    dist = []
    for comp in r["all_cores"]:
        cu = np.array([float(q.u) for q in comp])[:, None, None]
        ct = np.array([q.t for q in comp], dtype=float)[:, None, None]
        dist.append(np.min(np.maximum(np.abs(UU - cu) / HPF, np.abs(TT - ct) / HTF), axis=0))
    published = {z["component"]: len(z["members"]) for z in r["zones"]}
    if dist:
        dist = np.array(dist)
        best = dist.min(axis=0)
        owner = dist.argmin(axis=0)
        unique = (dist == best).sum(axis=0) == 1
        inside = (best <= 1) & unique & (TT >= dom[0]) & (TT <= dom[1])
        for k, n in published.items():
            mask = (inside & (owner == k)).astype(float)
            ax.contour(TT, UU, mask, levels=[0.5], colors=[INK], linewidths=2.0, zorder=4)
            yy, xx = np.nonzero(mask)
            ax.text(TT[0, xx.max()] + 3, UU[yy.min(), 0] - 0.03, f"CN-1 · {n} сесс. ({n / s['N']:.0%})", color=INK,
                    fontsize=8.5, fontweight="bold", va="top", zorder=5, bbox=dict(fc=SURF, ec="none", alpha=0.85, pad=1.2))
    # zone-map-3 zones of the same family, as on the screen today
    win = (s["key"]["window"][0] - formed) // 15
    raw = Z.map_of(s["members"], ev, formed, end, win, [mm["id"] for mm in s["members"]])
    for z in raw["zones"]:
        cells = set(map(tuple, z["cells"]))
        for k, b in cells:
            x0, x1, y0, y1 = formed + 15 * b, formed + 15 * b + 15, k / 10, (k + 1) / 10
            for nb, seg in (((k + 1, b), ((x0, x1), (y1, y1))), ((k - 1, b), ((x0, x1), (y0, y0))),
                            ((k, b - 1), ((x0, x0), (y0, y1))), ((k, b + 1), ((x1, x1), (y0, y1)))):
                if nb not in cells:
                    ax.plot(seg[0], seg[1], color=INK2, lw=1.4, linestyle=(0, (4, 2)), zorder=3)
    ax.set_ylim(*ylim)
    ax.set_xlim(formed, end + 75)
    ticks = list(range(formed, end + 1, 60))
    ax.set_xticks(ticks)
    ax.set_xticklabels([hm(t) for t in ticks])
    ax.set_xlabel("время ET (открытие M5)")
    ax.set_ylabel("цена в ширинах IDR от края IDR (SD); 0 — край по подтверждению")
    ax.set_facecolor(SURF)
    title = "R — окончательный откат" if ev == "R" else "X — окончательное расширение"
    ax.set_title(f"{title}\nзоны: CN-1 {len(r['zones'])} · zone-map-3 {len(raw['zones'])}", fontsize=9.5, color=INK, loc="left")
    cb = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.01)
    cb.set_label("событий семьи в окрестности ±0,15 SD × ±20 мин", color=INK2, fontsize=8)
    cb.outline.set_edgecolor(GRID)


fig, axs = plt.subplots(1, 2, figsize=(15.5, 7.4), facecolor=SURF)
panel(axs[0], "R", "Oranges", (-3.0, 0.8))
panel(axs[1], "X", "Blues", (-0.4, 3.2))
axs[0].legend(handles=[Line2D([], [], color=INK, lw=2, label="область CN-1 (точный предикат, растр для показа)"),
                       Line2D([], [], color=INK2, lw=1.4, ls=(0, (4, 2)), label="зона zone-map-3 (как на экране сейчас)")],
              loc="upper left", bbox_to_anchor=(0.0, -0.12), ncol=2, fontsize=8, frameon=False)
fig.suptitle(f"YM · RDR · вторник · лонг · подтверждение 10:30–10:45 · N = {snap['N']} (2006–2025) · CN-1 ±0,15 SD × ±20 мин, опора {m}",
             x=0.01, ha="left", fontsize=11, color=INK)
fig.tight_layout(rect=(0, 0, 1, 0.95))
(HERE / "img").mkdir(exist_ok=True)
fig.savefig(HERE / "img" / "cn1-ym-rdr.png", dpi=130, facecolor=SURF)
print(json.dumps({k: v for k, v in out.items() if k != "D_half_sample_maps"}, ensure_ascii=False, indent=1))
