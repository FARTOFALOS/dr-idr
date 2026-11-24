# Part 4/8 DR/IDR V1.5 · M5 STD (own fork, 393 lines). All colours are inputs; no hard-coded colours; width input applies to all lines (=2).
Entities: DR high/low (wick range of hour; RDR 09:30–10:30 / ADR / ODR) white solid, live during hour, extended through lines time (RDR→16:00, ADR→02:00, ODR→08:30); no state change on touch/break; history kept.
IDR high/low (body range) white dashed; same lifecycle.
Middle DR line black α.19 dotted (ON); middle IDR OFF.
Opening line (session open) #00BCD4 solid, extended to session end.
DR/IDR box (type IDR) during hour: up (close > open) #4CAF50 α.15, down #FF5252 α.15; border #FF5252 α.185 both (up border input changed to red). Colour flips live; frozen after hour.
STD lines: only RDR in this fork, from M5 IDR frozen at 10:30, levels IDRhigh + k·0.5·width, k=1..6 and below; white solid w2, 10:30 → 08:30 next day; no reaction to price. Labels «0.5»…«3», «-0.5»…«-3» at right end, text = STD colour (white), no bg, default size. Previous set deleted when next RDR set drawn (All OFF).
Line style is an input per DR/IDR/middle/opening/STD; label colour tied to STD colour (f_newLabel textcolor=stdLineColor) — cannot differ from line colour without code edit.
Public DR/IDR V1.5 right panes: same inputs, STD for every session.
