"""Research measurement (not a screen number): the two statistical checks asked on 08.10.

On the same seeded states as now_joint.py, one cut per day-session (30 min after the confirmation), the B0 set of
lab/now24.py exactly as the screen takes it, and for every member its own state at the cut:
  1. joint vs marginals: the share of members that later made BOTH a new R and a new X, against the product of the
     two marginal shares (what independence would give);
  2. order conditioned on the member's own state: the share "new R came first" (among members with a known first new
     extreme, the same M5 excluded) by how close the member stood to its own extreme R vs X at the cut, against a
     driftless random walk between the two extremes (gambler's ruin: P(lower first) = d_high / (d_low + d_high)).
Read only: imports lab modules, writes research/rabota-1/order_by_state.json (local, never committed: market data)."""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(r"C:\Users\Admin\Claude\dr-idr")
sys.path.insert(0, str(ROOT / "lab"))
import now24 as N  # noqa: E402
import scene24  # noqa: E402

rows = json.loads((ROOT / "research" / "rabota-1" / "now_joint.json").read_text(encoding="utf-8"))
states = [r for r in rows if r["after_min"] == 30]
joint, order = [], []
for st in states:
    inst, session, date, cut = st["inst"], st["session"], st["date"], st["cut"]
    fam = scene24.family(inst, session, cut, date, "auto")
    today = fam["today"]; d = today["side"]
    grid, formed = fam["grid"], fam["schedule"]["formed"]
    c, a_t = (cut - formed - 5) // 5, (today["c0"] - formed - 5) // 5
    day = scene24.day_view(inst, date)
    tick = float(day.get("tick") or 0.25)
    w_t = int(round((today["idrH"] - today["idrL"]) / tick))
    P = N.today_path(day["bars"], grid, tick, d, today["idrH"] if d == 1 else today["idrL"], cut)
    T = N.series(P, a_t, None)
    S, w, a_mem = N._member_series(fam)
    m = N.masks(S, w, a_mem, T, w_t, a_t, [c])["B0"][:, 0]
    nR, nX, tR, tX = S["newR"][:, c], S["newX"][:, c], S["tauR"][:, c], S["tauX"][:, c]
    r, x, cl = S["r"][:, c], S["x"][:, c], S["cl"][:, c]
    k = m & (nR >= 0) & (nX >= 0)
    if k.sum() >= 20:
        pr, px = (nR[k] == 1).mean(), (nX[k] == 1).mean()
        joint.append(dict(date=date, inst=inst, session=session, n=int(k.sum()), pR=float(pr), pX=float(px),
                          both=float(((nR == 1) & (nX == 1))[k].mean()), product=float(pr * px)))
    # the first new extreme of every member with a known first time, in its own IDR widths
    for j in np.where(m)[0]:
        if nR[j] < 0 or nX[j] < 0: continue
        rf = nR[j] == 1 and (nX[j] == 0 or (tR[j] > 0 and tX[j] > 0 and tR[j] < tX[j]))
        xf = nX[j] == 1 and (nR[j] == 0 or (tR[j] > 0 and tX[j] > 0 and tX[j] < tR[j]))
        if not (rf or xf): continue                                   # neither, the same M5, or an unknown first time
        dl, dh = (cl[j] - r[j]) / w[j], (x[j] - cl[j]) / w[j]
        if dl < 0 or dh < 0 or dl + dh == 0: continue
        order.append(dict(date=date, inst=inst, R_first=bool(rf), d_low=float(dl), d_high=float(dh)))
    print(inst, session, date, len(joint), len(order), flush=True)

out = ROOT / "research" / "rabota-1" / "order_by_state.json"
out.write_text(json.dumps(dict(joint=joint, order=order)), encoding="utf-8")

J = joint
diff = np.array([q["both"] - q["product"] for q in J])
print(f"\n1. joint vs product of marginals, {len(J)} states (one per day-session): both — median {np.median([q['both'] for q in J]):.3f}; "
      f"product — median {np.median([q['product'] for q in J]):.3f}; both − product median {np.median(diff):+.3f}, q10–q90 {np.quantile(diff, .1):+.3f}…{np.quantile(diff, .9):+.3f}; "
      f"both < product in {int((diff < 0).sum())} of {len(J)}")
O = order
pos = np.array([q["d_low"] / (q["d_low"] + q["d_high"]) for q in O])      # 0 = at its own bottom, 1 = at its own top
rf = np.array([q["R_first"] for q in O])
gr = np.array([q["d_high"] / (q["d_low"] + q["d_high"]) for q in O])     # random walk: lower first
print(f"\n2. order by the member's own position at the cut ({len(O)} member-cases; members repeat across states):")
for lo, hi in ((0, .2), (.2, .4), (.4, .6), (.6, .8), (.8, 1.0001)):
    s = (pos >= lo) & (pos < hi)
    if s.sum(): print(f"   position {lo:.1f}–{min(hi, 1):.1f} (0 = own bottom): n {int(s.sum()):5d} · R first {rf[s].mean():.2f} · random walk {gr[s].mean():.2f}")
print(f"   all: R first {rf.mean():.2f} · random walk {gr.mean():.2f}")
