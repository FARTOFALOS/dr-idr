"""«Слой от Anthropic» on screen 23.5 — the candidate DR-LAB-ANT-0.1 (meaning/28-sloj-ot-anthropic.md).

    python -B tests/ant235.py

On a synthetic confirmation family (integer ticks, RDR grid): today's state at the cut (lab/contract.py::ref_ant_today);
the set CS:ANT-LIKE-NOW-1 (eligible at the cut, the deepest point so far in today's window of T's clock, the top so far
within a quarter of the IDR width of today's); the outcome «reached the level after the cut before the own DR broke» with its
unknowns; the condition of the window's levels (DR held, the pullback before the top in the window); the page's
one-pass summary (ant235.js::antAhead) equals the reference level by level; the candidate gate recomputes the passports
and refuses a wrong count, a level not above today's top, a range that is not a window of T's clock, a window without
today's deepest point, a broken DR and an incomplete prefix; the accepted gate does not know these estimands; the
accepted registry still has its 55 estimands. Exit code 0 = every check passed.
"""
import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lab"))
import contract as C  # noqa: E402
import integration24 as I  # noqa: E402

bad = []


def check(ok, what):
    print(("  ok   " if ok else "  FAIL ") + what)
    if not ok: bad.append(what)


F_, E_ = 630, 960                                   # RDR: formed 10:30, block end 16:00
GRID = list(range(F_ + 5, E_ + 1, 5))
TICK = 0.25
E_T, W_T, OPP_T = 420, 40, -60                      # today: IDR 95-105 (edge 105 = 420 ticks), width 40 ticks, DR low 90


def path(rows, flat=(-2, 2, 0), upto=None):
    """{close minute: (low, high, close)} in directed ticks; other M5 flat; None where rows says None."""
    out = []
    for T in GRID:
        if T in rows: out.append(None if rows[T] is None else list(rows[T]))
        elif upto is not None and T > upto: out.append(None)
        else: out.append(list(flat))
    return out


R = lambda t: dict(s="known", v=-20, t=t, ties=[t])
UNK = dict(s="unknown", v=None, t=None, ties=[])
X = dict(s="known", v=30, t=800, ties=[800])


def mem(i, rows, R_=None, outcome="held", w=40, oppv=-60, act=645):
    return dict(id=f"M{i}", date=f"2020-01-{i + 1:02d}", w=w, act=act, conf=act, path=path(rows), oppv=oppv, outcome=outcome,
                R=R_ or R(650), X=X, brk=None)


# today's directed M5 after the activation (645) up to the cut 700: deepest -20 on the M5 660-665 (cell 2), top +16
TODAY = {650: (-8, 10, 4), 655: (-4, 12, 6), 660: (-12, 8, -2), 665: (-20, 0, -10), 670: (-15, 5, 2), 675: (-6, 9, 3),
         680: (-5, 11, 6), 685: (-3, 13, 8), 690: (-2, 16, 9), 695: (-4, 14, 7), 700: (-6, 12, 5)}
like = {665: (-25, -5, -15), 690: (-3, 12, 6)}                      # deepest on the M5 660-665, top +12 (within ¼ of +16)
M = [
    mem(0, {**like, 740: (5, 30, 20), 800: (-70, 0, -65)}, R(660)),                  # in; reaches cell 7, later breaks
    mem(1, {665: (-10, 5, 0), 700: (-30, 2, -5)}),                                       # deepest on the M5 695-700: cell 4
    mem(2, {665: (-25, -5, -15), 690: (-3, 27, 6)}),                                      # top +27: more than ¼ width above +16
    mem(14, {665: (-25, -5, -15), 690: (-3, 5, 2)}),                                      # top +5: more than ¼ width below +16
    mem(3, {665: (-25, -5, -15), 690: (-70, 0, -62)}, outcome="broken"),                  # DR broken before the cut
    mem(4, {665: (-25, -5, -15), 680: None}),                                             # a missing M5 before the cut
    mem(5, {**like, 720: (-80, -20, -65)}, outcome="broken"),                       # in; breaks first
    mem(6, {**like, 705: (0, 18, 10), 710: None, 730: (10, 40, 30)}, UNK),         # in; a gap before the reach
    mem(7, {665: (-10, -2, -5), 690: (-1, 7, 3), 750: (5, 12, 10)}, R(700), w=20, oppv=-30),   # in (half width); cell 6
    mem(8, {}, act=705),                                                                  # its activation after the cut
    mem(9, {**like, 705: (-70, 22, -61)}, outcome="unknown"),                       # in; the break M5 does not count
    mem(10, {700: (-30, 2, -5)}, R(665)), mem(11, {700: (-30, 2, -5)}, R(665)),         # out (deepest in cell 4); for the clock
    mem(12, {700: (-30, 2, -5)}, R(670)), mem(13, {700: (-30, 2, -5)}, R(670)),
]
FAM = dict(view="conf", grid=GRID, schedule=dict(formed=F_, end=E_), N=len(M), members=M, zones={},
           key=dict(window=[645, 660]), today=dict(c0=645, side=1, idrH=105.0, idrL=95.0, drH=110.0, drL=90.0))
price = lambda v: (E_T + v) * TICK
BARS = [[T - 5, price(c), price(h), price(lo), price(c)] for T, (lo, h, c) in TODAY.items()]

# T's clock of this family: held R at 650 x4, 660, 665 x2, 670 x2, 700 -> the bunch 10:45-11:15, median 11:00: W1 = cells [1, 3)
clock = C.ref_tp_clock([m["R"] for m in M if m["outcome"] == "held"], F_, 1, E_, len(M))
check(clock["windows"]["W1"] == [1, 3], f"the synthetic T's clock: W1 = cells [1, 3) ({clock['windows']})")

t = C.ref_ant_today(FAM, BARS, TICK, 700)
check(t == dict(cut=700, r=-20, b=2, x=16, w=40, intact=True), f"today at 11:40: deepest -20 on an M5 of cell 2, top +16, width 40, DR whole ({t})")
t2, Ct = C.ref_ant_like_now(FAM, BARS, TICK, 700, 1, 3)
if t2 is None: print("  FAIL no set:", Ct); sys.exit(1)
check([m["id"] for m in Ct] == ["M0", "M5", "M6", "M7", "M9"],
      "like today: eligible, deepest point so far in W1, top so far within ¼ IDR width of today's — M1 (deepest in cell 4), M2 and M14 (top too far "
      f"above or below), M3 (DR broken), M4 (a hole), M8 (activation after the cut) stay out ({[m['id'] for m in Ct]})")


def tally(k):
    res = [C.ref_ant_reach_before_break(m["path"], GRID, 700, E_, k, m["w"], m["oppv"]) for m in Ct]
    return res.count("yes"), res.count("unknown"), res.count("no")


check(tally(5) == (2, 1, 2), f"level +0.5: M0 and M7 reached it, M6 unknown (a hole first), M5 broke first, M9's break M5 does not count ({tally(5)})")
check(tally(7) == (1, 1, 3), f"level +0.7: only M0 ({tally(7)})")
check(all(tally(k)[0] >= tally(k + 1)[0] for k in range(5, 12)), "«дошли» does not grow with the level")
cond = [C.ref_ant_true_in_window(m, F_, 1, 3) for m in Ct]
check(cond == ["yes", "no", "unknown", "no", "unknown"], f"the window's condition: M0 true and R in W1; M5 broken; M6 R unknown; M7 R in cell 4; M9 outcome unknown ({cond})")


# the page's one pass (design/sozvezdiya-23-5/src/ant235.js::antAhead): the farthest cell before the first hole and the
# break, and whether a hole came before the break or the end; «yes» = top >= k, else «unknown» if a hole, else «no»
def ahead(m, cut):
    top, gap = None, False
    for j, T in enumerate(GRID):
        if T <= cut or T > E_: continue
        q = m["path"][j]
        if q is None: gap = True; continue
        if q[2] < m["oppv"]: break
        if not gap: top = max(top, C.ref_cell(q[1], m["w"])) if top is not None else C.ref_cell(q[1], m["w"])
    return top, gap


same = True
for m in M:
    for cut in (650, 700, 745, 800):
        top, gap = ahead(m, cut)
        for k in range(-6, 14):
            want = C.ref_ant_reach_before_break(m["path"], GRID, cut, E_, k, m["w"], m["oppv"])
            got = "yes" if top is not None and top >= k else "unknown" if gap else "no"
            same &= want == got
check(same, "the page's one-pass summary equals the reference outcome for every member, cut and level")

G = I.review_gate()
pp = lambda est, y, u, n, **a: dict(id=1, estimand=est, params=dict(dict(cut=700, b0=1, b1=3), **a), yes_count=y, unknown_count=u, no_event_count=n, N=len(M))
check(G.get("EST:ANT-REACH-AHEAD") is not None and G.get("CS:ANT-LIKE-NOW-1")["role"] == "MATCHED_AT_CUT", "the candidate edition registers the layer (MATCHED_AT_CUT, C1)")
check(C.get("EST:ANT-REACH-AHEAD") is None and len(C.registry()["estimands"]) == 55, "the accepted registry does not know it and keeps its 55 estimands")
check(G.verify_passports(FAM, BARS, TICK, [pp("EST:ANT-REACH-AHEAD", 2, 1, 2, k=5), pp("EST:ANT-REACH-AHEAD", 1, 1, 3, k=7), pp("EST:ANT-COND-WINDOW", 1, 2, 2)]) == [],
      "the candidate gate recomputes the passports of the levels and of the condition")
check(G.verify_passports(FAM, BARS, TICK, [pp("EST:ANT-REACH-AHEAD", 3, 0, 2, k=5)]) != [], "a wrong count is refused")
e = G.verify_passports(FAM, BARS, TICK, [pp("EST:ANT-REACH-AHEAD", 5, 0, 0, k=4)])
check(e and "not above today's top" in e[0]["error"], "a level not above today's top so far is refused")
e = G.verify_passports(FAM, BARS, TICK, [pp("EST:ANT-COND-WINDOW", 0, 0, 0, b0=2, b1=3)])
check(e and "not a window of T's clock" in e[0]["error"], "a range that is not a window of T's clock is refused")
e = G.verify_passports(FAM, BARS, TICK, [pp("EST:ANT-COND-WINDOW", 0, 0, 0, b0=3, b1=22)])
check(e and "is not in the window" in e[0]["error"], "a window without today's deepest point is refused")
B2 = copy.deepcopy(BARS); B2[-1][4] = price(-61)
e = G.verify_passports(FAM, B2, TICK, [pp("EST:ANT-COND-WINDOW", 1, 2, 2)])
check(e and "already broken" in e[0]["error"], "today's DR broken at the cut: no set")
e = G.verify_passports(FAM, BARS[:5] + BARS[6:], TICK, [pp("EST:ANT-COND-WINDOW", 1, 2, 2)])
check(e and "incomplete prefix" in e[0]["error"], "an incomplete prefix: no set")
e = C.verify_passports(FAM, BARS, TICK, [pp("EST:ANT-REACH-AHEAD", 2, 1, 2, k=5)])
check(e and e[0]["error"] == "unregistered estimand", "the accepted gate refuses a candidate number")
print("ALL GOOD" if not bad else f"{len(bad)} FAILED")
sys.exit(1 if bad else 0)
