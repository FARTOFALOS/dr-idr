"""Pictures for check 2 of lens 4 from fields.npz (mean fields over states; aggregates only).

Three panels per instrument-session, same axes: the screen's stars (first M5 in a place, at its high / low), the first
visits on a plain 0.1 IDR x 5 min grid (no places), the visits (where price was). Each panel is scaled to its own
maximum: the pictures compare shapes, not levels. One sequential hue (dataviz reference ramp), light surface.
python -B plot_fields.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

HERE = Path(__file__).parent
IMG = Path(__file__).resolve().parents[2] / "meaning" / "img"
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#d9d8d3"
RAMP = ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
CMAP = LinearSegmentedColormap.from_list("seq", RAMP)
MOMENT = {"RDR": 660, "ODR": 300}
END = {"RDR": 960, "ODR": 510}
TITLES = ("Звёзды экрана сейчас:\nпервая M5 в месте, на её high / low",
          "Первые приходы без трёх мест, сетка\n0,1 IDR × 5 мин (шкала без первых 15 мин)",
          "Где цена бывала:\nдоля похожих в клетке")

z = np.load(HERE / "fields.npz")
rows = z["rows"]
clk = lambda m: f"{(m // 60) % 24:02d}:{m % 60:02d}"

for key in ("NQ-RDR", "NQ-ODR"):
    sess = key.split("-")[1]
    t0, t1 = MOMENT[sess], END[sess]
    F = [z[f"{key}-ST"], z[f"{key}-FV"], z[f"{key}-OC"]]
    n = int(z[f"{key}-n"])
    fig, axes = plt.subplots(1, 3, figsize=(15, 6.2), sharey=True, facecolor=SURF)
    for pi, (ax, M, title) in enumerate(zip(axes, F, TITLES)):
        ax.set_facecolor(SURF)
        K = M.shape[1]
        ext = (t0, t0 + 5 * K, rows[0], rows[-1] + 0.1)
        top = M[:, 3:].max() if pi == 1 else M.max()          # first visits: the scale without the first 15 minutes
        ax.imshow(np.minimum(M / max(top, 1e-12), 1), origin="lower", aspect="auto", extent=ext, cmap=CMAP, vmin=0, vmax=1, interpolation="nearest")
        for y in np.arange(-2.0, 3.01, 0.5):
            ax.axhline(y, color=GRID, lw=0.6, zorder=1)
        for y, lab in ((0.0, "край IDR"), (-1.0, "другой край IDR"), (-0.5, "mid")):
            ax.axhline(y, color=INK2, lw=0.9, zorder=2)
        for y in (-0.75, -0.25, 1.0, 1.5):
            ax.axhline(y, color=INK, lw=0.9, ls=(0, (4, 3)), zorder=3)
        ax.axhspan(0.25, 0.5, xmin=0, xmax=0.012, color="#eb6834", zorder=4)
        ax.set_title(title, color=INK, fontsize=11, loc="left")
        ax.set_xlim(t0, t1)
        ticks = list(range(t0, t1 + 1, 60))
        ax.set_xticks(ticks, [clk(m) for m in ticks], color=INK2, fontsize=9)
        ax.tick_params(colors=INK2, labelsize=9)
        for s in ax.spines.values(): s.set_color(GRID)
    axes[0].set_ylabel("цена, в ширинах IDR (0 = край IDR подтверждения)", color=INK2, fontsize=10)
    axes[0].set_yticks(np.arange(-2.0, 3.01, 0.5))
    for y, lab in ((0.0, "0 край IDR"), (-0.5, "−0,5 mid"), (-1.0, "−1 другой край")):
        axes[2].annotate(lab, (t1, y), xytext=(4, 0), textcoords="offset points", va="center", fontsize=8, color=INK2, annotation_clip=False)
    fig.suptitle(f"{key}: подтверждено, момент {clk(t0)}, цена сопоставлена ●, сейчас +0,25…+0,5 (оранжевая метка слева); "
                 f"среднее по {n} моментам 2016–2025", color=INK, fontsize=12, x=0.01, ha="left")
    fig.text(0.01, 0.01, "Пунктир — границы трёх мест экрана (−0,75, −0,25, +1,0, +1,5). Каждая панель в своей шкале: сравниваются формы.",
             color=INK2, fontsize=9)
    fig.tight_layout(rect=(0, 0.03, 0.97, 0.95))
    out = IMG / f"lens4-pole-{key.lower()}.png"
    fig.savefig(out, dpi=110, facecolor=SURF)
    print(out)
