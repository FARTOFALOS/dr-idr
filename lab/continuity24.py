"""Executable fixed-target candidate; no HTTP/UI publication and no issue-store writes.

F stays immutable. G -> clock-eligible -> POS_GEO is shared across regions. A
residual question may additionally require WINDOW_NO_VISIT; its risk set is named,
never passed off as the common POS_GEO set. All frequencies are research C1 only.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction as Q
import hashlib
import math
import numpy as np

from revisions24 import digest

VERSION = "FIXED-WINDOW-CONTINUITY-1"
METHOD = "POS_GEO:quarter:common-clock:1"


def ratio(value):
    return Q(str(value)) if not isinstance(value, Q) else value


def pair(value):
    x = ratio(value)
    return [x.numerator, x.denominator]


@dataclass(frozen=True)
class Frame:
    instrument: str
    date: str
    block: str
    direction: int
    edge: str
    width: str
    activation: int
    end: int

    def __post_init__(self):
        if self.block not in ("ODR", "RDR") or self.direction not in (-1, 1):
            raise ValueError("candidate supports original ODR/RDR only")
        if self.date > "2025-12-31" or ratio(self.width) <= 0:
            raise ValueError("invalid frame / closed 2026 boundary")


@dataclass(frozen=True)
class Target:
    frame: Frame
    low: tuple[int, int]
    high: tuple[int, int]
    first_close: int
    last_close: int
    created_at: int
    parent: str | None = None
    creation_kind: str = "INITIAL_VISIT"

    @property
    def id(self):
        return digest({k: v for k, v in asdict(self).items() if k != "created_at"})

    @property
    def physical(self):
        # Edges stay associated with directed [low, high), including for a short.
        return [pair(ratio(self.frame.edge) + self.frame.direction * ratio(self.frame.width) * Q(*v))
                for v in (self.low, self.high)]

    def record(self):
        return dict(id=self.id, **asdict(self), physical_edges=self.physical,
                    window_open=self.first_close - 5, window_close=self.last_close,
                    boundary="directed [low,high); physical first included, second excluded")


def pin(frame, low, high, first_close, last_close, cut, parent=None, creation_kind="INITIAL_VISIT"):
    lo, hi = ratio(low), ratio(high)
    if (lo >= hi or cut % 5 or first_close % 5 or last_close % 5 or
            not frame.activation <= cut < first_close <= last_close <= frame.end):
        raise ValueError("pin requires an ordered band and a wholly future M5 window")
    return Target(frame, tuple(pair(lo)), tuple(pair(hi)), first_close, last_close, cut, parent, creation_kind)


def _window(grid, first, last):
    return np.flatnonzero((np.asarray(grid) >= first) & (np.asarray(grid) <= last))


def visit(case, grid, target, first=None, last=None):
    """Union of actual M5 ranges, not an envelope across gaps. YES dominates gaps."""
    first = target.first_close if first is None else first
    last = target.last_close if last is None else last
    js = _window(grid, first, last)
    if not len(js):
        return "NO"
    lo, hi = Q(*target.low) * int(case["w"]), Q(*target.high) * int(case["w"])
    unknown = False
    for j in js:
        p = case["P"][j]
        if not np.isfinite(p).all():
            unknown = True
        elif int(p[0]) < hi and int(p[1]) >= lo:
            return "YES"
    return "UNKNOWN" if unknown else "NO"


def prefix(case, grid, cut):
    js = np.flatnonzero((np.arange(len(grid)) > case["a"]) & (np.asarray(grid) <= cut))
    if not len(js):
        return "NO_PREFIX", None
    part = case["P"][js]
    if not np.isfinite(part).all():
        return "PREFIX_GAP", None
    if case.get("oppv") is not None and np.any(part[:, 2] < case["oppv"]):
        return "DR_BROKEN", None
    return "OK", int(part[-1, 2])


def select(cases, today, grid, cut):
    """No historical labels, target geometry or target future are selector inputs."""
    status, close = prefix(today, grid, cut)
    prior = [c for c in cases if c["date"] < today["date"]]
    if any(c["date"] > "2025-12-31" for c in cases):
        raise ValueError("2026 is closed")
    eligible, matched, reasons = [], [], {}
    for c in prior:
        why, v = prefix(c, grid, cut)
        if why != "OK":
            reasons[c["id"]] = why
            continue
        eligible.append(c["id"])
        if status == "OK" and 4 * abs(v * today["w"] - close * c["w"]) <= c["w"] * today["w"]:
            matched.append(c["id"])
        else:
            reasons[c["id"]] = "POSITION_FAR" if status == "OK" else "TODAY_" + status
    common = dict(method=METHOD, compared="POSITION_AT_COMMON_CLOCK", full_path_compared=False,
                  G=[c["id"] for c in prior], eligible=eligible, M=matched, exclusions=reasons,
                  target_prefix_status=status)
    common["snapshot_id"] = digest(dict(method=METHOD, cut=cut, date=today["date"], G=common["G"], M=matched))
    return common


def observed(case, grid, target, cut):
    end = min(cut, target.last_close)
    result = visit(case, grid, target, last=end)
    if result == "YES":
        hits = [int(grid[j]) for j in _window(grid, target.first_close, end)
                if visit(case, grid, target, int(grid[j]), int(grid[j])) == "YES"]
        witness = hits[0]
        earlier = visit(case, grid, target, last=witness - 5)
        return dict(status="FACT_YES", value="YES", available_at=witness,
                    witness_bar=[witness - 5, witness], first_time_known=earlier == "NO")
    if cut >= target.last_close:
        return dict(status="FACT_NO" if result == "NO" else "UNKNOWN_FINAL", value=result,
                    available_at=target.last_close if result == "NO" else None)
    return dict(status="OBSERVATION_GAP" if result == "UNKNOWN" else "OPEN", value=result,
                available_at=None)


def sequence_value(case, grid, condition, cut):
    """Existence of A before B; different M5 witnesses prove order, one M5 cannot."""
    first = max(condition["first_close"], int(grid[case["a"]]) + 5) if case["a"] >= 0 else condition["first_close"]
    seen_a, ambiguous = False, False
    for j in _window(grid, first, min(cut, condition["last_close"])):
        p = case["P"][j]
        if not np.isfinite(p).all():
            ambiguous = True
            continue
        def hit(band):
            return int(p[0]) < Q(*band[1]) * case["w"] and int(p[1]) >= Q(*band[0]) * case["w"]
        a, b = hit(condition["A"]), hit(condition["B"])
        if seen_a and b:
            return "YES"
        ambiguous |= a and b
        seen_a |= a
    return "UNKNOWN" if ambiguous else "NO"


def support(labels):
    n = len(labels)
    y, no, u = (sum(v == name for v in labels.values()) for name in ("YES", "NO", "UNKNOWN"))
    known = y + no
    enough = n >= 20 and known >= 20
    return dict(n_total=n, n_known=known, yes=y, no=no, unknown=u,
                point_known=y / known if known else None,
                bounds=[y / n, (y + u) / n] if n else None,
                primary="ABSENT_SMALL_SUPPORT" if not enough else "BOUNDS" if u else "POINT",
                point_is_comparison_score=enough and u == 0)


def original_record(family):
    """Immutable historical geometry, not today's changing reachability/clock status."""
    keys = ("family_id", "snapshot_id", "N", "ids", "members", "counts", "zones", "grid", "scale", "schedule")
    return {k: family[k] for k in keys if k in family}


def history_revision(cases, grid, cutoff):
    h = hashlib.sha256(np.asarray(grid, dtype=np.int64).tobytes())
    for c in sorted((c for c in cases if c["date"] < cutoff), key=lambda c: c["id"]):
        h.update(digest([c["id"], c["date"], c["a"], c["w"], c.get("oppv")]).encode())
        h.update(np.asarray(c["P"], dtype=np.float64).tobytes())
    return h.hexdigest()


def release(cases, today, grid, target, cut, original, sequence=None):
    if cut % 5 or cut < target.created_at or cut < target.frame.activation or cut > target.frame.end:
        raise ValueError("closed M5 cut outside original block")
    if target.frame.date != today["date"] or (today["a"] >= 0 and grid[today["a"]] != target.frame.activation):
        raise ValueError("target belongs to another scene")
    if (today["instrument"] != target.frame.instrument or today["block"] != target.frame.block or
            today["side"] != target.frame.direction or
            ratio(target.frame.width) != today["w"] * ratio(today["tick"]) or
            ratio(target.frame.edge) != ratio(today["edge"])):
        raise ValueError("target frame changed; never drift the physical pin")
    if len({c["id"] for c in cases}) != len(cases) or any(
            (c["instrument"], c["block"]) != (today["instrument"], today["block"]) for c in cases):
        raise ValueError("mixed or duplicated historical corpus")
    base = original_record(original)
    state = observed(today, grid, target, cut)
    selection = select(cases, today, grid, cut)
    remaining = max(target.first_close, cut + 5)
    condition = []
    if target.first_close <= cut < target.last_close and state["status"] == "OPEN":
        condition.append(dict(kind="WINDOW_NO_VISIT", first_close=target.first_close, last_close=cut))
    if sequence is not None:
        if sequence.get("kind") != "A_THEN_B" or sequence["last_close"] > cut:
            raise ValueError("sequence must be a named known-prefix condition")
        if sequence_value(today, grid, sequence, cut) != "YES":
            raise ValueError("A -> B is not established on today's prefix")
        condition.append(sequence)
    question = dict(target_id=target.id, event="RANGE_WINDOW_VISIT",
                    first_close=remaining if state["status"] == "OPEN" else target.first_close,
                    last_close=target.last_close, conditions=condition, active=state["status"] == "OPEN")
    # Before the window, the question stays identical although knowledge/selection changes.
    question["id"] = digest(question)
    by_id = {c["id"]: c for c in cases}
    risk, excluded = [], {}
    for cid in selection["M"]:
        c = by_id[cid]
        why = None
        for cond in condition:
            if cond["kind"] == "WINDOW_NO_VISIT":
                if c["a"] >= 0 and grid[c["a"]] >= target.first_close:
                    why = "NOT_ACTIVE_AT_WINDOW_START"
                elif visit(c, grid, target, last=cut) != "NO":
                    why = "WINDOW_ALREADY_VISITED_OR_UNKNOWN"
            elif sequence_value(c, grid, cond, cut) != "YES":
                why = "SEQUENCE_NOT_ESTABLISHED"
            if why:
                break
        if why:
            excluded[cid] = why
        else:
            risk.append(cid)
    labels = {cid: visit(by_id[cid], grid, target, remaining) for cid in risk} if (
        state["status"] == "OPEN" and remaining <= target.last_close) else {}
    result = support(labels)
    publication = "RESEARCH_ONLY"
    if state["status"] != "OPEN":
        publication = state["status"]
    elif selection["target_prefix_status"] != "OK":
        publication = "WITHHELD_" + selection["target_prefix_status"]
    elif result["primary"] == "ABSENT_SMALL_SUPPORT":
        publication = "WITHHELD_SMALL_SUPPORT"
    # No point or bounds are issued after the fact, in a gap or on an unsupported phase.
    estimate = result if publication == "RESEARCH_ONLY" else None
    prefix_values = [[int(grid[j]), [None if not math.isfinite(v) else int(v) for v in p]]
                     for j, p in enumerate(today["P"]) if grid[j] <= cut]
    context = dict(instrument=target.frame.instrument, date=today["date"], block=target.frame.block,
                   cut=cut, target_id=target.id, question_id=question["id"], method=METHOD,
                   prefix_revision=digest(prefix_values), original_revision=digest(base),
                   history_revision=history_revision(cases, grid, today["date"]),
                   common_snapshot=selection["snapshot_id"], conditions=condition, version=VERSION)
    context["id"] = digest(context)
    return dict(context=context, target=target.record(), question=question, observed=state,
                selection=selection, risk_set=dict(ids=risk, exclusions=excluded, parent=selection["snapshot_id"],
                                                  snapshot_id=digest([selection["snapshot_id"], condition, risk])),
                labels=labels, support=result, estimate=estimate, status=publication,
                admission=dict(profile="FIXED-WINDOW-CANDIDATE", claim="C1_RESEARCH_ONLY",
                               ui_publication=False, human_acceptance="PENDING",
                               fixed_window_sequence_validation="MECHANICAL_ONLY"))


def revisit(target, cut, first_close, last_close, today, grid):
    """A return requires a known hit followed by a later wholly outside M5.

    Merely remaining in the band is not named a return. The new estimate must use
    its own explicit A -> outside prefix condition; this helper does not issue it.
    """
    fact = observed(today, grid, target, cut)
    if fact["status"] != "FACT_YES":
        raise ValueError("no established visit")
    exited = []
    for j in _window(grid, fact["available_at"] + 5, cut):
        if np.isfinite(today["P"][j]).all() and visit(today, grid, target, grid[j], grid[j]) == "NO":
            exited.append(int(grid[j]))
    if not exited:
        raise ValueError("return requires an established departure, not continued occupancy")
    child = pin(target.frame, Q(*target.low), Q(*target.high), first_close, last_close, cut,
                target.id, "REVISIT_AFTER_OBSERVED_EXIT")
    question = dict(target_id=child.id, event="RETURN_AFTER_OBSERVED_EXIT",
                    first_close=first_close, last_close=last_close,
                    conditions=[dict(kind="VISIT_THEN_FULL_BAR_OUTSIDE", parent_target=target.id,
                                     parent_window=[target.first_close, target.last_close], known_by=cut)])
    question["id"] = digest(question)
    return dict(target=child.record(), question=question, visit_fact=fact, departure_fact=dict(available_at=exited[0]),
                estimator_status="NOT_ISSUED_REQUIRES_OWN_SEQUENCE_RULE")
