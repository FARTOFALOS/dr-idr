"""DR Lab — the Q1 pilot engine (Q1-PILOT-0.2, mode C1).

The question (Q1 §1): «after this cut, until the block end, of the sessions that stood comparably and had not yet been
at the chosen place L, how many reached L?», next to the status of the same place today.

Meaning (Q1 §§2-4; KADR-1.1 ed. 2 §§3-5; nothing here is chosen anew):
- a case = one instrument, one trading date, one ODR or RDR block; history = cases of strictly earlier dates, 2006-2025;
- frame: each case's own IDR edge e on its side d and width w; u = d (p - e) / w; IDR from M5 bodies; a short mirrors;
- activation: the close of the case's own first confirmation beyond DR; the activating M5 is not in its extremes;
- cut t: a close of the common ET clock of the block; a case is eligible at t when at least one whole M5 has closed
  after its own activation, no M5 of the prefix is missing and its DR is intact — the B0 rule of NOW-1.0
  (lab/now24.py::series, reused, not re-implemented);
- place L in {0, -1/2, -7/10}; open today while today's post-activation low is above L (the close then is too);
- event: some M5 closing in (t, H] has low_u <= L (an open beyond L counts: reach, not a fill);
- members: the estimator's parent, eligible at t, not yet at L, and 4 |v_m w_t - v_t w_m| <= w_m w_t
  (lab/now24.py::_near with 1/4);
- a member's outcome: YES (seen), NO (the rest is complete and it is not seen), UNKNOWN (not seen, an M5 missing);
- counters N_parent -> N_eligible -> N_not_yet -> n_match; yes / no / unknown; n_known; no number below n_match 20.

Information boundary (Q1 §5): an attempt reads the target only through its prefix — its rows after the cut are cut off
before anything is computed — and the earlier sessions completely, because their later candles are their labels (an
input of the estimate, never of the selection). The input digest covers exactly that: the target's prefix and every
session of the block before the target date. A change of the target's future therefore leaves an issue byte-identical,
its identity included; a change of an analogue's future changes the input digest, so it is another issue.
"""
from __future__ import annotations

import bisect
import inspect
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

LAB = Path(__file__).resolve().parents[1]
REPO = LAB.parent
if str(LAB) not in sys.path:
    sys.path.insert(0, str(LAB))

import now24 as N            # noqa: E402  series (eligibility, prefix extremes), _near (the exact 1/4)
import now24_validate as V   # noqa: E402  universe: the population of the A/D measurements
import scene21               # noqa: E402
import scene24               # noqa: E402
from q1 import passport      # noqa: E402
from q1.store import ISSUE_KIND, canonical, issue_id, outcome_id, sha, target_id  # noqa: E402

QUESTION = "Q1-PILOT-0.2/REACH-L"
ENGINE = "q1-engine-1"
BLOCKS = ("ODR", "RDR")
INSTRUMENTS = ("NQ", "ES", "YM")
LEVELS = {"0": (0, 1), "-1/2": (-1, 2), "-7/10": (-7, 10)}
TOL = (1, 4)
SUPPORT = 20
AD_STEP = 3              # the original A/D cuts: every 15 minutes of the common clock, (c + 1) % 3 == 0
AD_MIN_FAMILY = 40       # A/D targets: a weekday family of at least 40
SAMPLE_EXCLUDED = 200    # excluded parent members re-derived by the second implementation per issue
ESTIMATORS = tuple(passport.ESTIMATORS)
REASONS = ("NOT_ACTIVATED", "PREFIX_HOLE", "DR_BROKEN", "ALREADY_AT_L", "FAR", "MATCH")
CORPUS = {"path": None}


def clk(t):
    t = int(t) % 1440
    return f"{t // 60:02d}:{t % 60:02d}"


# ---------- the corpus (read only) ----------
def _git(*args):
    try:
        r = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        return None


def code_version():
    head = _git("rev-parse", "HEAD")
    dirty = _git("status", "--porcelain", "--", "lab/q1")
    return dict(commit=head, lab_q1_dirty=bool(dirty))


def corpus_candidates():
    if os.environ.get("DR_IDR_RUNTIME"):
        yield Path(os.environ["DR_IDR_RUNTIME"])
    yield LAB / ".runtime"
    common = _git("rev-parse", "--git-common-dir")          # a worktree reads the main checkout's base by path
    if common:
        p = Path(common)
        yield (p if p.is_absolute() else REPO / p).resolve().parent / "lab" / ".runtime"


def bind_corpus(path=None):
    """Point the base readers at a built session base. Nothing is copied or written there."""
    for p in ([Path(path)] if path else corpus_candidates()):
        if all((p / f"boxes_{i.lower()}_meta.json").exists() for i in INSTRUMENTS):
            scene21.RUNTIME = p
            scene24.RUNTIME = p
            CORPUS["path"] = p
            return p
    raise FileNotFoundError("no built session base (boxes_*): set DR_IDR_RUNTIME to a lab/.runtime folder")


# ---------- the model version: the code that defines the computation ----------
def _src(obj):
    try:
        return inspect.getsource(obj).replace("\r\n", "\n")
    except (OSError, TypeError):
        return repr(obj)


def model_digest():
    used = (N.series, N._near, N.stack, V.universe, scene24.directed, scene24.window_of, scene24._rows,
            scene24._missing, scene24._sid, scene21._boxes)
    return sha(dict(engine=ENGINE, question=QUESTION, levels=LEVELS, tol=list(TOL), support=SUPPORT,
                    engine_source=Path(__file__).read_text(encoding="utf-8").replace("\r\n", "\n"),
                    used={f"{f.__module__}.{f.__name__}": _src(f) for f in used},
                    sess=scene21.SESS, shift=scene21.SHIFT))


MODEL = model_digest()


# ---------- raw access: the session base, or synthetic cases for the tests ----------
class BaseProvider:
    """One instrument x block of the session base (lab/.runtime/boxes_*), read only."""

    kind = "base"

    def __init__(self, inst, block):
        self.inst, self.block = inst, block
        self.B = scene24._base(inst)
        if self.B is None:
            raise FileNotFoundError("no session base: bind_corpus() first")
        self.tick = float(self.B["tick"])
        self.version = self.B["info"].get("version")
        self.shift = scene24.SHIFT[block]
        self.order = sorted((b["date"], i) for i, b in enumerate(self.B["boxes"]) if b["session"] == block)
        self._dates = [d for d, _ in self.order]
        self._dig = {}

    def key(self, case):
        return self.B["idx"][(case["date"], self.block)]

    def box(self, k):
        return self.B["boxes"][k]

    def bars(self, k):
        return np.ascontiguousarray(self.B["bars"][self.B["off"][k]:self.B["off"][k + 1]], dtype=np.int64)

    def _fields(self, k, drop=()):
        b = self.B["boxes"][k]
        return {f: b[f] for f in sorted(b) if f not in drop}

    def session_digest(self, k):
        d = self._dig.get(k)
        if d is None:
            d = self._dig[k] = sha(canonical(["session", self.inst, self._fields(k)]) + self.bars(k).tobytes())
        return d

    def prefix_digest(self, k, c, cut_minute):
        """The target as known at the cut: its box without the later DR break (its future) and its M5 closing no later
        than the cut."""
        bars = self.bars(k)
        keep = bars[bars[:, 0] - self.shift <= cut_minute]
        return sha(canonical(["prefix", self.inst, self._fields(k, drop=("fail",)), int(cut_minute)]) + keep.tobytes())

    def domain_digest(self, date):
        """Every session of the block, confirmed or not, of a strictly earlier trading date: what a parent may use."""
        n = bisect.bisect_left(self._dates, date)
        lines = "".join(f"{scene24._sid(self.inst, self.B['boxes'][k])}:{self.session_digest(k)}\n" for _, k in self.order[:n])
        return sha(lines.encode()), n

    def frame(self, k, side):
        b = self.B["boxes"][k]
        e = b["idr_high"] if side == 1 else b["idr_low"]
        return dict(e=int(e), w=int(b["idr_high"] - b["idr_low"]), tick=self.tick)

    def directed_rows(self, k, d, e):
        """{close minute: (low_u, high_u, close_u)} straight from the raw bars (the second implementation's input)."""
        out = {}
        for t, o, h, lo, c in self.bars(k).tolist():
            t -= self.shift
            out[t] = (lo - e, h - e, c - e) if d == 1 else (e - h, e - lo, e - c)
        return out

    def physical(self, k, upto=None):
        """[open minute, o, h, l, c] in prices for the page (the box hour included)."""
        rows = []
        for t, o, h, lo, c in self.bars(k).tolist():
            t -= self.shift
            if upto is not None and t > upto:
                break
            rows.append([t - 5, o * self.tick, h * self.tick, lo * self.tick, c * self.tick])
        return rows


class SyntheticProvider:
    """Cases given directly as directed paths on a grid (tests): each case dict is its own raw record."""

    kind = "synthetic"
    tick = 1.0
    version = "synthetic"

    def __init__(self, cases, grid):
        self.cases = {c["id"]: c for c in cases}
        self.grid = list(grid)

    def key(self, case):
        return case["id"]

    def _fields(self, k, drop=()):
        c = self.cases[k]
        return {f: c[f] for f in sorted(c) if f not in ("P",) + tuple(drop)}

    def session_digest(self, k):
        return sha(canonical(["session", self._fields(k)]) + np.ascontiguousarray(self.cases[k]["P"]).tobytes())

    def prefix_digest(self, k, c, cut_minute):
        return sha(canonical(["prefix", self._fields(k, drop=("fail",)), int(cut_minute)])
                   + np.ascontiguousarray(self.cases[k]["P"][:c + 1]).tobytes())

    def domain_digest(self, date):
        ks = sorted(k for k, c in self.cases.items() if c["date"] < date)
        return sha("".join(f"{k}:{self.session_digest(k)}\n" for k in ks).encode()), len(ks)

    def frame(self, k, side):
        return dict(e=0, w=int(self.cases[k]["w"]), tick=1.0)

    def directed_rows(self, k, d, e):
        P = self.cases[k]["P"]
        return {self.grid[j]: tuple(int(v) for v in P[j]) for j in range(len(P)) if not np.isnan(P[j][0])}

    def physical(self, k, upto=None):
        P = self.cases[k]["P"]
        return [[self.grid[j] - 5, float(P[j][2]), float(P[j][1]), float(P[j][0]), float(P[j][2])]
                for j in range(len(P)) if not np.isnan(P[j][0]) and (upto is None or self.grid[j] <= upto)]


# ---------- the population of one instrument x block ----------
class Table:
    """The A/D population (every confirmation session of the block that joins a family, lab/now24_validate.universe)
    with the per-cut arrays the question needs. Rows are sorted by date, as the universe is."""

    def __init__(self, inst, block, cases, grid, provider):
        self.inst, self.block, self.grid = inst, block, list(grid)
        self.formed, self.end = self.grid[0] - 5, self.grid[-1]
        self.provider = provider
        L = len(self.grid)
        self.cases = cases
        self.ids = [c["id"] for c in cases]
        self.pos = {sid: j for j, sid in enumerate(self.ids)}
        self.keys = [provider.key(c) for c in cases]
        self.dates = np.array([c["date"] for c in cases], dtype=object)
        for f in ("side", "win", "weekday", "a", "w", "oppv"):
            setattr(self, f, np.array([int(c[f]) for c in cases], dtype=np.int64))
        self.P = np.stack([c["P"] for c in cases]) if cases else np.zeros((0, L, 3))
        S = N.stack([N.series(c["P"], c["a"], c["oppv"]) for c in cases]) if cases else None
        n = len(cases)
        self.VALID = S["valid"] if n else np.zeros((0, L), bool)
        self.R = S["r"] if n else np.zeros((0, L), np.int64)
        self.CL = S["cl"] if n else np.zeros((0, L), np.int64)
        idx = np.arange(L)
        nan = np.isnan(self.P[:, :, 0])
        self.POST = idx[None, :] > self.a[:, None]
        self.BAD = np.logical_or.accumulate(self.POST & nan, axis=1)
        cl0 = np.where(nan, 0, self.P[:, :, 2])
        self.ALIVE = ~np.logical_or.accumulate(self.POST & ~nan & (cl0 < self.oppv[:, None]), axis=1)
        if not np.array_equal(self.VALID, self.POST & ~self.BAD & self.ALIVE):
            raise AssertionError("eligibility reasons do not add up to lab/now24.py::series valid")
        lo = np.where(nan, np.inf, self.P[:, :, 0])
        self.FMIN = np.concatenate([np.minimum.accumulate(lo[:, ::-1], axis=1)[:, ::-1][:, 1:], np.full((n, 1), np.inf)], axis=1)
        self.FNAN = np.concatenate([np.logical_or.accumulate(nan[:, ::-1], axis=1)[:, ::-1][:, 1:], np.zeros((n, 1), bool)], axis=1)

    # -- parents (Q1 §2, D1: named variants, no default)
    def parent(self, i, est):
        m = self.dates < self.dates[i]                     # strictly earlier trading dates
        if est in ("NODEPOS_ALL", "NODEPOS_WD"):
            m &= (self.side == self.side[i]) & (self.win == self.win[i])
        if est == "NODEPOS_WD":
            m &= self.weekday == self.weekday[i]
        elif est not in ("GEO", "NODEPOS_ALL"):
            raise ValueError(f"unknown estimator {est}")
        return np.flatnonzero(m)

    # -- today at the cut: the target's prefix only
    def target_state(self, i, c, level):
        la, lb = level
        L = len(self.grid)
        a_t, w_t = int(self.a[i]), int(self.w[i])
        st = dict(cut=int(c), cut_close=clk(self.grid[c]), activation_close=clk(self.grid[a_t]), w=w_t,
                  horizon_end=clk(self.end), elapsed_m5=int(c - a_t))
        if c >= L - 1:
            return dict(st, status="BLOCK_OVER")
        if c <= a_t:
            return dict(st, status="NO_PREFIX")
        P = self.P[i].copy()
        P[c + 1:] = np.nan                                 # the target's future never enters (Q1 §5, FR04)
        s = N.series(P, a_t, int(self.oppv[i]))
        nan = np.isnan(P[:, 0])
        post = np.arange(L) > a_t
        holes = np.flatnonzero((post & nan)[:c + 1])
        if len(holes):
            return dict(st, status="PREFIX_UNKNOWN", time=clk(self.grid[holes[0]]))
        if not s["valid"][c]:
            k = int(np.flatnonzero(post[:c + 1] & (P[:c + 1, 2] < self.oppv[i]))[0])
            return dict(st, status="DR_BROKEN", time=clk(self.grid[k]))
        r, cl, x = int(s["r"][c]), int(s["cl"][c]), int(s["x"][c])
        st.update(close_v=cl, r_v=r, x_v=x)
        if r * lb <= la * w_t:
            k = int(np.flatnonzero(post[:c + 1] & (P[:c + 1, 0] * lb <= la * w_t))[0])
            return dict(st, status="RESOLVED", time=clk(self.grid[k]))
        return dict(st, status="OPEN")

    # -- membership and labels of parent rows at cuts (vectorised; the page and the A/D reconciliation share it)
    def select(self, par, cs, level, cl_t, w_t):
        la, lb = level
        ix = np.ix_(par, cs)
        W = self.w[par][:, None]
        valid = self.VALID[ix]
        notyet = valid & (self.R[ix] * lb > la * W)
        near = N._near(self.CL[ix], W, np.asarray(cl_t, dtype=np.int64)[None, :], int(w_t), TOL)
        reach = self.FMIN[ix] * lb <= la * W
        return dict(post=self.POST[ix], bad=self.BAD[ix], alive=self.ALIVE[ix], valid=valid, notyet=notyet, near=near,
                    match=notyet & near, reach=reach, unk=~reach & self.FNAN[ix])

    @staticmethod
    def reasons(m):
        """One reason per parent row (first that applies), in the order of the eligibility chain."""
        out = np.full(m["match"].shape, "MATCH", dtype=object)
        out[m["notyet"] & ~m["near"]] = "FAR"
        out[m["valid"] & ~m["notyet"]] = "ALREADY_AT_L"
        out[m["post"] & ~m["bad"] & ~m["alive"]] = "DR_BROKEN"
        out[m["post"] & m["bad"]] = "PREFIX_HOLE"
        out[~m["post"]] = "NOT_ACTIVATED"
        return out

    def first_reach(self, j, c, level):
        """The first M5 after c reaching L for row j: (grid index, time known) or None."""
        la, lb = level
        lo = self.P[j, c + 1:, 0]
        nan = np.isnan(lo)
        hit = ~nan & (np.where(nan, 0, lo) * lb <= la * self.w[j])
        if not hit.any():
            return None
        k = int(np.argmax(hit))
        return c + 1 + k, not bool(nan[:k].any())

    # -- one attempt: the target's state, and if open the estimator's set, counts and estimate
    def attempt(self, i, c, level_name, est):
        level = LEVELS[level_name]
        st = self.target_state(i, c, level)
        out = dict(target=int(i), cut=int(c), level=level_name, estimator=est, state=st)
        if st["status"] != "OPEN":
            return out
        par = self.parent(i, est)
        m = {k: v[:, 0] for k, v in self.select(par, np.array([c]), level, [st["close_v"]], st["w"]).items()}
        reason = self.reasons(m)
        match, reach, unk = m["match"], m["reach"], m["unk"]
        n, yes, unknown = int(match.sum()), int((match & reach).sum()), int((match & unk).sum())
        no = n - yes - unknown
        counts = dict(N_parent=int(len(par)), N_eligible=int(m["valid"].sum()), N_not_yet=int(m["notyet"].sum()), n_match=n,
                      yes=yes, no=no, unknown=unknown, n_known=yes + no,
                      excluded={r: int((reason == r).sum()) for r in REASONS if r != "MATCH"})
        pub = "WITHHELD_FEW_SESSIONS" if n < SUPPORT else "NO_KNOWN_OUTCOME" if yes + no == 0 else "PUBLISHED"
        members = []
        for j, rs, yh, uk in zip(par[match], reason[match], reach[match], unk[match]):
            fr = self.first_reach(j, c, level) if yh else None
            members.append(dict(id=self.ids[j], date=str(self.dates[j]), weekday=int(self.weekday[j]), side=int(self.side[j]),
                                window=int(self.win[j]), activation_close=clk(self.grid[self.a[j]]), w=int(self.w[j]),
                                close_v=int(self.CL[j, c]), r_v=int(self.R[j, c]),
                                label="YES" if yh else "UNKNOWN" if uk else "NO",
                                first_reach=None if fr is None else dict(close=clk(self.grid[fr[0]]), time_known=fr[1])))
        out.update(par=par, mask=m, reason=reason, counts=counts, members=members,
                   estimate=dict(publication=pub, point=dict(num=yes, den=yes + no) if yes + no else None,
                                 bounds=[dict(num=yes, den=n), dict(num=yes + unknown, den=n)] if n else None))
        return out

    # -- identities and inputs
    def target_record(self, i, level_name):
        k = self.keys[i]
        side = int(self.side[i])
        la, lb = LEVELS[level_name]
        fr = self.provider.frame(k, side)
        return dict(question=QUESTION, instrument=self.inst, date=str(self.dates[i]), block=self.block, side=side,
                    frame=dict(e_ticks=fr["e"], w_ticks=int(self.w[i]), tick=str(fr["tick"]), activation_close=clk(self.grid[self.a[i]])),
                    level=dict(name=level_name, a=la, b=lb), horizon_end=clk(self.end))

    def inputs(self, i, c):
        k = self.keys[i]
        tp = self.provider.prefix_digest(k, c, self.grid[c])
        dd, dn = self.provider.domain_digest(str(self.dates[i]))
        return dict(model=MODEL, input_digest=sha(["q1-inputs-1", tp, dd]), target_prefix_digest=tp, domain_digest=dd,
                    domain_sessions=dn, corpus=self.provider.version)

    # -- the second implementation (raw rows, scalar): the same definitions, another code path
    def scalar_classify(self, j, c, level, cl_t, w_t):
        """Reason and label of row j at cut c from its raw rows. It proves arithmetic and membership under these very
        definitions; it does not prove that the definitions answer the trader's question (the contract's examples do)."""
        la, lb = level
        k, d = self.keys[j], int(self.side[j])
        fr = self.provider.frame(k, d)
        rows = self.provider.directed_rows(k, d, fr["e"])
        act, T, w = int(self.grid[self.a[j]]), int(self.grid[c]), int(self.w[j])
        if T <= act:
            return "NOT_ACTIVATED", None
        r, cl, broken = None, None, False
        for t in range(act + 5, T + 1, 5):
            row = rows.get(t)
            if row is None:
                return "PREFIX_HOLE", None
            lo, hi, cc = row
            broken = broken or cc < int(self.oppv[j])
            r = lo if r is None else min(r, lo)
            cl = cc
        if broken:
            return "DR_BROKEN", None
        if r * lb <= la * w:
            return "ALREADY_AT_L", None
        n_, d_ = TOL
        if not d_ * abs(cl * w_t - cl_t * w) <= n_ * w * w_t:
            return "FAR", None
        gap = False
        for t in range(T + 5, self.end + 1, 5):
            row = rows.get(t)
            if row is None:
                gap = True
                continue
            if row[0] * lb <= la * w:
                return "MATCH", "YES"
        return "MATCH", "UNKNOWN" if gap else "NO"

    def reference_check(self, att, seed):
        par, reason, m = att["par"], att["reason"], att["mask"]
        st, level = att["state"], LEVELS[att["level"]]
        c = att["cut"]
        lab = np.where(m["reach"], "YES", np.where(m["unk"], "UNKNOWN", "NO"))
        matched = np.flatnonzero(m["match"])
        excl = np.flatnonzero(~m["match"])
        if len(excl) > SAMPLE_EXCLUDED:
            order = sorted(excl.tolist(), key=lambda q: sha(f"{seed}:{self.ids[par[q]]}".encode()))
            excl = np.array(sorted(order[:SAMPLE_EXCLUDED]), dtype=int)
        bad = []
        for q in list(matched) + list(excl):
            rs, lb = self.scalar_classify(int(par[q]), c, level, st["close_v"], st["w"])
            want = (str(reason[q]), str(lab[q]) if reason[q] == "MATCH" else None)
            if (rs, lb) != want:
                bad.append(dict(id=self.ids[par[q]], vector=list(want), scalar=[rs, lb]))
        return dict(implementation="scalar-raw-rows-1", members_checked=int(len(matched)), excluded_checked=int(len(excl)),
                    excluded_total=int((~m["match"]).sum()), disagreements=bad)

    # -- the issue payload of one attempt (canonical: integers, strings, booleans)
    def issue_payload(self, i, c, level_name, est):
        att = self.attempt(i, c, level_name, est)
        if att["state"]["status"] != "OPEN":
            return None, att
        tgt = self.target_record(i, level_name)
        tid = target_id(tgt)
        inp = self.inputs(i, c)
        iid = issue_id(tid, c, est, MODEL, inp["input_digest"], ISSUE_KIND)
        ref = self.reference_check(att, f"{tid}:{c}:{est}")
        est_rec = dict(id=est, name=passport.ESTIMATORS[est]["name"], parent_rule=passport.ESTIMATORS[est]["rule"],
                       tolerance=f"{TOL[0]}/{TOL[1]}", support_min=SUPPORT, engine=ENGINE)
        estimate = dict(att["estimate"])
        if ref["disagreements"]:
            estimate["publication"] = "REFERENCE_MISMATCH"
        st = att["state"]
        wd = len(self.parent(i, "NODEPOS_WD"))
        payload = dict(
            record="Q1_ISSUE", schema="q1-issue-1", issue_kind=ISSUE_KIND, claim="C1", profile=passport.PROFILE,
            issue_id=iid, target_id=tid, target=tgt,
            cut=dict(index=int(c), close=clk(self.grid[c]), schedule="M5", on_ad_15min_grid=bool((c + 1) % AD_STEP == 0)),
            estimator=est_rec, inputs=inp,
            state=dict(status=st["status"], close_v=st["close_v"], r_v=st["r_v"], x_v=st["x_v"], w=st["w"], elapsed_m5=st["elapsed_m5"]),
            counts=att["counts"], estimate=estimate, members=att["members"], reference_check=ref,
            evidence_scope=dict(weekday_family=wd, ad_target_domain=bool(wd >= AD_MIN_FAMILY),
                                on_ad_15min_grid=bool((c + 1) % AD_STEP == 0)))
        return payload, att

    # -- the target's own future: only for an outcome record, never for an attempt
    def observe(self, i, level):
        la, lb = level
        L = len(self.grid)
        a_t, w_t = int(self.a[i]), int(self.w[i])
        lo = self.P[i, :, 0]
        nan = np.isnan(lo)
        post = np.arange(L) > a_t
        hit = post & ~nan & (np.where(nan, 0, lo) * lb <= la * w_t)
        first = int(np.argmax(hit)) if hit.any() else None
        missing = np.flatnonzero(post & nan)
        return dict(first=first, missing=missing,
                    label="YES" if first is not None else "UNKNOWN" if len(missing) else "NO",
                    time_known=first is not None and not bool((post & nan)[:first].any()))

    def outcome_payload(self, issue, revision=1, supersedes=None, reason=None):
        """The observed outcome of the issue's target event over (cut, H]. The target's event is shared by all its open
        cuts; this record resolves ONE issue, and only after checking the invariant that makes the event the same: the
        prefix the outcome was computed on is the prefix the issue was made on, and up to the cut L was not reached and
        no M5 was missing (so every reach and every hole of the target lies after the cut)."""
        pl = issue["payload"]
        i = self.row(pl["target"]["date"])
        c = pl["cut"]["index"]
        level = LEVELS[pl["target"]["level"]["name"]]
        ob = self.observe(i, level)
        k = self.keys[i]
        a_t = int(self.a[i])
        check = dict(same_target=target_id(self.target_record(i, pl["target"]["level"]["name"])) == pl["target_id"],
                     same_prefix=self.provider.prefix_digest(k, c, self.grid[c]) == pl["inputs"]["target_prefix_digest"],
                     not_reached_by_cut=ob["first"] is None or ob["first"] > c,
                     no_missing_by_cut=not bool(((ob["missing"] > a_t) & (ob["missing"] <= c)).any()))
        observed = dict(label=ob["label"], through=clk(self.end),
                        first_reach=None if ob["first"] is None else dict(close=clk(self.grid[ob["first"]]), time_known=ob["time_known"]),
                        missing_after_cut=[clk(self.grid[q]) for q in ob["missing"] if q > c])
        basis = dict(target_rows_digest=self.provider.session_digest(k), model=MODEL)
        payload = dict(record="Q1_OUTCOME", schema="q1-outcome-1", issue_id=pl["issue_id"], issue_payload_sha256=sha(pl),
                       target_id=pl["target_id"], cut=dict(pl["cut"]), observed=observed, check=check, basis=basis,
                       revision=int(revision), supersedes=supersedes, reason=reason)
        payload["outcome_id"] = outcome_id(pl["issue_id"], observed, basis, revision, supersedes)
        return payload

    def _row_by_date(self, date):
        hits = np.flatnonzero(self.dates == date)
        if not len(hits):
            raise KeyError(date)
        return int(hits[0])

    def row(self, date):
        return self._row_by_date(date)

    def open_cuts(self, i):
        """Grid indices a target can be asked at: closes after its activation, before the block end."""
        return list(range(int(self.a[i]) + 1, len(self.grid) - 1))


# ---------- loaded tables (per process) ----------
_TABLES = {}


def table(inst, block):
    if inst not in INSTRUMENTS or block not in BLOCKS:
        raise ValueError("instrument / block outside the pilot (NQ, ES, YM x ODR, RDR)")
    if CORPUS["path"] is None:
        bind_corpus()
    key = (inst, block, str(CORPUS["path"]))
    if key not in _TABLES:
        U, grid = V.universe(inst, block, "conf")
        _TABLES[key] = Table(inst, block, U, grid, BaseProvider(inst, block))
    return _TABLES[key]


# ---------- workflow over a store ----------
def issue(store, tbl, i, c, level_name, est, meta=None):
    """Compute one attempt from the target's prefix and the earlier sessions and write it once (any publication
    status, «мало сессий» included: the coverage of the method is counted over attempts, not over convenient answers)."""
    payload, att = tbl.issue_payload(i, c, level_name, est)
    if payload is None:
        return None, att, None
    m = dict(code=code_version(), corpus_path=str(CORPUS["path"]) if tbl.provider.kind == "base" else "synthetic",
             target_future_on_disk=True)
    status, rec = store.put_issue(payload, dict(m, **(meta or {})))
    return status, att, rec


def reproduce(store, tbl, rid):
    """Reopen a stored issue and recompute it on its original inputs. IDENTICAL means byte-identical payload; a changed
    model or changed inputs are reported as such — current data are never passed off as the original snapshot."""
    rec = store.get_issue(rid)
    if rec is None:
        return dict(status="NOT_FOUND")
    pl = rec["payload"]
    integrity = sha(pl) == rec["meta"]["payload_sha256"]
    if pl["inputs"]["model"] != MODEL:
        return dict(status="MODEL_CHANGED", integrity=integrity, stored_model=pl["inputs"]["model"], current_model=MODEL,
                    code=rec["meta"].get("code"))
    i = tbl.row(pl["target"]["date"])
    c = pl["cut"]["index"]
    now = tbl.inputs(i, c)
    if now["input_digest"] != pl["inputs"]["input_digest"]:
        changed = [nm for nm in ("target_prefix_digest", "domain_digest") if now[nm] != pl["inputs"][nm]]
        return dict(status="INPUTS_CHANGED", integrity=integrity, changed=changed)
    fresh, _ = tbl.issue_payload(i, c, pl["target"]["level"]["name"], pl["estimator"]["id"])
    same = fresh is not None and canonical(fresh) == canonical(pl)
    return dict(status="IDENTICAL" if same else "DIFFERENT", integrity=integrity, payload_sha256=sha(pl),
                recomputed_sha256=None if fresh is None else sha(fresh))


def attach_outcome(store, tbl, rid):
    """A separate outcome record for one issue; a changed basis becomes a new revision that supersedes the last one."""
    rec = store.get_issue(rid)
    if rec is None:
        raise KeyError(rid)
    prev = sorted(store.outcomes(issue_id_=rid), key=lambda r: r["payload"]["revision"])
    last = prev[-1]["payload"] if prev else None
    probe = tbl.outcome_payload(rec)
    if not all(probe["check"].values()):
        return "REFUSED", probe
    if last and last["observed"] == probe["observed"] and last["basis"] == probe["basis"]:
        return "IDEMPOTENT", store.get_outcome(last["outcome_id"])
    payload = probe if last is None else tbl.outcome_payload(rec, revision=last["revision"] + 1, supersedes=last["outcome_id"],
                                                            reason="basis changed: the target's rows or the model differ")
    return store.put_outcome(payload, dict(code=code_version()))
