"""DR-LAB-PB-0.1 · does a pullback constellation say more than «price was here»? (21.10.2026, aggregates only)

For every constellation of the candidate «Откаты до обновления» on a scene and scale, three shares of the same family N:
  L      sessions with an established pullback bottom L in the zone's cells (the candidate's own share, lower bound);
  visit  sessions whose price visited those cells at all: a closed M5 after the own activation whose directed range
         meets the cell's price band in the cell's own 15-minute column (the same test as the candidate's «today»);
  low    sessions that made an M5 low there (the M5's directed low inside a cell of the zone), any M5 after activation.
If L ≈ visit, the pullback map repeats the visitation density; the ratio L / visit says how selective the event is.
Nothing is written but the printed aggregates.

    python -B studies/pb_vs_visits_2026_10_21.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lab"))
import pullbacks24 as P  # noqa: E402
import scene24 as S  # noqa: E402

SCENES = [("NQ", "RDR", 670, "2025-12-17", "auto", "weekday"), ("NQ", "RDR", 670, "2025-12-17", "auto", "all"),
          ("ES", "ODR", 300, "2025-11-12", "auto", "weekday"), ("YM", "ADR", -100, "2025-10-08", "auto", "weekday")]


def shares(H, fam, zone):
    formed = S.SESS[fam["key"]["session"]][1]
    grid, cs = H["grid"], {tuple(c) for c in zone["cell_mask"]}
    cols = {}
    for k, b in cs: cols.setdefault(b, set()).add(k)
    visit = low = 0
    for s in H["sessions"]:
        w, v, lw = s["w"], False, False
        for j in range(s["act_i"] + 1, len(grid)):
            q = s["bars"][j]
            if q is None: continue
            ks = cols.get(P.tcell(grid[j] - 5, formed))
            if not ks: continue
            if any(10 * q[2] < (k + 1) * w and 10 * q[1] >= k * w for k in ks): v = True
            if P.cell(q[2], w) in ks: lw = True
        visit += v; low += lw
    return zone["n_known"], visit, low


def main():
    for args in SCENES:
        st, fam, B, day, proof = P.build(*args)
        if st != "OK":
            print(args, st); continue
        H = P.history(fam, B)
        N = fam["N"]
        print(f"\n{args[0]} {args[1]} {args[3]} {args[2] // 60:02d}:{args[2] % 60:02d} · {args[5]} · N = {N}")
        print("scale zone  window       L%    visit%  low%   L/visit")
        for s in P.SCALES:
            for z in H["maps"][s]["zones"]:
                L, v, lw = shares(H, fam, z)
                t0, t1 = z["time_start"], z["time_end"]
                print(f"{s:>5} {z['label']:<4}  {t0 // 60:02d}:{t0 % 60:02d}-{t1 // 60:02d}:{t1 % 60:02d}  "
                      f"{100 * L / N:5.1f}  {100 * v / N:6.1f}  {100 * lw / N:5.1f}  {L / v if v else float('nan'):6.2f}")


if __name__ == "__main__":
    main()
