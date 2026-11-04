"""Research probe of CN-1; no server/UI imports or writes to the market base.

Only aggregates are written. Exact integer/Fraction comparisons define membership.
This is a specification witness, not an installed product calculator.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import statistics
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VERSION = "constellation-neighbourhood-1"
HP, HT = Fraction(3, 20), 20


@dataclass(frozen=True)
class Point:
    sid: str
    v: int
    w: int
    t: int

    @property
    def u(self):
        return Fraction(self.v, self.w)


def near(a, b, hp=HP, ht=HT):
    return abs(a.t-b.t) <= ht and abs(a.v*b.w-b.v*a.w)*hp.denominator <= hp.numerator*a.w*b.w


def distance(a, b, hp=HP, ht=HT):
    return max(Fraction(abs(a.v*b.w-b.v*a.w)*hp.denominator, a.w*b.w*hp.numerator), Fraction(abs(a.t-b.t), ht))


def cn(points, N, hp=HP, ht=HT, time_domain=None):
    pts = sorted(points, key=lambda p: p.sid)
    if N < len(pts) or N < 0 or len({p.sid for p in pts}) != len(pts):
        raise ValueError("one point per unique case, within full N")
    if any(p.w <= 0 for p in pts) or hp <= 0 or ht <= 0:
        raise ValueError("positive scales required")
    if time_domain is not None and any(not time_domain[0] <= p.t <= time_domain[1] for p in pts):
        raise ValueError("point outside source outcome time domain")
    m = max(4, (N+19)//20)
    neighbours = [[i] for i in range(len(pts))]
    for i, a in enumerate(pts):
        for j in range(i):
            if near(a, pts[j], hp, ht):
                neighbours[i].append(j)
                neighbours[j].append(i)
    cores = {i for i, row in enumerate(neighbours) if len(row) >= m}
    components, owner = [], {}
    for i in sorted(cores):
        if i in owner:
            continue
        k, stack, component = len(components), [i], []
        owner[i] = k
        while stack:
            j = stack.pop()
            component.append(j)
            for q in neighbours[j]:
                if q in cores and q not in owner:
                    owner[q] = k
                    stack.append(q)
        components.append(sorted(component))
    members = [[] for _ in components]
    shared, outside = [], []
    for i, p in enumerate(pts):
        ds = {}
        for j in neighbours[i]:
            if j in cores:
                k, d = owner[j], distance(p, pts[j], hp, ht)
                ds[k] = min(ds.get(k, d), d)
        if not ds:
            outside.append(p.sid)
            continue
        best = min(ds.values())
        winners = [k for k, d in ds.items() if d == best]
        if len(winners) != 1:
            shared.append(p.sid)
        else:
            members[winners[0]].append(p.sid)
    zones, rejected = [], []
    for k, row in enumerate(members):
        record = dict(component=k, members=set(row), cores=[pts[i] for i in components[k]])
        (zones if len(row) >= m else rejected).append(record)
    residual = set(shared+outside) | set().union(*(z["members"] for z in rejected))
    used = set().union(*(z["members"] for z in zones))
    assert not used & residual and len(used)+len(residual) == len(pts)
    assert sum(len(z["members"]) for z in zones) == len(used)
    return dict(zones=zones, rejected=rejected, residual=residual, shared=set(shared), outside=set(outside),
                need=m, N=N, known=len(pts), without_coordinate=N-len(pts), components=components,
                all_cores=[[pts[i] for i in component] for component in components], time_domain=time_domain)


def region_owner(point, result, hp=HP, ht=HT):
    bounds = result.get('time_domain')
    if bounds is not None and not bounds[0] <= point.t <= bounds[1]:
        return None
    ds = [min(distance(point, q, hp, ht) for q in component) for component in result["all_cores"]]
    if not ds or min(ds) > 1:
        return None
    winners = [k for k, d in enumerate(ds) if d == min(ds)]
    return winners[0] if len(winners) == 1 else None


def canonical(result):
    return sorted(sorted(z["members"]) for z in result["zones"]), sorted(result["residual"])


def make(values):
    return [Point(str(i), Fraction(u).numerator, Fraction(u).denominator, t) for i, (u, t) in enumerate(values)]


def synthetic():
    passed = []

    def expect(name, predicate):
        if not predicate:
            raise AssertionError(name)
        passed.append(name)

    island = make([(Fraction(i, 100), 5*(i % 3)) for i in range(8)])
    a = cn(island, 100)
    expect("one compact island, no forced 70 percent coverage", len(a["zones"]) == 1 and len(a["zones"][0]["members"]) == 8)
    two = make([(Fraction(i, 100), 5*(i % 3)) for i in range(8)] + [(1+Fraction(i, 100), 120+5*(i % 3)) for i in range(8)])
    expect("two islands", len(cn(two, 100)["zones"]) == 2)
    same_price = make([(Fraction(i, 100), 5*(i % 3)) for i in range(8)] + [(Fraction(i, 100), 180+5*(i % 3)) for i in range(8)])
    expect("same price at separate hours is not one time-price constellation", len(cn(same_price, 100)["zones"]) == 2)
    expect("sparse field has no forced region", not cn(make([(i, 60*i) for i in range(30)]), 100)["zones"])
    plateau = make([(Fraction(i, 20), 5*j) for i in range(3) for j in range(3)])
    expect("dense plateau remains one component", len(cn(plateau, 100)["zones"]) == 1)
    sparse = make([(0, 0)]*10 + [(Fraction(4, 5), 0)]*10 + [(Fraction(i, 20), 0) for i in [3, 6, 9, 12, 13]])
    expect("non-core bridge cannot merge cores", len(cn(sparse, 100)["zones"]) == 2)
    dense = make([(Fraction(i, 10), 0) for i in range(9) for _ in range(5)])
    expect("dense bridge is explicitly one ridge", len(cn(dense, 100)["zones"]) == 1)
    border = make([(0, 0)]+[(Fraction(-12, 100), 0)]*4+[(Fraction(3, 10), 0)]+[(Fraction(42, 100), 0)]*4+[(Fraction(15, 100), 0)])
    b = cn(border, 100)
    expect("shared border is residual, not arbitrary assignment", len(b["zones"]) == 2 and b["shared"] == {"10"})
    shuffled = list(border)
    random.Random(17).shuffle(shuffled)
    expect("input permutation invariance", canonical(b) == canonical(cn(shuffled, 100)))
    shifted = [Point(p.sid, (p.u+Fraction(3, 40)).numerator, (p.u+Fraction(3, 40)).denominator, p.t+7) for p in border]
    expect("translation invariance without a bin origin", canonical(b) == canonical(cn(shifted, 100)))
    expect("tick representation invariance", canonical(b) == canonical(cn([Point(p.sid, p.v*7, p.w*7, p.t) for p in border], 100)))
    expect("different cases at the same location retain their votes", len(cn(make([(0, 0)]*7), 100)["zones"][0]["members"]) == 7)
    try:
        cn(island+[island[0]], 100)
    except ValueError:
        passed.append("duplicate case id rejected")
    else:
        raise AssertionError("duplicate case id accepted")
    expect("non-coordinate cases remain in N and support threshold", a["without_coordinate"] == 92 and not cn(island, 200)["zones"])
    boundary = make([(0, 0)]*3+[(Fraction(3, 20), 20)])
    expect("closed exact neighbourhood boundary", len(cn(boundary, 20)["zones"]) == 1)
    expect("outside exact time boundary", not cn(make([(0, 0)]*3+[(Fraction(3, 20), 25)]), 20)["zones"])
    limited = cn(island, 100, time_domain=(0, 20))
    expect("source time domain clips region, not member counts", region_owner(Point('query', 0, 1, -1), limited) is None and canonical(limited) == canonical(a))
    small_values = [(0, 0)]
    for sx, st in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        small_values += [(sx*Fraction(12, 100), st*15), (sx*Fraction(1, 5), st*25)] + [(sx*Fraction(3, 10), st*40)]*4
    small = cn(make(small_values), 100)
    expect("small component is residual without reassignment", len(small['rejected']) == 1 and small['rejected'][0]['members'] == {'0'} and len(small['zones']) == 4)
    for pts in [island, two, same_price, plateau, border, dense, make(small_values)]:
        result = cn(pts, 100)
        for zone in result["zones"]:
            actual = {p.sid for p in pts if region_owner(p, result) == zone["component"]}
            expect("region predicate equals membership", actual == zone["members"])
    return dict(outcome="PASS", assertions=len(passed), cases=passed)


def points_of(members, event):
    return [Point(m["id"], int(m[event]["v"]), int(m["w"]), int(m[event]["t"])) for m in members if m[event]["s"] == "known"]


def old_map(members, event, snap, Z):
    formed, end = snap["schedule"]["formed"], snap["schedule"]["end"]
    win = (snap["key"]["window"][0]-formed)//15
    raw = Z.map_of(members, event, formed, end, win, [m["id"] for m in members])
    return dict(zones=[dict(members=set(z["members"])) for z in raw["zones"]], residual=set(raw["residual"]))


def summary(result, pts, N):
    byid = {p.sid: p for p in pts}
    sizes = [len(z["members"]) for z in result["zones"]]
    spans = [(float(max(byid[s].u for s in z["members"])-min(byid[s].u for s in z["members"])),
              max(byid[s].t for s in z["members"])-min(byid[s].t for s in z["members"])) for z in result["zones"]]
    return dict(zones=len(sizes), covered=sum(sizes), coverage=sum(sizes)/N if N else 0,
                largest_share=max(sizes, default=0)/N if N else 0,
                largest_price_span=max((p for p, _ in spans), default=0),
                largest_time_span=max((t for _, t in spans), default=0))


def recovery(original, changed, retained=None):
    values = []
    for zone in original["zones"]:
        a = zone["members"] if retained is None else zone["members"] & retained
        if not a:
            continue
        values.append(max((len(a & b["members"])/len(a | b["members"]) for b in changed["zones"]), default=0))
    return statistics.mean(values) if values else None


def historical():
    sys.path.insert(0, str(ROOT/"lab"))
    import scene24 as S
    import zonemap24 as Z
    start = time.monotonic()
    groups, selected, rows, base_versions = defaultdict(list), [], [], {}
    for inst in ("NQ", "ES", "YM"):
        B = S._base(inst)
        assert B is not None and B["info"]["stop_exclusive"] == "2026-01-01"
        assert max(m["date"] for m in B["boxes"]) <= "2025-12-31"
        base_versions[inst] = S.source_version(inst, B)
        for block in ("ADR", "ODR", "RDR"):
            for weekday in range(5):
                for side in (1, -1):
                    for win in (0, 1, 2):
                        snap = S._snapshot(inst, B, block, weekday, side, "conf", win, "2026-01-01")
                        N = snap["N"]
                        nclass = "N<20" if N < 20 else "N20-59" if N < 60 else "N>=60"
                        for event in ("R", "X"):
                            pts = points_of(snap["members"], event)
                            old = old_map(snap["members"], event, snap, Z)
                            domain = (snap['schedule']['formed']+15*win+5, snap['schedule']['end']-5)
                            new = cn(pts, N, time_domain=domain)
                            row = dict(instrument=inst, block=block, weekday=weekday, side=side, window=win,
                                       N=N, known=len(pts), old=summary(old, pts, N), cn1=summary(new, pts, N),
                                       shared=len(new["shared"]), rejected_components=len(new["rejected"]),
                                       source_statuses=dict(Counter(m[event]['s'] for m in snap['members'])))
                            groups[(block, event, nclass)].append(row)
                            rows.append(dict(row, event=event))
                            if weekday == 1 and side == 1 and win == 0:
                                selected.append((inst, block, event, snap, pts, old, new))
        print("static maps complete:", inst, flush=True)
    aggregate = {}
    for key, cases in sorted(groups.items()):
        aggregate[" ".join(key)] = dict(family_event_maps=len(cases), mean_N=statistics.mean(r["N"] for r in cases),
            old={f: statistics.mean(r["old"][f] for r in cases) for f in cases[0]["old"]},
            cn1={f: statistics.mean(r["cn1"][f] for r in cases) for f in cases[0]["cn1"]})
    diagnostics = []
    for inst, block, event, snap, pts, old, new in selected:
        label = f"{inst} {block} {event} Tuesday long window0"
        rng = random.Random(int(hashlib.sha256(label.encode()).hexdigest()[:16], 16))
        members, drop_old, drop_new = snap["members"], [], []
        for _ in range(20):
            discard = set(rng.sample(range(len(members)), max(1, len(members)//10)))
            kept = [m for i, m in enumerate(members) if i not in discard]
            ids = {m["id"] for m in kept}
            drop_old.append(recovery(old, old_map(kept, event, snap, Z), ids))
            drop_new.append(recovery(new, cn(points_of(kept, event), len(kept), time_domain=new['time_domain']), ids))
        scales = []
        for hp, ht in [(Fraction(1, 10), 20), (Fraction(1, 5), 20), (HP, 15), (HP, 25)]:
            alternate = cn(pts, snap["N"], hp, ht, time_domain=new['time_domain'])
            scales.append(dict(price_radius=str(hp), time_radius=ht, **summary(alternate, pts, snap["N"]),
                               recovery=recovery(new, alternate)))
        zone_rows = []
        if inst == "YM" and block == "RDR":
            byid = {p.sid: p for p in pts}
            for zone in sorted(new["zones"], key=lambda z: min(byid[s].t for s in z["members"])):
                members_here = [byid[s] for s in zone["members"]]
                zone_rows.append(dict(n=len(members_here), share=len(members_here)/snap["N"], core_n=len(zone["cores"]),
                    member_price_min_max=[float(min(p.u for p in members_here)), float(max(p.u for p in members_here))],
                    member_time_min_max=[min(p.t for p in members_here), max(p.t for p in members_here)]))
        diagnostics.append(dict(label=label, N=snap["N"], known=len(pts),
            source_statuses=dict(Counter(m[event]['s'] for m in members)),
            old=summary(old, pts, snap["N"]), cn1=summary(new, pts, snap["N"]),
            deletion_recovery_old=statistics.mean(x for x in drop_old if x is not None) if any(x is not None for x in drop_old) else None,
            deletion_recovery_cn1=statistics.mean(x for x in drop_new if x is not None) if any(x is not None for x in drop_new) else None,
            scales=scales, ym_zone_aggregates=zone_rows))
        print("diagnostics complete:", label, flush=True)
    return dict(scope="270 fixed end-of-2025 confirmation families, R and X separately; not walk-forward",
                family_event_maps=len(rows), base_versions=base_versions, groups=aggregate, diagnostics=diagnostics,
                seconds=round(time.monotonic()-start, 3),
                limitations=["seen history", "only activation windows 0,1,2", "stability subset Tuesday long window0",
                             "coverage and Jaccard do not measure predictive value or operator understanding",
                             "no new pullback outcome calculated", "no 2026 historical observations"])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--history", action="store_true")
    args = p.parse_args()
    result = dict(algorithm=VERSION, price_radius=str(HP), time_radius=HT,
                  protocol_sha256=hashlib.sha256((HERE/"PROTOCOL.md").read_bytes()).hexdigest(),
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), synthetic=synthetic())
    result["repository_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    result["calculator_sha256_lf"] = {name: hashlib.sha256((ROOT/name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                                      for name in ["lab/scene24.py", "lab/scene21.py", "lab/zonemap24.py"]}
    print("synthetic:", result["synthetic"]["outcome"], result["synthetic"]["assertions"], flush=True)
    if args.history:
        result["historical"] = historical()
    target = HERE/("probe-results.json" if args.history else "synthetic-results.json")
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("saved", target, flush=True)


if __name__ == "__main__":
    main()
