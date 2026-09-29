"""Screen.cohort (lenscommon) must select exactly what replay_core.cohort selects (which replay_equivalence.py checked
against lab/scene21.cohort), for confirmed states on the 15-minute grid. Prints the share of identical cohorts."""
from __future__ import annotations

import numpy as np

from lenscommon import INST, Screen, dense, prep, rc_cohort

rng = np.random.default_rng(3)
tot = same = 0
for inst in INST:
    for sess in ("RDR", "ODR"):
        d = dense(inst, sess)
        grid, P, conf_by, fail_by = prep(d)
        S = Screen(d)
        ids = np.flatnonzero(d["complete"] & (d["conf"] >= 0) & (d["year"] >= 2016))
        for i in rng.choice(ids, 60, replace=False):
            for t in grid:
                if not (conf_by(t)[i] and not fail_by(t)[i] and P[t]["avail"][i]): continue
                years = d["year"] < d["year"][i]
                _, a, ba, _ = rc_cohort(d, P, t, i, "conf", conf_by, fail_by, years.copy())
                b, bb, _ = S.cohort(i, t, years.copy())
                tot += 1; same += int(ba == bb and np.array_equal(np.sort(a), np.sort(b)))
print(f"identical cohorts: {same} of {tot}")
