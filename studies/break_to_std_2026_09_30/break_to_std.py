"""After a DR break by close: does price reach the opposite 1.0 STD level by the session end? (NQ, read-only)

The operator's question (2026-09-30), about the DR/IDR method (TheMas7er / M7DR): a session confirms long or short (the
first M5 close beyond its DR after the box); sometimes the confirmed session then «breaks»: an M5 closes beyond the
OPPOSITE edge of its DR («DR false»). The author's hypothesis as the operator remembers it: after such a break, in most
cases price then reaches the opposite 1.0 standard deviation level. How often is that so on 20 years of NQ, for ADR,
ODR and RDR, in the last 5 years and in the rest?

Frozen definitions (set before counting, not tuned):
  population  complete sessions with conf != null and fail != null (confirmed sessions whose DR broke)
  w           IDR width = idr_high - idr_low (ticks)
  level       the STD grid of the Pine script (steps of 0.5 IDR from the IDR edges, as on the operator's screen);
              the opposite 1.0 level is
                long confirmation broken down (side = 1):   L = idr_low  - 1.0 * w, reached when a bar's LOW  <= L
                short confirmation broken up  (side = -1):  L = idr_high + 1.0 * w, reached when a bar's HIGH >= L
  horizon     from the breaking bar (close_minute == fail) through the last bar of the session
  A           L reached at any bar from the breaking bar (inclusive) to the session end
  B           L first touched only AFTER the breaking bar closed: not touched on or before it, touched at a later bar
  C           L already touched on the breaking bar or earlier in the session (after the box formation hour)
  periods     by the year of the trading date: 2021-2025 (the last 5 years), first year ... 2020 (the rest), all years
Partition used to make the relation explicit (mutually exclusive, by the bar of the FIRST touch of L):
  before_only   touched before the breaking bar and never at or after it      (in C, not in A)
  before_again  touched before the breaking bar and again at or after it      (in C and in A)
  on_first      first touched by the breaking bar itself                      (in C and in A)
  B             first touched after the breaking bar closed                   (in A)
  never         not touched up to the session end
  so  A = before_again + on_first + B,  C = before_only + before_again + on_first,  N = C + B + never.

Cuts added AFTER the first look at the main tables, as explanation and robustness (labelled so in the README; they do not
touch the definitions above): the time left after the break (the >= 60 minutes cut and the 30/60/120 minute bins), the
distance of the breaking close from the level, and a third naive counting route. The share of B among breaks not yet at the
level, the ladder of other STD steps, the one-tick and the early-close variants were in the first version.

Read-only: loads lab/.runtime/boxes_nq_meta.json and boxes_nq.npz (the git-ignored market base) and writes only
break_to_std.log next to this file: aggregates only (counts and percentages), no prices, no bars, no per-session rows.
Run from anywhere:  PYTHONIOENCODING=utf-8 python -B studies/break_to_std_2026_09_30/break_to_std.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RT = HERE.parents[1] / "lab" / ".runtime"
LOG = HERE / "break_to_std.log"

Z = 1.96                                   # 95 % Wilson interval
RECENT_FROM, RECENT_TO = 2021, 2025        # «последние 5 лет»; the rest is everything up to 2020
SESSIONS = ("ADR", "ODR", "RDR")
DIRS = ((0, "оба"), (1, "лонг сломан вниз"), (-1, "шорт сломан вверх"))
PERIODS = (("recent", "2021–2025"), ("rest", None), ("all", "все годы"))   # the label of «rest» is filled with the real first year
LADDER = (0.0, 0.5, 1.0, 1.5, 2.0, 2.5)    # multiples of the IDR width beyond the IDR edge (context only; 1.0 is the question)
SMALL_N = 100                              # below this a cell is called small in the reading

_log = []


def out(s=""):
    print(s)
    _log.append(s)


def wilson(k, n):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    den = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / den
    h = Z * np.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / den
    return 100 * (c - h), 100 * (c + h)


def pct(k, n):
    return 100.0 * k / n if n else float("nan")


# ----------------------------------------------------------------------------------------------------------- data
def load():
    meta = json.loads((RT / "boxes_nq_meta.json").read_text(encoding="utf-8"))
    z = np.load(RT / "boxes_nq.npz")
    return meta["info"], meta["boxes"], z["bars"], z["offsets"]


INFO, BOXES, BARS, OFF = load()
SESS = {k: tuple(v) for k, v in INFO["sessions"].items()}     # name -> (start, formed, end) in ET minutes; ADR +1440


def bars_of(i):
    a = BARS[OFF[i]:OFF[i + 1]].astype(np.int64)
    return a[:, 0], a[:, 1], a[:, 2], a[:, 3], a[:, 4]        # close_minute, open, high, low, close


# ------------------------------------------------------------------------------------ independent recomputation
def recompute_controls():
    """Recompute DR, IDR, confirmation and DR break of EVERY box from its own bars; count disagreements with the meta."""
    bad = dict(dr=0, idr=0, conf=0, side=0, fail=0, window=0)
    for i, b in enumerate(BOXES):
        start, formed, end = SESS[b["session"]]
        cm, op, hi, lo, cl = bars_of(i)
        win = cm <= formed
        if int(win.sum()) != (formed - start) // 5:
            bad["window"] += 1
        if hi[win].max() != b["dr_high"] or lo[win].min() != b["dr_low"]:
            bad["dr"] += 1
        if np.maximum(op[win], cl[win]).max() != b["idr_high"] or np.minimum(op[win], cl[win]).min() != b["idr_low"]:
            bad["idr"] += 1
        post = cm > formed
        up = np.flatnonzero(post & (cl > b["dr_high"]))
        dn = np.flatnonzero(post & (cl < b["dr_low"]))
        k_up = up[0] if len(up) else None
        k_dn = dn[0] if len(dn) else None
        if k_up is None and k_dn is None:
            conf, side, fail = None, 0, None
        else:
            k = k_up if (k_dn is None or (k_up is not None and k_up < k_dn)) else k_dn
            side = 1 if k == k_up else -1
            conf = int(cm[k])
            opp = b["dr_low"] if side == 1 else b["dr_high"]
            later = np.flatnonzero(post & (cm > conf) & (side * (cl - opp) < 0))
            fail = int(cm[later[0]]) if len(later) else None
        if conf != b["conf"]:
            bad["conf"] += 1
        if side != b["side"]:
            bad["side"] += 1
        if fail != b["fail"]:
            bad["fail"] += 1
    return bad


# ------------------------------------------------------------------------------------------------ one session
def one(i, mult=1.0, margin=0):
    """Flags of one broken session for the level mult * IDR width beyond the IDR edge on the side opposite to the
    confirmation (margin: extra ticks beyond the level, used only for the stricter sensitivity run)."""
    b = BOXES[i]
    start, formed, end = SESS[b["session"]]
    cm, op, hi, lo, cl = bars_of(i)
    w = b["idr_high"] - b["idr_low"]
    fail = b["fail"]
    if b["side"] == 1:                                   # long confirmed, broken down: the level is below
        lvl = b["idr_low"] - mult * w - margin
        touch = lo <= lvl
        inside_dr = lvl >= b["dr_low"]                   # the level is not deeper than the DR edge the break closed beyond
    else:                                                # short confirmed, broken up: the level is above
        lvl = b["idr_high"] + mult * w + margin
        touch = hi >= lvl
        inside_dr = lvl <= b["dr_high"]
    kf = np.flatnonzero(cm == fail)
    assert len(kf) == 1, "the breaking bar must be among the session's bars exactly once"
    kf = int(kf[0])
    post = cm > formed                                   # bars after the formation hour: the level exists from then on
    aft = cm > fail
    before = bool(touch[post & (cm < fail)].any())
    on = bool(touch[kf])
    after = bool(touch[aft].any())
    first_min = float(cm[np.flatnonzero(aft & touch)[0]] - fail) if after else float("nan")
    conf_bar = np.flatnonzero(cm == b["conf"])
    pre_conf = bool(touch[post & (cm <= b["conf"])].any()) if len(conf_bar) else False
    # how far the breaking close is from the level, in IDR widths (positive = the level is still ahead)
    dist = ((cl[kf] - lvl) if b["side"] == 1 else (lvl - cl[kf])) / w
    return dict(session=b["session"], side=b["side"], year=int(b["date"][:4]), before=before, on=on, after=after,
                first_min=first_min, left=int(cm[-1] - fail), early=bool(cm[-1] < end), inside_dr=bool(inside_dr),
                form_touch=bool(touch[cm <= formed].any()), pre_conf=pre_conf, dist=float(dist))


def one_alt(i, mult=1.0):
    """The same A and B by a different route (running extremes instead of any()): used only to cross-check one()."""
    b = BOXES[i]
    cm, op, hi, lo, cl = bars_of(i)
    formed = SESS[b["session"]][1]
    w = b["idr_high"] - b["idr_low"]
    kf = int(np.flatnonzero(cm == b["fail"])[0])
    k0 = int(np.searchsorted(cm, formed, side="right"))   # first bar after the formation hour
    if b["side"] == 1:
        lvl = b["idr_low"] - mult * w
        reach = lambda seg: len(seg) > 0 and seg.min() <= lvl
        arr = lo
    else:
        lvl = b["idr_high"] + mult * w
        reach = lambda seg: len(seg) > 0 and seg.max() >= lvl
        arr = hi
    a = reach(arr[kf:])
    bb = reach(arr[kf + 1:]) and not reach(arr[k0:kf + 1])
    return a, bb


def one_loop(i, mult=1.0):
    """A third, deliberately naive route: a plain Python loop over the bars (no numpy masks), same three flags as one()."""
    b = BOXES[i]
    formed = SESS[b["session"]][1]
    w = b["idr_high"] - b["idr_low"]
    before = on = after = False
    for row in BARS[OFF[i]:OFF[i + 1]].tolist():
        cm, op, hi, lo, cl = row
        if cm <= formed:
            continue
        if b["side"] == 1:
            hit = lo <= b["idr_low"] - mult * w
        else:
            hit = hi >= b["idr_high"] + mult * w
        if cm < b["fail"]:
            before = before or hit
        elif cm == b["fail"]:
            on = on or hit
        else:
            after = after or hit
    return before, on, after


def build(pop, mult=1.0, margin=0):
    rows = [one(i, mult, margin) for i in pop]
    R = {k: np.array([r[k] for r in rows]) for k in rows[0]}
    return R


# --------------------------------------------------------------------------------------------------- aggregation
def mask(R, sess=None, side=0, period="all", no_early=False):
    m = np.ones(len(R["year"]), bool)
    if sess:
        m &= R["session"] == sess
    if side:
        m &= R["side"] == side
    if period == "recent":
        m &= (R["year"] >= RECENT_FROM) & (R["year"] <= RECENT_TO)
    elif period == "rest":
        m &= R["year"] < RECENT_FROM
    if no_early:
        m &= ~R["early"]
    return m


def stats(R, m):
    n = int(m.sum())
    before, on, after = R["before"][m], R["on"][m], R["after"][m]
    A = on | after
    Bm = ~before & ~on & after
    C = before | on
    s = dict(n=n, A=int(A.sum()), B=int(Bm.sum()), C=int(C.sum()),
             before_only=int((before & ~A).sum()), before_again=int((before & A).sum()),
             on_first=int((~before & on).sum()), never=int((~before & ~on & ~after).sum()),
             minutes=R["first_min"][m][Bm], left=R["left"][m])
    assert s["before_only"] + s["before_again"] + s["on_first"] + s["B"] + s["never"] == n      # partition of N
    assert s["A"] == s["before_again"] + s["on_first"] + s["B"]                                 # A = again + on + B
    assert s["C"] == s["before_only"] + s["before_again"] + s["on_first"]                        # C = before + on
    s["open"] = s["B"] + s["never"]                       # N - C: the level was not yet touched when the break bar closed
    return s


def verdict(k, n):
    lo, hi = wilson(k, n)
    if n == 0:
        return "нет данных"
    if lo > 50:
        return "да, больше половины (нижняя граница ДИ > 50 %)"
    if hi < 50:
        return "нет, меньше половины (верхняя граница ДИ < 50 %)"
    return "не ясно (ДИ накрывает 50 %)"


def period_label(key, first_year):
    return {"recent": f"последние 5 лет {RECENT_FROM}–{RECENT_TO}",
            "rest": f"остальное {first_year}–{RECENT_FROM - 1}",
            "all": f"все годы {first_year}–{RECENT_TO}"}[key]


def main():
    # ------------------------------------------------------------------------------- 1. data and controls
    out("Слом DR по закрытию -> доходит ли цена до -1,0 SD с противоположной стороны к концу сессии (NQ)")
    out("Только агрегаты: счётчики и проценты; цен, свечей и строк по сессиям здесь нет.")
    out("")
    out("=== 1. Данные и контроль")
    out(f"файлы: lab/.runtime/boxes_nq_meta.json (версия {INFO['version']}), boxes_nq.npz; инструмент {INFO['instrument']}, "
        f"тик {INFO['tick']}; коробок {len(BOXES)}; строк свечей {len(BARS)}")
    assert INFO["instrument"] == "NQ"
    assert len(OFF) == len(BOXES) + 1 and int(OFF[-1]) == len(BARS)
    years_all = np.array([int(b["date"][:4]) for b in BOXES])
    last_date = max(b["date"] for b in BOXES)
    first_year = int(years_all.min())
    assert int(years_all.max()) <= 2025 and all(b["date"] < "2026-01-01" for b in BOXES), "2026 must stay hidden"
    out(f"первый год в данных {first_year}; последний год {int(years_all.max())} (последняя торговая дата в базе {last_date}); "
        f"записей с годом 2026 и позже: {int((years_all >= 2026).sum())}  [проверено assert: 2026 в данных нет]")
    assert INFO["hidden"] == "2026" and INFO["stop_exclusive"] == "2026-01-01"

    bad = recompute_controls()
    out(f"пересчёт из самих свечей по всем {len(BOXES)} коробкам (DR, IDR, подтверждение, сторона, слом DR): "
        f"расхождений с базой {bad}")
    assert sum(bad.values()) == 0, f"the base contradicts the definitions: {bad}"

    # population
    pop = [i for i, b in enumerate(BOXES) if b["complete"] and b["conf"] is not None and b["fail"] is not None]
    earlier = {"RDR": (4730, 803), "ODR": (4735, 1072)}            # the repository's earlier measure, from the task brief
    out("")
    out("сессия   коробок  завершённых  подтверждённых  сломанных  доля сломанных среди подтверждённых   прежний замер репозитория")
    cnt = {}
    for s in SESSIONS:
        allb = [b for b in BOXES if b["session"] == s]
        comp = [b for b in allb if b["complete"]]
        conf = [b for b in comp if b["conf"] is not None]
        brk = [b for b in conf if b["fail"] is not None]
        cnt[s] = (len(allb), len(comp), len(conf), len(brk))
        note = ""
        if s in earlier:
            ec, eb = earlier[s]
            note = f"{ec} / {eb}: " + ("совпало" if (len(conf), len(brk)) == (ec, eb) else f"НЕ совпало ({len(conf)} / {len(brk)})")
        out(f"{s:<7} {len(allb):>8} {len(comp):>12} {len(conf):>15} {len(brk):>10} {pct(len(brk), len(conf)):>30.1f} %   {note}")
    assert len(pop) == sum(c[3] for c in cnt.values())
    out(f"население (завершена, подтверждена, сломана): {len(pop)} сессий")
    inc = sum(1 for b in BOXES if not b["complete"])
    out(f"незавершённых сессий в базе {inc} — в население не входят")
    out(f"сломанных сессий с подтверждением без стороны или стороной без подтверждения: "
        f"{sum(1 for i in pop if BOXES[i]['side'] == 0)} (должно быть 0)")

    # ------------------------------------------------------------------------------- 2. the flags
    R = build(pop, 1.0)
    # cross-check A and B by an independent route
    mism = 0
    for k, i in enumerate(pop):
        a, bb = one_alt(i, 1.0)
        on_, af = R["on"][k], R["after"][k]
        if a != (on_ or af) or bb != ((not R["before"][k]) and (not on_) and af):
            mism += 1
    out(f"второй способ подсчёта A и B (бегущие экстремумы вместо any) по всем {len(pop)} сломам: расхождений {mism}")
    assert mism == 0
    mism3 = sum(1 for k, i in enumerate(pop) if one_loop(i, 1.0) != (bool(R["before"][k]), bool(R["on"][k]), bool(R["after"][k])))
    out(f"третий способ (простой цикл по свечам, без numpy) — три признака «до слома / на свече слома / после» по всем {len(pop)} сломам: расхождений {mism3}")
    assert mism3 == 0
    first_year_pop = {p: int(R["year"][mask(R, None, 0, p)].min()) for p in ("rest", "all")}
    out(f"первый год среди сломанных сессий: {first_year_pop['all']}; по сессиям (остальное): " +
        ", ".join(f"{s} {int(R['year'][mask(R, s, 0, 'rest')].min())}" for s in SESSIONS))
    fy = first_year

    # ------------------------------------------------------------------------------- 3. definitions
    out("")
    out("=== 2. Определения (заморожены до подсчёта)")
    out("слом: после подтверждения первое закрытие M5 за противоположным краем DR (для лонга ниже низа DR, для шорта выше верха DR)")
    out("ширина IDR w = верх IDR - низ IDR; уровень -1,0 SD с противоположной стороны (сетка STD Pine, шаг 0,5 IDR от краёв IDR):")
    out("  лонг сломан вниз:  L = низ IDR - 1,0 * w, достигнут, если LOW свечи <= L")
    out("  шорт сломан вверх: L = верх IDR + 1,0 * w, достигнут, если HIGH свечи >= L")
    out("горизонт: от свечи слома (close_minute == fail) включительно до последней свечи сессии")
    out("A = достигнут на любой свече от свечи слома (включительно) до конца сессии")
    out("B = впервые достигнут только после закрытия свечи слома (не на ней и не раньше)")
    out("C = уже был достигнут на свече слома или раньше в сессии (после формирующего часа)")
    out("разбиение по свече ПЕРВОГО касания: до слома (и потом снова / и больше нет) | на свече слома | после слома (B) | не достигнут")
    out("  A = до слома и снова + на свече слома (впервые) + B;  C = до слома (обе группы) + на свече слома (впервые);  N = C + B + не достигнут")

    # ------------------------------------------------------------------------------- 4. main table
    out("")
    out(f"=== 3. Главная таблица (95 % интервал Уилсона для A; N < {SMALL_N} отмечено звёздочкой)")
    md_main = []
    for pkey, _ in PERIODS:
        out("")
        out(f"-- {period_label(pkey, fy)}")
        out("сессия  что сломано           N сломов    A: дошли к концу сессии   [95 % ДИ]        B: впервые после свечи слома    C: уже были к слому")
        for s in SESSIONS:
            for side, dname in DIRS:
                st = stats(R, mask(R, s, side, pkey))
                lo, hi = wilson(st["A"], st["n"])
                star = "*" if st["n"] < SMALL_N else " "
                out(f"{s:<7} {dname:<20} {st['n']:>6}{star}   {pct(st['A'], st['n']):>6.1f} % ({st['A']:>4})   [{lo:5.1f}–{hi:5.1f}]   "
                    f"{pct(st['B'], st['n']):>6.1f} % ({st['B']:>4})               {pct(st['C'], st['n']):>6.1f} % ({st['C']:>4})")
        st = stats(R, mask(R, None, 0, pkey))
        lo, hi = wilson(st["A"], st["n"])
        out(f"{'все три':<7} {'оба':<20} {st['n']:>6}    {pct(st['A'], st['n']):>6.1f} % ({st['A']:>4})   [{lo:5.1f}–{hi:5.1f}]   "
            f"{pct(st['B'], st['n']):>6.1f} % ({st['B']:>4})               {pct(st['C'], st['n']):>6.1f} % ({st['C']:>4})")

    # the README version: one table, periods side by side
    def cell(s, side, pkey):
        st = stats(R, mask(R, s, side, pkey))
        lo, hi = wilson(st["A"], st["n"])
        small = "\\*" if st["n"] < SMALL_N else ""
        return (f"{st['n']}{small}", f"{pct(st['A'], st['n']):.0f} ({lo:.0f}–{hi:.0f})", f"{pct(st['B'], st['n']):.0f}")

    md_main.append(f"| Сессия | Что сломано | {period_label('recent', fy)}: N | A, % (95 % ДИ) | B, % | "
                   f"{period_label('rest', fy)}: N | A, % (95 % ДИ) | B, % | {period_label('all', fy)}: N | A, % (95 % ДИ) | B, % |")
    md_main.append("|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for s in SESSIONS:
        for side, dname in DIRS:
            cells = []
            for pkey, _ in PERIODS[:3]:
                cells += list(cell(s, side, pkey))
            name = f"**{s}**" if side == 0 else s
            dn = f"**{dname}**" if side == 0 else dname
            md_main.append(f"| {name} | {dn} | " + " | ".join(cells) + " |")
    cells = []
    for pkey, _ in PERIODS[:3]:
        cells += list(cell(None, 0, pkey))
    md_main.append("| **все три** | **оба** | " + " | ".join(cells) + " |")

    # ------------------------------------------------------------------------------- 5. the reading against 50 %
    out("")
    out("=== 4. «В большинстве случаев» (> 50 %): оба направления вместе; вердикт по границам интервала Уилсона")
    for pkey, _ in PERIODS:
        out(f"-- {period_label(pkey, fy)}")
        for s in SESSIONS + (None,):
            st = stats(R, mask(R, s, 0, pkey))
            name = s or "все три"
            out(f"  {name:<8} N {st['n']:>5}: A {pct(st['A'], st['n']):5.1f} % -> {verdict(st['A'], st['n'])}")
    out("-- по направлениям, последние 5 лет и все годы")
    for pkey in ("recent", "all"):
        for s in SESSIONS:
            for side, dname in DIRS[1:]:
                st = stats(R, mask(R, s, side, pkey))
                out(f"  {pkey:<6} {s} {dname:<19} N {st['n']:>4}: A {pct(st['A'], st['n']):5.1f} % -> {verdict(st['A'], st['n'])}")

    # ------------------------------------------------------------------------------- 6. partition and relation
    out("")
    out("=== 5. Когда уровень был впервые достигнут: разбиение N на взаимоисключающие части (оба направления)")
    out("   до слома: уровень тронут свечой раньше свечи слома (после формирующего часа); снова = и на/после свечи слома")
    md_part = ["| Сессия | Период | N | уже до слома (и снова после) | уже до слома (и больше нет) | впервые на свече слома | впервые ПОСЛЕ слома (B) | не достигнут до конца сессии | A (итого) | C (уже к слому) |",
               "|---|---|--:|--:|--:|--:|--:|--:|--:|--:|"]
    for s in SESSIONS + (None,):
        for pkey in ("recent", "rest", "all"):
            st = stats(R, mask(R, s, 0, pkey))
            n = st["n"]
            name = s or "все три"
            out(f"  {name:<8} {period_label(pkey, fy):<28} N {n:>5} = до слома и снова {st['before_again']:>3} + до слома и больше нет {st['before_only']:>3} "
                f"+ на свече слома {st['on_first']:>3} + B {st['B']:>4} + не достигнут {st['never']:>4}   |  A {st['A']:>4} = {st['before_again']}+{st['on_first']}+{st['B']}; "
                f"C {st['C']:>3} = {st['before_only']}+{st['before_again']}+{st['on_first']}")
            md_part.append(f"| {name} | {period_label(pkey, fy)} | {n} | {st['before_again']} | {st['before_only']} | {st['on_first']} | {st['B']} | {st['never']} | {st['A']} | {st['C']} |")
    out("")
    out("   доля B среди сломов, где к закрытию свечи слома уровня ещё не было (N - C): это «вперёд-вероятность» для того, кто видит закрытие свечи слома")
    md_fwd = ["| Сессия | Период | сломов без касания к закрытию свечи слома | из них дошли позже, % (95 % ДИ) |", "|---|---|--:|--:|"]
    for s in SESSIONS + (None,):
        for pkey in ("recent", "rest", "all"):
            st = stats(R, mask(R, s, 0, pkey))
            lo, hi = wilson(st["B"], st["open"])
            name = s or "все три"
            out(f"  {name:<8} {period_label(pkey, fy):<28} N-C {st['open']:>5}: дошли позже {st['B']:>4} = {pct(st['B'], st['open']):5.1f} % [{lo:5.1f}–{hi:5.1f}] -> {verdict(st['B'], st['open'])}")
            md_fwd.append(f"| {name} | {period_label(pkey, fy)} | {st['open']} | {pct(st['B'], st['open']):.0f} ({lo:.0f}–{hi:.0f}) |")

    # ------------------------------------------------------------------------------- 7. timing
    out("")
    out("=== 6. Время: от закрытия свечи слома до закрытия свечи, в которой уровень тронут впервые (только группа B; шаг 5 минут)")
    out("   (касание случилось где-то внутри этой M5, поэтому точность — одна свеча, то есть 5 минут; 5 = уже в следующей свече)")
    md_time = ["| Сессия | Период | B, сломов | медиана, мин | 25–75 % | в первой же свече (5 мин), % от B | осталось до конца сессии после слома, медиана мин (все сломы) |", "|---|---|--:|--:|--:|--:|--:|"]
    for s in SESSIONS + (None,):
        for pkey in ("recent", "rest", "all"):
            st = stats(R, mask(R, s, 0, pkey))
            mins = st["minutes"]
            name = s or "все три"
            if len(mins):
                med = float(np.median(mins)); q1, q3 = np.percentile(mins, [25, 75]); first = pct(int((mins <= 5).sum()), len(mins))
            else:
                med = q1 = q3 = first = float("nan")
            left_med = float(np.median(st["left"]))
            out(f"  {name:<8} {period_label(pkey, fy):<28} B {len(mins):>4}: медиана {med:6.1f} мин, 25–75 % [{q1:5.1f}–{q3:5.1f}], в первой же свече {first:5.1f} %; "
                f"после слома до конца сессии, медиана всех сломов {left_med:6.1f} мин")
            md_time.append(f"| {name} | {period_label(pkey, fy)} | {len(mins)} | {med:.0f} | {q1:.0f}–{q3:.0f} | {first:.0f} | {left_med:.0f} |")
    out("   мало времени после слома: осталось меньше 60 минут — доля сломов, оба направления:")
    for s in SESSIONS:
        for pkey in ("recent", "all"):
            m = mask(R, s, 0, pkey)
            out(f"  {s} {period_label(pkey, fy):<28} N {int(m.sum()):>4}: {pct(int((R['left'][m] < 60).sum()), int(m.sum())):5.1f} %  "
                f"(ровно на последней свече сессии: {int((R['left'][m] == 0).sum())})")

    # ------------------------------------------------------------------------------- 8. robustness
    out("")
    out("=== 7. Проверки устойчивости и геометрии (оба направления вместе)")
    geo = {}
    for s in SESSIONS:
        m = mask(R, s, 0, "all")
        geo[s] = (int(R["inside_dr"][m].sum()), int(m.sum()), int(R["form_touch"][m].sum()), int(R["pre_conf"][m].sum()),
                  int(R["early"][m].sum()))
        out(f"  {s}: уровень -1,0 SD не глубже края DR (достигается самой свечой слома по построению): {geo[s][0]} из {geo[s][1]}; "
            f"тронут уже в формирующий час (уровня ещё не было): {geo[s][2]}; тронут до закрытия подтверждающей свечи включительно: {geo[s][3]}; "
            f"рынок закрылся раньше срока (короткая сессия): {geo[s][4]}")
    out("  сравнение A при разных вариантах (последние 5 лет | все годы):")
    R_tick = build(pop, 1.0, margin=1)
    for s in SESSIONS + (None,):
        name = s or "все три"
        parts = []
        for pkey in ("recent", "all"):
            base = stats(R, mask(R, s, 0, pkey))
            noe = stats(R, mask(R, s, 0, pkey, no_early=True))
            tick = stats(R_tick, mask(R_tick, s, 0, pkey))
            parts.append(f"{period_label(pkey, fy)}: A {pct(base['A'], base['n']):5.1f} % | без коротких сессий (N {noe['n']}) {pct(noe['A'], noe['n']):5.1f} % | "
                         f"на тик глубже уровня {pct(tick['A'], tick['n']):5.1f} %")
        out(f"  {name:<8} " + "  ||  ".join(parts))
    d_period = max(abs(pct(stats(R, mask(R, s, 0, "recent"))["A"], stats(R, mask(R, s, 0, "recent"))["n"])
                       - pct(stats(R, mask(R, s, 0, "rest"))["A"], stats(R, mask(R, s, 0, "rest"))["n"])) for s in SESSIONS)
    d_early = max(abs(pct(stats(R, mask(R, s, 0, p))["A"], stats(R, mask(R, s, 0, p))["n"])
                      - pct(stats(R, mask(R, s, 0, p, no_early=True))["A"], stats(R, mask(R, s, 0, p, no_early=True))["n"]))
                  for s in SESSIONS + (None,) for p in ("recent", "all"))
    out(f"  наибольшая разница A между 2021–2025 и остальным по сессиям (оба направления): {d_period:.1f} пункта; "
        f"наибольшее изменение A при исключении коротких сессий: {d_early:.1f} пункта")
    out("  только сломы, после которых до конца сессии оставалось не меньше 60 минут (A, %; N в скобках):")
    for s in SESSIONS + (None,):
        name = s or "все три"
        parts = []
        for pkey in ("recent", "all"):
            m = mask(R, s, 0, pkey) & (R["left"] >= 60)
            st = stats(R, m)
            lo, hi = wilson(st["A"], st["n"])
            parts.append(f"{period_label(pkey, fy)}: {pct(st['A'], st['n']):5.1f} % [{lo:5.1f}–{hi:5.1f}] (N {st['n']})")
        out(f"  {name:<8} " + "  ||  ".join(parts))
    out("  A в зависимости от времени, оставшегося до конца сессии после закрытия свечи слома (известно в момент слома); A, % (N):")
    bins = ((0, 30, "меньше 30 мин"), (30, 60, "30–59 мин"), (60, 120, "60–119 мин"), (120, 10 ** 9, "120 мин и больше"))
    md_left = ["| Осталось после слома | ADR 2021–2025 | ODR 2021–2025 | RDR 2021–2025 | все три 2021–2025 | ADR все годы | ODR все годы | RDR все годы | все три все годы |",
               "|---|--:|--:|--:|--:|--:|--:|--:|--:|"]
    for lo_, hi_, label in bins:
        row = []
        for pkey in ("recent", "all"):
            for s in SESSIONS + (None,):
                m = mask(R, s, 0, pkey) & (R["left"] >= lo_) & (R["left"] < hi_)
                st = stats(R, m)
                row.append(f"{pct(st['A'], st['n']):.0f} ({st['n']})")
        out(f"  {label:<18} 2021–2025: ADR {row[0]:>9} ODR {row[1]:>9} RDR {row[2]:>9} все {row[3]:>9}   |   все годы: ADR {row[4]:>10} ODR {row[5]:>10} RDR {row[6]:>10} все {row[7]:>10}")
        md_left.append(f"| {label} | " + " | ".join(row) + " |")
    out("  как далеко закрытие свечи слома от уровня -1,0 SD, в ширинах IDR (медиана; 25–75 %) — чем больше, тем дальше идти:")
    for s in SESSIONS + (None,):
        name = s or "все три"
        parts = []
        for pkey in ("recent", "all"):
            d = R["dist"][mask(R, s, 0, pkey)]
            q1, q3 = np.percentile(d, [25, 75])
            parts.append(f"{period_label(pkey, fy)}: {np.median(d):.2f} ({q1:.2f}–{q3:.2f})")
        out(f"  {name:<8} " + "  ||  ".join(parts))
    med = {s: float(np.median(R["dist"][mask(R, s, 0, "recent")])) for s in SESSIONS}
    out(f"  разброс медиан расстояния между сессиями (2021–2025): {max(med.values()) - min(med.values()):.2f} ширины IDR")

    # ------------------------------------------------------------------------------- 9. ladder
    out("")
    out("=== 8. Контекст (вне вопроса): та же доля A для других ступеней сетки STD; 0,0 = сам противоположный край IDR (на шкале отката репозитория это -1,0), 1,0 = вопрос оператора")
    ladder = {}
    for mult in LADDER:
        Rm = build(pop, mult)
        ladder[mult] = Rm
    md_lad = ["| Ступень STD с противоположной стороны | ADR 2021–2025 | ODR 2021–2025 | RDR 2021–2025 | ADR все годы | ODR все годы | RDR все годы |", "|---|--:|--:|--:|--:|--:|--:|"]
    for mult in LADDER:
        Rm = ladder[mult]
        row = []
        for pkey in ("recent", "all"):
            for s in SESSIONS:
                st = stats(Rm, mask(Rm, s, 0, pkey))
                row.append(f"{pct(st['A'], st['n']):.0f}")
        out(f"  ступень {mult:>3.1f}:  2021–2025  ADR {row[0]:>3} ODR {row[1]:>3} RDR {row[2]:>3}   |   все годы  ADR {row[3]:>3} ODR {row[4]:>3} RDR {row[5]:>3}   (A, %)")
        label = f"{mult:.1f}".replace(".", ",") + (" (край IDR)" if mult == 0 else "")
        md_lad.append(f"| {label} | " + " | ".join(row) + " |")

    # ------------------------------------------------------------------------------- 10. by year
    out("")
    out("=== 9. По годам: N сломов и A, % (оба направления)")
    for y in sorted(set(R["year"].tolist())):
        parts = []
        for s in SESSIONS:
            m = mask(R, s, 0, "all") & (R["year"] == y)
            st = stats(R, m)
            parts.append(f"{s} N {st['n']:>3} A {pct(st['A'], st['n']):5.1f} %")
        m = mask(R, None, 0, "all") & (R["year"] == y)
        st = stats(R, m)
        out(f"  {y}:  " + "   ".join(parts) + f"   | все три N {st['n']:>3} A {pct(st['A'], st['n']):5.1f} %")
    years = sorted(set(R["year"].tolist()))
    n_all = [int(mask(R, None, 0, "all")[R["year"] == y].sum()) for y in years]
    a_all = [pct(stats(R, mask(R, None, 0, "all") & (R["year"] == y))["A"], n_all[k]) for k, y in enumerate(years)]
    cell_n = [int((mask(R, s, 0, "all") & (R["year"] == y)).sum()) for s in SESSIONS for y in years]
    out(f"  у трёх сессий вместе по году: сломов от {min(n_all)} до {max(n_all)}; A от {min(a_all):.1f} до {max(a_all):.1f} %; "
        f"в одной ячейке «год × сессия» сломов от {min(cell_n)} до {max(cell_n)}")
    out("  интервалы Уилсона считают сессии независимыми; соседние сессии одного дня связаны общим режимом волатильности, поэтому "
        "реальная неопределённость чуть шире.")

    # ------------------------------------------------------------------------------- 11. markdown blocks
    out("")
    out("=== 10. Готовые таблицы для README (Markdown)")
    for title, block in (("ГЛАВНАЯ", md_main), ("РАЗБИЕНИЕ", md_part), ("ВПЕРЁД", md_fwd), ("ВРЕМЯ", md_time),
                         ("ОСТАЛОСЬ", md_left), ("СТУПЕНИ", md_lad)):
        out("")
        out(f"[{title}]")
        for line in block:
            out(line)

    LOG.write_text("\n".join(_log) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
