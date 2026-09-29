"""The diagnostic read of anchor_placebo.json: across all start times of a one-hour window (every 5 minutes, starts
with >= 1500 windows), DR true against the median ratio of the box range to the REALISED range of the next 240 minutes
(a quadratic in the log ratio). Residuals at the anchors 03:00, 09:30, 19:30. This explains the frequencies after the
fact; for what is known before the window closes see anchor_exante.py.

python -B studies/audit_2026_09_29/anchor_placebo_fit.py > studies/audit_2026_09_29/anchor_placebo_fit.log
"""
import json
from pathlib import Path

import numpy as np

d = json.loads(Path(__file__).with_name("anchor_placebo.json").read_text(encoding="utf-8"))
for inst, r in d.items():
    xs, ys, ts = [], [], []
    for j, v in r.items():
        if v["true"] is None or v["n"] < 1500: continue
        xs.append(v["ratio"]); ys.append(v["true"]); ts.append(v["t"])
    xs, ys = np.array(xs), np.array(ys)
    X = np.vstack([np.ones_like(xs), np.log(xs), np.log(xs) ** 2]).T
    b, *_ = np.linalg.lstsq(X, ys, rcond=None)
    fit = X @ b; res = ys - fit
    r2 = 1 - ((ys - fit) ** 2).sum() / ((ys - ys.mean()) ** 2).sum()
    print(f"{inst}: starts {len(xs)}, corr(DR true, log ratio) {np.corrcoef(np.log(xs), ys)[0, 1]:.3f}, R2 {r2:.3f}, residual sd {res.std():.2f} pp")
    for a in ("03:00", "09:30", "19:30"):
        k = ts.index(a)
        print(f"   {a}: DR true {ys[k]:.1f}%, curve {fit[k]:.1f}%, residual {res[k]:+.2f} pp (rank {int((res > res[k]).sum()) + 1} of {len(xs)})")
    top = np.argsort(-ys)[:4]
    print("   highest DR true:", ", ".join(f"{ts[k]} {ys[k]:.1f}% (ratio {xs[k]:.2f})" for k in top))
