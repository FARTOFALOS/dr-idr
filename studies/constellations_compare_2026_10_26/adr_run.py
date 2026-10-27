"""The 26.10 comparison stand on ADR confirmation families (not covered by the study). Aggregates only: results_adr.json. python -B studies/constellations_compare_2026_10_26/adr_run.py"""
import json
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lab"))
import compare as C  # noqa: E402

if __name__ == "__main__":
    total = defaultdict(lambda: defaultdict(float))
    with ProcessPoolExecutor(max_workers=3) as ex:
        for inst, session, acc, sec in ex.map(C.job, [(i, "ADR") for i in C.INSTS]):
            print(inst, session, sec, "s", flush=True)
            for k, v in acc.items():
                for f, x in v.items(): total[k][f] += x
    res = {}
    for k, v in total.items():
        n = v["targets"]
        res[k] = dict(targets=int(n), zones=v["zones"] / n, empty=v["empty"] / n, mass=v["mass"] / n,
                      transfer=v["landed"] / v["mass"] if v["mass"] else None, top_share=v["top_share"] / n,
                      top_transfer=v["top_landed"] / v["top_mass"] if v["top_mass"] else None,
                      rest_transfer=v["rest_landed"] / v["rest_mass"] if v["rest_mass"] else None,
                      grid_flip=v["flip_any"] / v["flip_n"] if v["flip_n"] else None,
                      post_share=v["post_share"] / v["post_n"] if v["post_n"] else None)
    json.dump(res, open(C.HERE / "results_adr.json", "w"), indent=1)
    print("done")
