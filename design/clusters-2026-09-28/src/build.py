"""Assembles the three .dc.html artboards and project/canvas.json of the DR Lab cluster mockups (synthetic data only).

python build.py            -> ../built/project/{Main,Summary,Projections}.dc.html and canvas.json
"""
import datetime as dt
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'built', 'project')
os.makedirs(OUT, exist_ok=True)
rd = lambda n: open(os.path.join(HERE, n), encoding='utf-8').read()


def sub(s, **kw):
    for k, v in kw.items():
        s = s.replace('%' + k + '%', str(v))
    return s


ICON_MENU = '<svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M3 5h12M3 9h12M3 13h12"></path></svg>'
ICON_REFRESH = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M13.5 8a5.5 5.5 0 1 1-1.6-3.9"></path><path d="M13.5 2.5v3h-3"></path></svg>'
ICON_REWIND = '<svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor"><path d="M7 3.2v7.6L2 7zM12.5 3.2v7.6L7.5 7z"></path></svg>'
ICON_MINUS = '<svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M2 6h8"></path></svg>'
ICON_PLUS = '<svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M2 6h8M6 2v8"></path></svg>'
ICON_RESET = '<svg width="13" height="13" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 7a4.5 4.5 0 1 0 1.3-3.2"></path><path d="M2.5 2v2.5H5"></path></svg>'
ICON_CLOSE = '<svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M2 2l8 8M10 2l-8 8"></path></svg>'

SEG = 'display: flex; gap: 2px; padding: 3px; background: #161A21; border-radius: 7px'
SEGBTN = 'height: 26px; padding: 0px 10px; border: 0px; border-radius: 5px; font-family: inherit; font-size: 13px; font-weight: 600; cursor: pointer; white-space: nowrap'

TOOLBAR = '''<div style="position: absolute; left: 0px; top: 0px; width: 1920px; height: 44px; box-sizing: border-box; display: flex; align-items: center; gap: 12px; padding: 0px 12px; background: #0F1216; border-bottom: 1px solid #1E232B">
<button type="button" aria-label="Меню исследования" style="width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; padding: 0px; background: transparent; border: 0px; border-radius: 6px; color: #B2B5BE; cursor: pointer">%ICON_MENU%</button>
<div style="%SEG%"><sc-for list="{{tb.inst}}" as="b" hint-placeholder-count="3"><button type="button" style="%SEGBTN%; background: {{b.bg}}; color: {{b.c}}">{{b.t}}</button></sc-for></div>
<div style="%SEG%"><sc-for list="{{tb.sess}}" as="b" hint-placeholder-count="3"><button type="button" onClick="{{b.click}}" onMouseEnter="{{b.enter}}" onMouseLeave="{{b.leave}}" style="%SEGBTN%; background: {{b.bg}}; color: {{b.c}}; display: flex; align-items: center; gap: 6px"><span style="width: 6px; height: 6px; border-radius: 3px; background: {{b.dot}}"></span><span>{{b.t}}</span></button></sc-for></div>
<span style="font-size: 13px; color: #9598A1; white-space: nowrap">{{tb.date}}</span>
<div style="width: 1px; height: 22px; background: #252A33"></div>
<span style="font-size: 12px; color: #8F939E; white-space: nowrap">Пример</span>
<div style="%SEG%"><sc-for list="{{tb.scenes}}" as="b" hint-placeholder-count="3"><button type="button" onClick="{{b.click}}" style="%SEGBTN%; background: {{b.bg}}; color: {{b.c}}">{{b.t}}</button></sc-for></div>
<div style="flex-grow: 1"></div>
<div style="display: flex; gap: 6px"><sc-for list="{{tb.layers}}" as="l" hint-placeholder-count="3"><button type="button" onClick="{{l.click}}" style="height: 28px; padding: 0px 10px; border: {{l.bd}}; border-radius: 6px; background: {{l.bg}}; color: {{l.c}}; font-family: inherit; font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 7px; white-space: nowrap"><span style="width: 11px; height: 10px; border-radius: 2px; background: {{l.sw}}; opacity: {{l.swop}}; clip-path: {{l.clip}}"></span><span>{{l.t}}</span></button></sc-for></div>
<div style="width: 1px; height: 22px; background: #252A33"></div>
<sc-if value="{{tb.live}}" hint-placeholder-val="{{true}}"><div style="display: flex; align-items: center; gap: 8px; font-size: 13px; color: #D1D4DC; white-space: nowrap"><span style="width: 8px; height: 8px; border-radius: 4px; background: #089981; box-shadow: 0 0 0 3px rgba(8,153,129,0.22)"></span><span style="font-weight: 600">LIVE</span><span style="color: #9598A1">{{tb.clock}}</span></div></sc-if>
<sc-if value="{{tb.replay}}" hint-placeholder-val="{{false}}"><div style="display: flex; align-items: center; gap: 8px; height: 28px; box-sizing: border-box; padding: 0px 3px 0px 10px; border: 1px solid #F7C948; border-radius: 6px; font-size: 13px; color: #F7C948; white-space: nowrap">%ICON_REWIND%<span>Повтор</span><span style="font-weight: 600">{{tb.rpText}}</span><button type="button" onClick="{{tb.toLive}}" style="height: 22px; padding: 0px 9px; border: 0px; border-radius: 4px; background: #F7C948; color: #0B0D10; font-family: inherit; font-size: 12px; font-weight: 700; cursor: pointer">В live</button></div></sc-if>
<button type="button" aria-label="Обновить из TradingView" style="width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; padding: 0px; background: transparent; border: 0px; border-radius: 6px; color: #B2B5BE; cursor: pointer">%ICON_REFRESH%</button>
</div>'''

DENSITY = '''<svg width="%PW%" height="%PH%" viewBox="0 0 %PW% %PH%" style="position: absolute; left: 0px; top: 0px; pointer-events: none">
<g opacity="{{ds.A.op}}"><path d="{{ds.A.p3}}" fill="{{ds.A.c3}}"></path><path d="{{ds.A.p2}}" fill="{{ds.A.c2}}"></path><path d="{{ds.A.sp}}" fill="none" stroke="{{ds.A.sc}}" stroke-width="1.2"></path><path d="{{ds.A.p1}}" fill="{{ds.A.c1}}"></path><path d="{{ds.A.p0}}" fill="{{ds.A.c0}}"></path></g>
<g opacity="{{ds.B.op}}"><path d="{{ds.B.p3}}" fill="{{ds.B.c3}}"></path><path d="{{ds.B.p2}}" fill="{{ds.B.c2}}"></path><path d="{{ds.B.sp}}" fill="none" stroke="{{ds.B.sc}}" stroke-width="1.2"></path><path d="{{ds.B.p1}}" fill="{{ds.B.c1}}"></path><path d="{{ds.B.p0}}" fill="{{ds.B.c0}}"></path></g>
</svg>'''

CHART = '''<div onClick="{{m.bg}}" style="position: absolute; left: 0px; top: 0px; width: %PW%px; height: %PH%px"></div>
<sc-for list="{{boxes}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: {{e.w}}px; height: {{e.h}}px; background: {{e.bg}}; opacity: {{e.op}}; pointer-events: none"></div></sc-for>
<sc-for list="{{grid}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: {{e.w}}px; height: 1px; background: {{e.bg}}; pointer-events: none"></div></sc-for>
<sc-for list="{{gridT}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; transform: translateX(-100%); padding: 0px 3px; border-radius: 2px; background: rgba(11,13,16,0.86); font-size: 11px; line-height: 14px; color: #A3A8B3; pointer-events: none">{{e.t}}</div></sc-for>
<sc-for list="{{lines}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: {{e.w}}px; height: {{e.h}}px; background: {{e.bg}}; opacity: {{e.op}}; box-shadow: {{e.sh}}; pointer-events: none"></div></sc-for>
<sc-for list="{{lhits}}" as="e" hint-placeholder-count="0"><div onMouseEnter="{{e.enter}}" onMouseLeave="{{e.leave}}" onClick="{{e.click}}" style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: {{e.w}}px; height: {{e.h}}px"></div></sc-for>
%DENSITY%
<sc-for list="{{cells}}" as="e" hint-placeholder-count="0"><div onMouseEnter="{{e.enter}}" onMouseLeave="{{e.leave}}" onClick="{{e.click}}" style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: {{e.w}}px; height: {{e.h}}px; cursor: pointer"></div></sc-for>
<svg width="%PW%" height="%PH%" viewBox="0 0 %PW% %PH%" style="position: absolute; left: 0px; top: 0px; pointer-events: none"><path d="{{hlp.fill}}" fill="{{hlp.fc}}"></path><path d="{{hlp.line}}" fill="none" stroke="{{hlp.lc}}" stroke-width="{{hlp.w}}"></path></svg>
<sc-for list="{{hl}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: {{e.w}}px; height: {{e.h}}px; box-sizing: border-box; border: {{e.bd}}; background: {{e.bg}}; border-radius: 2px; pointer-events: none"></div></sc-for>
<div style="position: absolute; left: {{priceLine.x}}px; top: {{priceLine.y}}px; width: {{priceLine.w}}px; height: 1px; background: {{priceLine.bg}}; opacity: {{priceLine.op}}; pointer-events: none"></div>
<sc-for list="{{wicks}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: 1px; height: {{e.h}}px; background: {{e.bg}}; opacity: {{e.op}}; pointer-events: none"></div></sc-for>
<sc-for list="{{bodies}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: {{e.w}}px; height: {{e.h}}px; background: {{e.bg}}; opacity: {{e.op}}; outline: {{e.bd}}; pointer-events: none"></div></sc-for>
<sc-for list="{{chits}}" as="e" hint-placeholder-count="0"><div onClick="{{e.click}}" style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: {{e.w}}px; height: {{e.h}}px; cursor: pointer"></div></sc-for>
<sc-for list="{{pills}}" as="e" hint-placeholder-count="0"><div onMouseEnter="{{e.enter}}" onMouseLeave="{{e.leave}}" onClick="{{e.click}}" style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: {{e.w}}px; height: 18px; box-sizing: border-box; border-radius: 9px; background: {{e.bg}}; border: {{e.bd}}; opacity: {{e.op}}; color: #FFFFFF; font-size: 11px; font-weight: 700; line-height: 16px; text-align: center; white-space: nowrap; cursor: default">{{e.t}}</div></sc-for>
%OVER%
<sc-for list="{{vlines}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: 1px; height: {{e.h}}px; background: {{e.bg}}; opacity: {{e.op}}; pointer-events: none"></div></sc-for>
<sc-for list="{{glines}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: {{e.w}}px; height: {{e.h}}px; background: {{e.bg}}; pointer-events: none"></div></sc-for>
<sc-for list="{{xh}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: {{e.w}}px; height: {{e.h}}px; background: {{e.bg}}; pointer-events: none"></div></sc-for>
<sc-for list="{{slabels}}" as="e" hint-placeholder-count="0"><div onClick="{{e.click}}" onMouseEnter="{{e.enter}}" onMouseLeave="{{e.leave}}" style="position: absolute; left: {{e.x}}px; top: %SLY%px; height: 22px; box-sizing: border-box; padding: 0px 8px; border-radius: 5px; background: {{e.bg}}; display: flex; align-items: center; gap: 6px; cursor: pointer; white-space: nowrap"><span style="width: 6px; height: 6px; border-radius: 3px; background: #089981; display: {{e.dot}}"></span><span style="font-size: 12px; font-weight: {{e.fw}}; color: {{e.c}}">{{e.t}}</span><span style="font-size: 11.5px; color: #8F939E">{{e.sub}}</span></div></sc-for>
<div style="position: absolute; left: %ZX%px; top: %ZY%px; display: flex; gap: 4px">
<button type="button" aria-label="Отдалить" onClick="{{zoomOut}}" style="width: 30px; height: 28px; display: flex; align-items: center; justify-content: center; padding: 0px; border: 1px solid #2B313C; border-radius: 6px; background: rgba(22,26,33,0.92); color: #B2B5BE; cursor: pointer">%ICON_MINUS%</button>
<button type="button" aria-label="Приблизить" onClick="{{zoomIn}}" style="width: 30px; height: 28px; display: flex; align-items: center; justify-content: center; padding: 0px; border: 1px solid #2B313C; border-radius: 6px; background: rgba(22,26,33,0.92); color: #B2B5BE; cursor: pointer">%ICON_PLUS%</button>
<button type="button" aria-label="Вся сессия" onClick="{{reset}}" style="width: 30px; height: 28px; display: flex; align-items: center; justify-content: center; padding: 0px; border: 1px solid #2B313C; border-radius: 6px; background: rgba(22,26,33,0.92); color: #B2B5BE; cursor: pointer">%ICON_RESET%</button>
</div>'''

SCALE = '''<div style="position: absolute; left: %XS%px; top: 0px; width: %SW%px; height: %PH%px; background: #0B0D10; border-left: 1px solid #262B34"></div>
<sc-for list="{{ticks}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: %XS10%px; top: {{e.y}}px; font-size: 12px; line-height: 16px; color: #B2B5BE; pointer-events: none">{{e.t}}</div></sc-for>
<sc-for list="{{tags}}" as="e" hint-placeholder-count="0"><div onMouseEnter="{{e.enter}}" onMouseLeave="{{e.leave}}" onClick="{{e.click}}" style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; height: {{e.h}}px; box-sizing: border-box; padding: 0px 6px; display: flex; flex-direction: column; justify-content: center; background: {{e.bg}}; color: {{e.fg}}; border: {{e.bd}}; border-radius: 3px; font-size: {{e.fs}}; font-weight: {{e.fw}}; line-height: 15px; white-space: nowrap; cursor: default"><div style="display: flex; gap: 6px; align-items: baseline"><span style="display: {{e.nd}}; font-size: 11px; font-weight: 700; opacity: 0.8">{{e.name}}</span><span>{{e.price}}</span></div><div style="display: {{e.sd}}; font-size: 11px; opacity: 0.85">{{e.sub}}</div></div></sc-for>'''

AXIS = '''<div style="position: absolute; left: 0px; top: %AX%px; width: %W%px; height: 28px; background: #0B0D10; border-top: 1px solid #262B34"></div>
<sc-for list="{{tlabels}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{e.x}}px; top: %AX6%px; transform: translateX(-50%); font-size: 14px; line-height: 16px; color: #D1D4DC; white-space: nowrap; pointer-events: none">{{e.t}}</div></sc-for>
<sc-for list="{{ttags}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{e.x}}px; top: %AX4%px; transform: translateX(-50%); height: 20px; padding: 0px 7px; border-radius: 3px; background: {{e.col}}; color: {{e.fg}}; font-size: 12.5px; font-weight: 600; line-height: 20px; white-space: nowrap; pointer-events: none">{{e.t}}</div></sc-for>'''

BAND = '''<div onMouseMove="{{sb.move}}" onMouseLeave="{{sb.leave}}" onClick="{{sb.click}}" style="position: absolute; left: 0px; top: %PH%px; width: %PW%px; height: %BH%px; box-sizing: border-box; background: #0D0F13; border-top: 1px solid #1B1F26; cursor: col-resize">
<div style="position: absolute; left: 0px; top: %MID%px; width: %PW%px; height: 1px; background: #20252E; pointer-events: none"></div>
<sc-for list="{{band}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: {{e.w}}px; height: {{e.h}}px; border-radius: 1px; background: {{e.bg}}; pointer-events: none"></div></sc-for>
%BANDTEXT%
<div style="position: absolute; left: {{bandMark.x}}px; top: 0px; width: 2px; height: %BH%px; background: {{bandMark.bg}}; pointer-events: none"></div>
</div>'''

BANDTEXT = '''<sc-for list="{{bandT}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; transform: translateX(-50%); font-size: 11px; line-height: 13px; color: {{e.c}}; white-space: nowrap; pointer-events: none">{{e.t}}</div></sc-for>'''

KEYLINE = '''<div style="color: #9AA1AD; font-size: 12px; line-height: 16px">{{dkey}}</div>'''

STATELINE = '''<sc-if value="{{hasState}}" hint-placeholder-val="{{true}}"><div style="color: #B2B5BE; font-size: 12.5px; line-height: 16px">{{stateLine}}</div></sc-if>'''

LEGEND = '''<div style="position: absolute; left: 6px; top: 6px; display: flex; flex-direction: column; gap: 3px; padding: 4px 8px 5px 8px; border-radius: 6px; background: rgba(11,13,16,0.8); pointer-events: none; font-size: 13px; line-height: 17px; white-space: nowrap">
<div style="display: flex; align-items: center; gap: 8px"><span style="color: #D1D4DC; font-weight: 600">NQ1! · 5 · <span>{{act}}</span></span><sc-for list="{{chips}}" as="c" hint-placeholder-count="1"><span style="height: 18px; padding: 0px 7px; border-radius: 9px; background: {{c.bg}}; color: #FFFFFF; font-size: 11.5px; font-weight: 700; display: inline-flex; align-items: center">{{c.t}}</span></sc-for></div>
<div style="display: flex; gap: 10px; color: #9598A1"><span>O <span style="color: {{lg.col}}">{{lg.o}}</span></span><span>H <span style="color: {{lg.col}}">{{lg.h}}</span></span><span>L <span style="color: {{lg.col}}">{{lg.l}}</span></span><span>C <span style="color: {{lg.col}}">{{lg.c}}</span></span><span style="color: {{lg.col}}">{{lg.ch}}</span><span>{{lg.when}}</span></div>
%STATE%
%KEY%
</div>'''

NAV = '''<div onClick="{{nav.click}}" style="position: absolute; left: 0px; top: 954px; width: %NW%px; height: 46px; background: #0D0F13; border-top: 1px solid #1E232B; cursor: pointer; overflow: hidden">
<sc-for list="{{nav.segs}}" as="e" hint-placeholder-count="3"><div style="position: absolute; left: 0px; top: 0px"><div onClick="{{e.click}}" onMouseEnter="{{e.enter}}" onMouseLeave="{{e.leave}}" style="position: absolute; left: {{e.x}}px; top: 4px; width: {{e.w}}px; height: 38px; box-sizing: border-box; border-radius: 5px; background: {{e.bg}}; border: {{e.bd}}; cursor: pointer"></div><div style="position: absolute; left: {{e.wx}}px; top: 4px; width: {{e.ww}}px; height: 38px; border-radius: 5px 0px 0px 5px; background: rgba(255,255,255,0.05); pointer-events: none"></div><div style="position: absolute; left: {{e.x}}px; top: 6px; padding-left: 8px; display: flex; gap: 6px; font-size: 11.5px; line-height: 14px; white-space: nowrap; pointer-events: none"><span style="font-weight: 700; color: {{e.c}}">{{e.t}}</span><span style="color: #8F939E">{{e.sub}}</span></div></div></sc-for>
<svg width="%NW%" height="46" viewBox="0 0 %NW% 46" style="position: absolute; left: 0px; top: 0px; pointer-events: none"><path d="{{nav.spark}}" fill="none" stroke="rgba(178,181,190,0.6)" stroke-width="1"></path></svg>
<div style="position: absolute; left: {{nav.fx}}px; top: 2px; width: {{nav.fw}}px; height: 42px; box-sizing: border-box; border: 1px solid rgba(209,212,220,0.6); border-radius: 4px; background: rgba(209,212,220,0.06); pointer-events: none"></div>
<div style="position: absolute; left: {{nav.nowx}}px; top: 4px; width: 2px; height: 38px; background: #089981; pointer-events: none"></div>
<div style="position: absolute; left: {{nav.mx}}px; top: 4px; width: 2px; height: 38px; background: #F7C948; pointer-events: none"></div>
</div>'''

CARD = '''<sc-if value="{{card.show}}" hint-placeholder-val="{{false}}"><div style="position: absolute; left: {{card.x}}px; top: {{card.y}}px; width: 262px; box-sizing: border-box; padding: 10px 12px 11px 12px; background: rgba(15,18,22,0.97); border: 1px solid #2B313C; border-top: 2px solid {{card.hue}}; border-radius: 8px; box-shadow: 0 12px 32px rgba(0,0,0,0.6); pointer-events: {{card.pe}}">
<div style="display: flex; align-items: center; gap: 8px; min-height: 22px"><span style="flex-grow: 1; font-size: 13px; font-weight: 700; color: {{card.hue}}">{{card.title}}</span><button type="button" aria-label="Открепить" onClick="{{card.close}}" style="display: {{card.pin}}; width: 22px; height: 22px; padding: 0px; border: 0px; border-radius: 4px; background: transparent; color: #9598A1; cursor: pointer; align-items: center; justify-content: center">%ICON_CLOSE%</button></div>
<div style="display: {{card.bigShow}}; font-size: 26px; line-height: 32px; font-weight: 600; color: #FFFFFF">{{card.big}}</div>
<div style="font-size: 12px; line-height: 16px; color: #9AA1AD; margin-bottom: 4px">{{card.sub}}</div>
<sc-for list="{{card.rows}}" as="r" hint-placeholder-count="3"><div style="display: flex; justify-content: space-between; gap: 10px; font-size: 13px; line-height: 22px"><span style="color: #9598A1">{{r.l}}</span><span style="color: #E6E8EE">{{r.v}}</span></div></sc-for>
<div style="margin-top: 5px; padding-top: 5px; border-top: 1px solid #1E232B; font-size: 11.5px; line-height: 15px; color: #8F939E">{{card.cond}}</div>
</div></sc-if>'''

ZLAB = '''<sc-for list="{{zlab}}" as="e" hint-placeholder-count="0"><div onMouseEnter="{{e.enter}}" onMouseLeave="{{e.leave}}" onClick="{{e.click}}" style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; height: 18px; display: flex; align-items: center; gap: 6px; white-space: nowrap; cursor: pointer; text-shadow: 0 0 3px #0B0D10, 0 0 3px #0B0D10, 0 0 2px #0B0D10"><span style="display: {{e.ic}}; width: 9px; height: 8px; border-radius: {{e.rad}}; background: {{e.hue}}; clip-path: {{e.clip}}; flex-shrink: 0"></span><span style="display: {{e.ard}}; font-size: 13px; font-weight: 700; color: {{e.hue}}">{{e.ar}}</span><span style="font-size: 13px; font-weight: {{e.fw}}; color: {{e.pc}}">{{e.pct}}</span><span style="font-size: 12px; color: {{e.wc}}">{{e.when}}</span></div></sc-for>'''

RANKS = '''<sc-for list="{{ranks}}" as="e" hint-placeholder-count="0"><div onMouseEnter="{{e.enter}}" onMouseLeave="{{e.leave}}" onClick="{{e.click}}" style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; font-size: 11px; font-weight: 700; line-height: 13px; color: {{e.c}}; opacity: {{e.op}}; cursor: pointer; text-shadow: 0 0 3px #0B0D10, 0 0 3px #0B0D10">{{e.t}}</div></sc-for>'''

PROJ = '''<div style="position: absolute; left: %PW%px; top: 0px; width: %PJ%px; height: %PH%px; background: #0C0E12; border-left: 1px solid #1B1F26"></div>
<sc-for list="{{pbars}}" as="e" hint-placeholder-count="0"><div onMouseEnter="{{e.enter}}" onMouseLeave="{{e.leave}}" onClick="{{e.click}}" style="position: absolute; left: {{e.hx}}px; top: {{e.y}}px; width: {{e.hw}}px; height: {{e.h}}px; cursor: pointer"><div style="position: absolute; left: 6px; top: 0px; width: {{e.w}}px; height: {{e.h}}px; border-radius: 0px 2px 2px 0px; background: {{e.bg}}"></div></div></sc-for>
<sc-for list="{{ptexts}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; font-size: 11.5px; line-height: 14px; color: {{e.c}}; white-space: nowrap; pointer-events: none">{{e.t}}</div></sc-for>'''

SEC = 'font-size: 11px; font-weight: 700; letter-spacing: 0.1em; color: #9598A1'
PANEL = '''<div style="position: absolute; left: 1540px; top: 44px; width: 380px; height: 956px; box-sizing: border-box; padding: 14px 18px 12px 18px; background: #0F1216; border-left: 1px solid #1E232B; display: flex; flex-direction: column; gap: 15px; overflow: hidden">
<div style="height: 76px; flex-shrink: 0; box-sizing: border-box; padding: 9px 12px 10px 12px; border-radius: 8px; background: #13171E; border: 1px solid #1E232B; display: flex; flex-direction: column; gap: 3px">
<div style="display: flex; align-items: center; gap: 8px; white-space: nowrap"><span style="font-size: 13.5px; font-weight: 700; color: {{P.ins.hue}}">{{P.ins.title}}</span><span style="display: {{P.ins.bigShow}}; margin-left: auto; font-size: 18px; font-weight: 600; color: #FFFFFF">{{P.ins.big}}</span></div>
<div style="font-size: 12.5px; line-height: 17px; color: #C3C8D1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{{P.ins.line}}</div>
<div style="font-size: 12px; line-height: 16px; color: #8F939E; white-space: nowrap; overflow: hidden; text-overflow: ellipsis">{{P.ins.line2}}</div>
</div>
<div style="display: flex; flex-direction: column; gap: 2px">
<div style="%SEC%; margin-bottom: 4px">ДЕНЬ</div>
<sc-for list="{{P.days}}" as="d" hint-placeholder-count="3"><div onClick="{{d.click}}" onMouseEnter="{{d.enter}}" onMouseLeave="{{d.leave}}" style="display: flex; align-items: center; gap: 10px; height: 26px; padding: 0px 8px; margin: 0px -8px; border-radius: 6px; background: {{d.bg}}; cursor: pointer; font-size: 13px; white-space: nowrap"><span style="width: 36px; font-weight: 700; color: {{d.c}}">{{d.k}}</span><span style="width: 58px; color: {{d.ac}}">{{d.conf}}</span><span style="color: {{d.stc}}">{{d.st}}</span></div></sc-for>
<div style="margin-top: 5px; font-size: 12.5px; line-height: 18px; color: #B2B5BE">Ширина IDR: {{P.widths}}</div>
<div style="font-size: 12.5px; line-height: 18px; color: #B2B5BE">К {{P.md.prev}}: рост — {{P.md.up}} · снижение — {{P.md.dn}}</div>
</div>
<div style="display: flex; flex-direction: column; gap: 1px">
<div style="%SEC%; margin-bottom: 4px">{{P.sessHdr}}</div>
<sc-for list="{{P.facts}}" as="f" hint-placeholder-count="5"><div style="display: flex; justify-content: space-between; gap: 12px; font-size: 13px; line-height: 21px; white-space: nowrap"><span style="color: #8F939E">{{f.l}}</span><span style="color: #E6E8EE; overflow: hidden; text-overflow: ellipsis">{{f.v}}</span></div></sc-for>
</div>
<sc-if value="{{P.hasDir}}" hint-placeholder-val="{{false}}"><div style="display: flex; flex-direction: column; gap: 6px">
<div style="%SEC%">ПОДТВЕРЖДЕНИЕ ПОЗЖЕ</div>
<div style="display: flex; height: 8px; width: 320px; border-radius: 4px; overflow: hidden; background: #1A1E26"><div style="width: {{P.dir.wu}}px; height: 8px; background: #089981"></div><div style="width: {{P.dir.wd}}px; height: 8px; background: #F23645"></div><div style="width: {{P.dir.wn}}px; height: 8px; background: #3A404C"></div></div>
<div style="display: flex; gap: 14px; font-size: 13px; white-space: nowrap"><span style="color: #B2B5BE">вверх <span style="color: #FFFFFF; font-weight: 600">{{P.dir.up}}</span></span><span style="color: #B2B5BE">вниз <span style="color: #FFFFFF; font-weight: 600">{{P.dir.dn}}</span></span><span style="color: #B2B5BE">не будет <span style="color: #FFFFFF; font-weight: 600">{{P.dir.none}}</span></span></div>
<div style="font-size: 11.5px; color: #8F939E">{{P.dir.n}}</div>
</div></sc-if>
<sc-for list="{{P.groups}}" as="g" hint-placeholder-count="2"><div style="display: flex; flex-direction: column; gap: 1px">
<div style="display: flex; align-items: center; gap: 8px; %SEC%"><span style="width: 11px; height: 10px; border-radius: {{g.rad}}; background: {{g.hue}}; clip-path: {{g.clip}}"></span><span>{{g.title}}</span></div>
<div style="font-size: 12px; line-height: 16px; color: #8F939E; margin: 2px 0px 3px 0px">{{g.sub}}</div>
<sc-for list="{{g.rows}}" as="z" hint-placeholder-count="3"><div onMouseEnter="{{z.enter}}" onMouseLeave="{{z.leave}}" onClick="{{z.click}}" style="display: flex; align-items: center; gap: 10px; height: 30px; box-sizing: border-box; padding: 0px 8px; margin: 0px -8px; border-radius: 6px; background: {{z.bg}}; cursor: pointer; font-size: 13px; white-space: nowrap"><span style="width: 10px; color: #8F939E; font-size: 12px">{{z.rank}}</span><span style="width: 88px; color: #B2B5BE">{{z.time}}</span><span style="flex-grow: 1; color: #E6E8EE">{{z.price}}</span><span style="width: 40px; text-align: right; color: #FFFFFF; font-weight: 600">{{z.pct}}</span></div></sc-for>
</div></sc-for>
<div style="flex-grow: 1"></div>
<div style="font-size: 11.5px; line-height: 15px; color: #8F939E">{{P.foot}}</div>
</div>'''


def page(title, body, script):
    props = json.dumps({"$preview": {"width": 1920, "height": 1000}})
    return f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<style>
body{{margin:0;background:#0B0D10;font-family:-apple-system,BlinkMacSystemFont,'Trebuchet MS',Roboto,Ubuntu,sans-serif}}
</style>
</helmet>
{body}
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{props}'>
class Component extends DCLogic {{
{script}
}}
</script>
</body>
</html>
'''


def artboard(name, title, js, W, PW, PH, BH, over, extra_chart='', panel='', projW=0, bandtext='', state=True, mode=None):
    g = dict(PW=PW, PH=PH, W=W, BH=BH, MID=BH // 2, SW=132, XS=PW + projW, XS10=PW + projW + 10, AX=PH + BH, AX6=PH + BH + 6, AX4=PH + BH + 4,
             SLY=PH - 30, ZX=PW - 108, ZY=PH - 38, NW=W, PJ=projW, SEG=SEG, SEGBTN=SEGBTN, SEC=SEC,
             ICON_MENU=ICON_MENU, ICON_REFRESH=ICON_REFRESH, ICON_REWIND=ICON_REWIND, ICON_MINUS=ICON_MINUS, ICON_PLUS=ICON_PLUS, ICON_RESET=ICON_RESET, ICON_CLOSE=ICON_CLOSE)
    chart = sub(CHART, DENSITY=sub(DENSITY, **g), OVER=over)
    body = f'''<div style="position: relative; width: 1920px; height: 1000px; overflow: hidden; background: #0B0D10; color: #D1D4DC; font-family: -apple-system, BlinkMacSystemFont, 'Trebuchet MS', Roboto, Ubuntu, sans-serif; font-size: 13px; user-select: none">
{sub(TOOLBAR, **g)}
<div ref="{{{{chartRef}}}}" onMouseDown="{{{{m.down}}}}" onMouseMove="{{{{m.move}}}}" onMouseUp="{{{{m.up}}}}" onMouseLeave="{{{{m.leave}}}}" onWheel="{{{{m.wheel}}}}" style="position: absolute; left: 0px; top: 44px; width: {W}px; height: 910px; overflow: hidden; background: #0B0D10; cursor: {{{{cursor}}}}">
{sub(chart, **g)}
{sub(extra_chart, **g)}
{sub(BAND, BANDTEXT=bandtext, **g)}
{sub(SCALE, **g)}
{sub(AXIS, **g)}
{sub(LEGEND, STATE=STATELINE if state else '', KEY=KEYLINE if mode else '', **g)}
{sub(CARD, **g) if 'card' in js_names(name) else ''}
</div>
{sub(NAV, **g)}
{sub(panel, **g)}
</div>'''
    script = rd('engine.js').replace('__BARS_A__', rd('bars_a.min.json')).replace('__BARS_B__', rd('bars_b.min.json')) + '\n' + rd('view.js') + '\n' + rd(js)
    if mode:                                            # the density row: the same variant 1, another way to draw the density
        script += "\n  _dmode() { return '" + mode + "'; }\n"
    text = page(title, body, script)
    left = [k for k in g if '%' + k + '%' in text] + [t for t in ('__BARS_A__', '__BARS_B__', '%DENSITY%', '%OVER%', '%STATE%', '%KEY%', '%BANDTEXT%') if t in text]
    open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='\n').write(text)
    print(name, len(text), 'bytes', 'LEFT' if left else '', left)


def js_names(name):
    return '' if name == 'Summary.dc.html' else 'card'


NOTE = '''Как смотреть (кнопка Play на макете):
• «Пример» наверху: подтверждено; до подтверждения (10:40, коробка закрыта); слом DR (другой день)
• один знак = одна клетка 5 мин × 0,1 IDR: сюда у похожих сессий пришёлся экстремум до конца сессии; треугольник — откат (остриё по ходу отката), кружок — продолжение; до подтверждения серые «Верх» и «Низ»
• ряд 1 — три раскладки экрана; ряд 2 — четыре способа показать, какие места сильные (подтверждены многими сессиями), а какие случайные
• подпись у кластера — его доля и время; наведи на знак или подпись — время и цены на осях, карточка «k из N»; клик закрепляет
• колесо — масштаб, перетаскивание — сдвиг по дню; клик по свече — повтор; полоса над осью времени — быстрый повтор
Свечи, сессии и числа синтетические.'''

DENSITY_BOARDS = [
    ('Steps.dc.html', 'Плотность 1 · Ступени', 'steps'),
    ('Solid.dc.html', 'Плотность 2 · Надёжность: сплошной / контур', 'solid'),
    ('Units.dc.html', 'Плотность 3 · Единицы: знак = 1%', 'units'),
    ('Mosaic.dc.html', 'Своё · Мозаика клеток', 'mosaic'),
]

if __name__ == '__main__':
    artboard('Main.dc.html', 'DR Lab · 1 · Кластеры на графике', 'v1.js', 1920, 1788, 852, 30, ZLAB)
    artboard('Summary.dc.html', 'DR Lab · 2 · График + сводка', 'v2.js', 1540, 1408, 852, 30, RANKS, panel=PANEL, state=False)
    artboard('Projections.dc.html', 'DR Lab · 3 · Проекции', 'v3.js', 1920, 1676, 818, 64, '', extra_chart=PROJ, projW=112, bandtext=BANDTEXT)
    for fn, ttl, md in DENSITY_BOARDS:
        artboard(fn, 'DR Lab · плотность · ' + ttl, 'v1.js', 1920, 1788, 852, 30, ZLAB, mode=md)
    now = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    canvas = {
        "v": 3, "attachments": {}, "createdOnFiles": {"v": 1, "at": "2026-09-28T13:23:29Z"}, "title": "DR Lab · кластеры, три варианта", "launch": {"view": "canvas"}, "pages": [],
        "boards": {
            "Main.dc.html": {"x": 0, "y": 0, "w": 1920, "h": 1000, "title": "1 · Кластеры на графике", "is_interactive": True},
            "Summary.dc.html": {"x": 2000, "y": 0, "w": 1920, "h": 1000, "title": "2 · График + сводка", "is_interactive": True},
            "Projections.dc.html": {"x": 4000, "y": 0, "w": 1920, "h": 1000, "title": "3 · Проекции", "is_interactive": True},
            **{fn: {"x": 2000 * i, "y": 1500, "w": 1920, "h": 1000, "title": ttl, "is_interactive": True} for i, (fn, ttl, md) in enumerate(DENSITY_BOARDS)},
        },
        "order": ["Main.dc.html", "Summary.dc.html", "Projections.dc.html"] + [b[0] for b in DENSITY_BOARDS],
        "notes": {
            "title": {"x": 0, "y": -300, "text": "DR Lab — кластеры, три варианта раскладки", "kind": "title1", "maxW": 5920},
            "title2": {"x": 0, "y": 1200, "text": "Как рисовать плотность: три варианта с треугольниками и один свой", "kind": "title1", "maxW": 7920},
            "howto": {"x": 0, "y": 2620, "text": NOTE, "w": 620, "size": 40, "fill": "gray"}
        },
        "designSystems": []
    }
    open(os.path.join(OUT, 'canvas.json'), 'w', encoding='utf-8', newline='\n').write(json.dumps(canvas, ensure_ascii=False, indent=1))
    print('canvas.json written')
