"""Lens 10, step P2: the time-first field through its passport (pasport-polya.md) on synthetic paths, tests T1-T8 of the
specification and a few edge cases. Synthetic data only; bars are (close minute, open, top, bottom, close) in a
session's own units. The slice t = 10:45 (645), so the first future column is the bar 10:45-10:50 (close 650).
python -B synthetic_field.py  ->  synthetic_field.log
"""
from __future__ import annotations

from pathlib import Path

from field import V_area, bin_of, field, first_reach, gap_cross, session_cells, session_mass

HERE = Path(__file__).resolve().parent
T = 645


def clock(m):
    return f"{(m // 60) % 24:02d}:{m % 60:02d}"


def path(bars, close_at_t=0.30, complete=True):
    return dict(bars=[(T, close_at_t, close_at_t, close_at_t, close_at_t)] + bars, complete=complete)


def cells_of(p, H):
    return session_cells(p, T, H)[0]


def show(cells):
    by = {}
    for k, j in sorted(cells, key=lambda x: (x[1], x[0])): by.setdefault(j, []).append(k)
    return "; ".join(f"{clock(j)}: " + ",".join(f"{k / 10:+.1f}" for k in ks) for j, ks in by.items())


def run():
    R = []
    add = lambda name, expect, got, ok: R.append((name, expect, got, ok))

    # T1: a fast wide pass, then higher
    p = path([(650, .20, .80, .20, .75), (655, .90, 1.00, .90, .95)])
    c = cells_of(p, 655)
    col1 = {k for k, j in c if j == 650}; col2 = {k for k, j in c if j == 655}
    add("T1 быстрый проход", "+0,2…+0,8 только в 10:50; в 10:55 только +0,9 и +1,0", show(c),
        col1 == set(range(2, 9)) and col2 == {9, 10} and not (col2 & set(range(2, 9))))

    # T2: persistence around +0.5...+0.6 for four columns
    p = path([(650, .52, .58, .51, .55), (655, .55, .59, .52, .53), (660, .53, .57, .51, .56), (665, .56, .59, .54, .58)])
    c = cells_of(p, 665)
    add("T2 устойчивость", "ячейка +0,5 в четырёх соседних колонках", show(c), {j for k, j in c if k == 5} == {650, 655, 660, 665})

    # T3: a return after three columns; first reach stays the first
    p = path([(650, .45, .55, .45, .50), (655, .44, .44, .30, .32), (660, .32, .35, .20, .25), (665, .25, .40, .25, .38),
              (670, .42, .52, .42, .50)])
    c = cells_of(p, 670)
    fr = first_reach(p, T, 670, (0.5, 0.6))
    add("T3 возврат", "+0,5 в 10:50 и снова в 11:10; первое достижение — 10:50", show(c) + f" | первое достижение {clock(fr)}",
        {j for k, j in c if k == 5} == {650, 670} and fr == 650)

    # T4: the same close, different ranges
    a, b = path([(650, .38, .45, .35, .40)]), path([(650, .10, .80, .00, .40)])
    ca, cb = cells_of(a, 650), cells_of(b, 650)
    add("T4 одно закрытие, разные диапазоны", "поле различает; по закрытию обе в +0,4", f"A {show(ca)} | B {show(cb)}",
        ca != cb and bin_of(.40) == 4 and {k for k, _ in ca} == {3, 4} and {k for k, _ in cb} == set(range(0, 9)))

    # T5: the same range, different closes
    a, b = path([(650, .20, .60, .20, .25)]), path([(650, .20, .60, .20, .55)])
    add("T5 один диапазон, разные закрытия", "одинаковые клетки; закрытие — отдельная характеристика",
        f"A {show(cells_of(a, 650))} | B {show(cells_of(b, 650))}", cells_of(a, 650) == cells_of(b, 650))

    # T6: a gap through a bin
    p = path([(650, .25, .30, .22, .28), (655, .42, .50, .42, .47)])
    c, g = cells_of(p, 655), gap_cross(p, T, 655)
    add("T6 гэп через ячейку", "+0,3 без голоса; gap_cross (+0,3, 10:55)", show(c) + " | gap_cross " + show(g),
        (3, 655) not in c and g == {(3, 655)})

    # T7: one session, many cells; the contour's mass counts the session once
    p = path([(650, .10, .55, .10, .50)]); q = path([(650, .90, .95, .90, .92)])
    c = cells_of(p, 650)
    C = {(k, 650) for k in range(1, 6)}
    V, _, N = field([p, q], T, 650)
    add("T7 одна сессия — много клеток", "5 клеток; масса контура 1 сессия из 2 (0,5), а не сумма клеток 2,5",
        f"клеток {len(c)}, сумма клеток контура {sum(V.get(x, 0) for x in C):.1f}, масса {session_mass([p, q], T, 650, C):.1f}",
        len(c) == 5 and abs(session_mass([p, q], T, 650, C) - 0.5) < 1e-12)

    # T8: the same position at t, a different path; the base matcher (price at t) keeps both
    a = dict(bars=[(630, .20, .30, .10, .25), (640, .25, .40, .20, .35), (T, .30, .32, .18, .20)] + [(650, .20, .25, .10, .15)])
    b = dict(bars=[(630, .20, .60, .10, .55), (640, .55, .58, .30, .35), (T, .30, .32, .18, .20)] + [(650, .20, .25, .10, .15)])
    matcher = lambda p_: abs([x for x in p_["bars"] if x[0] == T][0][4] - 0.20) <= 0.25        # price at t only
    had05 = lambda p_: any(x[2] >= 0.5 for x in p_["bars"] if x[0] <= T)                        # a path feature
    base = [x for x in (a, b) if matcher(x)]
    cond = [x for x in base if had05(x)]
    add("T8 одна цена на t, разный путь", "базовый подбор берёт обе; признак «+0,5 уже была» делит, только если включён",
        f"базовая группа {len(base)}, условная (с признаком) {len(cond)}", len(base) == 2 and len(cond) == 1)

    # E1: an early end of the session (the market closed): later columns are a known «did not reach», not unknown
    p = path([(650, .30, .40, .25, .35), (655, .35, .38, .30, .32)])
    V, unk, N = field([p], T, 665)
    add("Д1 ранний конец сессии", "после 10:55 голосов нет, неизвестных нет", f"колонок с голосами {sorted({clock(j) for _, j in V})}, неизвестных {sum(unk.values())}",
        {j for _, j in V} == {650, 655} and sum(unk.values()) == 0)

    # E2: a missing bar inside a running session: that column is unknown for this session
    p1 = path([(650, .30, .40, .25, .35), (660, .35, .38, .30, .32)]); p2 = path([(650, .30, .40, .25, .35), (655, .35, .45, .33, .40), (660, .40, .42, .36, .40)])
    V, unk, N = field([p1, p2], T, 660)
    n = round(V.get((4, 655), 0) * N)
    add("Д2 пропуск свечи", "клетка (+0,4, 10:55): известно 1 из 2, неизвестно 1 → масса 0,5, диапазон [0,5; 1,0]",
        f"n {n}, u {unk[655]}, N {N}", n == 1 and unk[655] == 1 and N == 2)

    # E3: a wide area counts a session once per column, and once per window
    p = path([(650, .20, .80, .20, .70), (655, .70, .75, .60, .65)]); q = path([(650, .90, .95, .90, .92), (655, .92, .96, .88, .95)])
    add("Д3 широкая область", "V(K,10:50) = 1/2 при 7 задетых ячейках; V(K, окно) = 1/2",
        f"V(K,10:50) {V_area([p, q], T, 655, (0.2, 0.8), [650]):.2f}, V(K,окно) {V_area([p, q], T, 655, (0.2, 0.8)):.2f}",
        V_area([p, q], T, 655, (0.2, 0.8), [650]) == 0.5 and V_area([p, q], T, 655, (0.2, 0.8)) == 0.5)

    # E4: a level off the grid is not rounded: K = [-0.75; -0.25] with a bar down to -0.22 does not reach it
    p = path([(650, .10, .12, -.22, -.20)], close_at_t=0.10)
    add("Д4 уровень не на сетке", "низ −0,22 не достигает −0,25, хотя ячейка −0,3 [−0,3; −0,2) задета",
        f"V(K) {V_area([p], T, 650, (-0.75, -0.25)):.0f}, ячейка −0,3 {'задета' if (-3, 650) in cells_of(p, 650) else 'нет'}",
        V_area([p], T, 650, (-0.75, -0.25)) == 0 and (-3, 650) in cells_of(p, 650))

    # E5: the first column is the bar that opens at t
    p = path([(650, .30, .35, .28, .33)])
    add("Д5 первая колонка", "t = 10:45, первая колонка — свеча 10:45–10:50 (закрытие 10:50)", show(cells_of(p, 650)),
        {j for _, j in cells_of(p, 650)} == {650})
    return R


if __name__ == "__main__":
    R = run()
    out = ["Поле time-first на синтетических путях: тест | ожидание | получено | итог"]
    for name, expect, got, ok in R:
        out.append(f"[{'ok' if ok else 'СБОЙ'}] {name} | {expect} | {got}")
    out.append(f"Итого: {sum(ok for *_, ok in R)} из {len(R)}")
    text = "\n".join(out)
    (HERE / "synthetic_field.log").write_text(text + "\n", encoding="utf-8")
    print(text)
