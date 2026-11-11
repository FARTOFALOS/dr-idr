"""23.5 · the constellations of the joint table (table-cells-1, lab/zonemap24.py::table_map, operator 30.10): what holds on real days.

1. With ':tcells' the family is the same (identity, members, measurements), only its zones differ; without the flag its zones
   are zone-map-3 as they were (screen 24 unchanged).
2. Every cell of a constellation holds at least 2 of the family's known sessions (one session is not a place, an empty cell is
   never part of a constellation); its members are exactly the sessions of its cells; its peak anchor is its strongest cell.
3. Every star cell of the table is in a constellation or belongs to a group below the support; two constellations are more
   than 2 cells apart; zones + residual + unknown + no period = N.
4. The contract re-derives the zones with its own reference (ref_table_map) and the family is CONFORMANT, at every slice of
   the day, today's statuses included; a planted wrong zone is refused.
python -B tests/table_zones235.py
"""
import copy
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lab"))
import contract as C  # noqa: E402
import integration24 as I  # noqa: E402
import scene24 as S  # noqa: E402
import zonemap24 as Z  # noqa: E402

n = 0


def ck(ok, name):
    global n
    if not ok: raise SystemExit("FAIL " + name)
    n += 1
    print("PASS " + name)


conform = lambda f: ((f.get("contract") or {}).get("conformance") or (f.get("contract") or {}).get("status")) == "CONFORMANT"
DAYS = [("ES", "RDR", "2025-12-18", 640), ("NQ", "RDR", "2025-12-17", 645), ("YM", "RDR", "2025-12-18", 660), ("YM", "ODR", "2025-10-20", 270), ("ES", "ADR", "2025-11-20", -60)]
for inst, ses, date, at in DAYS:
    tag = f"{inst} {ses} {date}"
    r = I.scene(inst, ses, at, date, "auto:rpre:tcells", "weekday", [])
    p = I.scene(inst, ses, at, date, "auto:rpre", "weekday", [])
    if r.get("status") != "OK" or r["family"].get("status") != "ok": print(f"skip {tag}: no confirmed family"); continue
    fam, plain = r["family"], p["family"]
    ck(fam["snapshot_id"] == plain["snapshot_id"] and fam["family_id"] == plain["family_id"] and [m["id"] for m in fam["members"]] == [m["id"] for m in plain["members"]], f"{tag}: the same family with and without the flag")
    ck(fam["key"].get("zone_rule") == Z.TABLE_RULE and "zone_rule" not in plain["key"], f"{tag}: the rule is named in the key only when asked")
    ck(all(fam["zones"][e]["algorithm_version"] == Z.TABLE_VERSION and plain["zones"][e]["algorithm_version"] == Z.VERSION for e in "RX"), f"{tag}: {Z.TABLE_VERSION} with the flag, {Z.VERSION} without it")
    ck(conform(fam), f"{tag}: the contract's reference re-derives the zones, CONFORMANT")
    f, N = fam["schedule"]["formed"], fam["N"]
    for e in "RX":
        zm = fam["zones"][e]
        where = {}
        for m in fam["members"]:
            if m[e]["s"] == "known": where.setdefault((S.cell(m[e]["v"], m["w"]), (m[e]["t"] - f) // 15), []).append(m["id"])
        ok_cells = all(len(where.get(tuple(c), ())) >= 2 for z in zm["zones"] for c in z["cell_mask"])
        ok_mem = all(sorted(s for c in z["cell_mask"] for s in where[tuple(c)]) == sorted(z["member_session_ids"]) and z["n_zone"] == len(z["member_session_ids"]) for z in zm["zones"])
        ok_top = all(len(where[tuple(z["peak_anchor"])]) == max(len(where[tuple(c)]) for c in z["cell_mask"]) for z in zm["zones"])
        ck(ok_cells, f"{tag} {e}: every cell of {len(zm['zones'])} constellations holds 2+ sessions (no empty or single cell)")
        ck(ok_mem and ok_top, f"{tag} {e}: members = the sessions of its cells, the anchor = its strongest cell")
        cs = [{tuple(c) for c in z["cell_mask"]} for z in zm["zones"]]
        apart = all(max(abs(a[0] - q[0]), abs(a[1] - q[1])) > 2 for i in range(len(cs)) for j in range(i + 1, len(cs)) for a in cs[i] for q in cs[j])
        ck(apart, f"{tag} {e}: constellations stand more than 2 cells apart")
        ck(sum(z["n_zone"] for z in zm["zones"]) + zm["n_residual_total"] + zm["unknown_count"] + zm["no_event_count"] == N, f"{tag} {e}: zones + residual + unknown + no period = N {N}")
        ck(zm.get("study_refs") is None, f"{tag} {e}: the research table of zone-map-3 is not attached")
        pts = [(k, b, s) for (k, b), v in where.items() for s in v]
        win = (fam["key"]["window"][0] - f) // 15
        last = (fam["schedule"]["end"] - 5 - f) // 15
        want = C.ref_table_map(pts, N, win, last)
        ck([(z["cells"], z["members"]) for z in want["zones"]] == [(sorted(map(tuple, z["cell_mask"])), sorted(z["member_session_ids"])) for z in zm["zones"]], f"{tag} {e}: the reference finds the same constellations")
    bad = copy.deepcopy(fam)
    zs = bad["zones"]["R"]["zones"]
    if zs:
        zs[0]["cell_mask"] = zs[0]["cell_mask"][:-1]
        v, _ = C._verify_zones(bad, bad["zones"]["R"], "R", (r["family"].get("contract") or {}).get("_ref") or dict(members={m["id"]: dict(R=m["R"], X=m["X"]) for m in fam["members"]}))
        ck(any(code == "ZONE_MASK" for code, _, _ in v), f"{tag}: a planted wrong constellation is refused (ZONE_MASK)")
    # every slice of the day: statuses and passports pass the gate
    a, b = fam["schedule"]["formed"], fam["schedule"]["end"]
    slices = conf = 0
    for t in range(a + 15, b + 1, 30):
        q = I.scene(inst, ses, t, date, "auto:rpre:tcells", "weekday", [])
        ff = q.get("family") or {}
        if q.get("status") != "OK" or ff.get("status") != "ok": continue
        slices += 1; conf += conform(ff)
    ck(slices > 0 and slices == conf, f"{tag}: CONFORMANT at all {slices} slices of the day")
# the rule itself on a small table
pts = [(3, 1, "a"), (3, 1, "b"), (4, 1, "c"), (4, 1, "d"), (6, 3, "e"), (6, 3, "f"), (9, 3, "g"), (9, 3, "h"), (20, 8, "i")]
m = Z.table_map(pts, 40, 0, 20)
ck([z["cells"] for z in m["zones"]] == [[(3, 1), (4, 1), (6, 3)]] and m["zones"][0]["members"] == ["a", "b", "c", "d", "e", "f"], "a star cell 2 away joins, 3 away does not; a group below the support stays out")
ck(m["residual"] == ["g", "h", "i"], "the rest is the residual, a single session included")
ck(m["zones"][0]["anchor"] == (3, 1), "equal strongest cells: the earliest window, then nearest 0")
print(f"ALL GOOD · {n} checks")
