"""Lens 15: one family's R and X on the 0.1 SD x 15 min grid — the real sessions next to the expectation of memoryless
paths made of the same candles — with the main regions of the three definitions (M, J, G) from results_<inst>.json.

    python -B studies/lens15_2026_10_01/figure.py NQ ODR ср long 04:00 meaning/img/lens15-odr.png

Aggregates only: cell counts of the family and the averaged expectation; no dates, no paths.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import selector as SEL  # noqa: E402

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
SURF = "#fcfcfb"
COL = {"M": "#2a78d6", "J": "#eb6834", "G": "#1baf7a"}          # categorical slots 1-3 (validated all-pairs)
NAME = {"M": "M · где больше всего (0,3 SD × 45 мин)", "J": "J · сверх двух гистограмм (линза)",
        "G": "G · сверх пути без памяти"}
GRAYS = matplotlib.colors.LinearSegmentedColormap.from_list("seq", ["#fcfcfb", "#d9d8d3", "#9a9893", "#52514e", "#1d1c1a"])
K_FIG = 400


def family_data(inst, session, weekday, direction, window):
    recs, f, E = SEL.sessions_real(inst, session)
    side = 1 if direction == "long" else -1
    wd = SEL.DAYS.index(weekday)
    h, m = map(int, window.split(":"))
    t = h * 60 + m
    if session == "ADR" and t >= 12 * 60: t -= 1440
    w0 = (t - f) // 15
    mem = [r for r in recs if r["key"] == (wd, side, w0)]
    return mem, f, E, w0


def grid_of(mem, f, E, w0, rng):
    kn = [r for r in mem if r["known"]]
    w = np.array([r["w"] for r in kn])
    out = {}
    for ev in SEL.EVENTS:
        v = np.array([r[ev][0] for r in kn]); t = np.array([r[ev][1] for r in kn])
        k, b = SEL.cells(v, t, w, f)
        reps = [SEL.memoryless(r, K_FIG, rng) for r in kn]
        j = 0 if ev == "R" else 2
        kv = np.array([x[j] for x in reps]); kt = np.array([x[j + 1] for x in reps])
        kb, bb = SEL.cells(kv, kt, w[:, None], f)
        out[ev] = (k, b, kb.ravel(), bb.ravel())
    return out, len(mem)


def main():
    inst, session, weekday, direction, window, png = sys.argv[1:7]
    mem, f, E, w0 = family_data(inst, session, weekday, direction, window)
    res = json.loads((HERE / f"results_{inst.lower()}.json").read_text(encoding="utf-8"))
    fam = next(r for r in res["families"] if r["session"] == session and r["weekday"] == weekday
               and r["direction"] == direction and r["window"][0] == window)
    data, N = grid_of(mem, f, E, w0, np.random.default_rng(SEL.SEED + 7))
    b_lo, b_hi = SEL.domain(w0, f, E)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "figure.facecolor": SURF, "axes.facecolor": SURF})
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.6), sharex=True, constrained_layout=True)
    ev_name = {"R": "R — самая глубокая точка против подтверждения", "X": "X — самая дальняя точка по подтверждению"}
    for row, ev in enumerate(SEL.EVENTS):
        k, b, kb, bb = data[ev]
        regs = [fam["res"][f"real/{ev}/{s}"]["main"]["cells"] for s in SEL.SELECTORS if fam["res"][f"real/{ev}/{s}"]["main"]]
        lo = min([int(np.percentile(k, 3))] + [r[0] for r in regs]) - 2
        hi = max([int(np.percentile(k, 97))] + [r[1] for r in regs]) + 3
        nk, nb = hi - lo + 1, b_hi - b_lo + 1

        def tab(kk, bbb, wgt=1.0):
            s = (kk >= lo) & (kk <= hi)
            T = np.zeros((nk, nb)); np.add.at(T, (kk[s] - lo, bbb[s] - b_lo), wgt)
            return 100 * T / N
        real, null = tab(k, b), tab(kb, bb, 1.0 / K_FIG)
        vmax = max(real.max(), null.max())
        for col, (T, title) in enumerate(((real, "сессии семьи"), (null, "путь без памяти из тех же свечей (ожидание)"))):
            ax = axes[row, col]
            ext = (f + 15 * b_lo, f + 15 * (b_hi + 1), lo / 10, (hi + 1) / 10)
            im = ax.imshow(T, origin="lower", aspect="auto", extent=ext, cmap=GRAYS, vmin=0, vmax=vmax, interpolation="nearest")
            ax.set_title(f"{ev_name[ev]}\n{title}", fontsize=9, color=INK, loc="left")
            ax.axhline(0, color=INK2, lw=0.8, ls=":")
            ax.axhline(-1, color=INK2, lw=0.8, ls=":")
            for sel in SEL.SELECTORS:
                x = fam["res"][f"real/{ev}/{sel}"]
                if not x["main"]: continue
                k1, k2, b1, b2 = x["main"]["cells"]
                ls = "-" if x["confirmed"] else "--"
                ax.add_patch(Rectangle((f + 15 * b1, k1 / 10), 15 * (b2 - b1 + 1), (k2 - k1 + 1) / 10, fill=False,
                                       ec=COL[sel], lw=2, ls=ls))
                if col == 0:
                    y, va = ((k1 / 10) - 0.03, "top") if sel == "M" else ((k2 + 1) / 10 + 0.03, "bottom")
                    ax.text(f + 15 * (b2 + 1) + 3, y, f"{sel} {x['main']['share']:g} %", color=INK, fontsize=8,
                            va=va, ha="left", bbox=dict(fc=SURF, ec=COL[sel], lw=1, pad=1.5))
            ticks = list(range(f + 15 * b_lo - (f + 15 * b_lo) % 60 + 60, f + 15 * (b_hi + 1) + 1, 60))
            ax.set_xticks(ticks, [SEL.clk(t) for t in ticks])
            ax.set_ylabel("SD (ширина IDR) от края игры")
            ax.grid(False)
            cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.01)
            cb.set_label("% семьи в клетке 0,1 SD × 15 мин", color=INK2)
            cb.outline.set_edgecolor(GRID)
    handles = [plt.Line2D([], [], color=COL[s], lw=2, label=NAME[s]) for s in SEL.SELECTORS]
    handles += [plt.Line2D([], [], color=INK2, lw=2, ls="-", label="сплошная — подтверждён по §7.2"),
                plt.Line2D([], [], color=INK2, lw=2, ls="--", label="пунктир — только кандидат")]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.07), fontsize=8.5)
    fig.suptitle(f"{inst} {session} · {weekday} · {'лонг' if direction == 'long' else 'шорт'} · подтверждение "
                 f"{window}–{SEL.clk(f + 15 * w0 + 15)} · N {N} (2006–2025)", color=INK, fontsize=11, x=0.01, ha="left")
    fig.savefig(png, dpi=130, bbox_inches="tight")
    print("written", png)


if __name__ == "__main__":
    main()
