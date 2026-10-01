"""Where the next session lands relative to a zone: in its exact mask, in a hole of its envelope (a cell no historical
event occupied, so outside the mask by §8 / §10), elsewhere. Weekday scope, families of 60+, targets 2018-2025.

    python -B studies/zone_map_2_audit_2026_10_01/holes.py --out studies/zone_map_2_audit_2026_10_01/holes_results.json
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "lab")); sys.path.insert(0, str(HERE))
import scene24 as S  # noqa: E402
import zonemap as Z  # noqa: E402

S.cluster24.of_snapshot = lambda snap, ev: None
ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
res = defaultdict(Counter)
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
            ms = snap["members"]
            for j in range(60, len(ms)):
                if ms[j]["date"] < "2018-01-01": continue
                for e in ("R", "X"):
                    x = ms[j][e]
                    if x["s"] == "unknown": continue
                    tgt = ((10 * x["v"]) // ms[j]["w"], (x["t"] - formed) // 15) if x["s"] == "known" else None
                    pts = [((10 * m[e]["v"]) // m["w"], (m[e]["t"] - formed) // 15, m["id"]) for m in ms[:j] if m[e]["s"] == "known"]
                    occ = {(k, b) for k, b, _ in pts}
                    zm = Z.zone_map(pts, j)
                    c = res[f"{session} {e}"]
                    c["targets"] += 1
                    for z in zm["zones"]:
                        env = (z["k1"] - z["k0"]) * (z["b1"] - z["b0"])
                        holes = [(k, b) for k in range(z["k0"], z["k1"]) for b in range(z["b0"], z["b1"]) if (k, b) not in occ]
                        c["zones"] += 1; c["mask_cells"] += len(z["mask"]); c["envelope_cells"] += env; c["hole_cells"] += len(holes)
                        c["mass"] += z["n"] / j
                        if tgt is None: continue
                        if tgt in z["mask"]: c["in_mask"] += 1
                        elif tgt in set(holes): c["in_hole"] += 1
        print(inst, session, flush=True)
out = {}
for k, c in sorted(res.items()):
    out[k] = dict(targets=c["targets"], zones=c["zones"], hole_share_of_envelope=round(c["hole_cells"] / c["envelope_cells"], 3),
                  mask_share_of_envelope=round(c["mask_cells"] / c["envelope_cells"], 3),
                  landed_in_mask=c["in_mask"], landed_in_hole=c["in_hole"], hole_over_mask=round(c["in_hole"] / max(1, c["in_mask"]), 3),
                  mean_zone_mass=round(c["mass"] / max(1, c["zones"]), 4))
Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False))
