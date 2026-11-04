"""The blind spot of the 23.5 local layer «Съёмы лоу» (SW-0.1), question 6 of the sharpened lens of 27.10.

SW-0.1 watches only the session's lowest low after confirmation. This counts, among the sessions it calls «лоу не
снимали», those in which a 5-minute swing low ABOVE that low was taken and the session then made a new high: a stop
under such a swing was taken although the layer says «not swept». Swing low = an M5 whose low is below the lows of the
k M5 before it and not above the lows of the k M5 after it (k = 1 or 2). The four families of tests/sweeps235_page.mjs;
needs a running 23.5 server (8735); prints counts only.
python -B studies/sweeps_blind_spot_2026_10_27/check.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "lab"))
import sweeps235_ref as R  # noqa: E402


def swept_then_high(bars, k):
    lo = [b[1] for b in bars]; hi = [b[2] for b in bars]
    for i in range(k, len(bars) - k):
        if not (lo[i] < min(lo[i - k:i]) and lo[i] <= min(lo[i + 1:i + k + 1])): continue
        j = next((j for j in range(i + k + 1, len(bars)) if lo[j] < lo[i]), None)
        if j is None: continue
        top = max(hi[:j + 1])
        if any(hi[l] > top for l in range(j + 1, len(bars))): return True
    return False


if __name__ == "__main__":
    for inst, sess, date, at in (("NQ", "RDR", "2025-12-17", 670), ("ES", "RDR", "2025-11-12", 660),
                                 ("YM", "ODR", "2025-10-20", 270), ("YM", "RDR", "2025-12-18", 660)):
        fam = R.fetch("http://127.0.0.1:8735", instrument=inst, session=sess, at=at, date=date)
        grid = fam["grid"]
        cnt = {"NONE": [0, 0, 0], "NOCONT": [0, 0, 0], "CONT": [0, 0, 0]}
        for m in fam["members"]:
            st, ev = R.session(grid, m)
            if st != "KNOWN": continue
            cat = "CONT" if any(e["cont"] is not None for e in ev) else "NOCONT" if ev else "NONE"
            bars = [(T, q[0], q[1]) for T, q in zip(grid, m["path"]) if T > m["act"]]
            cnt[cat][0] += 1
            cnt[cat][1] += int(swept_then_high(bars, 1))
            cnt[cat][2] += int(swept_then_high(bars, 2))
        print(inst, sess, date, "N", fam["N"],
              {c: f"{v[0]} sessions; a swing taken, then a new high: k=1 {v[1]}, k=2 {v[2]}" for c, v in cnt.items()})
