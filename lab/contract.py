"""DR Lab — the runtime gate of the semantic contract DR-LAB-SC-1.1 (Python standard library only).

The contract text (spec/DR-LAB-Semantic-Contract-1.1-(patched).md) is the source of truth. Its machine form is the
LinkML schema contract/schema/dr_lab_sc.yaml and the registry contract/registry/*.yaml, compiled by
contract/tools/build.py into contract/build/registry.json and contract/build/runtime_spec.json. LinkML is not needed
at runtime: this module reads the compiled artifacts, and checks on every request that they still match their
sources (otherwise the contract is CONTRACT_STALE and no statistic is published).

What this module does, and what it deliberately does not do:
- reference definitions (ref_*): the literal executable form of the registry's OutcomeSpecifications and of the
  frozen NOW-1.0 rules, one small function per definition, versioned with it. They are not a second DR Lab: no
  caching, no drawing, no product decisions, no diagnostics recomputation; they exist so that a published number is
  re-derived from the primary records of its cases (the M5 path, the activation, the width) instead of being trusted
  because it carries the right name (SC-1.1 K31).
- verification at the boundary where an object is created: the family snapshot (membership re-derived from the
  session base, every member's path and outcomes re-derived, the counts recounted), the zone map (regions
  re-derived), today's statuses, the NOW numbers at the cut. Expensive derivations are cached per snapshot.
- admissible claims: the machine computes which claim classes the evidence admits; the claim itself is the explicit
  ClaimForm of the registry and is published only if its class is admissible (no default class, SC-1.1 §10.1).
- the envelope (ContractEnvelope of the schema) next to each SC-1.1 response, and the response gate: every number of
  an SC-1.1 route must match a declared field encoding; the envelope must be structurally valid.
- fail closed: a stale contract publishes no statistic; a violated object is withheld and the violation is named.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import time
import uuid
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "contract" / "build"
REGISTRY_FILE = BUILD / "registry.json"
SPEC_FILE = BUILD / "runtime_spec.json"
EDITION = "DR-LAB-SC-1.1"
GATE_VERSION = "contract-gate-1"

C0, C1, C2, C3 = "DescriptiveClaim", "ConditionalDescriptiveClaim", "PredictiveClaim", "DecisionClaim"


class ContractViolation(Exception):
    """Raised in strict mode (tests) instead of withholding."""


STRICT = {"on": False}       # tests switch it on: a violation raises instead of being withheld


# =====================================================================================================================
# loading the compiled contract and checking that it still matches its sources
# =====================================================================================================================
_S = {"loaded": None, "reg": None, "spec": None, "index": None, "stamps": None, "mtimes": None, "stale": None, "error": None}


def sha256_lf(path):
    """SHA-256 of a text file with CRLF normalised to LF (git checkouts on Windows convert line endings)."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _sources(stamps):
    return {rel: ROOT / rel for rel in stamps.get("sources", {})}


def _load():
    try:
        reg = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        spec = json.loads(SPEC_FILE.read_text(encoding="utf-8"))
    except Exception as exc:                      # a missing or broken artifact is a stale contract, never a pass
        _S.update(loaded=time.time(), reg=None, spec=None, index=None, stamps=None, mtimes=None,
                  stale=[f"compiled contract unreadable: {exc}"], error=str(exc))
        return
    idx = {}
    for coll, items in reg["registry"].items():
        if isinstance(items, list):
            for it in items:
                if isinstance(it, dict) and "id" in it: idx[it["id"]] = dict(it, _collection=coll)
    _S.update(loaded=time.time(), reg=reg["registry"], spec=spec, index=idx, stamps=reg["stamps"], mtimes=None, stale=None, error=None)


def _check_stale():
    """The compiled artifacts carry the SHA-256 of every source they were built from (the schema, every registry
    file, the contract document). A mismatch means the executable contract no longer represents its source."""
    st = _S["stamps"]
    if st is None: return
    srcs = _sources(st)
    mt = {k: (p.stat().st_mtime if p.exists() else None) for k, p in srcs.items()}
    mt["__spec__"] = SPEC_FILE.stat().st_mtime if SPEC_FILE.exists() else None
    mt["__reg__"] = REGISTRY_FILE.stat().st_mtime if REGISTRY_FILE.exists() else None
    if mt == _S["mtimes"]: return
    reasons = []
    for rel, want in st["sources"].items():
        p = srcs[rel]
        if not p.exists(): reasons.append(f"source missing: {rel}"); continue
        if sha256_lf(p) != want: reasons.append(f"source changed since the build: {rel}")
    on_disk = sorted(str(p.relative_to(ROOT)).replace("\\", "/") for p in (ROOT / "contract" / "registry").glob("*.yaml"))
    for rel in on_disk:
        if rel not in st["sources"]: reasons.append(f"registry file not compiled: {rel}")
    if SPEC_FILE.exists() and sha256_lf(SPEC_FILE) != st.get("runtime_spec_sha256"): reasons.append("runtime_spec.json does not match the registry stamps")
    _S["stale"] = reasons or None
    _S["mtimes"] = mt


_TTL = {"at": 0.0}


def state():
    """The loaded contract; its sources are re-checked at most once a second (a request reads it many times)."""
    now = time.monotonic()
    if _S["loaded"] is not None and now - _TTL["at"] < 1.0: return _S
    _TTL["at"] = now
    if _S["loaded"] is None or (REGISTRY_FILE.exists() and _S["mtimes"] and _S["mtimes"].get("__reg__") != REGISTRY_FILE.stat().st_mtime):
        _load()
    _check_stale()
    return _S


def stale():
    s = state()
    return s["stale"]


def registry():
    s = state()
    return s["reg"]


def get(ident):
    s = state()
    return (s["index"] or {}).get(ident)


def registry_hash():
    s = state()
    return (s["stamps"] or {}).get("registry_sha256", "none")[:16]


def public_registry():
    """What /api/contract serves: the compiled registry, its stamps and the current runtime status."""
    s = state()
    return dict(edition=EDITION, gate=GATE_VERSION, status="CONTRACT_STALE" if s["stale"] else "CONFORMANT",
                stale_reasons=s["stale"] or [], stamps=s["stamps"], registry=s["reg"])


# =====================================================================================================================
# structural validation from the LinkML schema (compiled into runtime_spec.json by contract/tools/build.py)
# =====================================================================================================================
_TYPES = {"string": str, "integer": int, "float": (int, float), "double": (int, float), "boolean": bool, "date": str, "uriorcurie": str}


def validate(obj, cls, path="$"):
    """Structural errors of obj as an instance of schema class cls (closed world, like the generated JSON Schema)."""
    spec = state()["spec"]
    if spec is None: return [f"{path}: no runtime spec"]
    errs = []
    C = spec["classes"].get(cls)
    if C is None: return [f"{path}: unknown class {cls}"]
    if not isinstance(obj, dict): return [f"{path}: {cls} expects an object"]
    dt = C.get("designator")
    if dt and isinstance(obj.get(dt), str):
        sub = obj[dt]
        if sub not in C.get("descendants", []) and sub != cls: return [f"{path}.{dt}: {sub} is not a {cls}"]
        if sub != cls: C, cls = spec["classes"][sub], sub
    if C.get("abstract"): return [f"{path}: abstract class {cls} needs its designator"]
    slots = C["slots"]
    for k in obj:
        if k not in slots: errs.append(f"{path}.{k}: not a slot of {cls}")
    for name, S in slots.items():
        v = obj.get(name)
        if v is None:
            if S.get("required"): errs.append(f"{path}.{name}: required")
            continue
        vals = v if S.get("multivalued") else [v]
        if S.get("multivalued"):
            if not isinstance(v, list): errs.append(f"{path}.{name}: expects a list"); continue
            if S.get("min_card") is not None and len(v) < S["min_card"]: errs.append(f"{path}.{name}: fewer than {S['min_card']}")
            if S.get("max_card") is not None and len(v) > S["max_card"]: errs.append(f"{path}.{name}: more than {S['max_card']}")
        for i, x in enumerate(vals):
            p = f"{path}.{name}" + (f"[{i}]" if S.get("multivalued") else "")
            rng = S["range"]
            if rng in spec["enums"]:
                if x not in spec["enums"][rng]: errs.append(f"{p}: {x!r} not in {rng}")
            elif rng in spec["classes"]:
                if S.get("inlined"): errs += validate(x, rng, p)
                elif not isinstance(x, str): errs.append(f"{p}: a reference to {rng} is an id string")
            else:
                t = _TYPES.get(rng, str)
                if isinstance(x, bool) and rng != "boolean": errs.append(f"{p}: boolean where {rng} expected"); continue
                if not isinstance(x, t): errs.append(f"{p}: {type(x).__name__} where {rng} expected"); continue
                if rng == "date" and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", x): errs.append(f"{p}: not a date")
            if isinstance(x, (int, float)) and not isinstance(x, bool):
                if S.get("min") is not None and x < S["min"]: errs.append(f"{p}: {x} < {S['min']}")
                if S.get("max") is not None and x > S["max"]: errs.append(f"{p}: {x} > {S['max']}")
            if S.get("pattern") and isinstance(x, str) and not re.search(S["pattern"], x): errs.append(f"{p}: does not match {S['pattern']}")
    for rule in C.get("rules", []):
        if all(obj.get(s) == c for s, c in rule["pre"].items()):
            for s, cond in rule["post"].items():
                if cond.get("required") and obj.get(s) is None: errs.append(f"{path}.{s}: required when {rule['pre']}")
                if "equals" in cond and obj.get(s) is not None and obj.get(s) != cond["equals"]: errs.append(f"{path}.{s}: must be {cond['equals']} when {rule['pre']}")
                if cond.get("absent") and s in obj: errs.append(f"{path}.{s}: must be absent when {rule['pre']}")
                if cond.get("min") is not None and isinstance(obj.get(s), (int, float)) and obj[s] < cond["min"]: errs.append(f"{path}.{s}: < {cond['min']} when {rule['pre']}")
    return errs


# =====================================================================================================================
# reference definitions: the executable form of the registry's definitions (one function per definition)
# =====================================================================================================================
def ref_directed(row, d, e):
    """M0: (low_u, high_u, close_u) numerators in directed ticks of an M5 (o, h, l, c ticks); for a short the
    physical high and low swap roles."""
    _, h, l, c = row
    return (l - e, h - e, c - e) if d == 1 else (e - h, e - l, e - c)


def ref_cell(v, w):
    """M1: the price cell floor(10 v / w) of a directed value (integers; negative values floor down)."""
    return (10 * v) // w


def ref_window(close, formed):
    """H1: the 15-minute window of an event by the open minute of its M5 (close - 5), counted from the box end."""
    return (close - 5 - formed) // 15


def _horizon(grid, start, end):
    """P0.1: the grid indices of the M5 closing in (start, end] — the activating M5 excluded, the one closing at end in."""
    return [j for j, T in enumerate(grid) if start < T <= end]


def ref_final_extreme(path, grid, act, end, ev):
    """P0.1: the final R (min low_u) or X (max high_u) of one case over its own horizon, with the first open minute,
    every tie, and the endpoint status KNOWN / UNKNOWN / NO_PERIOD (an observed extreme with a hole is a bound)."""
    hor = _horizon(grid, act, end)
    if not hor: return dict(s="none")
    obs = [(j, path[j]) for j in hor if path[j] is not None]
    pos = 0 if ev == "R" else 1
    pick = min if ev == "R" else max
    if len(obs) < len(hor):
        out = dict(s="unknown")
        if obs: out["bound"] = int(pick(q[pos] for _, q in obs))
        return out
    v = pick(q[pos] for _, q in obs)
    ties = [grid[j] - 5 for j, q in obs if q[pos] == v]
    return dict(s="known", v=int(v), t=ties[0], ties=ties)


def ref_dr_outcome(path, grid, act, end, oppv):
    """P0.2: BROKEN (an observed close strictly beyond the own opposite DR) / HELD / UNKNOWN / NO_PERIOD, the break
    close, and whether its first time is known (no hole before it)."""
    hor = _horizon(grid, act, end)
    if not hor: return "none", None, False
    brk, hole_before = None, False
    for j in hor:
        q = path[j]
        if q is None: hole_before = True; continue
        if q[2] < oppv: brk = grid[j]; break
    if brk is not None: return "broken", brk, not hole_before
    return ("unknown" if any(path[j] is None for j in hor) else "held"), None, False


def ref_first_order(R, X):
    """P0.2: the order of the first achievements of the final R and X (SAME_M5 hides the order inside the candle)."""
    if R["s"] == "none" or X["s"] == "none": return "no_period"
    if R["s"] != "known" or X["s"] != "known": return "unknown"
    return "R_before_X" if R["t"] < X["t"] else "X_before_R" if X["t"] < R["t"] else "same_M5"


def ref_order_detail(R, X):
    rt, xt = R["ties"], X["ties"]
    return dict(all_x_before_all_r=max(xt) < min(rt), all_r_before_all_x=max(rt) < min(xt),
                x_again_after_r=any(t > rt[0] for t in xt), r_again_after_x=any(t > xt[0] for t in rt))


def ref_reach(path, grid, start, end, a, b, w, up):
    """P0.2 «на уровне L или дальше», L = a / b: YES if an observed M5 reaches it (evidence stands with holes
    elsewhere), UNKNOWN if not reached and an M5 is missing, NO otherwise (an empty horizon is NO)."""
    gap = False
    for j in _horizon(grid, start, end):
        q = path[j]
        if q is None: gap = True; continue
        if (q[1] * b >= a * w) if up else (q[0] * b <= a * w): return "yes"
    return "unknown" if gap else "no"


def ref_cross(path, grid, start, end, a, b, w):
    """P0.2: the literal crossing low_u <= L <= high_u by one M5 (a gap past the level is no crossing)."""
    gap = False
    for j in _horizon(grid, start, end):
        q = path[j]
        if q is None: gap = True; continue
        if q[0] * b <= a * w <= q[1] * b: return "yes"
    return "unknown" if gap else "no"


def ref_visit(path, grid, start, end, k0, k1, w):
    """P0.2: a visit of the band [k0/10, k1/10): an M5 with low_u < k1/10 and high_u >= k0/10."""
    gap = False
    for j in _horizon(grid, start, end):
        q = path[j]
        if q is None: gap = True; continue
        if 10 * q[0] < k1 * w and 10 * q[1] >= k0 * w: return "yes"
    return "unknown" if gap else "no"


def ref_close_cell(path, j, w):
    """P0.2: the price cell of the close on common clock M5 j, or None (a missing M5)."""
    q = path[j]
    return None if q is None else (10 * q[2]) // w


def ref_range_touch(path, j, k, w):
    """P0.2: does the high-low range of M5 j touch band k (low_u < (k+1)/10 and high_u >= k/10)? None = missing."""
    q = path[j]
    return None if q is None else (10 * q[0] < (k + 1) * w and 10 * q[1] >= k * w)


def ref_clock_split(t_open, cut):
    """E4: an event is EARLIER when its M5 closed not after the cut (t_open + 5 <= cut), LATER otherwise."""
    return "EARLIER" if t_open + 5 <= cut else "LATER"


def ref_zone_map(points, n_family, b_lo, b_hi, ratio=(1, 2), min_abs=4, min_frac=(1, 20)):
    """P3 zone-map-3 written from its definition (no scipy): D(cell) = known events of one kind in the 3 x 3
    neighbourhood at every cell; a zone = the 8-connected component of {D >= half of its own apex} that holds no cell
    above that apex; support n >= max(4, ceil(0.05 N)); zones ordered by start time, share, nearness to u = 0."""
    need = max(min_abs, -(-min_frac[0] * n_family // min_frac[1]))
    where = {}
    for k, b, sid in points: where.setdefault((k, b), []).append(sid)
    if not points: return dict(zones=[], residual=[], need=need)
    ks = [k for k, _, _ in points]
    k_lo, k_hi = min(ks) - 1, max(ks) + 1
    A = Counter((k, b) for k, b, _ in points if b_lo <= b <= b_hi)
    cells = [(k, b) for k in range(k_lo, k_hi + 1) for b in range(b_lo, b_hi + 1)]
    D = {c: sum(A.get((c[0] + dk, c[1] + db), 0) for dk in (-1, 0, 1) for db in (-1, 0, 1)) for c in cells}
    nb = lambda c: [(c[0] + dk, c[1] + db) for dk in (-1, 0, 1) for db in (-1, 0, 1) if (dk or db) and (c[0] + dk, c[1] + db) in D]
    peaks = [c for c in cells if D[c] > 0 and all(D[c] >= D[n] for n in nb(c))]
    zones, seen = [], set()
    for top in sorted({D[c] for c in peaks}, reverse=True):
        for p in sorted(c for c in peaks if D[c] == top):
            comp, stack = {p}, [p]
            while stack:                                      # the component of {D >= ratio x top} holding p
                c = stack.pop()
                for n in nb(c):
                    if n not in comp and ratio[1] * D[n] >= ratio[0] * top: comp.add(n); stack.append(n)
            key = (top, min(comp))
            if key in seen: continue
            seen.add(key)
            if max(D[c] for c in comp) != top: continue           # a higher cell inside: not its own apex
            members = sorted({s for c in comp for s in where.get(c, ())})
            if len(members) < need: continue
            apex = [c for c in comp if D[c] == top]
            anchor = min(apex, key=lambda c: (c[1], abs(2 * c[0] + 1), c[0]))
            kk = [c[0] for c in comp]; bb = [c[1] for c in comp]
            zones.append(dict(cells=sorted(comp), members=members, n=len(members), anchor=anchor,
                              price=[min(kk), max(kk) + 1], time=[min(bb), max(bb) + 1]))
    near0 = lambda z: 0 if z["price"][0] <= 0 < z["price"][1] else z["price"][0] if z["price"][0] > 0 else -z["price"][1]
    zones.sort(key=lambda z: (z["time"][0], -z["n"], near0(z)))
    used = {s for z in zones for s in z["members"]}
    return dict(zones=zones, residual=sorted({s for _, _, s in points} - used), need=need)


def ref_reachability(cells, ev, q, v10, w, t_next, formed, last_open):
    """E3: HOLDS (today's provisional extreme lies in the region) / POSSIBLE (a strictly further new extreme can
    still land in a cell of it in time) / IMPOSSIBLE. q = None before the first M5 after the activation."""
    cs = {tuple(c) for c in cells}
    if q is not None and tuple(q) in cs: return "HOLDS"
    if t_next > last_open: return "IMPOSSIBLE"
    for k, b in cs:
        if q is not None and not (k * w < v10 if ev == "R" else (k + 1) * w > v10): continue
        if formed + 15 * b + 10 >= t_next and formed + 15 * b <= last_open: return "POSSIBLE"
    return "IMPOSSIBLE"


def ref_history_clock(cells, times, t_next, formed, last_open):
    """E4: FUTURE_PRESENT / FUTURE_EMPTY / PAST_ONLY of a region's family events against the common clock cut."""
    if any(ref_clock_split(t, t_next) == "LATER" for t in times): return "FUTURE_PRESENT"
    if any(formed + 15 * b + 10 >= t_next and formed + 15 * b <= last_open for _, b in cells): return "FUTURE_EMPTY"
    return "PAST_ONLY"


def ref_prefix(path, a, c, oppv=None):
    """E1 (NOW): the state of one case at grid cut c from its own activation index a — None when not eligible (no M5
    after the activation yet, a hole in the prefix, or, in the confirmation family, already closed beyond its own
    opposite DR: another phase). Returns (r_seen, x_seen) in directed ticks; the activating M5 is excluded."""
    if c <= a: return None
    seg = path[a + 1:c + 1]
    if any(q is None for q in seg): return None
    if oppv is not None and any(q[2] < oppv for q in seg): return None
    return min(q[0] for q in seg), max(q[1] for q in seg)


def ref_residual(path, c, seen, ev):
    """P0.3: after cut c relative to the case's own seen extreme: new (YES / NO / UNKNOWN; a tie is not new),
    delta (known only with the whole remainder observed; 0 without a new extreme) and tau (the first future M5 of the
    strictly new extreme; unknown after a hole before it; NO_EVENT without one)."""
    fut = list(enumerate(path))[c + 1:]
    pos = 0 if ev == "R" else 1
    beyond = (lambda v: v < seen) if ev == "R" else (lambda v: v > seen)
    first = next((j for j, q in fut if q is not None and beyond(q[pos])), None)
    missing = any(q is None for _, q in fut)
    new = "YES" if first is not None else "UNKNOWN" if missing else "NO"
    if missing: delta = None
    else:
        vals = [q[pos] for _, q in fut]
        delta = (seen - min([seen] + vals)) if ev == "R" else (max([seen] + vals) - seen)
    if new == "YES":
        tau = None if any(path[i] is None for i in range(c + 1, first)) else first - c
        tau_s = "KNOWN" if tau is not None else "UNKNOWN"
    else:
        tau, tau_s = None, ("NO_EVENT" if new == "NO" else "UNKNOWN")
    return dict(new=new, delta=delta, tau=tau, tau_s=tau_s)


def _near(a, wa, b, wb, n, d):
    """|a / wa - b / wb| <= n / d exactly in integers."""
    return d * abs(a * wb - b * wa) <= n * wa * wb


def ref_matchers(st_m, st_t, w_m, w_t, path_m, path_t, a_m, a_t, c):
    """H3 NOW-1.0: membership of one eligible case in M1 (per event), M2 and M3 at cut c (frozen rules, exact)."""
    (rm, xm), (rt, xt) = st_m, st_t
    m1r, m1x = _near(rm, w_m, rt, w_t, 1, 4), _near(xm, w_m, xt, w_t, 1, 4)
    m2 = m1r and m1x
    m3 = False
    n = min(6, c - a_t)
    if m2 and n >= 3:
        p0 = c - n + 1
        if a_m < p0:
            dif = [abs(path_m[j][2] * w_t - path_t[j][2] * w_m) for j in range(p0, c + 1)]
            lim = w_m * w_t
            m3 = 5 * sum(dif) <= 1 * n * lim and 20 * max(dif) <= 7 * lim
    return dict(M1R=m1r, M1X=m1x, M2=m2, M3=m3)


def ref_quantile(values, q):
    """The linear quantile (numpy's default) of exact values: h = (n - 1) q, interpolated."""
    a = sorted(values)
    if not a: return None
    h = (len(a) - 1) * Fraction(q)
    lo = math.floor(h)
    hi = min(lo + 1, len(a) - 1)
    return a[lo] + (h - lo) * (a[hi] - a[lo])


def est_count_over_n(count, n):
    """V0 COUNT_OVER_N: a share of the family's one N; N = 0 gives no estimate (never 0 %)."""
    return None if not n else Fraction(count, n)


def est_binary_bounds(yes, no, unknown):
    """V2.1: yes + no + unknown = D; bounds [yes / D, (yes + unknown) / D] from holes (no confidence interval)."""
    D = yes + no + unknown
    return None if not D else (Fraction(yes, D), Fraction(yes + unknown, D))


def est_categories(counts, n):
    return None if not n else {k: Fraction(v, n) for k, v in counts.items()}


def est_joint_cells(cells, n):
    return None if not n else [(k, b, Fraction(c, n)) for k, b, c in cells]


def check_zone_diagnostics(z):
    """P3 / V3: diagnostics are properties of a zone; their admissible ranges and their provenance only (the random
    procedures themselves are not repeated at runtime)."""
    errs = []
    g = z.get("grid_member_jaccard") or {}
    for k in ("price_half", "time_5", "time_10", "min"):
        if g.get(k) is not None and not 0 <= g[k] <= 1: errs.append(f"jaccard {k} outside [0, 1]")
    if g and g.get("min") is not None and abs(g["min"] - min(g["price_half"], g["time_5"], g["time_10"])) > 1e-9: errs.append("jaccard min is not the minimum")
    b = z.get("bootstrap_recovery") or {}
    for k in ("mean", "share_ge_half"):
        if b.get(k) is not None and not 0 <= b[k] <= 1: errs.append(f"bootstrap {k} outside [0, 1]")
    if z.get("null_status") == "measured":
        for k in ("p_real_mask", "p_null_mask"):
            if not 0 <= z[k] <= 1: errs.append(f"{k} outside [0, 1]")
        if abs(z["null_excess"] - round(z["p_real_mask"] - z["p_null_mask"], 4)) > 2e-4: errs.append("null excess is not p_real - p_null")
        if z["null_validation_n"] < 10: errs.append("null measured on fewer than 10 events")
        lo, hi = z["null_interval"]
        if lo > hi: errs.append("null interval not ordered")
    elif not str(z.get("null_status", "")).startswith("not_applicable"): errs.append("null status neither measured nor named not applicable")
    return errs


def check_study_refs(z, session, ev):
    """V3: the research figures of a zone are the stored research table, named as exploration."""
    s = z.get("study_refs")
    if s is None: return []
    return [] if s.get("study_id") == "zone_map_3_2026_10_01" and "не шанс" in s.get("text", "") else ["study reference without its research label"]


# =====================================================================================================================
# the session base: re-deriving boxes, confirmations and breaks from the stored M5 (O1 -> S1 -> S2)
# =====================================================================================================================
_DERIVED = {}


def _blocks():
    rule = get("RULE:DRIDR-24-1")
    return {b["block"]: b for b in rule["blocks"]}


def derive_base(inst, B, session):
    """S1 / S2 re-derived for every session instance of a block from its stored M5 (cached per base build): box
    levels, the first confirmation, the break, the wholly missing M5 after the box (day minutes)."""
    key = (inst, session, int(B["info"].get("boxes", 0)), id(B["bars"]))
    if key in _DERIVED: return _DERIVED[key]
    blk = _blocks()[session]
    fs, fe, end, shift = blk["formation_start"], blk["formation_end"], blk["block_end"], blk["history_minute_shift"]
    expected = list(range(fe + 5, end + 1, 5))
    out = {}
    bars, off = B["bars"], B["off"]
    for i, m in enumerate(B["boxes"]):
        if m["session"] != session: continue
        a = bars[off[i]:off[i + 1]].tolist()
        rows = {int(r[0]) - shift: (int(r[1]), int(r[2]), int(r[3]), int(r[4])) for r in a}
        box = [rows.get(T) for T in range(fs + 5, fe + 1, 5)]
        rec = dict(rows=rows)
        if any(x is None for x in box) or len(box) != blk["formation_m5_count"]:
            rec["box_error"] = "incomplete formation window in the base"
        else:
            rec.update(dr_high=max(x[1] for x in box), dr_low=min(x[2] for x in box),
                       idr_high=max(max(x[0], x[3]) for x in box), idr_low=min(min(x[0], x[3]) for x in box))
        missing = [T for T in expected if T not in rows]
        conf = side = fail = None
        if "dr_high" in rec:
            for T in expected:
                r = rows.get(T)
                if r is None: continue
                if r[3] > rec["dr_high"]: conf, side = T, 1; break
                if r[3] < rec["dr_low"]: conf, side = T, -1; break
            if conf is not None:
                opp = rec["dr_low"] if side == 1 else rec["dr_high"]
                for T in expected:
                    r = rows.get(T)
                    if T <= conf or r is None: continue
                    if side * (r[3] - opp) < 0: fail = T; break
        rec.update(conf=conf, side=side, fail=fail, missing=missing)
        out[i] = rec
    if len(_DERIVED) > 12: _DERIVED.clear()
    _DERIVED[key] = out
    return out


def ref_family(inst, B, session, weekday, side, view, win, cutoff, scope):
    """H1 / H2: the members of the family key and the journal of undetermined keys, re-derived from the base."""
    blk = _blocks()[session]
    fe, shift = blk["formation_end"], blk["history_minute_shift"]
    der = derive_base(inst, B, session)
    w_start, w_end = fe + 15 * win, fe + 15 * (win + 1)
    members, journal, errs = [], Counter(), []
    for i, m in enumerate(B["boxes"]):
        if m["session"] != session or (scope == "weekday" and m["weekday"] != weekday) or m["date"] >= cutoff: continue
        d = der[i]
        if "box_error" in d: errs.append(f"{m['date']}: {d['box_error']}"); continue
        for k in ("dr_high", "dr_low", "idr_high", "idr_low"):
            if d[k] != m[k]: errs.append(f"{m['date']} {session}: stored {k} {m[k]} != re-derived {d[k]}")
        sc = None if m["conf"] is None else int(m["conf"]) - shift
        sf = None if m["fail"] is None else int(m["fail"]) - shift
        if (sc, m["side"] if sc is not None else None, sf) != (d["conf"], d["side"], d["fail"]):
            errs.append(f"{m['date']} {session}: stored confirmation / break ({sc}, {m['side']}, {sf}) != re-derived ({d['conf']}, {d['side']}, {d['fail']})")
        conf, gaps, fail = d["conf"], d["missing"], d["fail"]
        if conf is None:
            if gaps:
                journal["confirmation_undetermined"] += 1
                if gaps[0] <= w_end: journal["confirmation_undetermined_could_be_this_window"] += 1
            continue
        if any(T < conf for T in gaps):
            journal["confirmation_undetermined"] += 1
            if gaps[0] <= w_end and conf > w_start: journal["confirmation_undetermined_could_be_this_window"] += 1
            continue
        if d["side"] != side: continue
        if view == "conf":
            if ref_window(conf, fe) != win: continue
            act, dd = conf, side
        else:
            if fail is None:
                if any(T > conf for T in gaps):
                    journal["break_undetermined"] += 1
                    if any(conf < T <= w_end for T in gaps): journal["break_undetermined_could_be_this_window"] += 1
                continue
            if any(conf < T < fail for T in gaps):
                journal["break_undetermined"] += 1
                continue
            if ref_window(fail, fe) != win: continue
            act, dd = fail, -side
        members.append((i, act, dd))
    return members, dict(journal), errs


# =====================================================================================================================
# verification of a family snapshot (cached per snapshot): membership, paths, outcomes, counts, identity
# =====================================================================================================================
_VER = {}


def _sid(inst, m):
    return f"{inst}-{m['date'].replace('-', '')}-{m['session']}"


def verify_snapshot(inst, B, snap):
    """Re-derives the snapshot from the session base by the reference definitions and returns (violations,
    reference) — the reference holds the recounted R / X tables, outcome and order counts per member set."""
    sid = snap["snapshot_id"]
    # cached per snapshot object: scene24 serves one cached member list per snapshot; a copy claiming the same id with
    # other content is verified anew (K31: a structurally valid object is not trusted by its name)
    ck = (sid, id(snap["members"]))
    if ck in _VER: return _VER[ck]
    key, sch = snap["key"], snap["schedule"]
    session, formed, end = key["session"], sch["formed"], sch["end"]
    view = "conf" if key["event"] == "confirmation" else "brk"
    side = 1 if key["direction"] == "long" else -1
    win = (key["window"][0] - formed) // 15
    v = []
    blk = _blocks().get(session)
    if blk is None or (blk["formation_start"], blk["formation_end"], blk["block_end"]) != (sch["start"], formed, end):
        v.append(("SCHEDULE", ["S1"], f"schedule {sch} differs from the registry's block {blk}"))
    if snap["grid"] != list(range(formed + 5, end + 1, 5)):
        v.append(("GRID", ["M1"], "the common clock grid is not every M5 close after the box"))
    mem, journal, base_errs = ref_family(inst, B, session, key["weekday"], side, view, win, key["cutoff"], key.get("scope", "weekday"))
    for e in base_errs[:5]: v.append(("BASE_DERIVATION", ["O1", "S1", "S2"], e))
    ids_ref = sorted(_sid(inst, B["boxes"][i]) for i, _, _ in mem)
    if sorted(snap["ids"]) != ids_ref or len(set(snap["ids"])) != len(snap["ids"]):
        v.append(("MEMBERSHIP", ["H1", "H2"], f"members differ from the key's re-derived set ({len(snap['ids'])} vs {len(ids_ref)})"))
    if snap["N"] != len(ids_ref) or snap["N"] != len(snap["members"]):
        v.append(("DENOMINATOR", ["H2", "V1"], f"N {snap['N']} is not the number of unique participants {len(ids_ref)}"))
    if dict(snap.get("journal") or {}) != journal:
        v.append(("JOURNAL", ["H1", "K11"], f"journal {snap.get('journal')} != re-derived {journal}"))
    der = derive_base(inst, B, session)
    by_id = {_sid(inst, B["boxes"][i]): (i, act, dd) for i, act, dd in mem}
    grid = snap["grid"]
    ref = dict(R=Counter(), X=Counter(), unknown=Counter(), none=Counter(), outcome=Counter(), order=Counter(), members={})
    for m in snap["members"]:
        if m["id"] not in by_id: continue
        i, act, dd = by_id[m["id"]]
        box, d = B["boxes"][i], der[i]
        e = box["idr_high"] if dd == 1 else box["idr_low"]
        w = box["idr_high"] - box["idr_low"]
        if (m["act"], m["w"]) != (act, w): v.append(("ACTIVATION", ["S2", "M0"], f"{m['id']}: activation / width differ")); continue
        path = [list(ref_directed(d["rows"][T], dd, e)) if T in d["rows"] else None for T in grid]
        if m["path"] != path: v.append(("PATH", ["O1", "M0"], f"{m['id']}: the directed path differs from the base")); continue
        r = {}
        for ev in ("R", "X"):
            x = ref_final_extreme(path, grid, act, end, ev)
            mine = {k: m[ev][k] for k in m[ev] if k in ("s", "v", "t", "ties", "bound")}
            if mine != x: v.append(("OUTCOME", ["P0.1", "P1", "K31"], f"{m['id']}: {ev} {m[ev]} != reference {x}"))
            r[ev] = x
            ref[ev if x["s"] == "known" else ("unknown" if x["s"] == "unknown" else "none")][(ref_cell(x["v"], w), (x["t"] - formed) // 15) if x["s"] == "known" else ev] += 1
        o = ref_first_order(r["R"], r["X"])
        if m["order"] != o: v.append(("ORDER", ["P0.2"], f"{m['id']}: order {m['order']} != reference {o}"))
        ref["order"][o] += 1
        if o in ("R_before_X", "X_before_R", "same_M5") and m.get("orderDetail") != ref_order_detail(r["R"], r["X"]):
            v.append(("ORDER", ["P0.2", "K20"], f"{m['id']}: order detail differs"))
        if view == "conf":
            oppv = dd * ((box["dr_low"] if side == 1 else box["dr_high"]) - e)
            cat, brk, known_t = ref_dr_outcome(path, grid, act, end, oppv)
            if (m.get("oppv"), m.get("outcome"), m.get("brk"), m.get("brkKnown")) != (oppv, cat, brk, known_t):
                v.append(("DR_OUTCOME", ["P0.2", "K14"], f"{m['id']}: DR outcome {m.get('outcome')} != reference {cat}"))
            ref["outcome"][cat] += 1
        ref["members"][m["id"]] = dict(path=path, act=act, w=w, R=r["R"], X=r["X"])
    for ev in ("R", "X"):
        c = snap["counts"][ev]
        cells = sorted([k, b, n] for (k, b), n in ref[ev].items())
        if sorted(c["cells"]) != cells or c["unknown"] != ref["unknown"][ev] or c["none"] != ref["none"][ev] or c["known"] != sum(ref[ev].values()):
            v.append(("COUNTS", ["V2.1", "K31"], f"{ev}: the published table differs from the recount"))
        if sum(n for _, _, n in c["cells"]) + c["unknown"] + c["none"] != snap["N"]:
            v.append(("DENOMINATOR", ["V2.1"], f"{ev}: cells + unknown + no period != N"))
    if dict(snap["counts"]["order"]) != {k: n for k, n in ref["order"].items()}:
        v.append(("COUNTS", ["P0.2"], "order counts differ from the recount"))
    if view == "conf":
        want = {k: ref["outcome"].get(k, 0) for k in ("held", "broken", "unknown", "none")}
        if snap["counts"].get("outcome") != want: v.append(("COUNTS", ["P0.2"], "DR outcome counts differ from the recount"))
    elif "outcome" in snap["counts"]:
        v.append(("COUNTS", ["H1", "K26"], "a break family carries a DR-outcome share"))
    # identity: the family id binds the rule and the participants, the snapshot id binds the measurements (K09)
    sem = snap.get("semantics")
    fid = hashlib.sha1(json.dumps([sem, inst, session, key["weekday"] if key.get("scope", "weekday") == "weekday" else "all", side, view, win, key["cutoff"], snap["ids"]]).encode()).hexdigest()[:16]
    measured = [[m["id"], m["R"], m["X"], m.get("outcome"), m["order"]] for m in snap["members"]]
    ssid = hashlib.sha1(json.dumps([fid, snap["source"], measured], sort_keys=True).encode()).hexdigest()[:16]
    if (snap["family_id"], snap["snapshot_id"]) != (fid, ssid): v.append(("IDENTITY", ["H2", "K09", "§1.2"], "family_id / snapshot_id do not bind the rule, participants and measurements"))
    res = (v, ref)
    if len(_VER) > 64: _VER.clear()
    _VER[ck] = res
    return res


_ZV = {}


def verify_zones(snap, zm, ev, ref):
    """P3: the zone map of one event re-derived from the verified final points by the reference algorithm (cached per
    snapshot and event: the zones of a snapshot never move with the slice)."""
    key = (snap["snapshot_id"], ev, id(zm))
    if key not in _ZV:
        if len(_ZV) > 128: _ZV.clear()
        _ZV[key] = _verify_zones(snap, zm, ev, ref)
    return _ZV[key]


def _verify_zones(snap, zm, ev, ref):
    v = []
    sch, key = snap["schedule"], snap["key"]
    formed, end = sch["formed"], sch["end"]
    win = (key["window"][0] - formed) // 15
    pts = []
    for m in snap["members"]:
        x = ref["members"].get(m["id"], {}).get(ev)
        if x and x["s"] == "known": pts.append((ref_cell(x["v"], m["w"]), (x["t"] - formed) // 15, m["id"]))
    alg = get("ALG:ZONE-MAP-3")
    t_first, t_last = formed + 15 * win + 5, end - 5
    R = ref_zone_map(pts, snap["N"], (t_first - formed) // 15, (t_last - formed) // 15)
    if zm.get("algorithm_version") != alg["version"]: v.append(("ALGORITHM", ["P3"], f"{ev}: algorithm {zm.get('algorithm_version')} is not the registry's {alg['version']}"))
    if zm.get("min_support") != R["need"]: v.append(("SUPPORT", ["P3"], f"{ev}: minimum support differs"))
    got = [(sorted(map(tuple, z["cell_mask"])), sorted(z["member_session_ids"]), z["n_zone"], tuple(z["peak_anchor"])) for z in zm.get("zones", [])]
    want = [(z["cells"], z["members"], z["n"], z["anchor"]) for z in R["zones"]]
    if got != want: v.append(("ZONE_MASK", ["P3", "K30", "K31"], f"{ev}: the zones differ from the reference algorithm ({len(got)} vs {len(want)})"))
    if sorted(zm.get("residual_ids", [])) != R["residual"] or zm.get("n_residual_total") != len(R["residual"]): v.append(("RESIDUAL", ["P3"], f"{ev}: residual differs"))
    N = snap["N"]
    unk = sum(1 for m in snap["members"] if ref["members"].get(m["id"], {}).get(ev, {}).get("s") == "unknown")
    none = sum(1 for m in snap["members"] if ref["members"].get(m["id"], {}).get(ev, {}).get("s") == "none")
    if (zm.get("unknown_count"), zm.get("no_event_count"), zm.get("N_family")) != (unk, none, N): v.append(("SUPPORT", ["P3", "V2.1"], f"{ev}: unknown / no period / N differ"))
    if sum(z["n_zone"] for z in zm.get("zones", [])) + zm.get("n_residual_total", 0) + unk + none != N: v.append(("DENOMINATOR", ["V2.1"], f"{ev}: zones + residual + unknown + none != N"))
    for z in zm.get("zones", []):
        if N and abs(z["p_snapshot"] - z["n_zone"] / N) > 1e-12: v.append(("SHARE", ["P3"], f"{ev} {z['label']}: share is not n / N"))
        zid = hashlib.sha1("|".join(map(str, (snap["snapshot_id"], ev, tuple(z["peak_anchor"]), alg["version"]))).encode()).hexdigest()[:12]
        if z["zone_id"] != zid: v.append(("IDENTITY", ["P3", "K30"], f"{ev} {z['label']}: zone id does not bind snapshot, event, apex and version"))
        for e in check_zone_diagnostics(z): v.append(("DIAGNOSTIC", ["P3", "V3"], f"{ev} {z['label']}: {e}"))
        for e in check_study_refs(z, key["session"], ev): v.append(("STUDY", ["V3"], f"{ev} {z['label']}: {e}"))
    return v, R


def today_state(bars, session, obs, now, is_live, tick):
    """S1 / S2 / E0 for the viewed day re-derived from its M5 (closed ones only; the rules of the registry)."""
    blk = _blocks()[session]
    fs, fe, end = blk["formation_start"], blk["formation_end"], blk["block_end"]
    closed_by = now if is_live else obs
    closed = {int(b[0]) + 5: b for b in bars if int(b[0]) + 5 <= closed_by}
    win = [closed.get(T) for T in range(fs + 5, fe + 1, 5)]
    if any(x is None for x in win): return None
    tk = lambda p: int(round(p / tick))
    dr_h, dr_l = max(tk(x[2]) for x in win), min(tk(x[3]) for x in win)
    idr_h, idr_l = max(max(tk(x[1]), tk(x[4])) for x in win), min(min(tk(x[1]), tk(x[4])) for x in win)
    lim = min(obs, end)
    conf = side = brk = None
    for T in sorted(closed):
        if T <= fe or T > lim: continue
        c = tk(closed[T][4])
        if c > dr_h: conf, side = T, 1; break
        if c < dr_l: conf, side = T, -1; break
    if conf is not None:
        opp = dr_l if side == 1 else dr_h
        brk = next((T for T in sorted(closed) if conf < T <= lim and side * (tk(closed[T][4]) - opp) < 0), None)
    return dict(dr_high=dr_h, dr_low=dr_l, idr_high=idr_h, idr_low=idr_l, conf=conf, side=side, brk=brk, closed=closed)


def verify_today_zones(fam, bars, tick, zones_ref):
    """E3 / E4 at the request's slice: today's provisional extremes from today's closed M5 after the activation and
    every zone's two independent statuses, re-derived."""
    v = []
    today, sch = fam["today"], fam["schedule"]
    formed, end = sch["formed"], sch["end"]
    view = fam["view"]
    side = today["side"]
    d = side if view == "conf" else -side
    act = today["c0"] if view == "conf" else today["brk"]
    tk = lambda p: int(round(p / tick))
    e_t = tk(today["idrH"] if d == 1 else today["idrL"])
    w_t = tk(today["idrH"] - today["idrL"])
    have = {int(b[0]) + 5: b for b in bars}
    slice_ = today["slice"]
    rows, gap = [], False
    for T in range(act + 5, slice_ + 1, 5):
        b = have.get(T)
        if b is None: gap = True; continue
        lo, hi = (b[3], b[2]) if d == 1 else (b[2], b[3])
        rows.append((T, d * (tk(lo) - e_t), d * (tk(hi) - e_t)))
    out = {}
    for ev, zm in (fam.get("zones") or {}).items():
        srv = (today.get("zones") or {}).get(ev, {})
        times = {m["id"]: m[ev]["t"] for m in fam["members"] if m[ev]["s"] == "known"}
        clock = [ref_history_clock(z["cell_mask"], [times[s] for s in z["member_session_ids"] if s in times], slice_, formed, end - 5) for z in zm["zones"]]
        if gap: status, q, v10 = ["UNKNOWN"] * len(zm["zones"]), None, None
        elif rows:
            j = min(range(len(rows)), key=lambda i: (rows[i][1], i)) if ev == "R" else min(range(len(rows)), key=lambda i: (-rows[i][2], i))
            val = rows[j][1] if ev == "R" else rows[j][2]
            q, v10 = (ref_cell(val, w_t), (rows[j][0] - 5 - formed) // 15), 10 * val
            status = [ref_reachability(z["cell_mask"], ev, q, v10, w_t, slice_, formed, end - 5) for z in zm["zones"]]
        else:
            q, v10 = None, None
            status = [ref_reachability(z["cell_mask"], ev, None, None, w_t, slice_, formed, end - 5) for z in zm["zones"]]
        tok = {"STATUS_UNKNOWN": "UNKNOWN"}
        if [tok.get(s, s) for s in srv.get("status", [])] != status: v.append(("REACHABILITY", ["E3", "K24"], f"{ev}: today's zone statuses differ from the reference"))
        if srv.get("clock", []) != clock: v.append(("HISTORY_CLOCK", ["E4", "K25"], f"{ev}: the history clock differs from the reference"))
        out[ev] = dict(status=status, clock=clock, q=q, v10=v10, w=w_t, rows=rows, gap=gap)
    return v, out


# =====================================================================================================================
# admissible claims (computed from the evidence) against the declared claim form (an explicit normative object)
# =====================================================================================================================
def admissible_claims(estimand_id, case_set_id):
    """The claim classes the evidence admits for one estimand on one case-set rule. No class is defaulted:
    C0 needs a fixed composition (a base family or the universe) and a historical target; C1 needs a named
    selection condition (prefix-available or retrospective — availability decides live use, not the class); C2 needs
    a PredictiveAdmission for exactly this estimand; C3 needs a PolicySpecification. None of C2 / C3 exists."""
    est, cs = get(estimand_id), get(case_set_id)
    if est is None or cs is None: return set()
    if case_set_id not in est["q4_case_set"]: return set()
    out = set()
    if est["q2_target"] == "FIXED_HISTORICAL_SET":
        if cs["role"] in ("BASE_FAMILY", "HISTORICAL_UNIVERSE"): out.add(C0)
        if cs["role"] in ("ELIGIBLE_AT_CUT", "MATCHED_AT_CUT", "OUTCOME_SUBGROUP", "RETROSPECTIVE_RESEARCH") and cs.get("condition_ru"): out.add(C1)
    reg = registry() or {}
    if any(a["estimand"] == estimand_id for a in reg.get("predictive_admissions", [])): out.add(C2)
    if reg.get("policies"): out.add(C3)
    return out


def claim_form_of(estimand_id):
    forms = [c for c in (registry() or {}).get("claim_forms", []) if c["estimand"] == estimand_id]
    return forms[0] if len(forms) == 1 else None


# =====================================================================================================================
# building the envelope: bundles, records, checks, violations
# =====================================================================================================================
def _fmt_pct(fr):
    if fr is None: return "—"
    x = round(float(fr) * 100, 1)
    return (f"{x:.1f}".rstrip("0").rstrip(".")).replace(".", ",") + " %"


def _fmt(x, nd=2):
    if x is None: return "—"
    s = f"{float(x):.{nd}f}".rstrip("0").rstrip(".") if nd else str(int(round(float(x))))
    return s.replace(".", ",")


def _render(template, values):
    return re.sub(r"\{([A-Za-z0-9_]+)\}", lambda m: str(values.get(m.group(1), "—")), template)


class Envelope:
    """Collects the contract section of one response."""

    def __init__(self, route, profile, params):
        self.route, self.profile = route, profile
        self.d = dict(edition=EDITION, registry_hash=registry_hash(), status="CONFORMANT", route=route, profile=profile,
                      request=dict(request_id=uuid.uuid4().hex[:16], requester="LOCAL_HTTP_CLIENT",
                                   requested_at_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                   parameters=json.dumps(params, ensure_ascii=False, sort_keys=True), authority="NONE_DESCRIPTIVE"),
                      checks=[], violations=[])
        self.bundles = []
        self.withheld = set()

    def check(self, name, ok, checked=None, note=None):
        c = dict(check=name, outcome="PASS" if ok else "FAIL")
        if checked is not None: c["checked"] = int(checked)
        if note: c["note"] = note
        self.d["checks"].append(c)

    def violate(self, code, refs, message, withheld=(), severity="BLOCKING", path=None):
        if STRICT["on"]: raise ContractViolation(f"{code}: {message}")
        v = dict(code=code, sc_ref=list(refs), message=message, severity=severity)
        if path: v["path"] = path
        if withheld: v["withheld"] = list(withheld); self.withheld.update(withheld)
        self.d["violations"].append(v)
        if severity == "BLOCKING": self.d["status"] = "VIOLATION"

    def bundle(self, estimand_id, case_set_id, case_set_snapshot, operation, inputs, estimates, supports, values,
               parameters=None, verification="VERIFIED_BY_REFERENCE", claim_extra=None, validations=None):
        """One published statistic. Its claim is the registry's explicit form, published only if its class is
        admissible for this evidence; otherwise the statistic is withheld with the reason."""
        est, form = get(estimand_id), claim_form_of(estimand_id)
        if est is None or form is None:
            self.violate("UNREGISTERED_ESTIMAND", ["T1", "§12.3"], f"{estimand_id} has no estimand or no single claim form", withheld=[estimand_id]); return None
        adm = admissible_claims(estimand_id, case_set_id)
        if form["claim_class"] not in adm:
            self.violate("CLAIM_NOT_ADMISSIBLE", ["§10.1", "C1", "C2", "K33"], f"{estimand_id}: the form's class {form['claim_class']} is not admissible on {case_set_id} (admissible: {sorted(adm)})", withheld=[estimand_id]); return None
        n = len(self.bundles) + 1
        der = dict(derivation_id=f"D{n}", operation=operation, reference_definition=est and _reference_of(estimand_id),
                   inputs=inputs, executed_at_utc=self.d["request"]["requested_at_utc"], verification=verification)
        claim = dict(claim_class=form["claim_class"], claim_form=form["id"], statement_ru=_render(form["statement_ru"], values),
                     estimand=estimand_id, applies_to_ru="история этого набора на этот срез; не сегодняшний исход",
                     forbidden_readings_ru=form["forbidden_readings_ru"])
        cs = get(case_set_id)
        if form["claim_class"] == C0: claim["case_set_snapshot"] = case_set_snapshot
        elif form["claim_class"] == C1:
            claim.update(parent_case_set=(claim_extra or {}).get("parent_case_set", case_set_snapshot), selected_case_set=case_set_id,
                         condition_ru=form.get("condition_ru") or cs["condition_ru"], condition_availability=cs["condition_availability"])
            if (claim_extra or {}).get("cut") is not None: claim["cut_close_minute"] = int(claim_extra["cut"])
        b = dict(id=f"B{n}", estimand=estimand_id, claim_form=form["id"], derivation=der,
                 estimates=[dict(e, estimate_id=f"B{n}.E{i + 1}") for i, e in enumerate(estimates)],
                 supports=[dict(s, support_id=f"B{n}.S{i + 1}") for i, s in enumerate(supports)],
                 admissible_claims=sorted(adm), claim=claim)
        if parameters: b["parameters"] = json.dumps(parameters, ensure_ascii=False, sort_keys=True)
        if validations: b["validations"] = list(validations)
        self.bundles.append(b)
        return b

    def finish(self, extra=None):
        out = dict(self.d)
        if extra: out.update(extra)
        if out["status"] != "CONTRACT_STALE": out["bundles"] = self.bundles
        errs = validate(out, "ContractEnvelope")
        if errs:
            if STRICT["on"]: raise ContractViolation("envelope: " + "; ".join(errs[:5]))
            out["violations"] = out["violations"] + [dict(code="ENVELOPE_STRUCTURE", sc_ref=["§14.4"], message="; ".join(errs[:5]), severity="BLOCKING")]
            out["status"] = "VIOLATION"
            out.pop("bundles", None)
        return out


def _reference_of(estimand_id):
    est = get(estimand_id)
    out = get(est["q5_outcome"]) if est else None
    return out["reference_definition"] if out else "none"


def _share_est(estimator, count, n, unit="share of N_base"):
    fr = est_count_over_n(count, n)
    if fr is None: return dict(estimator=estimator, value_kind="NO_ESTIMATE", unit=unit, no_estimate_reason="N = 0: no estimate")
    return dict(estimator=estimator, value_kind="POINT", value=float(fr), numerator=int(count), denominator=int(n), unit=unit)


def _inputs(snap, extra=()):
    src = snap.get("source") or {}
    return [dict(input_kind="OBSERVATION_SNAPSHOT", ref="OBS:G3-TAPE", version=f"{src.get('base')}@{src.get('built')}"),
            dict(input_kind="CASE_SET_SNAPSHOT", ref=snap["family_id"], version=snap["snapshot_id"]),
            dict(input_kind="REGISTRY", ref=EDITION, version=registry_hash()),
            dict(input_kind="CODE", ref=GATE_VERSION, version=_code_hash())] + list(extra)


_CODE = {}


def _code_hash():
    if "h" not in _CODE:
        h = hashlib.sha1()
        for f in ("contract.py", "scene24.py", "zonemap24.py", "now24.py", "scene21.py"):
            p = Path(__file__).resolve().parent / f
            if p.exists(): h.update(p.read_bytes().replace(b"\r\n", b"\n"))
        _CODE["h"] = h.hexdigest()[:12]
    return _CODE["h"]


def case_set_spec_of(snap):
    k = snap["key"]
    return {("confirmation", "weekday"): "CS:F-CONF-1", ("confirmation", "all"): "CS:F-CONF-ALL-1",
            ("break", "weekday"): "CS:F-BREAK-1", ("break", "all"): "CS:F-BREAK-ALL-1"}[(k["event"], k.get("scope", "weekday"))]


# =====================================================================================================================
# the family response (/api/d24/family)
# =====================================================================================================================
def attach_family(out, inst, B, day, params):
    """Verifies the family response at its creation boundary, withholds what fails, and attaches the envelope."""
    env = Envelope("/api/d24/family", "PROFILE:BASE-24", params)
    bars, tick = (day or {}).get("bars") or [], float((day or {}).get("tick") or 0.25)
    if out.get("status") != "ok" or "members" not in out:
        out["contract"] = env.finish(); return out
    snap = out
    cs_id = case_set_spec_of(snap)
    viol, ref = verify_snapshot(inst, B, snap)
    env.check("verify_snapshot: membership, paths, outcomes, counts, identity re-derived from the base", not viol, snap["N"])
    if viol:
        for code, refs, msg in viol: env.violate(code, refs, msg, withheld=["family"])
        return _withhold_family(out, env)
    N = snap["N"]
    # records
    src = snap["source"]
    env.d["observation"] = dict(source="OBS:G3-TAPE", content_version=f"{src.get('base')}@{src.get('built')}", history_range=src.get("history"),
                                mode="LIVE" if (out.get("today") or {}).get("source") == "live" else "HISTORY_DAY_REPLAY_BY_CLOSE")
    env.d["case_sets"] = [dict(spec=cs_id, family_id=snap["family_id"], snapshot_id=snap["snapshot_id"], n_members=N, cutoff_date=snap["key"]["cutoff"],
                               exclusions=[dict(reason=k, count=int(n)) for k, n in sorted((snap.get("journal") or {}).items())], data_revision=f"{src.get('base')}@{src.get('built')}")]
    today = out.get("today") or {}
    view = snap["view"]
    side = today.get("side")
    if side:
        d = side if view == "conf" else -side
        e_px = today["idrH"] if d == 1 else today["idrL"]
        env.d["frame"] = dict(spec="MF:CONFIRMATION-1" if view == "conf" else "MF:BREAK-1", origin_price=float(e_px), direction=d,
                              width_ticks=int(round((today["idrH"] - today["idrL"]) / tick)), tick_size=float(tick))
        env.d["session"] = dict(instrument=inst, trading_date=today["date"], block=snap["key"]["session"], rule="RULE:DRIDR-24-1",
                                dr_high=float(today["drH"]), dr_low=float(today["drL"]), idr_high=float(today["idrH"]), idr_low=float(today["idrL"]),
                                activation=dict(kind="CONFIRMATION", direction="LONG" if side == 1 else "SHORT", evidence_close_minute=int(today["c0"]), window_index=int(today["window"]), first_time_known=True))
        if today.get("brk") is not None:
            env.d["session"]["dr_break"] = dict(kind="DR_BREAK", direction="LONG" if side == 1 else "SHORT", evidence_close_minute=int(today["brk"]), window_index=int(today["brkWindow"]), first_time_known=True)
        live = today.get("source") == "live" and params.get("at") is None      # a replay of the live day reads closed M5 only
        st = today_state(bars, snap["key"]["session"], today["obs"], float(day.get("now") or today["obs"]) if live else today["obs"], live, tick)
        if st is not None and (st["conf"], st["side"], st["brk"]) != (today["c0"], today["side"], today.get("brk")):
            env.violate("TODAY_STATE", ["S1", "S2", "E0"], "today's confirmation / break differ from the re-derivation", withheld=["family"])
            return _withhold_family(out, env)
    env.d["cut"] = dict(spec="CUT:LAST-CLOSED-M5-1", target_session=f"{inst}-{(today.get('date') or '').replace('-', '')}-{snap['key']['session']}",
                        cut_close_minute=int(today.get("slice", 0)), cut_clock_et=_clk(today.get("slice", 0)),
                        mode="LIVE" if today.get("source") == "live" else "HISTORY_DAY_REPLAY_BY_CLOSE")
    inputs = _inputs(snap)
    sid = snap["snapshot_id"]
    # B-RX joint tables
    for ev in ("R", "X"):
        c = snap["counts"][ev]
        cells = [dict(price_cell=int(k), time_cell=int(b), count=int(n)) for k, b, n in c["cells"]]
        est = dict(estimator="ESTR:JOINT-CELLS-1", value_kind="DISTRIBUTION" if N else "NO_ESTIMATE", unit="cells of N_base", denominator=N)
        if N: est["cells"] = cells
        else: est["no_estimate_reason"] = "N = 0: no estimate"
        env.bundle(f"EST:B-RX-JOINT-{ev}", cs_id, sid, "lab/scene24.py::_snapshot", inputs, [est],
                   [dict(case_set=sid, n_base=N, components=[dict(component="ENDPOINT", of=N, known=c["known"], unknown=c["unknown"], no_period=c["none"])])],
                   dict(known=c["known"], N=N, unknown=c["unknown"], no_period=c["none"]))
    if view == "conf":
        o = snap["counts"]["outcome"]
        cats = {"held": "HELD", "broken": "BROKEN", "unknown": "UNKNOWN", "none": "NO_PERIOD"}
        env.bundle("EST:B-DR", cs_id, sid, "lab/scene24.py::measure", inputs,
                   [dict(estimator="ESTR:CATEGORY-COUNTS-1", value_kind="CATEGORY_SHARES", unit="categories of N_base", denominator=N,
                         categories=[dict(category=cats[k], count=int(o[k])) for k in ("held", "broken", "unknown", "none")])],
                   [dict(case_set=sid, n_base=N, components=[dict(component="CATEGORY", of=N, known=o["held"] + o["broken"], unknown=o["unknown"], no_period=o["none"])])],
                   dict(N=N, held=o["held"], broken=o["broken"], unknown=o["unknown"], no_period=o["none"]))
    tok = {"R_before_X": "R_BEFORE_X", "X_before_R": "X_BEFORE_R", "same_M5": "SAME_M5", "unknown": "UNKNOWN", "no_period": "NO_PERIOD"}
    oc = snap["counts"]["order"]
    env.bundle("EST:B-ORDER", cs_id, sid, "lab/scene24.py::measure", inputs,
               [dict(estimator="ESTR:CATEGORY-COUNTS-1", value_kind="CATEGORY_SHARES", unit="categories of N_base", denominator=N,
                     categories=[dict(category=tok[k], count=int(n)) for k, n in sorted(oc.items())])],
               [dict(case_set=sid, n_base=N, components=[dict(component="CATEGORY", of=N, unknown=int(oc.get("unknown", 0)), no_period=int(oc.get("no_period", 0)))])],
               dict({tok[k]: n for k, n in oc.items()}, N=N, **{t: oc.get(k, 0) for k, t in tok.items() if k not in oc}))
    # zones
    for ev in ("R", "X"):
        zm = (snap.get("zones") or {}).get(ev)
        if zm is None: continue
        zv, _ = verify_zones(snap, zm, ev, ref)
        env.check(f"verify_zones {ev}: masks re-derived by the reference zone-map-3", not zv, len(zm["zones"]))
        if zv:
            for code, refs, msg in zv: env.violate(code, refs, msg, withheld=[f"zones.{ev}"])
            continue
        unk, none = zm["unknown_count"], zm["no_event_count"]
        for z in zm["zones"]:
            env.d.setdefault("regions", []).append(dict(zone_id=z["zone_id"], algorithm="ALG:ZONE-MAP-3", event=ev, snapshot_id=sid, n_cells=len(z["cell_mask"]),
                                                        n_zone=z["n_zone"], min_support=zm["min_support"], mask_verified=True))
            env.bundle(f"EST:B-ZONE-{ev}", cs_id, sid, "lab/zonemap24.py::evaluate", inputs, [_share_est("ESTR:ZONE-SHARE-1", z["n_zone"], N)],
                       [dict(case_set=sid, n_base=N, components=[dict(component="MEMBERSHIP", of=N, yes=z["n_zone"], unknown=unk, no_period=none)])],
                       dict(yes=z["n_zone"], N=N, label=z["label"], unknown=unk + none), parameters=dict(zone_id=z["zone_id"], label=z["label"]))
            g, b = z["grid_member_jaccard"], z["bootstrap_recovery"]
            env.bundle(f"EST:ZD-GRID-{ev}", cs_id, sid, "lab/zonemap24.py::evaluate", inputs,
                       [dict(estimator="ESTR:ZONE-JACCARD-1", value_kind="INDEX", value=float(g["min"]), unit="Jaccard of member sets (min of three shifts)")],
                       [dict(case_set=sid, n_base=N, components=[dict(component="MEMBERSHIP", of=N, known=N - unk - none)])],
                       dict(label=z["label"], value=_fmt(g["min"], 2)), parameters=dict(zone_id=z["zone_id"]), verification="NOT_RECOMPUTED")
            if b.get("mean") is not None:
                env.bundle(f"EST:ZD-BOOT-{ev}", cs_id, sid, "lab/zonemap24.py::evaluate", inputs,
                           [dict(estimator="ESTR:ZONE-JACCARD-1", value_kind="INDEX", value=float(b["mean"]), unit="mean Jaccard over resamplings")],
                           [dict(case_set=sid, n_base=N, components=[dict(component="MEMBERSHIP", of=int(b["of"]))])],
                           dict(label=z["label"], value=_fmt(b["mean"], 2), share=_fmt_pct(b["share_ge_half"])), parameters=dict(zone_id=z["zone_id"]), verification="NOT_RECOMPUTED")
            if z.get("null_status") == "measured":
                env.bundle(f"EST:ZD-NULL-{ev}", cs_id, sid, "lab/zonemap24.py::_null", inputs,
                           [dict(estimator="ESTR:ZONE-NULL-1", value_kind="INDEX", value=float(z["null_excess"]), lower=float(z["null_interval"][0]), upper=float(z["null_interval"][1]), unit="excess share in the frozen region (held-out half), with its year-bootstrap interval")],
                           [dict(case_set=sid, n_base=N, components=[dict(component="MEMBERSHIP", of=int(z["null_validation_n"]))])],
                           dict(label=z["label"], p_real=_fmt_pct(z["p_real_mask"]), p_null=_fmt_pct(z["p_null_mask"]), excess=_fmt(z["null_excess"] * 100, 1) + " п.п."),
                           parameters=dict(zone_id=z["zone_id"]), verification="NOT_RECOMPUTED")
        env.bundle(f"EST:B-ZONE-RESIDUAL-{ev}", cs_id, sid, "lab/zonemap24.py::evaluate", inputs, [_share_est("ESTR:ZONE-SHARE-1", zm["n_residual_total"], N)],
                   [dict(case_set=sid, n_base=N, components=[dict(component="MEMBERSHIP", of=N, yes=zm["n_residual_total"], unknown=unk, no_period=none)])],
                   dict(yes=zm["n_residual_total"], N=N))
        if zm.get("study_refs"):
            env.bundle("EST:ZM3-STUDY", "CS:ZM3-STUDY-1", sid, "lab/zonemap24.py::study_refs", inputs,
                       [dict(estimator="ESTR:STUDY-TABLE-1", value_kind="STORED_TABLE", table_ru=zm["study_refs"]["text"], unit="stored research table")],
                       [dict(case_set="CS:ZM3-STUDY-1", n_base=0, components=[dict(component="MEMBERSHIP", of=0)])],
                       dict(holds="(см. таблицу)", possible="(см. таблицу)"), parameters=dict(event=ev, session=snap["key"]["session"]),
                       verification="NOT_RECOMPUTED", validations=["VAL:ZM3-STUDY"], claim_extra=dict(parent_case_set=sid))
    # today's two axes (E3, E4)
    if today.get("zones"):
        tv, tref = verify_today_zones(snap, bars, tick, None)
        env.check("verify_today_zones: reachability and history clock re-derived at the slice", not tv)
        if tv:
            for code, refs, msg in tv: env.violate(code, refs, msg, withheld=["today.zones"])
        else:
            for ev, zm in (snap.get("zones") or {}).items():
                for i, z in enumerate(zm["zones"]):
                    env.d.setdefault("reachability", []).append(dict(region_id=z["zone_id"], event=ev, reachability=tref[ev]["status"][i], cut_close_minute=int(today["slice"]), logic_version="zone-map-3/E3"))
                    env.d.setdefault("history_clock", []).append(dict(region_id=z["zone_id"], event=ev, history_clock=tref[ev]["clock"][i], cut_close_minute=int(today["slice"])))
    env.check("admissible claims: every published form is of an admissible class", True, len(env.bundles))
    out["contract"] = env.finish()
    _apply_withheld(out, env)
    return out


def _withhold_family(out, env):
    """A violated base family is not published: its statistics are removed and the reason is named."""
    keep = {k: out[k] for k in ("session", "today", "view", "key") if k in out}
    keep.update(status="contract_violation", message="нарушение контракта SC-1.1: " + "; ".join(v["message"] for v in env.d["violations"])[:300],
                contract=env.finish())
    return keep


def _apply_withheld(out, env):
    """Removes withheld objects from this response only (the cached snapshot is never mutated)."""
    for w in env.withheld:
        if w.startswith("zones."):
            ev = w.split(".")[1]
            out["zones"] = {k: v for k, v in (out.get("zones") or {}).items() if k != ev}
            if out.get("today") and out["today"].get("zones"):
                out["today"] = dict(out["today"], zones={k: v for k, v in out["today"]["zones"].items() if k != ev})
        if w == "today.zones" and out.get("today"): out["today"] = {k: v for k, v in out["today"].items() if k != "zones"}


def _clk(t):
    t = int(t) % 1440
    return f"{t // 60:02d}:{t % 60:02d}"


# =====================================================================================================================
# the NOW response (/api/d24/now)
# =====================================================================================================================
def ref_now_sets(fam, bars, tick, cut):
    """The NOW sets at a common clock cut, re-derived: today's state, every member's eligibility (B0), its matcher
    memberships and its residual outcomes for R and X."""
    today, sch, grid = fam["today"], fam["schedule"], fam["grid"]
    formed = sch["formed"]
    view = fam["view"]
    side = today["side"]
    d = side if view == "conf" else -side
    act = today["c0"] if view == "conf" else today["brk"]
    tk = lambda p: int(round(p / tick))
    e = tk(today["idrH"] if d == 1 else today["idrL"])
    w_t = tk(today["idrH"] - today["idrL"])
    have = {int(b[0]) + 5: b for b in bars}
    path_t = []
    for T in grid:
        b = have.get(T) if T <= cut else None
        if b is None: path_t.append(None); continue
        h, l, c = tk(b[2]), tk(b[3]), tk(b[4])
        path_t.append([l - e, h - e, c - e] if d == 1 else [e - h, e - l, e - c])
    c_i = (cut - formed - 5) // 5
    a_t = (act - formed - 5) // 5
    st_t = ref_prefix(path_t, a_t, c_i)
    rows = []
    for m in fam["members"]:
        a_m = (m["act"] - formed - 5) // 5
        st = ref_prefix(m["path"], a_m, c_i, m.get("oppv") if view == "conf" else None)
        if st is None: continue
        mt = ref_matchers(st, st_t, m["w"], w_t, m["path"], path_t, a_m, a_t, c_i) if st_t else {}
        res = {ev: ref_residual(m["path"], c_i, st[0] if ev == "R" else st[1], ev) for ev in ("R", "X")}
        rows.append(dict(id=m["id"], w=m["w"], match=mt, res=res))
    return dict(today=st_t, w_t=w_t, c=c_i, a_t=a_t, rows=rows)


def ref_forecast(rows, ev, keep):
    """The NOW numbers of one set by the reference: supports per component and the estimates (exact)."""
    sel = [r for r in rows if keep(r)]
    res = [r["res"][ev] for r in sel]
    yes = sum(1 for x in res if x["new"] == "YES"); no = sum(1 for x in res if x["new"] == "NO"); unk = len(res) - yes - no
    dk = [(Fraction(x["delta"], r["w"])) for r, x in zip(sel, res) if x["delta"] is not None]
    dpos = [v for v in dk if v > 0]
    new_yes_delta_unknown = sum(1 for x in res if x["new"] == "YES" and x["delta"] is None)
    taus = [x["tau"] for x in res if x["new"] == "YES" and x["tau"] is not None]
    return dict(total=len(res), yes=yes, no=no, unknown=unk, deltas=dk, dpos=dpos, dpos_unknown=new_yes_delta_unknown,
                taus=taus, tau_unknown=sum(1 for x in res if x["new"] == "YES" and x["tau"] is None), no_event=no)


def _close(a, b, tol=5.0001e-5):
    if a is None or b is None: return a is None and b is None
    return abs(float(a) - float(b)) <= tol


def verify_forecast(prod, ref, ref_delta=None, ref_time=None):
    """Production NOW numbers of one set against the reference (exact values rounded as the production rounds). The
    remaining movement and the time may come from another set (B0) when the path did not pass their own gates."""
    errs = []
    s = prod["support"]
    if (s["N_match_total"], s["N_match_unknown"], s["N_match_known"]) != (ref["total"], ref["unknown"], ref["total"] - ref["unknown"]): errs.append("support of new")
    if s.get("N_new_yes") is not None and (s["N_new_yes"], s["N_new_no"]) != (ref["yes"], ref["no"]): errs.append("existence supports")
    known = ref["total"] - ref["unknown"]
    if not _close(prod["p_new_extreme"], Fraction(ref["yes"], known) if known else None): errs.append("p_new_extreme")
    bounds = est_binary_bounds(ref["yes"], ref["no"], ref["unknown"])
    if bounds and not (_close(prod["p_new_bounds"][0], bounds[0]) and _close(prod["p_new_bounds"][1], bounds[1])): errs.append("p_new_bounds")
    if known and not _close(prod["p_no_new_extreme"], 1 - Fraction(ref["yes"], known), tol=1.0001e-4): errs.append("p_no_new_extreme")
    rd, rt = ref_delta or ref, ref_time or ref
    if s.get("N_delta_known") != len((ref_delta or ref)["deltas"]) and ref_delta is None: errs.append("support of delta")
    if s.get("N_delta_unknown") is not None and ref_delta is None and s["N_delta_unknown"] != ref["total"] - len(ref["deltas"]): errs.append("delta unknown")
    for qk, q in (("q25", 0.25), ("q50", 0.5), ("q75", 0.75)):
        if not _close(prod["delta"][qk], ref_quantile(rd["deltas"], q)): errs.append(f"delta {qk}")
        if not _close(prod["delta_if_new"][qk], ref_quantile(rd["dpos"], q)): errs.append(f"delta_if_new {qk}")
        if not _close(prod["time_to_new"][qk + "_m5"], ref_quantile(rt["taus"], q)): errs.append(f"time {qk}")
    for (n, dd), key in zip(((1, 10), (1, 5), (2, 5)), ("p_ge_0_10", "p_ge_0_20", "p_ge_0_40")):
        want = Fraction(sum(1 for v in rd["deltas"] if v >= Fraction(n, dd)), len(rd["deltas"])) if rd["deltas"] else None
        if not _close(prod["delta"][key], want): errs.append(key)
    if prod["delta_if_new"]["n"] != len(rd["dpos"]): errs.append("delta_if_new n")
    if prod["time_to_new"]["n"] != len(rt["taus"]): errs.append("time n")
    if prod["delta_if_new"].get("n_unknown") is not None and prod["delta_if_new"]["n_unknown"] != rd["dpos_unknown"]: errs.append("delta_if_new n_unknown")
    if prod["time_to_new"].get("n_unknown") is not None and (prod["time_to_new"]["n_unknown"], prod["time_to_new"]["n_no_event"]) != (rt["tau_unknown"], rt["no_event"]): errs.append("time n_unknown / n_no_event")
    return errs


_SETS = {"B0": ("CS:NOW-ELIGIBLE-1", lambda ev: (lambda r: True)), "M1": ("CS:NOW-MATCH-M1-1", lambda ev: (lambda r: r["match"].get("M1" + ev, False))),
         "M2": ("CS:NOW-MATCH-M2-1", lambda ev: (lambda r: r["match"].get("M2", False))), "M3": ("CS:NOW-MATCH-M3-1", lambda ev: (lambda r: r["match"].get("M3", False)))}


def attach_now(out, fam, bars, tick, params):
    """Verifies a NOW payload at its creation boundary against the reference, withholds an event block that fails,
    attaches the envelope with one bundle per published number (all C1)."""
    env = Envelope("/api/d24/now", "PROFILE:NOW-1.0", params)
    if out.get("status") not in ("OK", "FROZEN_AT_BREAK") or "cut" not in out or fam.get("status") != "ok":
        out["contract"] = env.finish(); return out
    cut = out["cut"]["cut"]
    if out["base"]["N_base"] != fam["N"]: env.violate("DENOMINATOR", ["K27", "H2"], "NOW reports another N_base than the base family", withheld=["R", "X"])
    today = fam["today"]
    if fam["view"] == "conf" and today.get("brk") is not None and today["slice"] >= today["brk"] and (out["status"], cut) != ("FROZEN_AT_BREAK", today["brk"] - 5):
        env.violate("CUT", ["E0", "§12.2"], "the original family's NOW is not frozen at the last cut before today's break", withheld=["R", "X"])
    ref = ref_now_sets(fam, bars, tick, cut)
    if ref["today"] is None: env.violate("PREFIX", ["E1", "K08"], "today's prefix at the cut is not complete but NOW published numbers", withheld=["R", "X"])
    env.d["cut"] = dict(spec="CUT:NOW-COMMON-CLOCK-1", target_session=f"{fam['key']['instrument']}-{today['date'].replace('-', '')}-{fam['key']['session']}",
                        cut_close_minute=int(cut), cut_clock_et=_clk(cut), mode="LIVE" if today.get("source") == "live" else "HISTORY_DAY_REPLAY_BY_CLOSE",
                        state_age_m5=int(out["cut"].get("today_elapsed_m5", 0)))
    if out["status"] == "FROZEN_AT_BREAK": env.d["cut"]["frozen_reason"] = "the original family freezes on the last cut before today's DR break (NOW-1.0 §18)"
    if ref["today"]:
        for ev, val in (("R", ref["today"][0]), ("X", ref["today"][1])):
            env.d.setdefault("prefix", []).append(dict(case="today", event=ev, prefix_status="OK", from_close_minute=int(fam["grid"][ref["a_t"] + 1]) if ref["a_t"] + 1 < len(fam["grid"]) else int(cut),
                                                       to_close_minute=int(cut), seen_ticks=int(val), seen_u=round(val / ref["w_t"], 6)))
    sid, N = fam["snapshot_id"], fam["N"]
    inputs = _inputs(fam, [dict(input_kind="TODAY_PREFIX", ref="today", version=str(cut)), dict(input_kind="VALIDATION", ref="VAL:NOW-1.0-WALKFORWARD", version=str((out.get("R") or {}).get("validation", {}).get("rules_id")))])
    env.d["case_sets"] = [dict(spec=case_set_spec_of(fam), family_id=fam["family_id"], snapshot_id=sid, n_members=N, data_revision=str(fam["source"].get("built")))]
    for ev in ("R", "X"):
        E = out.get(ev)
        if not E or ev in env.withheld: continue
        b0 = ref_forecast(ref["rows"], ev, _SETS["B0"][1](ev))
        if E["mode"] == "INSUFFICIENT_SUPPORT":
            if b0["total"] >= 20 or E.get("continuation") is not None: env.violate("SUPPORT_GATE", ["§12.2", "K27"], f"{ev}: INSUFFICIENT_SUPPORT with B0 support {b0['total']}", withheld=[ev])
            continue
        if b0["total"] < 20: env.violate("SUPPORT_GATE", ["§12.2"], f"{ev}: a NOW number published on B0 support {b0['total']} < 20", withheld=[ev]); continue
        val = E.get("validation") or {}
        if E["mode"] == "PATH_CONDITIONED" and (val.get("status") != "VALIDATED" or E.get("matcher") not in ("M1", "M2", "M3")):
            env.violate("CLAIM_NOT_ADMISSIBLE", ["K28", "§12.2"], f"{ev}: a path-conditioned NOW without a VALIDATED matcher", withheld=[ev]); continue
        blocks = [("BASELINE", "B0", E["baseline"])]
        main_set = E.get("matcher") if E["mode"] == "PATH_CONDITIONED" else "B0"
        blocks.append(("MAIN", main_set, E["continuation"]))
        for k, R_ in (E.get("research") or {}).items(): blocks.append(("RESEARCH", k, R_))
        bad, refs_by_set = [], {}
        ref_of = lambda k: refs_by_set.setdefault(k, ref_forecast(ref["rows"], ev, _SETS[k][1](ev)))
        for role, setk, prod in blocks:
            # the remaining movement and the time of a path-conditioned NOW come from B0 unless they passed their own
            # gates (NOW-1.0 §14.2-14.3): each component is checked against the set it actually came from
            d_set = "B0" if prod.get("delta_source") == "B0" else setk
            t_set = "B0" if prod.get("time_source") == "B0" else setk
            errs = verify_forecast(prod, ref_of(setk), ref_of(d_set) if d_set != setk else None, ref_of(t_set) if t_set != setk else None)
            if errs: bad.append(f"{role} {setk}: {', '.join(errs)}")
        env.check(f"verify NOW {ev}: supports and numbers re-derived at the cut", not bad, len(blocks))
        if bad:
            env.violate("NOW_RECOMPUTATION", ["P0.3", "V2", "V2.2", "K31"], f"{ev}: " + "; ".join(bad), withheld=[ev]); continue
        for role, setk, prod in blocks:
            d_set = "B0" if prod.get("delta_source") == "B0" else setk
            t_set = "B0" if prod.get("time_source") == "B0" else setk
            _now_bundles(env, ev, role, setk, prod, ref_of(setk), ref_of(d_set), ref_of(t_set), d_set, t_set, sid, N, inputs, cut, b0["total"])
    out["contract"] = env.finish()
    for ev in ("R", "X"):
        if ev in env.withheld and out.get(ev):
            out[ev] = dict(mode="WITHHELD", matcher=None, continuation=None, note="нарушение контракта SC-1.1: число не опубликовано", state=out[ev].get("state"))
    return out


def _now_bundles(env, ev, role, setk, prod, r, rd, rt, d_set, t_set, sid, N, inputs, cut, n_eligible):
    """The bundles of one NOW set: N-NEW / N-NO-NEW on the set itself, N-DELTA and N-IF-NEW on the set the
    remaining movement came from, N-TIME on the set the time came from (each with its own support, V2.2)."""
    cs_id = _SETS[setk][0]
    D = r["total"]
    known = D - r["unknown"]
    cut_s = _clk(cut)
    params = dict(set=setk, role=role, cut=cut_s, event=ev)
    sup_new = dict(case_set=cs_id, n_base=N, n_eligible=n_eligible, n_match=D,
                   components=[dict(component="EXISTENCE", of=D, yes=r["yes"], no=r["no"], unknown=r["unknown"])])
    extra = dict(parent_case_set=sid, cut=cut)
    p = Fraction(r["yes"], known) if known else None
    bnd = est_binary_bounds(r["yes"], r["no"], r["unknown"])
    if known:
        ests = [dict(estimator="ESTR:NOW-POINT-BOUNDS-1", value_kind="POINT", value=float(prod["p_new_extreme"]), numerator=r["yes"], denominator=known, unit="share among known outcomes")]
    else:
        ests = [dict(estimator="ESTR:NOW-POINT-BOUNDS-1", value_kind="NO_ESTIMATE", unit="share", no_estimate_reason="no known outcome")]
    if bnd: ests.append(dict(estimator="ESTR:NOW-POINT-BOUNDS-1", value_kind="BOUNDS", lower=float(bnd[0]), upper=float(bnd[1]), denominator=D, unit="bounds over D from holes"))
    env.bundle(f"EST:N-NEW-{ev}", cs_id, sid, "lab/now24.py::forecast", inputs, ests, [sup_new],
               dict(cut=cut_s, pct=_fmt_pct(p), yes=r["yes"], D=D, unknown=r["unknown"]), parameters=params, claim_extra=extra, validations=["VAL:NOW-1.0-WALKFORWARD"])
    if known:
        env.bundle(f"EST:N-NO-NEW-{ev}", cs_id, sid, "lab/now24.py::forecast", inputs,
                   [dict(estimator="ESTR:NOW-POINT-BOUNDS-1", value_kind="POINT", value=float(prod["p_no_new_extreme"]), numerator=r["no"], denominator=known, unit="share among known outcomes")],
                   [sup_new], dict(cut=cut_s, pct=_fmt_pct(Fraction(r["no"], known))), parameters=params, claim_extra=extra)
    # the remaining movement: its own set (B0 when the path did not pass the magnitude gate) and its own support
    Dd, nd = rd["total"], len(rd["deltas"])
    pd = dict(params, set=d_set)
    parent_d = dict(parent_case_set=f"{_SETS[d_set][0]}@{cut_s}", cut=cut)
    sup_d = dict(case_set="CS:NOW-DELTA-KNOWN-1", n_base=N, n_eligible=n_eligible, n_match=Dd,
                 components=[dict(component="MAGNITUDE", of=Dd, known=nd, unknown=Dd - nd, condition_ru="известна окончательная добавка")])
    q = lambda vals, qq: dict(quantile=qq, value=None if not vals else float(ref_quantile(vals, qq)))
    d_est = dict(estimator="ESTR:NOW-QUANTILES-1", value_kind="QUANTILES" if nd else "NO_ESTIMATE", unit="IDR widths", denominator=nd)
    if nd: d_est["quantiles"] = [q(rd["deltas"], 0.25), q(rd["deltas"], 0.5), q(rd["deltas"], 0.75)]
    else: d_est["no_estimate_reason"] = "no known delta"
    env.bundle(f"EST:N-DELTA-Q-{ev}", "CS:NOW-DELTA-KNOWN-1", sid, "lab/now24.py::forecast", inputs, [d_est], [sup_d],
               dict(cut=cut_s, n=nd, unknown=Dd - nd, q25=_fmt(prod["delta"]["q25"]), q50=_fmt(prod["delta"]["q50"]), q75=_fmt(prod["delta"]["q75"])),
               parameters=pd, claim_extra=parent_d)
    for (n_, dd), key, thr in zip(((1, 10), (1, 5), (2, 5)), ("p_ge_0_10", "p_ge_0_20", "p_ge_0_40"), ("0,1", "0,2", "0,4")):
        if prod["delta"].get(key) is None or not nd: continue
        cnt = sum(1 for v in rd["deltas"] if v >= Fraction(n_, dd))
        env.bundle(f"EST:N-DELTA-GE-{ev}", "CS:NOW-DELTA-KNOWN-1", sid, "lab/now24.py::forecast", inputs,
                   [dict(estimator="ESTR:NOW-THRESHOLD-1", value_kind="POINT", value=float(prod["delta"][key]), numerator=cnt, denominator=nd, unit="share of known deltas")],
                   [sup_d], dict(threshold=thr, pct=_fmt_pct(Fraction(cnt, nd))), parameters=dict(pd, threshold=f"{n_}/{dd}"), claim_extra=parent_d)
    npos = len(rd["dpos"])
    sup_if = dict(case_set="CS:NOW-NEW-YES-DELTA-1", n_base=N, n_eligible=n_eligible, n_match=Dd,
                  components=[dict(component="MAGNITUDE", of=rd["yes"], known=npos, unknown=rd["dpos_unknown"], condition_ru="после среза был новый экстремум")])
    if_est = dict(estimator="ESTR:NOW-QUANTILES-1", value_kind="QUANTILES" if npos else "NO_ESTIMATE", unit="IDR widths", denominator=npos)
    if npos: if_est["quantiles"] = [q(rd["dpos"], 0.25), q(rd["dpos"], 0.5), q(rd["dpos"], 0.75)]
    else: if_est["no_estimate_reason"] = "no known positive delta"
    di = prod["delta_if_new"]
    env.bundle(f"EST:N-IF-NEW-{ev}", "CS:NOW-NEW-YES-DELTA-1", sid, "lab/now24.py::forecast", inputs, [if_est], [sup_if],
               dict(cut=cut_s, n=npos, unknown=rd["dpos_unknown"], q25=_fmt(di["q25"]), q50=_fmt(di["q50"]), q75=_fmt(di["q75"]), p25="—", p50="—", p75="—"),
               parameters=pd, claim_extra=parent_d)
    # the time to the first new extreme: its own set and support; «no new», «time unknown», «existence unknown» apart
    Dt, nt = rt["total"], len(rt["taus"])
    pt = dict(params, set=t_set)
    sup_t = dict(case_set="CS:NOW-NEW-YES-TAU-1", n_base=N, n_eligible=n_eligible, n_match=Dt,
                 components=[dict(component="FIRST_TIME", of=Dt, known=nt, unknown=rt["tau_unknown"] + rt["unknown"], no_event=rt["no_event"], condition_ru="после среза был новый экстремум")])
    t_est = dict(estimator="ESTR:NOW-QUANTILES-1", value_kind="QUANTILES" if nt else "NO_ESTIMATE", unit="M5 after the cut", denominator=nt)
    if nt: t_est["quantiles"] = [q(rt["taus"], 0.25), q(rt["taus"], 0.5), q(rt["taus"], 0.75)]
    else: t_est["no_estimate_reason"] = "no known first M5 of a new extreme"
    tm = prod["time_to_new"]
    env.bundle(f"EST:N-TIME-{ev}", "CS:NOW-NEW-YES-TAU-1", sid, "lab/now24.py::forecast", inputs, [t_est], [sup_t],
               dict(cut=cut_s, n=nt, unknown=rt["tau_unknown"], no_event=rt["no_event"], exist_unknown=rt["unknown"], q25_min=_fmt(tm["q25_min"], 0), q50_min=_fmt(tm["q50_min"], 0), q75_min=_fmt(tm["q75_min"], 0)),
               parameters=pt, claim_extra=dict(parent_case_set=f"{_SETS[t_set][0]}@{cut_s}", cut=cut))


# =====================================================================================================================
# the day (/api/d24/day): observation records, no statistic
# =====================================================================================================================
def attach_day(out, params):
    env = Envelope("/api/d24/day", "PROFILE:BASE-24", params)
    if out.get("status") == "ok":
        bad = [i for i, b in enumerate(out["bars"]) if not (b[3] <= min(b[1], b[4]) and max(b[1], b[4]) <= b[2])]
        env.check("O1 OHLC invariant on every bar", not bad, len(out["bars"]))
        if bad: env.violate("OHLC", ["O1"], f"{len(bad)} bars break low <= open, close <= high", severity="BLOCKING")
        live = out.get("source") == "live"
        last = max((b[0] for b in out["bars"]), default=None)
        env.d["observation"] = dict(source="OBS:TV-LIVE" if live else "OBS:G3-TAPE", content_version=str(out.get("fetched_at") or out.get("date")),
                                    mode="LIVE" if live else "HISTORY_DAY_REPLAY_BY_CLOSE",
                                    forming_m5_present=bool(live and last is not None and last + 5 > out.get("now", 0)),
                                    closed_through_minute=int(max((b[0] + 5 for b in out["bars"] if b[0] + 5 <= out.get("now", 0)), default=0)))
    out["contract"] = env.finish()
    return out


# =====================================================================================================================
# the response gate: every number of an SC-1.1 route has a declared meaning; staleness; the marking header
# =====================================================================================================================
_PAT = {}


def _compile(path):
    toks = []
    for seg in path.split("."):
        m = re.fullmatch(r"([^\[\]]*)((?:\[[^\]]*\])*)", seg)
        if m is None: raise ValueError(f"field encoding path not in the path syntax: {path} (segment {seg})")
        head, idx = m.group(1), m.group(2)
        if head == "{*}": toks.append(("any",))
        elif head.startswith("{"): toks.append(("set", frozenset(head[1:-1].split(","))))
        elif head: toks.append(("key", head))
        for i in re.findall(r"\[([^\]]*)\]", idx): toks.append(("idx", None if i == "*" else int(i)))
    return toks


def _match(toks, shape):
    if len(toks) != len(shape): return False
    for t, s in zip(toks, shape):
        if t[0] == "idx":
            if not isinstance(s, int) or (t[1] is not None and t[1] != s): return False
        elif isinstance(s, int): return False
        elif t[0] == "key" and t[1] != s: return False
        elif t[0] == "set" and s not in t[1]: return False
    return True


def _encodings(route):
    if route not in _PAT:
        _PAT[route] = [(e["id"], _compile(e["path"]), e) for e in (registry() or {}).get("encodings", []) if e["surface"] == "API:" + route]
    return _PAT[route]


def undeclared_numbers(route, body, limit=5):
    """The numeric leaves of a response that no field encoding of its route declares (the contract section excluded)."""
    pats, cache, bad = _encodings(route), {}, []
    exact = {d for _, t, _ in pats for d, tok in enumerate(t) if tok[0] == "idx" and tok[1] is not None}   # depths with [n]

    def walk(x, path):
        if isinstance(x, bool) or x is None or isinstance(x, str): return
        if isinstance(x, (int, float)):
            key = tuple(p if not isinstance(p, int) or d in exact else "#" for d, p in enumerate(path))
            hit = cache.get(key)
            if hit is None:
                hit = any(_match(t, tuple(path)) for _, t, _ in pats)
                cache[key] = hit
            if not hit and len(bad) < limit: bad.append(".".join(str(p) for p in path))
            return
        if isinstance(x, dict):
            for k, v in x.items():
                if not path and k == "contract": continue
                walk(v, path + [k])
        elif isinstance(x, list):
            for i, v in enumerate(x): walk(v, path + [i])
    walk(body, [])
    return bad


def surface_of(route):
    for s in (registry() or {}).get("surfaces", []):
        if s["route"] == route: return s
    return None


def header_for(route):
    s = surface_of(route)
    st = "CONTRACT_STALE" if stale() else "CONFORMANT"
    if s is None: return f"{EDITION}; profile=UNDECLARED; status=VIOLATION"
    out = s["surface_profile"]
    if out.startswith("LEGACY") or out == "SERVICE": return f"{EDITION}; profile={out}; status=OUTSIDE_SC11"
    return f"{EDITION}; profile={out}; status={st}; registry={registry_hash()}"


def stale_response(route, params):
    """CONTRACT_STALE: the executable contract does not represent its source, so no statistic of an SC-1.1 route is
    published; observations of the day are still served (they carry no claim)."""
    env = Envelope(route, "PROFILE:NOW-1.0" if route.endswith("/now") else "PROFILE:BASE-24", params)
    env.d["status"] = "CONTRACT_STALE"
    env.d["violations"].append(dict(code="CONTRACT_STALE", sc_ref=["§14.4"], message="; ".join(stale() or ["compiled contract unavailable"])[:400], severity="BLOCKING"))
    msg = "контракт SC-1.1 не пересобран после правки: числа не публикуются (python contract/tools/build.py)"
    body = dict(status="contract_stale", message=msg) if not route.endswith("/now") else dict(now_version="DR-LAB-NOW-1.0", status="CONTRACT_STALE", note=msg)
    body["contract"] = env.finish()
    return body


def finalize(route, body):
    """The last gate before a response leaves: undeclared numbers make the response a violation (fail closed for
    statistical routes); the envelope must be structurally valid."""
    s = surface_of(route)
    if s is None or s["surface_profile"] not in ("SC11_BASE_24", "SC11_NOW_1_0", "SC11_OBSERVATION"): return body
    bad = undeclared_numbers(route, body)
    if bad:
        if STRICT["on"]: raise ContractViolation(f"undeclared numbers in {route}: {bad}")
        env = body.get("contract") or {}
        env.setdefault("violations", []).append(dict(code="UNDECLARED_NUMBER", sc_ref=["§12.3", "§14.4"], message=f"numbers without a declared meaning: {bad}", severity="BLOCKING"))
        env["status"] = "VIOLATION"
        env.pop("bundles", None)
        if s["surface_profile"] != "SC11_OBSERVATION":
            body = dict(status="contract_violation" if route.endswith("family") else "CONTRACT_VIOLATION",
                        message="нарушение контракта SC-1.1: число без объявленного смысла", note="нарушение контракта SC-1.1: число без объявленного смысла", contract=env)
        else:
            body["contract"] = env
    return body


# =====================================================================================================================
# verification of page passports (/api/d24/verify): the page's own statistics recomputed by the reference
# =====================================================================================================================
def verify_passports(fam, bars, tick, passports):
    """Each page passport {estimand, params, yes_count, unknown_count, no_event_count, N} recomputed from the family
    members by the reference definitions. Returns the mismatches."""
    out, grid, formed, end, N = [], fam["grid"], fam["schedule"]["formed"], fam["schedule"]["end"], fam["N"]
    M = fam["members"]

    def points(ev):
        return [(ref_cell(m[ev]["v"], m["w"]), (m[ev]["t"] - formed) // 15, m[ev]["t"], m) for m in M if m[ev]["s"] == "known"]
    for p in passports:
        e, a = p.get("estimand"), p.get("params") or {}
        try:
            if p.get("N") != N: out.append(dict(id=p.get("id"), estimand=e, error=f"N {p.get('N')} != {N}")); continue
            if e is None or get(e) is None: out.append(dict(id=p.get("id"), estimand=e, error="unregistered estimand")); continue
            want = None
            ev = e[-1] if e[-2:] in ("-R", "-X") else a.get("ev")
            if e.startswith("EST:B-RX-BAND"): want = (sum(1 for k, _, _, _ in points(ev) if a["k0"] <= k < a["k1"]),)
            elif e.startswith("EST:B-RX-DIFF"):
                inr = lambda k, b: (a["k0"] is None or a["k0"] <= k < a["k1"]) and (a["b0"] is None or a["b0"] <= b < a["b1"])
                want = (sum(1 for k, b, _, _ in points("X") if inr(k, b)) - sum(1 for k, b, _, _ in points("R") if inr(k, b)),)
            elif e.startswith("EST:B-RX-WINDOW"): want = (sum(1 for _, b, _, _ in points(ev) if a["b0"] <= b < a["b1"]),)
            elif e.startswith("EST:B-RX-REGION"): want = (sum(1 for k, b, _, _ in points(ev) if a["k0"] <= k < a["k1"] and a["b0"] <= b < a["b1"]),)
            elif e.startswith("EST:B-RX-KNOWN"): want = (sum(1 for m in M if m[ev]["s"] == "known"),)
            elif e.startswith("EST:B-RX-UNDETERMINED"):
                part = a.get("part", "BOTH")
                want = (sum(1 for m in M if (m[ev]["s"] == "unknown" and part in ("UNKNOWN", "BOTH")) or (m[ev]["s"] == "none" and part in ("NO_PERIOD", "BOTH"))),)
            elif e.startswith("EST:B-RX-OUTFRAME"):
                want = (sum(1 for k, _, _, _ in points(ev) if a["k0"] <= k < a["k1"]),)
            elif e.startswith("EST:B-ZONE-RESIDUAL"):
                zm = (fam.get("zones") or {}).get(ev) or {"zones": []}
                inz = {s for z in zm["zones"] for s in z["member_session_ids"]}
                want = (sum(1 for m in M if m[ev]["s"] == "known" and m["id"] not in inz),)
            elif e.startswith("EST:B-ZONE"):
                zm = (fam.get("zones") or {}).get(ev) or {"zones": []}
                z = next((z for z in zm["zones"] if z["zone_id"] == a.get("zone_id")), None)
                cells = {tuple(c) for c in z["cell_mask"]} if z else set()
                want = (sum(1 for k, b, _, _ in points(ev) if (k, b) in cells),)
            elif e == "EST:B-DR":
                want = (sum(1 for m in M if m.get("outcome") == a["category"]),)
            elif e == "EST:B-ORDER":
                want = (sum(1 for m in M if m["order"] == a["category"]),)
            elif e in ("EST:B-CLOSE", "EST:B-CLOSE-MISSING", "EST:B-CLOSE-PREACT", "EST:B-RANGE"):
                j = a["j"]
                if e == "EST:B-CLOSE":
                    cells = [ref_close_cell(m["path"], j, m["w"]) for m in M]
                    want = (sum(1 for k in cells if k is not None and a["k0"] <= k < a["k1"]), sum(1 for k in cells if k is None))
                elif e == "EST:B-CLOSE-MISSING": want = (sum(1 for m in M if m["path"][j] is None),)
                elif e == "EST:B-CLOSE-PREACT": want = (sum(1 for m in M if m["path"][j] is not None and grid[j] < m["act"]),)
                else: want = (sum(1 for m in M if ref_range_touch(m["path"], j, a["k"], m["w"]) is True),)
            elif e in ("EST:B-LEVEL-FULL", "EST:B-LEVEL-REST", "EST:B-CROSS-FULL"):
                la, lb, up = a["a"], a["b"], a["up"]
                res = []
                for m in M:
                    start = m["act"] if e != "EST:B-LEVEL-REST" else a["cut"]      # (t, H] on the common clock (OUT:REACH-REST-1)
                    res.append(ref_cross(m["path"], grid, start, end, la, lb, m["w"]) if e == "EST:B-CROSS-FULL" else ref_reach(m["path"], grid, start, end, la, lb, m["w"], up))
                want = (res.count("yes"), res.count("unknown"), res.count("no"))
            elif e in ("EST:B-VISIT-FULL", "EST:B-VISIT-REST"):
                res = [ref_visit(m["path"], grid, m["act"] if e == "EST:B-VISIT-FULL" else a["cut"], end, a["k0"], a["k1"], m["w"]) for m in M]
                want = (res.count("yes"), res.count("unknown"), res.count("no"))
            elif e.startswith("EST:B-CLOCK-PEAK"):
                ahead = a.get("past") != "PAST"
                reach = _reach_k(fam, bars, tick, a["cut"], ev) if ahead else None
                want = (sum(1 for k, b, t, m in points(ev) if b == a["b"] and _in_region(a, ev, k, b, fam) and (not ahead or (ref_clock_split(t, a["cut"]) == "LATER" and reach(k)))),)
            elif e.startswith("EST:B-CLOCK"):
                want = (sum(1 for k, b, t, m in points(ev) if _in_region(a, ev, k, b, fam) and ref_clock_split(t, a["cut"]) == a["part"]),)
            if want is None: out.append(dict(id=p.get("id"), estimand=e, error="no reference for this estimand")); continue
            got = (p.get("yes_count"),) if len(want) == 1 else (p.get("yes_count"), p.get("unknown_count")) if len(want) == 2 else (p.get("yes_count"), p.get("unknown_count"), p.get("no_event_count"))
            if tuple(got) != tuple(want): out.append(dict(id=p.get("id"), estimand=e, error=f"page {got} != reference {want}", params=a))
        except (KeyError, TypeError, IndexError) as exc:
            out.append(dict(id=p.get("id"), estimand=e, error=f"passport parameters incomplete: {exc}"))
    return out


def _reach_k(fam, bars, tick, cut, ev):
    """E3 for one price cell at the cut (EST:B-CLOCK-PEAK «ещё достижимых сегодня»): today's provisional extreme from
    today's closed M5 after the activation up to the cut; today's final R can only lie as deep or deeper (cell k <= the
    extreme's cell), the final X only as far or further (k >= it); after the block's last M5 only the extreme's own cell;
    an incomplete prefix leaves every cell open. The same rule as the page's reachOf (design 24) and the zone status."""
    today, sch = fam["today"], fam["schedule"]
    d = today["side"] if fam["view"] == "conf" else -today["side"]
    act = today["c0"] if fam["view"] == "conf" else today["brk"]
    tk = lambda p: int(round(p / tick))
    e_t, w_t = tk(today["idrH"] if d == 1 else today["idrL"]), tk(today["idrH"] - today["idrL"])
    have = {int(b[0]) + 5: b for b in bars}
    rows = []
    for T in range(act + 5, cut + 1, 5):
        b = have.get(T)
        if b is None: return lambda k: True
        lo, hi = (b[3], b[2]) if d == 1 else (b[2], b[3])
        rows.append((d * (tk(lo) - e_t), d * (tk(hi) - e_t)))
    open_ = cut <= sch["end"] - 5
    if not rows: return (lambda k: True) if open_ else (lambda k: False)
    kc = ref_cell(min(r[0] for r in rows), w_t) if ev == "R" else ref_cell(max(r[1] for r in rows), w_t)
    if not open_: return lambda k: k == kc
    return (lambda k: k <= kc) if ev == "R" else (lambda k: k >= kc)


def _in_region(a, ev, k, b, fam):
    if a.get("zone_id"):
        zm = (fam.get("zones") or {}).get(ev) or {"zones": []}
        z = next((z for z in zm["zones"] if z["zone_id"] == a["zone_id"]), None)
        return bool(z) and [k, b] in z["cell_mask"]
    return a["k0"] <= k < a["k1"]
