"""E6: «пусто» (gapOf in design/sozvezdiya-21/src/panel21.js) out of sample.
The panel shows the widest interval (0.05 IDR steps, >= 0.1 wide, between the 3 % quantile / the opposite DR and the
price) where no similar session's pullback ended, as a place for a stop. If the emptiness were structural, today's
pullback would end inside it much less often than inside an equally wide interval right next to it. Walk-forward
cohorts as in replay_core.py (confirmed, DR intact).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import INST, dense  # noqa: E402
from replay_core import TEST_YEARS, cohort, prep  # noqa: E402


def gap_of(us, u0, wall, stp=0.05):
    us = np.sort(us)
    q3 = us[min(len(us) - 1, int(round(0.03 * (len(us) - 1))))]
    lo = max(q3, wall)
    if lo >= u0: return None
    n = int(np.ceil((u0 - lo) / stp))
    k = np.floor((us - lo) / stp).astype(int)
    cnt = np.bincount(k[(k >= 0) & (k < n)], minlength=n)
    best = None; a = 0
    while a < n:
        if cnt[a]: a += 1; continue
        b = a
        while b < n and not cnt[b]: b += 1
        if a > 0 and b < n and b - a >= 2 and (best is None or b - a > best[1] - best[0]): best = (a, b)
        a = b
    return None if best is None else (lo + best[0] * stp, lo + best[1] * stp)


if __name__ == "__main__":
    for inst in INST:
        for sess in ("RDR", "ODR"):
            d = dense(inst, sess)
            grid, P, conf_by, fail_by = prep(d)
            w = d["idrh"] - d["idrl"]
            opp_u = np.where(d["side"] == 1, (d["drl"] - d["idrh"]) / w, -(d["drh"] - d["idrl"]) / w)   # opposite DR in own conf units
            shown = inside = above = below = 0; widths = []
            for Y in TEST_YEARS:
                for i in np.flatnonzero((d["year"] == Y) & d["complete"]):
                    for t in grid[::2]:
                        if not P[t]["avail"][i] or not conf_by(t)[i] or fail_by(t)[i]: continue
                        pool, sel, band, u0 = cohort(d, P, t, i, "conf", conf_by, fail_by, d["year"] < Y)
                        if len(sel) < 20: continue
                        g = gap_of(P[t]["conf"]["mn"][sel], u0, opp_u[i])
                        if g is None: continue
                        a, b = g; wd = b - a; shown += 1; widths.append(wd)
                        y = P[t]["conf"]["mn"][i]
                        inside += a <= y < b; above += b <= y < b + wd; below += a - wd <= y < a
            print(f"{inst} {sess}: gap shown in {shown} states, median width {np.median(widths):.2f} IDR | today's pullback ended "
                  f"inside the gap {100 * inside / shown:.1f}% vs in the equal interval just above {100 * above / shown:.1f}% / just below {100 * below / shown:.1f}%", flush=True)
