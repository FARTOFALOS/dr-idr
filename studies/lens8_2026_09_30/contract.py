"""The frozen contract of lens 8, version 1.1, for one path and one area (rules: dogovor.md; lens:
meaning/lens/2026-09-30-linza-8.md).

The reference implementation, written to be read rather than to be fast. synthetic_trace.py uses it directly;
tape_diagnostic.py checks its vectorised code against it on sampled similar sessions.

Coordinates are the session's own (conf mode of lab/scene21.py): 0 = its confirmation-side IDR edge, -1 = the opposite
IDR edge, +1 = one IDR width further in the confirmation direction. A bar is (close minute, open, top, bottom, close),
top = its extreme in the confirmation direction, bottom = against it. An area K = (lo, hi) is a closed interval below
the price, approached from above (a pullback area); L is a level above (the continuation reference).
"""
from __future__ import annotations


def clock(m):
    return f"{(m // 60) % 24:02d}:{m % 60:02d}"


def status_at(bars, t, K):
    """before / inside / beyond / unknown: the close of the bar closing exactly at t against K (bounds belong to K)."""
    lo, hi = K
    at = [b for b in bars if b[0] == t]
    if not at: return "unknown"
    x = at[0][4]
    return "before" if x > hi else ("inside" if x >= lo else "beyond")


def eligible(bars, t, L):
    """L not reached (touch counts) by any bar closed by t, from the start of the box hour."""
    return not any(b[2] >= L for b in bars if b[0] <= t)


def future(bars, t, H):
    """The M5 closes after t up to the session's last available bar (not after H); a missing bar is None."""
    have = {b[0]: b for b in bars if t < b[0] <= H}
    if not have: return []
    return [have.get(m) for m in range(t + 5, max(have) + 5, 5)]


def order_in_bar(minutes, hi, L):
    """One M5 bar touched both K (bottom <= hi) and L (top >= L): 'K' or 'L' by the first minute of each touch; None
    when both touches are in the same minute or the bar's five minute bars are not all there."""
    if not minutes or len(minutes) < 5: return None
    mK = next((m for m, top, bot in minutes if bot <= hi), None)
    mL = next((m for m, top, bot in minutes if top >= L), None)
    if mK is None or mL is None or mK == mL: return None
    return "K" if mK < mL else "L"


def classify(path, K, L=1.0):
    """One similar session at the slice path['t'] and one area K.

    path: bars (list of bars, see above), t (an M5 close minute), ou (the session's opposite DR in its own units: an M5
    close strictly beyond it is the invalidation), H (the end of the session), complete (True: the data reach the end
    of the session or the market closed early; False: the data stop earlier), minutes ({bar close: [(minute open, top,
    bottom), ...]}, only to order two touches inside one M5 bar).
    Returns the trace row: eligible, status, old (the previous screen's count), new, tau, adm, outcome, the reasons, and
    the contributions c_new / c_adm / c_q / c_seq: 1, 0, None (unknown) or '-' (not in that number's denominator).
    """
    bars, t, ou, H = path["bars"], path["t"], path["ou"], path["H"]
    complete, minutes = path.get("complete", True), path.get("minutes", {})
    lo, hi = K
    F = future(bars, t, H)
    close_of = lambda k: t + 5 * (k + 1)
    r = dict(eligible=eligible(bars, t, L), status=status_at(bars, t, K), new=None, tau=None, gap_before=False, adm=None,
             outcome=None, first=None, why="")
    # the previous screen (design 22, app.js arrivalsOf): any later bar strictly below the near edge, whatever the status
    r["old"] = any(b is not None and b[3] < hi for b in F)

    # 1. a new arrival: the first touch after t (touches before t do not count), only from 'before'; no touch after t
    #    in gap-free data that reach the end of the session = no arrival whatever the status (version 1.1)
    k = next((k for k, b in enumerate(F) if b is not None and b[3] <= hi), None)
    if r["status"] in ("inside", "beyond"):
        r["new"] = False
        r["why"] = "на t уже " + ("внутри" if r["status"] == "inside" else "за областью")
    elif k is None:
        if any(b is None for b in F) or not complete:
            r["why"] = "прихода нет в данных, но данные неполные"
        else:
            r["new"] = False
            r["why"] = "прихода не было до конца сессии"
    elif r["status"] == "unknown":
        r["why"] = "касание после t есть, но свечи в t нет: статус неизвестен"
    else:
        r["new"], r["tau"] = True, k
        r["gap_before"] = any(b is None for b in F[:k])

    # 2. admissible: the scenario is still alive at the touch (no invalidation in an earlier bar; a close beyond DR in
    #    the same bar comes after the touch inside it) and L has not been reached after t before the touch
    #    (a missing bar before the observed touch may hide an earlier touch: only events before the first gap decide)
    same_bar_L = False
    if r["new"] and not r["eligible"]:
        r["why"] = "L достигнута до t: сессия вне группы сценария"
    elif r["new"]:
        tau = r["tau"]
        g = next((k for k in range(tau) if F[k] is None), None)
        lim = tau if g is None else g
        kI = next((k for k in range(lim) if F[k][4] < ou), None)
        kL = next((k for k in range(lim) if F[k][2] >= L), None)
        if kL is not None and (kI is None or kL <= kI):
            r["adm"] = False; r["why"] = "L достигнута после t раньше прихода"
        elif kI is not None:
            r["adm"] = False; r["why"] = "отмена (закрытие за DR) раньше прихода"
        elif g is not None:
            r["why"] = "пропуск свечи до прихода: порядок с L и отменой неизвестен"
        elif F[tau][2] >= L:
            o = order_in_bar(minutes.get(close_of(tau)), hi, L)
            if o == "K": r["adm"], same_bar_L = True, True; r["why"] = "K и L в одной свече; по минутам K раньше"
            elif o == "L": r["adm"] = False; r["why"] = "K и L в одной свече; по минутам L раньше"
            else: r["why"] = "K и L в одной свече; порядок не восстановить"
        else:
            r["adm"] = True
    elif r["new"] is False:
        r["adm"] = False

    # 3. after an admissible arrival the clock restarts at tau: L before the invalidation (a touch inside a bar comes
    #    before that bar's close) and not after H; neither by H is a known non-success; missing data = unknown
    if r["adm"]:
        for k in range(r["tau"], len(F)):
            b = F[k]
            if b is None:
                r["outcome"] = None; r["why"] = "пропуск свечи до исхода"; break
            if b[2] >= L and (k > r["tau"] or same_bar_L):
                r["outcome"], r["first"] = "success", ("L", close_of(k)); break
            if b[4] < ou:
                r["outcome"], r["first"] = "invalidated", ("отмена", close_of(k)); break
        else:
            if complete: r["outcome"] = "neither"; r["first"] = ("—", None)
            else: r["outcome"] = None; r["why"] = "данные оборвались до исхода"

    # contributions: p_new, p_adm, p_seq over N_scenario (eligible sessions); q over admissible arrivals with a known
    # outcome; None = unknown: the value is taken on the known cases, the unknowns give its bounds
    if not r["eligible"]:
        r.update(c_new="-", c_adm="-", c_q="-", c_seq="-")
    else:
        r["c_new"] = None if r["new"] is None else int(r["new"])
        r["c_adm"] = None if r["adm"] is None and r["new"] is not False else int(bool(r["adm"]))
        if r["adm"]:
            r["c_q"] = None if r["outcome"] is None else int(r["outcome"] == "success")
            r["c_seq"] = r["c_q"]
        elif r["c_adm"] is None:
            r["c_q"] = r["c_seq"] = None      # unknown admissibility: could be in q's denominator, enters its bounds
        else:
            r["c_q"], r["c_seq"] = "-", 0
    return r
