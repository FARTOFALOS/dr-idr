"""What a constellation of screen 24 consists of (audit 2026-10-18, meaning/lens/2026-10-18-audit-sozvezdij/).

Every confirmation family of NQ, ES, YM (weekday scope, the screen's default) with N >= 20 on the whole base
2006-2025, built by the production functions lab/scene24.py::_snapshot and lab/zonemap24.py::map_of. A structural
description of the families as they stand at the end of the base, not a forward test.

Per session and event (R, X):
- how many zones a family has, how much of the family they hold, one zone's share;
- where in time the zone mass lies: early (the zone starts in the activation window or the next 15 minutes), late
  (it reaches the last 15 minutes of the block), middle (neither);
- the order of the session's own final R and X inside early / middle / late zones and in the residual;
- the median depth of early and late zones, and their DR-break share against the family's;
- when final extremes happen: within 60 minutes after the session's own activation, in the last 60 minutes, on the
  first M5 after the activation.

    python -B studies/audit_sozvezdij_2026_10_18/anatomy.py --out studies/audit_sozvezdij_2026_10_18/anatomy.json

Aggregates only (AGENTS.md rule 1).
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "lab"))
import scene21  # noqa: E402
import scene24  # noqa: E402
import zonemap24  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
fam = defaultdict(lambda: defaultdict(list))          # per (session, ev): per-family and per-zone lists
cls_mass = defaultdict(lambda: defaultdict(lambda: [0, 0]))   # members R-before-X, members, by zone class
timing = defaultdict(lambda: defaultdict(int))
for inst in ("NQ", "ES", "YM"):
    B = scene24._base(inst)
    for session in ("RDR", "ODR", "ADR"):
        start, formed, end = scene21.SESS[session]
        nb = (end - formed) // 15
        for wd in range(7):
            for side in (1, -1):
                for win in range(nb):
                    snap = scene24._snapshot(inst, B, session, wd, side, "conf", win, "2026-01-01", "weekday")
                    N = snap["N"]
                    if N < 20: continue
                    mem = snap["members"]; ids = [m["id"] for m in mem]; byid = {m["id"]: m for m in mem}
                    fam_brk = sum(1 for m in mem if m.get("outcome") == "broken") / N
                    for ev in ("R", "X"):
                        key = (session, ev); g = timing[key]; f = fam[key]
                        for m in mem:
                            x = m[ev]
                            if x["s"] != "known": g["unknown"] += 1; continue
                            g["known"] += 1
                            g["first60"] += x["t"] < m["act"] + 60
                            g["last60"] += x["t"] >= end - 60
                            g["first_bar"] += x["t"] == m["act"]
                        zm = zonemap24.map_of(mem, ev, formed, end, win, ids)
                        f["N"].append(N); f["zones"].append(len(zm["zones"]))
                        f["mass"].append(sum(z["n"] for z in zm["zones"]) / N); f["residual"].append(len(zm["residual"]) / N)
                        for z in zm["zones"]:
                            b0, b1 = z["time"]
                            cls = "early" if b0 <= win + 1 else "late" if b1 >= nb else "middle"
                            ms = [byid[s] for s in z["members"]]
                            f["share"].append(z["n"] / N)
                            c = cls_mass[key][cls]; c[0] += sum(1 for m in ms if m["order"] == "R_before_X"); c[1] += len(ms)
                            if cls != "middle":
                                f[cls + "_u"].append(median(m[ev]["v"] / m["w"] for m in ms))
                                f[cls + "_broken_minus_family"].append(sum(1 for m in ms if m.get("outcome") == "broken") / len(ms) - fam_brk)
                        res = [byid[s] for s in zm["residual"]]
                        c = cls_mass[key]["residual"]; c[0] += sum(1 for m in res if m["order"] == "R_before_X"); c[1] += len(res)


def q(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(p * (len(v) - 1) + 0.5))] if v else None


out = {}
for key in sorted(fam):
    f, c, g = fam[key], cls_mass[key], timing[key]
    zm = sum(c[k][1] for k in ("early", "middle", "late"))
    out[" ".join(key)] = dict(
        families=len(f["N"]), N_median=median(f["N"]), zones_per_family_median=median(f["zones"]),
        families_without_zone=round(sum(1 for n in f["zones"] if n == 0) / len(f["zones"]), 3),
        zone_mass_median=round(median(f["mass"]), 3), residual_median=round(median(f["residual"]), 3),
        zone_share_median=round(median(f["share"]), 3), zone_share_p90=round(q(f["share"], 0.9), 3),
        zone_mass_part={k: round(c[k][1] / zm, 3) for k in ("early", "middle", "late")},
        r_before_x={k: round(c[k][0] / max(1, c[k][1]), 3) for k in ("early", "middle", "late", "residual")},
        early_zone_median_u=round(median(f["early_u"]), 2) if f["early_u"] else None,
        late_zone_median_u=round(median(f["late_u"]), 2) if f["late_u"] else None,
        early_zone_broken_minus_family=round(median(f["early_broken_minus_family"]), 3) if f["early_broken_minus_family"] else None,
        late_zone_broken_minus_family=round(median(f["late_broken_minus_family"]), 3) if f["late_broken_minus_family"] else None,
        events_known=g["known"], share_unknown=round(g["unknown"] / (g["known"] + g["unknown"]), 3),
        final_within_60min_of_activation=round(g["first60"] / g["known"], 3),
        final_in_last_60min=round(g["last60"] / g["known"], 3), final_on_first_bar=round(g["first_bar"] / g["known"], 3))
Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
