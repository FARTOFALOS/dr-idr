"""DR Lab · lab/live.py: the minute refresh never lets tv_fetch.mjs switch a TradingView chart (operator 30.10, 05.11).

    python -B tests/live_fetch.py

The node process is replaced by a stand-in that records its arguments; the live folder is a temporary one, so the
operator's saved candles are never touched. Checked: an automatic fetch asks without «switch», only a manual one
(«⟳ Обновить») with it; «no pane» comes back as live.NoPane (the screen keeps its last bars, the server answers
code NO_PANE); several tabs at the same minute cost one read; the once-a-day 5-minute backfill switches only when manual.
Exit code 0 = every check passed.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lab"))
import live  # noqa: E402

bad = 0


def ck(ok, what):
    global bad
    bad += not ok
    print(("  ok   " if ok else "  FAIL ") + what)


calls, answer = [], {}


def fake_tv(inst, extra=()):
    calls.append(tuple(extra))
    d = answer["need5"] if "need5" in extra and "need5" in answer else answer["main"]
    return subprocess.CompletedProcess(["node"], 0, stdout=json.dumps(d) + "\n", stderr="")


def bars(n, step=300, t0=1793800800):
    return [[t0 + (i - n + 1) * step, 100.0 + i, 102.0 + i, 99.0 + i, 101.0 + i] for i in range(n)]


live._tv = fake_tv
with tempfile.TemporaryDirectory() as tmp:
    live.LIVE = Path(tmp)
    answer["main"] = dict(success=True, feed="CME_MINI:NQ1!", interval="5", switched=False, bars=bars(400))

    print("the minute refresh")
    out = live.fetch("NQ")
    ck(calls == [()], "tv_fetch asked without «switch» " + str(calls))
    ck(len(out["bars"]) == 400 and out["switched"] is False, "bars saved, nothing switched")
    calls.clear()
    live.fetch("NQ"); live.fetch("NQ")
    ck(calls == [], "two more tabs within 20 s: no new read of TradingView " + str(calls))

    print("«⟳ Обновить»")
    live.fetch("NQ", manual=True)
    ck(calls == [("switch",)], "a manual refresh reads again and may switch " + str(calls))

    print("no 1- or 5-minute pane anywhere")
    calls.clear()
    (live.LIVE / "ym.json").unlink(missing_ok=True)
    answer["main"] = dict(success=False, code="NO_PANE", error="YM1! нет на 1 или 5 мин ни в одном окне TradingView (окон: 2); график не трогаю")
    try:
        live.fetch("YM"); ck(False, "NoPane raised")
    except live.NoPane as e:
        ck("нет на 1 или 5 мин" in str(e), "live.NoPane with the reason (" + str(e) + ")")
    ck(calls == [()] and not (live.LIVE / "ym.json").exists(), "asked without «switch»; no candles file written")

    print("the once-a-day backfill from a 1-minute pane")
    calls.clear()
    answer["main"] = dict(success=True, feed="CME_MINI:ES1!", interval="1", switched=False, bars=bars(600, step=60))
    answer["need5"] = dict(success=False, code="NO_PANE", error="no 5-minute pane")
    out = live.fetch("ES")
    ck(calls == [(), ("need5",)], "the backfill asks without «switch» " + str(calls))
    m1 = answer["main"]["bars"]
    ck(len(out["bars"]) == 121 and out["bars"][-1] == [m1[-1][0], m1[-1][1], m1[-1][2], m1[-1][3], m1[-1][4]],
       "the 1-minute pane aggregated to clock M5; the last one is the forming M5 so far (" + str(len(out["bars"])) + " M5)")
    full = [b for b in m1 if out["bars"][-2][0] <= b[0] < out["bars"][-2][0] + 300]
    ck(out["bars"][-2] == [full[0][0], full[0][1], max(b[2] for b in full), min(b[3] for b in full), full[-1][4]],
       "a closed M5 = its five minutes: open of the first, high/low of all, close of the last")
    calls.clear()
    (live.LIVE / "es_backfill.txt").unlink()
    live.fetch("ES", manual=True)
    ck(calls == [("switch",), ("need5", "switch")], "a manual refresh may switch for the backfill " + str(calls))

print("ALL GOOD" if not bad else f"{bad} check(s) failed")
sys.exit(1 if bad else 0)
