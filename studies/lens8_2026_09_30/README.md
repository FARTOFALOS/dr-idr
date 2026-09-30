# Lens 8: one frozen contract, the distinguishing paths, the size of the mismatches already found (2026-09-30)

The directive: [`meaning/lens/2026-09-30-linza-8.md`](../../meaning/lens/2026-09-30-linza-8.md); the answer with the plain
reading of these results: [`meaning/lens/2026-09-30-otvet-8.md`](../../meaning/lens/2026-09-30-otvet-8.md).

One scenario: a new arrival of price into a pullback area K while the DR scenario is alive, then L = +1.0 before the
DR break. Research only: the working screen, rule 10, the places and the clouds are unchanged.

| File | What |
|---|---|
| `dogovor.md` | The frozen contract in Russian, version 1.1: groups, statuses, events, same-bar rules, unknowns, the denominator of every number; section 9 says what changed from 1.0 and why; section 10 says how to read the 1.1 numbers after lens 9 and lists the candidates for 1.2 |
| `contract.py` | The contract for one path and one area, written to be read (the reference) |
| `synthetic_trace.py` | Part B: 21 synthetic paths (the directive's 13 and 8 extra edge cases), a trace row per path and area, the small-cohort numbers, the identity p_seq = p_adm × q, boundary / same-bar / re-anchoring / prefix-invariance checks → `synthetic_trace.log`; `--paths` writes the paths alone → `puti.md` |
| `puti.md` | The synthetic paths without answers, for an independent reading |
| `screen_vs_event.log` | Lens 9 (15.3), `synthetic_trace.py --screen`: for paths 3, 1, 5, 12a and 7, where the working screen's star would stand (the first entering bar's depth, at the bar's open) and where the event «the near edge reached» lies (the edge, in its M5 interval) |
| `blind_check.md` | An independent reading of `puti.md` by a second agent that saw only `dogovor.md` 1.0 and `puti.md`: its table, its 14 ambiguities of the text, and the comparison |
| `compare_blind.py` | The second reader's table against `contract.py`, row by row (1.0: one real difference; 1.1: none) |
| `tape_diagnostic.py` | Parts C and D on the tape, NQ RDR: initial state against each place (8.1), minutes already lived inside an M5 (8.2), L already reached (8.3), incomplete observations (8.4), the A/B trader card → `tape_diagnostic.log`. Its vectorised code is checked against `contract.py` on sampled similar sessions |

Read-only over `lab/.runtime/boxes_nq*` (M5) and the G3 minute tape (for two touches inside one M5 bar and for 8.2).
Only aggregates are committed; per-state records go to the git-ignored `lab/.runtime/lens8_states.json.gz`. 2026 stays
hidden. Test states are the ones already used (audit `place_arrivals.py`, lens 4): complete NQ RDR sessions of
2016–2025, every 15 minutes 10:45–15:45, confirmed with the DR intact, similar sessions from the years before the test
year by the screen's rules. The trader card was fixed before counting: 11:00, today's price in [0; +0.5), today's L not
reached.

Run from this folder with the operator's Python: `python -B synthetic_trace.py`, `python -B tape_diagnostic.py`
(about 6 minutes).
