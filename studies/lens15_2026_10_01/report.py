"""Lens 15: the tables of the answer from results_<inst>.json (aggregates only).

    python -B studies/lens15_2026_10_01/report.py NQ [ES YM]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEL = ("M", "J", "G")
EV = ("R", "X")
COND = ("first_decade_same_place", "second_decade_holds", "grid_shifts", "resampling_and_one_session", "beats_chance")


def pct(a, b):
    return f"{100 * a / b:.0f} %" if b else "—"


def report(inst):
    doc = json.loads((HERE / f"results_{inst.lower()}.json").read_text(encoding="utf-8"))
    fams, total = doc["families"], sum(doc["sessions_total"].values())
    tested = sum(r["N"] for r in fams)
    print(f"\n## {inst}: {len(fams)} families with N >= 20 ({tested} of {total} confirmed sessions = {pct(tested, total)})")
    print("\nconfirmed main regions: families (sessions of the instrument in those families)")
    print("| event | definition | real | memoryless | real by N 20-49 / 50-99 / 100+ | memoryless by N |")
    print("|---|---|---|---|---|---|")
    for ev in EV:
        for s in SEL:
            row = []
            for ver in ("real", "null"):
                c = [r for r in fams if r["res"][f"{ver}/{ev}/{s}"]["confirmed"]]
                row.append(f"{len(c)} of {len(fams)} ({pct(sum(r['N'] for r in c), total)})")
            bins = []
            for ver in ("real", "null"):
                b = []
                for lo, hi in ((20, 49), (50, 99), (100, 10 ** 6)):
                    sub = [r for r in fams if lo <= r["N"] <= hi]
                    b.append(f"{sum(r['res'][f'{ver}/{ev}/{s}']['confirmed'] for r in sub)}/{len(sub)}")
                bins.append(" · ".join(b))
            print(f"| {ev} | {s} | {row[0]} | {row[1]} | {bins[0]} | {bins[1]} |")
    print("\nwhere the main region of all members lies (start = it begins in the first 30 min of the family's possible hours,")
    print("end = it reaches the last 30 min): real | memoryless; all tested families, then the confirmed ones")
    print("| event | definition | start / middle / end, real | memoryless | confirmed real | confirmed memoryless |")
    print("|---|---|---|---|---|---|")
    for ev in EV:
        for s in SEL:
            cells = []
            for ver in ("real", "null"):
                for only in (False, True):
                    xs = [r["res"][f"{ver}/{ev}/{s}"] for r in fams]
                    xs = [x for x in xs if x["main"] and (x["confirmed"] or not only)]
                    w = {k: sum(x["main"]["where"] == k for x in xs) for k in ("start", "middle", "end")}
                    cells.append(f"{w['start']} / {w['middle']} / {w['end']}")
            print(f"| {ev} | {s} | {cells[0]} | {cells[2]} | {cells[1]} | {cells[3]} |")
    print("\nconditions met (families), real | memoryless")
    print("| event | definition | " + " | ".join(COND) + " |")
    print("|---|---|" + "---|" * len(COND))
    for ev in EV:
        for s in SEL:
            vals = []
            for c in COND:
                a = [sum(bool(r["res"][f"{ver}/{ev}/{s}"].get("conditions", {}).get(c)) for r in fams) for ver in ("real", "null")]
                vals.append(f"{a[0]} \\| {a[1]}")
            print(f"| {ev} | {s} | " + " | ".join(vals) + " |")
    print("\nshare of N in the first / last 30 minutes of the possible hours (N-weighted mean over tested families)")
    for q in ("real/R", "null/R", "real/X", "null/X"):
        x = doc["summary"]["piles/" + q]
        print(f"  {q}: {x['first30']} % / {x['last30']} %")
    print("\nmain regions, median share of N and median ratio to its expectation (J: two histograms; G: memoryless)")
    for ev in EV:
        for s in SEL:
            for ver in ("real", "null"):
                xs = [r["res"][f"{ver}/{ev}/{s}"]["main"] for r in fams if r["res"][f"{ver}/{ev}/{s}"]["main"]]
                sh = sorted(x["share"] for x in xs)
                ra = sorted(x["ratio"] for x in xs if x["ratio"] is not None)
                med = lambda a: a[len(a) // 2] if a else None
                print(f"  {ev} {s} {ver}: share {med(sh)} %, ratio {med(ra)}")
    return fams


def examples(fams, keys):
    print("\nexamples")
    for session, wd, d, win in keys:
        r = next((r for r in fams if (r["session"], r["weekday"], r["direction"], r["window"][0]) == (session, wd, d, win)), None)
        if r is None: continue
        print(f"\n{session} {wd} {d} {win}: N {r['N']}, known {r['known']}, decades {r['first_decade']} / {r['second_decade']}; "
              f"piles {r['piles']}")
        for ev in EV:
            for s in SEL:
                for ver in ("real", "null"):
                    x = r["res"][f"{ver}/{ev}/{s}"]
                    m = x["main"]
                    if not m:
                        print(f"  {ver:4s} {ev} {s}: no region"); continue
                    c = x["conditions"]
                    flags = "".join("+" if c[k] else "." for k in COND)
                    print(f"  {ver:4s} {ev} {s}: {m['price'][0]:+.1f}..{m['price'][1]:+.1f} SD x {m['time'][0]}-{m['time'][1]} "
                          f"{m['share']} % ratio {m['ratio']} [{m['where']}] second decade p {x['second_decade']['p']} "
                          f"shifts {x['shifts_iou']} boot {x['bootstrap']} loo {x['loo_min_iou']} p_max {x['p_max']} {flags} "
                          f"{'CONFIRMED' if x['confirmed'] else ''}")


if __name__ == "__main__":
    for inst in sys.argv[1:] or ["NQ"]:
        fams = report(inst)
        if inst == "NQ":
            examples(fams, [("RDR", "ср", "long", "11:45"), ("ODR", "ср", "long", "04:00")])
