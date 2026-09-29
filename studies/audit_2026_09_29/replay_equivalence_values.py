"""Second half of the equivalence check: per-session measured values (extremes, their times, DR held) of the
production cohort vs the vectorised arrays, on sampled history states."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import replay_equivalence as E
from common import dense, load
from models_vec import model_arrays
from replay_core import prep

rng = np.random.default_rng(11)
bad = checked = 0
for inst in ("NQ", "ES", "YM"):
    info, boxes, bars, off = load(inst)
    by = {(b["date"], b["session"]): k for k, b in enumerate(boxes)}
    rdr = sorted(b["date"] for b in boxes if b["session"] == "RDR")
    for sess in ("RDR", "ODR"):
        d = dense(inst, sess); grid, P, conf_by, fail_by = prep(d); M = model_arrays(inst, d)
        cand = np.flatnonzero((d["year"] >= 2016) & d["complete"])
        n_ok = 0
        while n_ok < 12:
            i = int(rng.choice(cand)); t = int(rng.choice(grid))
            if not P[t]["avail"][i]: continue
            mode = ("brk" if fail_by(t)[i] else "conf") if conf_by(t)[i] else "wait"
            E.CUR[inst] = E.fake_raw(inst, str(d["date"][i]), boxes, bars, off, by, rdr, info["tick"])
            prod = E.scene21.cohort(inst, sess, at=t - E.SHIFT[sess])
            if prod.get("status") != "ok": continue
            sel, band, used = E.vec_cohort(d, P, t, i, mode, conf_by, fail_by, M)
            order = np.argsort(d["date"][sel]); sel = sel[order]
            po = np.argsort(prod["sims"]["date"])
            g = lambda k: np.asarray(prod["sims"][k], float)[po]
            Q = P[t][mode]
            same = (np.allclose(g("mx"), np.round(Q["mx"][sel], 4), atol=2e-4) and np.allclose(g("mn"), np.round(Q["mn"][sel], 4), atol=2e-4)
                    and np.array_equal(g("tmx"), Q["tmx"][sel]) and np.array_equal(g("tmn"), Q["tmn"][sel]))
            if mode == "conf": same = same and np.array_equal(np.asarray(prod["sims"]["held"])[po], P[t]["held"][sel])
            checked += 1; bad += not same; n_ok += 1
            if not same: print("   values differ", inst, sess, d["date"][i], t, mode)
        print(inst, sess, "checked", n_ok, flush=True)
print("states", checked, "with differing values", bad)
