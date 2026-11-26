"""«От этой свечи» (23.5 MVP, operator 25.11.2026): the local session library the page matches against.

For every confirmed historical session (NQ/ES/YM × ADR/ODR/RDR, the built base lab/.runtime, 2026 hidden as in the
base): its side, confirmation minute, IDR width, the directed opposite DR and the M5 path on the block's common clock
as (low, high, close) in directed ticks from the IDR edge of its side — the same numbers scene24._snapshot keeps per
family member. Market data: written to lab/dist/23-5/anchor/ with a .gitignore of '*', never published.

    python -B lab/anchor235_build.py
"""
import json
from pathlib import Path

import scene21

SESS, SHIFT = scene21.SESS, scene21.SHIFT       # the same clock as scene24 (scene24 needs scipy; this script does not)


def _rows(B, i, shift):
    a = B["bars"][B["off"][i]:B["off"][i + 1]]
    return {int(r[0]) - shift: (int(r[2]), int(r[3]), int(r[4])) for r in a}       # close minute -> (h, l, c) ticks


def _directed(r, d, e):
    h, l, c = r
    return [l - e, h - e, c - e] if d == 1 else [e - h, e - l, e - c]

OUT = Path(__file__).resolve().parent / "dist" / "23-5" / "anchor"


def build(inst, session):
    B = scene21._boxes(inst)
    if B is None: return None
    start, formed, end = SESS[session]
    shift = SHIFT[session]
    grid = list(range(formed + 5, end + 1, 5))
    rows_out = []
    for i, m in enumerate(B["boxes"]):
        if m["session"] != session or m["conf"] is None: continue
        side = m["side"]
        conf = int(m["conf"]) - shift
        rows = _rows(B, i, shift)
        e = m["idr_high"] if side == 1 else m["idr_low"]
        w = int(m["idr_high"] - m["idr_low"])
        if w <= 0: continue
        opp = side * ((m["dr_low"] if side == 1 else m["dr_high"]) - e)
        path = [_directed(rows[T], side, e) if T in rows else None for T in grid]
        rows_out.append(dict(d=m["date"], wd=m["weekday"], s=side, c=conf, w=w, o=int(opp), p=path))
    return dict(instrument=inst, session=session, tick=B["tick"], grid=grid, sessions=rows_out)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ".gitignore").write_text("*\n", encoding="utf-8")
    for inst in ("NQ", "ES", "YM"):
        for session in ("RDR", "ODR", "ADR"):
            lib = build(inst, session)
            if lib is None: continue
            p = OUT / f"{inst}_{session}.json"
            p.write_text(json.dumps(lib, separators=(",", ":")), encoding="utf-8")
            print(p.name, len(lib["sessions"]), f"{p.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
