"""Second recheck by Claude, 21.10.2026: two questions that decide what the CN-1 work means. Aggregates only.

F. Does CN-1 actually remove arbitrariness, or replace one arbitrary choice by another?
   zone-map-3: its own diagnostic grid shifts zonemap24.SHIFTS (+half price cell = 0.05 SD, +5 min, +10 min).
   CN-1: the nearest choices nobody could prefer over the declared one: price 0.13 and 0.17 SD with 20 min;
   time 15 and 25 min with 0.15 SD (15/25 are the nearest distinct values on the M5 clock).
   For each zone of the declared map: best Jaccard to the perturbed map; "survives" if >= 0.5.
   "Birth": a zone of the perturbed map with best Jaccard < 0.5 to every declared zone.
   Criterion fixed before the run: CN-1 removes the arbitrariness of zone-map-3 only if, for R and for X
   separately, the share of its zones surviving its perturbations is at least zone-map-3's under its grid shifts
   and its births per perturbed map are not higher. Otherwise non-arbitrariness is not a ground to show CN-1.

G. What a drawn zone contains for action: the share of zone members whose own event (final R or X) lies on the
   first two M5 of its horizon (offset from activation 0 or 5 minutes, i.e. within 10 minutes after the
   confirming M5 closed), against the family. For X, also how often such sessions later broke DR (a label that is
   not a function of the X coordinate). Descriptive; no claim about the market's mechanism.

    %LOCALAPPDATA%\\Python\\bin\\python.exe -B -X utf8 meaning/lens/2026-10-21-constellation-spec/recheck2.py
"""
from __future__ import annotations

import importlib.util
import json
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

CN_PERTURB = [(Fraction(13, 100), 20), (Fraction(17, 100), 20), (P.HP, 15), (P.HP, 25)]
ONSET = 5  # offsets 0 and 5: the first two M5 of the event's own horizon


def compare(base, pert, acc):
    for z in base:
        best = max((len(z & y) / len(z | y) for y in pert), default=0.0)
        acc["zones"] += 1
        acc["best_jaccard_sum"] += best
        acc["survived"] += best >= 0.5
    acc["births"] += sum(max((len(y & z) / len(y | z) for z in base), default=0.0) < 0.5 for y in pert)
    acc["perturbed_maps"] += 1


F = {m: {e: defaultdict(float) for e in "RX"} for m in ("zone-map-3", "CN-1")}
G = {m: {e: defaultdict(int) for e in "RX"} for m in ("family", "zone-map-3", "CN-1")}
for inst in ("NQ", "ES", "YM"):
    B = S._base(inst)
    for block in ("ADR", "ODR", "RDR"):
        for wd in range(5):
            for side in (1, -1):
                for win in (0, 1, 2):
                    snap = S._snapshot(inst, B, block, wd, side, "conf", win, "2026-01-01")
                    mem, N = snap["members"], snap["N"]
                    formed, end = snap["schedule"]["formed"], snap["schedule"]["end"]
                    ids = [m["id"] for m in mem]
                    byid = {m["id"]: m for m in mem}
                    dom = (formed + 15 * win + 5, end - 5)
                    for e in "RX":
                        zm = [set(z["members"]) for z in Z.map_of(mem, e, formed, end, win, ids)["zones"]]
                        for dk, dt in Z.SHIFTS:
                            sh = [set(z["members"]) for z in Z.map_of(mem, e, formed, end, win, ids, dk, dt)["zones"]]
                            compare(zm, sh, F["zone-map-3"][e])
                        pts = P.points_of(mem, e)
                        cn = [z["members"] for z in P.cn(pts, N, time_domain=dom)["zones"]]
                        for hp, ht in CN_PERTURB:
                            alt = [z["members"] for z in P.cn(pts, N, hp, ht, time_domain=dom)["zones"]]
                            compare(cn, alt, F["CN-1"][e])
                        known = [m for m in mem if m[e]["s"] == "known"]
                        for name, rows in (("family", [set(m["id"] for m in known)]), ("zone-map-3", zm), ("CN-1", cn)):
                            g = G[name][e]
                            for z in rows:
                                for sid in z:
                                    m = byid[sid]
                                    onset = m[e]["t"] - m["act"] <= ONSET
                                    g["members"] += 1
                                    g["onset"] += onset
                                    if e == "X" and m["outcome"] in ("held", "broken"):
                                        g["outcome_known_onset" if onset else "outcome_known_later"] += 1
                                        if m["outcome"] == "broken":
                                            g["broken_onset" if onset else "broken_later"] += 1

out = dict(author="Claude (Opus 5.5)", scope="540 confirmation-family maps (270 families x R/X), history < 2026-01-01; aggregates only",
           criterion=__doc__.split("Criterion fixed before the run: ")[1].split("\n\nG.")[0].replace("\n   ", " "))
out["F_arbitrariness"] = {
    m: {e: dict(zones=int(a["zones"]), perturbed_maps=int(a["perturbed_maps"]),
                survived_share=a["survived"] / a["zones"], mean_best_jaccard=a["best_jaccard_sum"] / a["zones"],
                births_per_perturbed_map=a["births"] / a["perturbed_maps"]) for e, a in F[m].items()} for m in F}
verdict = {}
for e in "RX":
    z, c = out["F_arbitrariness"]["zone-map-3"][e], out["F_arbitrariness"]["CN-1"][e]
    verdict[e] = c["survived_share"] >= z["survived_share"] and c["births_per_perturbed_map"] <= z["births_per_perturbed_map"]
out["F_cn1_removes_arbitrariness"] = verdict
out["G_onset_composition"] = {}
for m in G:
    for e in "RX":
        g = G[m][e]
        row = dict(members=g["members"], onset_share=g["onset"] / g["members"] if g["members"] else None)
        if e == "X":
            row["dr_broken_if_onset"] = g["broken_onset"] / g["outcome_known_onset"] if g["outcome_known_onset"] else None
            row["dr_broken_if_later"] = g["broken_later"] / g["outcome_known_later"] if g["outcome_known_later"] else None
        out["G_onset_composition"][f"{m} {e}"] = row
# the YM RDR Tuesday long window-0 R constellation quoted in ITOG.md: onset within two and within three M5
B = S._base("YM")
snap = S._snapshot("YM", B, "RDR", 1, 1, "conf", 0, "2026-01-01")
mem, byid = snap["members"], {m["id"]: m for m in snap["members"]}
formed, end = snap["schedule"]["formed"], snap["schedule"]["end"]
cn = P.cn(P.points_of(mem, "R"), snap["N"], time_domain=(formed + 5, end - 5))["zones"][0]["members"]
zm = set(Z.map_of(mem, "R", formed, end, 0, [m["id"] for m in mem])["zones"][0]["members"])
known = {m["id"] for m in mem if m["R"]["s"] == "known"}
out["G_ym_rdr_R"] = {name: dict(n=len(ids), onset_2_m5=sum(byid[i]["R"]["t"] - byid[i]["act"] <= 5 for i in ids) / len(ids),
                                onset_3_m5=sum(byid[i]["R"]["t"] - byid[i]["act"] <= 10 for i in ids) / len(ids))
                     for name, ids in (("family", known), ("zone-map-3 R1", zm), ("CN-1", cn), ("only CN-1", cn - zm))}
(HERE / "recheck2-results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1))
