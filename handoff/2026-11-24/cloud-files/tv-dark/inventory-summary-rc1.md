# TradingView inventory, read-only, 24.11.2026 (first pass, from the PC)
Layout kUwtVNuo, 4 windows × 2 panes: MNQ/NQ/YM left, QQQ/ES right. Same canvas/candles in all 8 panes. UI dark, chart background light grey.
Canvas: bg solid #B8B8B8 (saved unused gradient #181C27→#131722); grid #2E2E2E α.13/.19; crosshair #131722 α.57 dashed; scale text #131722 14px on #FFFFFF; out-of-session #2962FF 92% transp; session breaks off; alert lines #B8B8B8; watermark off.
Candles: up #388E3C body+border, down #536FBD body+border, wicks #131722. Bid #2962FF α.49, ask #F7525F α.45.
DR/IDR V1.5 (M5 STD left, public right): DR #FFFFFF solid, IDR #FFFFFF dashed, middle #000000 α.19 dotted, opening #00BCD4, STD #FFFFFF, box #787B86 α.25, up box #4CAF50 α.15, down box #FF5252 α.15, borders #FF5252 α.19 — all inputs.
90 · NQ / 90 v92: cyan #00BCD4, yellow #FDD835, SMT #9C27B0, bridge #2962FF, sync labels #00E676/#F23645 text #363A45/#FFFFFF, target #FF9800, gematria #00E676/#787B86/#F23645, digits #363A45; transp left .06–.12, right .18–.6. HARD-CODED: STD labels 0.5 #2962FF, DR white, −0.25 #0097A7, −1/−2.5 black α.6, rest color.black; v92 black lines+labels L2120–2122; aqua/yellow/blue/purple 50%.
RIZ v9.7: bull/bear #FFFFFF, tier3 #787B86, 2X+ #2962FF α.15–.18, MTF lines+font #D000FF, box digits #363A45; one label color.black L1014.
RIZ BLUE v1.0: #2962FF α.05 fill/border, caption #000000 α.97.
Sessions Liquidity Tracker (closed): 34 colour inputs; level labels #000000 α.83–.86; 9:30 line #000000 3px; sessions #2962FF/#C2185B; FVG green/red/white α.12–.14; NWOG #FFCC80 α.09.
Drawings 1,173: fib 183 (181 «dr»: −10…10 w2 all #000000 except 0.5 #2962FF, −0.25 #0097A7, −1/−2.5 black α.6, labels 16px); rectangle 351 (top #EF00FB fill α.10); trend 305 (top #000000 α.61); vertical 179 (#E65100 2px ×80); circle 89, hray 34, gann 11, R/R 20.
Fib templates: «dr», «retreysment» (w1), «50%», «FIB».
Files on PC: C:\Users\Admin\Claude\tv-colors-inventory\ (SUMMARY.md, json, pine\*.pine, screenshots).

## Part 1/8 additions (full SUMMARY)
Tabs: tab1 MNQZ2026 5 | QQQ 1; tab2 NQ1! 5 | QQQ 1; tab3 YM1! 10 | ES1! 5; tab4 NQ1! 21 | QQQ 1.
Pane separator #2A2E39; scale line invisible; axis highlight #2962FF α.25; drawing axis label #2962FF; session highlight pre-market #FF9800 92%, post #2962FF 92%, night #D500F9 92%; legend bg transp 55%.
SLT inputs (visible instance): in_26 #2962FF α.75 (def #4CAF50) 3px; in_31 #C2185B 2px; in_34 #898989 α.78 labels Large; in_38 #36383E α.5; in_42 #429DFF α.26; weekly dividers #FF9800; Levels: in_57 #000000 α.86 (def white) Large 3px; in_60 #880E4F α.76 3px; in_64 #000 α.83 (def white) 4px; in_67 #2195F3 α.51 4px; in_71 white α.83; in_74 #9B27B0 α.51; in_78 white; in_81 #55D341 α.46; in_85 white; in_88 #55D341 α.46; in_92 #000 α.83 (def white) 3px; in_95 #000 (def #DDFF46 α.46) 3px; in_99 #000 α.83 (def white) 2px; in_102 #FF4646 α.56; in_106 white; in_109 #FF4646 α.56; FVG EQ white α.47; bull FVG #4CAF4F α.14; bear FVG #FF5252 α.12; mitigated FVG white α.12; NWOG #FFCC80 α.09 border none, EQ white α.34 dashed; NDOG #4A4A4A α.10, EQ white α.84 dashed; MSS white/#FF5252 (off).
RIZ BLUE: fill+border #2962FF α.054, caption #000000 α.97; L419 duration-label box transparent, text lbl_col.
RIZ v9.7: bull/bear fill+border #FFFFFF (transparency set by separate inputs bull_tr etc.), T3 #787B86, 2X+ #2962FF α.18/.15, MTF #D000FF, box digits #363A45; L1014 text color.black.
DR/IDR M5 STD: DR white solid, IDR white dashed, middle #000 α.19 dotted, opening #00BCD4, STD white, box bg #787B86 α.25, up #4CAF50 α.15, down #FF5252 α.15, both borders #FF5252 α.185. No hard-coded colours.
90 NQ: intact cyan #00BCD4 α.09, broken yellow #FDD835 α.12, SMT purple #9C27B0 α.09, bridge #2962FF α.07, marker α.06, SMT line #9C27B0, SMT text #363A45 on #9C27B0, sync ▲ #00E676 α.8 text #363A45, ▼ #F23645 α.8 text white, target #FF9800, gematria green #00E676 / grey #787B86 / red #F23645, digit #363A45. Hard: L192–198 yellow50/blue50/purple30/aqua50; L949/1012 cycle-extreme boxes border aqua50 bg colorCyan; gematria active α70; L2030 ink: 0.5 #2962ff, regular DR white, −0.25 #0097a7, −1/−2.5 black α40transp, else black; L2032 label size 12.
90 v92: intact α.18, broken α.18, SMT α.35, bridge α.35, marker α.6; hard L2083/2085 ink, L2120 line.new color.black, L2122 label text black small.
Drawings: VertLine 179 (80× #E65100 w2 text white α.37); TrendLine 305 (23× black α.61 text black α.83); Circle 89 (13× bg #0097A7 α.37 text black); Rectangle 351 (79× #EF00FB α.31 bg α.10 mid line, text black); HorzRay 34 (6× black w2); RR long 10 #787B86 text white; RR short 10 text black α.79; Gann 11 #153899; Path 1 #089981 w4.
Fib variants: 181× dr; 1× retreysment w1 dashed 10px; 1× retreysment w2.
Templates 50% and FIB colourful (see SUMMARY on PC).
