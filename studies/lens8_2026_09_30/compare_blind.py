"""Lens 8: the independent reading (blind_check.md, table of section 1) against contract.py, row by row.

Compared per path and area: the status at t, the four contributions (p_new / p_adm / q / p_seq) and the previous screen's
count. python -B compare_blind.py
"""
from __future__ import annotations

import re
from pathlib import Path

from contract import classify
from synthetic_trace import A, B, L, PATHS

HERE = Path(__file__).resolve().parent


def blind_rows():
    rows = {}
    for line in (HERE / "blind_check.md").read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| Путь") or line.startswith("|---"): continue
        c = [x.strip() for x in line.strip("|").split("|")]
        if len(c) < 9: continue
        m = re.search(r"([01?\-])/([01?\-])/([01?\-])/([01?\-])", c[7])
        if not m: continue
        rows[(c[0].split()[0], c[1])] = (c[2].split()[0], m.groups(), "да" if c[8].startswith("да") else "нет")
    return rows


if __name__ == "__main__":
    theirs, bad = blind_rows(), 0
    cv = lambda v: "?" if v is None else str(v)
    for p in PATHS:
        for K, nm in ((A, "A"), (B, "B")):
            r = classify(p, K, L)
            mine = (r["status"], tuple(cv(r[k]) for k in ("c_new", "c_adm", "c_q", "c_seq")), "да" if r["old"] else "нет")
            if theirs.get((p["name"], nm)) != mine:
                bad += 1
                print("differs:", p["name"], nm, "contract.py", mine, "second reader", theirs.get((p["name"], nm)))
    print(f"rows {2 * len(PATHS)}, in the second reader's table {len(theirs)}, differences {bad}")
