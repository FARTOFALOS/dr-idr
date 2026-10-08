"""Research measurement (not a screen number): what the two marginal NOW shares leave open.

For seeded random history states of the confirmation family (the operator's live situation: after confirmation, before
any break), at cuts 15..120 min after the activation, the B0 set of lab/now24.py (every eligible session of the family
at that clock time) is taken exactly as the screen takes it, and for its sessions we count:
  pR, pX           = the two shares the block shows (cross-checked against /api/d24/now);
  both / R only / X only / neither after the cut;
  among those with any new extreme: which came first (R, X, the same M5).
Read only: imports lab modules, writes research/rabota-1/now_joint.json (local, never committed: market data)."""
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(r"C:\Users\Admin\Claude\dr-idr")
sys.path.insert(0, str(ROOT / "lab"))
import now24 as N  # noqa: E402
import scene24  # noqa: E402

OUT = ROOT / "research" / "rabota-1" / "now_joint.json"
rng = random.Random(20261008)
rows = []
t0 = time.time()
for inst in ("NQ", "ES", "YM"):
    ds = scene24.dates(inst)["dates"]
    for session in ("ODR", "RDR"):
        pool = [d for d, f in ds if session[0] in f and "2024-01-01" <= d <= "2025-12-31"]
        for date in rng.sample(pool, 20):
            f0 = scene24.family(inst, session, None, date, "conf")
            if f0.get("status") != "ok": continue
            c0 = f0["today"]["c0"]
            for dm in (15, 30, 60, 90, 120):
                cut = c0 + dm
                fam = scene24.family(inst, session, cut, date, "auto")
                if fam.get("status") != "ok" or fam.get("view") != "conf" or fam["today"].get("brk") is not None and fam["today"]["brk"] <= cut:
                    continue
                if cut > fam["schedule"]["end"] - 30: continue
                today = fam["today"]
                d = today["side"]
                grid, formed = fam["grid"], fam["schedule"]["formed"]
                c, a_t = (cut - formed - 5) // 5, (today["c0"] - formed - 5) // 5
                day = scene24.day_view(inst, date)
                tick = float(day.get("tick") or 0.25)
                w_t = int(round((today["idrH"] - today["idrL"]) / tick))
                P = N.today_path(day["bars"], grid, tick, d, today["idrH"] if d == 1 else today["idrL"], cut)
                T = N.series(P, a_t, None)
                if c <= a_t or not T["valid"][c]: continue
                S, w, a_mem = N._member_series(fam)
                if S is None: continue
                m = N.masks(S, w, a_mem, T, w_t, a_t, [c])["B0"][:, 0]
                nR, nX, tR, tX = S["newR"][:, c], S["newX"][:, c], S["tauR"][:, c], S["tauX"][:, c]
                k = m & (nR >= 0) & (nX >= 0)
                both, ro, xo, nei = [int((k & a & b).sum()) for a, b in ((nR == 1, nX == 1), (nR == 1, nX == 0), (nR == 0, nX == 1), (nR == 0, nX == 0))]
                kb = k & (nR == 1) & (nX == 1) & (tR > 0) & (tX > 0)
                rf, xf, same = int((kb & (tR < tX)).sum()), int((kb & (tX < tR)).sum()), int((kb & (tR == tX)).sum())
                fR = N.forecast(S, w, m, c, "R"); fX = N.forecast(S, w, m, c, "X")
                rows.append(dict(inst=inst, session=session, date=date, cut=cut, after_min=dm, n=int(m.sum()), known_joint=int(k.sum()),
                                 pR=fR["p_new_extreme"], pX=fX["p_new_extreme"], both=both, R_only=ro, X_only=xo, neither=nei,
                                 both_R_first=rf, both_X_first=xf, both_same_m5=same, both_order_unknown=both - rf - xf - same,
                                 r_seen=round(int(T["r"][c]) / w_t, 3), x_seen=round(int(T["x"][c]) / w_t, 3), close=round(int(T["cl"][c]) / w_t, 3)))
        print(inst, session, len(rows), round(time.time() - t0), flush=True)
OUT.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
print("rows", len(rows), "->", OUT)
