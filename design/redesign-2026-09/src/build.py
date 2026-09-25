"""Builds the three .dc.html artboards and project/canvas.json for the DR Lab design canvas."""
import json
import os
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'built')
os.makedirs(OUT, exist_ok=True)
rd = lambda n: open(os.path.join(HERE, n), encoding='utf-8').read()

BARS = rd('bars.min.json')
ENGINE = rd('engine.js').replace('__BARS__', BARS)
COMMON = rd('common.js')

ICON_MENU = '<svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M3 5h12M3 9h12M3 13h12"></path></svg>'
ICON_REFRESH = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M13.5 8a5.5 5.5 0 1 1-1.6-3.9"></path><path d="M13.5 2.5v3h-3"></path></svg>'
ICON_REWIND = '<svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor"><path d="M7 3.2v7.6L2 7zM12.5 3.2v7.6L7.5 7z"></path></svg>'
ICON_MINUS = '<svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M2 6h8"></path></svg>'
ICON_PLUS = '<svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M2 6h8M6 2v8"></path></svg>'
ICON_RESET = '<svg width="13" height="13" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 7a4.5 4.5 0 1 0 1.3-3.2"></path><path d="M2.5 2v2.5H5"></path></svg>'
ICON_CLOSE = '<svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><path d="M2 2l8 8M10 2l-8 8"></path></svg>'

SEG = 'display: flex; gap: 2px; padding: 3px; background: #161A21; border-radius: 7px'
SEGBTN = 'height: 26px; padding: 0px 10px; border: 0px; border-radius: 5px; font-family: inherit; font-size: 13px; font-weight: 600; cursor: pointer'


def toolbar(height=44, hud=''):
    return f'''<div style="position: absolute; left: 0px; top: 0px; width: 1920px; height: {height}px; box-sizing: border-box; display: flex; align-items: center; gap: 12px; padding: 0px 12px; background: #0F1216; border-bottom: 1px solid #1E232B">
<button type="button" aria-label="Меню исследования" style="width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; padding: 0px; background: transparent; border: 0px; border-radius: 6px; color: #B2B5BE; cursor: pointer">{ICON_MENU}</button>
<div style="{SEG}"><sc-for list="{{{{tb.inst}}}}" as="b" hint-placeholder-count="3"><button type="button" style="{SEGBTN}; background: {{{{b.bg}}}}; color: {{{{b.c}}}}">{{{{b.t}}}}</button></sc-for></div>
<div style="{SEG}"><sc-for list="{{{{tb.sess}}}}" as="b" hint-placeholder-count="3"><button type="button" title="{{{{b.tip}}}}" onClick="{{{{b.click}}}}" onMouseEnter="{{{{b.enter}}}}" onMouseLeave="{{{{b.leave}}}}" style="{SEGBTN}; background: {{{{b.bg}}}}; color: {{{{b.c}}}}; display: flex; align-items: center; gap: 6px"><span style="width: 6px; height: 6px; border-radius: 3px; background: {{{{b.dot}}}}"></span><span>{{{{b.t}}}}</span></button></sc-for></div>
<span style="font-size: 13px; color: #9598A1; white-space: nowrap">чт, 24 сен</span>
<div style="flex-grow: 1"></div>
{hud}
<div style="display: flex; gap: 6px"><sc-for list="{{{{tb.layers}}}}" as="l" hint-placeholder-count="4"><button type="button" onClick="{{{{l.click}}}}" style="height: 28px; padding: 0px 10px; border: {{{{l.bd}}}}; border-radius: 6px; background: {{{{l.bg}}}}; color: {{{{l.c}}}}; font-family: inherit; font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 7px; white-space: nowrap"><span style="width: 10px; height: 10px; border-radius: 2px; background: {{{{l.sw}}}}; opacity: {{{{l.swop}}}}"></span><span>{{{{l.t}}}}</span></button></sc-for></div>
<div style="width: 1px; height: 22px; background: #252A33"></div>
<sc-if value="{{{{tb.live}}}}" hint-placeholder-val="{{{{true}}}}"><div style="display: flex; align-items: center; gap: 8px; font-size: 13px; color: #D1D4DC; white-space: nowrap"><span style="width: 8px; height: 8px; border-radius: 4px; background: #089981; box-shadow: 0 0 0 3px rgba(8,153,129,0.22)"></span><span style="font-weight: 600">LIVE</span><span style="color: #9598A1">{{{{tb.clock}}}}</span></div></sc-if>
<sc-if value="{{{{tb.replay}}}}" hint-placeholder-val="{{{{false}}}}"><div style="display: flex; align-items: center; gap: 8px; height: 28px; box-sizing: border-box; padding: 0px 3px 0px 10px; border: 1px solid #F7C948; border-radius: 6px; font-size: 13px; color: #F7C948; white-space: nowrap">{ICON_REWIND}<span>Повтор</span><span style="font-weight: 600">{{{{tb.rpText}}}}</span><button type="button" onClick="{{{{tb.toLive}}}}" style="height: 22px; padding: 0px 9px; border: 0px; border-radius: 4px; background: #F7C948; color: #0B0D10; font-family: inherit; font-size: 12px; font-weight: 700; cursor: pointer">В live</button></div></sc-if>
<button type="button" aria-label="Обновить из TradingView" style="width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; padding: 0px; background: transparent; border: 0px; border-radius: 6px; color: #B2B5BE; cursor: pointer">{ICON_REFRESH}</button>
</div>'''


def chart_base(g, clusters, badges=True):
    PW, PH = g['PW'], g['PH']
    badge_html = '''<sc-for list="{{badges}}" as="e" hint-placeholder-count="0"><div onMouseEnter="{{e.enter}}" onMouseLeave="{{e.leave}}" onClick="{{e.click}}" style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: 18px; height: 18px; box-sizing: border-box; border-radius: 9px; background: {{e.bg}}; border: {{e.bd}}; color: #0B0D10; font-size: 11px; font-weight: 700; line-height: 16px; text-align: center; cursor: pointer; box-shadow: 0 0 0 2px #0B0D10">{{e.t}}</div></sc-for>''' if badges else ''
    return f'''<div onClick="{{{{m.bg}}}}" style="position: absolute; left: 0px; top: 0px; width: {PW}px; height: {PH}px"></div>
<sc-for list="{{{{boxes}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: {{{{e.w}}}}px; height: {{{{e.h}}}}px; background: {{{{e.bg}}}}; opacity: {{{{e.op}}}}; pointer-events: none"></div></sc-for>
<sc-for list="{{{{grid}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: {{{{e.w}}}}px; height: 1px; background: {{{{e.bg}}}}; pointer-events: none"></div></sc-for>
<sc-for list="{{{{gridT}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; transform: translateX(-100%); padding: 0px 3px; border-radius: 2px; background: rgba(11,13,16,0.86); font-size: 11px; line-height: 14px; color: #A3A8B3; pointer-events: none">{{{{e.t}}}}</div></sc-for>
<sc-for list="{{{{lines}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: {{{{e.w}}}}px; height: {{{{e.h}}}}px; background: {{{{e.bg}}}}; opacity: {{{{e.op}}}}; box-shadow: {{{{e.sh}}}}; pointer-events: none"></div></sc-for>
<sc-for list="{{{{lhits}}}}" as="e" hint-placeholder-count="0"><div onMouseEnter="{{{{e.enter}}}}" onMouseLeave="{{{{e.leave}}}}" onClick="{{{{e.click}}}}" style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: {{{{e.w}}}}px; height: {{{{e.h}}}}px"></div></sc-for>
<sc-if value="{{{{hasFan}}}}" hint-placeholder-val="{{{{false}}}}"><svg width="{PW}" height="{PH}" viewBox="0 0 {PW} {PH}" style="position: absolute; left: 0px; top: 0px; pointer-events: none"><path d="{{{{fanArea}}}}" fill="rgba(209,212,220,0.045)"></path><path d="{{{{fanMid}}}}" fill="none" stroke="rgba(209,212,220,0.7)" stroke-width="1.5" stroke-dasharray="6 4"></path></svg></sc-if>
{clusters}
<sc-for list="{{{{picks}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: {{{{e.w}}}}px; height: {{{{e.h}}}}px; box-sizing: border-box; background: {{{{e.bg}}}}; border: {{{{e.bd}}}}; border-radius: 2px; pointer-events: none"></div></sc-for>
<div style="position: absolute; left: {{{{priceLine.x}}}}px; top: {{{{priceLine.y}}}}px; width: {{{{priceLine.w}}}}px; height: 1px; background: {{{{priceLine.bg}}}}; opacity: {{{{priceLine.op}}}}; pointer-events: none"></div>
<div style="position: absolute; left: {{{{touchLine.x}}}}px; top: {{{{touchLine.y}}}}px; width: {{{{touchLine.w}}}}px; height: 2px; background: {{{{touchLine.bg}}}}; pointer-events: none"></div>
<sc-for list="{{{{wicks}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: 1px; height: {{{{e.h}}}}px; background: {{{{e.bg}}}}; opacity: {{{{e.op}}}}; pointer-events: none"></div></sc-for>
<sc-for list="{{{{bodies}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: {{{{e.w}}}}px; height: {{{{e.h}}}}px; background: {{{{e.bg}}}}; opacity: {{{{e.op}}}}; outline: {{{{e.bd}}}}; pointer-events: none"></div></sc-for>
<sc-for list="{{{{chits}}}}" as="e" hint-placeholder-count="0"><div onClick="{{{{e.click}}}}" style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: {{{{e.w}}}}px; height: {{{{e.h}}}}px; cursor: pointer"></div></sc-for>
<sc-for list="{{{{pills}}}}" as="e" hint-placeholder-count="0"><div onMouseEnter="{{{{e.enter}}}}" onMouseLeave="{{{{e.leave}}}}" onClick="{{{{e.click}}}}" style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: 42px; height: 18px; box-sizing: border-box; border-radius: 9px; background: {{{{e.bg}}}}; border: {{{{e.bd}}}}; opacity: {{{{e.op}}}}; color: #FFFFFF; font-size: 11px; font-weight: 700; line-height: 16px; text-align: center; cursor: default">{{{{e.t}}}}</div></sc-for>
{badge_html}
<sc-for list="{{{{vlines}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: 1px; height: {{{{e.h}}}}px; background: {{{{e.bg}}}}; opacity: {{{{e.op}}}}; pointer-events: none"></div></sc-for>
<sc-for list="{{{{glines}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: {{{{e.w}}}}px; height: {{{{e.h}}}}px; background: {{{{e.bg}}}}; pointer-events: none"></div></sc-for>
<sc-for list="{{{{xh}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: {{{{e.w}}}}px; height: {{{{e.h}}}}px; background: {{{{e.bg}}}}; pointer-events: none"></div></sc-for>
<sc-for list="{{{{slabels}}}}" as="e" hint-placeholder-count="0"><div onClick="{{{{e.click}}}}" onMouseEnter="{{{{e.enter}}}}" onMouseLeave="{{{{e.leave}}}}" style="position: absolute; left: {{{{e.x}}}}px; top: {PH - 30}px; height: 22px; box-sizing: border-box; padding: 0px 8px; border-radius: 5px; background: {{{{e.bg}}}}; display: flex; align-items: center; gap: 6px; cursor: pointer; white-space: nowrap"><span style="width: 6px; height: 6px; border-radius: 3px; background: #089981; display: {{{{e.dot}}}}"></span><span style="font-size: 12px; font-weight: {{{{e.fw}}}}; color: {{{{e.c}}}}">{{{{e.t}}}}</span><span style="font-size: 11.5px; color: #8F939E">{{{{e.sub}}}}</span></div></sc-for>
<div style="position: absolute; left: {PW - 108}px; top: {PH - 38}px; display: flex; gap: 4px">
<button type="button" aria-label="Отдалить" onClick="{{{{zoomOut}}}}" style="width: 30px; height: 28px; display: flex; align-items: center; justify-content: center; padding: 0px; border: 1px solid #2B313C; border-radius: 6px; background: rgba(22,26,33,0.92); color: #B2B5BE; cursor: pointer">{ICON_MINUS}</button>
<button type="button" aria-label="Приблизить" onClick="{{{{zoomIn}}}}" style="width: 30px; height: 28px; display: flex; align-items: center; justify-content: center; padding: 0px; border: 1px solid #2B313C; border-radius: 6px; background: rgba(22,26,33,0.92); color: #B2B5BE; cursor: pointer">{ICON_PLUS}</button>
<button type="button" aria-label="Вся сессия" onClick="{{{{reset}}}}" style="width: 30px; height: 28px; display: flex; align-items: center; justify-content: center; padding: 0px; border: 1px solid #2B313C; border-radius: 6px; background: rgba(22,26,33,0.92); color: #B2B5BE; cursor: pointer">{ICON_RESET}</button>
</div>'''


def scale(g, quiet=False):
    xs, sw, PH = g['xs'], g['scaleW'], g['PH']
    pw = '500; font-size: 11.5px' if quiet else '700'
    return f'''<div style="position: absolute; left: {xs}px; top: 0px; width: {sw}px; height: {PH}px; background: #0B0D10; border-left: 1px solid #262B34"></div>
<sc-for list="{{{{ticks}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {xs + 10}px; top: {{{{e.y}}}}px; font-size: 12px; line-height: 16px; color: #B2B5BE; pointer-events: none">{{{{e.t}}}}</div></sc-for>
<sc-for list="{{{{anchors}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {xs - 6}px; top: {{{{e.y}}}}px; width: 6px; height: 1px; background: {{{{e.bg}}}}; pointer-events: none"></div></sc-for>
<sc-for list="{{{{tags}}}}" as="e" hint-placeholder-count="0"><div onMouseEnter="{{{{e.enter}}}}" onMouseLeave="{{{{e.leave}}}}" onClick="{{{{e.click}}}}" style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; height: {{{{e.h}}}}px; box-sizing: border-box; padding: 0px 6px; display: flex; flex-direction: column; justify-content: center; background: {{{{e.bg}}}}; color: {{{{e.fg}}}}; border: {{{{e.bd}}}}; border-radius: 3px; font-size: 12.5px; font-weight: {{{{e.fw}}}}; line-height: 15px; white-space: nowrap; cursor: default"><div style="display: flex; gap: 6px; align-items: baseline"><span style="display: {{{{e.nd}}}}; font-size: 11px; font-weight: 700; opacity: 0.8">{{{{e.name}}}}</span><span>{{{{e.price}}}}</span><span style="display: {{{{e.pdisp}}}}; color: {{{{e.pcol}}}}; font-weight: {pw}">{{{{e.pct}}}}</span></div><div style="display: {{{{e.sd}}}}; font-size: 11px; opacity: 0.85">{{{{e.sub}}}}</div></div></sc-for>'''


def axis(g):
    PH, W = g['PH'], g['W']
    return f'''<div style="position: absolute; left: 0px; top: {PH}px; width: {W}px; height: {g['axisH']}px; background: #0B0D10; border-top: 1px solid #262B34"></div>
<sc-for list="{{{{tlabels}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{{{e.x}}}}px; top: {PH + 6}px; transform: translateX(-50%); font-size: 14px; line-height: 16px; color: #D1D4DC; white-space: nowrap; pointer-events: none">{{{{e.t}}}}</div></sc-for>
<sc-for list="{{{{ttags}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{{{e.x}}}}px; top: {PH + 4}px; transform: translateX(-50%); height: 20px; padding: 0px 7px; border-radius: 3px; background: {{{{e.col}}}}; color: {{{{e.fg}}}}; font-size: 12.5px; font-weight: 600; line-height: 20px; white-space: nowrap; pointer-events: none">{{{{e.t}}}}</div></sc-for>'''


LEGEND = '''<div style="position: absolute; left: 6px; top: 6px; display: flex; flex-direction: column; gap: 3px; padding: 4px 8px 5px 8px; border-radius: 6px; background: rgba(11,13,16,0.78); pointer-events: none; font-size: 13px; line-height: 17px; white-space: nowrap">
<div style="display: flex; align-items: center; gap: 8px"><span style="color: #D1D4DC; font-weight: 600">NQ1! · 5 · <span>{{act}}</span></span><span style="display: {{confShow}}; height: 18px; padding: 0px 7px; border-radius: 9px; background: {{confBg}}; color: #FFFFFF; font-size: 11.5px; font-weight: 700; align-items: center">{{conf}}</span></div>
<div style="display: flex; gap: 10px; color: #9598A1"><span>O <span style="color: {{lg.col}}">{{lg.o}}</span></span><span>H <span style="color: {{lg.col}}">{{lg.h}}</span></span><span>L <span style="color: {{lg.col}}">{{lg.l}}</span></span><span>C <span style="color: {{lg.col}}">{{lg.c}}</span></span><span style="color: {{lg.col}}">{{lg.ch}}</span><span>{{lg.when}}</span></div>
</div>'''

CARD_ROW = '<div style="display: flex; justify-content: space-between; gap: 10px; font-size: 13.5px; line-height: 22px"><span style="color: #9598A1">{label}</span><span style="color: #E6E8EE">{{{{card.{field}}}}}</span></div>'
CARD = f'''<sc-if value="{{{{card.show}}}}" hint-placeholder-val="{{{{false}}}}"><div style="position: absolute; left: {{{{card.x}}}}px; top: {{{{card.y}}}}px; width: 236px; box-sizing: border-box; padding: 10px 12px 12px 12px; background: rgba(15,18,22,0.97); border: 1px solid #2B313C; border-top: 2px solid {{{{card.hue}}}}; border-radius: 8px; box-shadow: 0 12px 32px rgba(0,0,0,0.6); cursor: default">
<div style="display: flex; align-items: center; gap: 8px"><span style="display: {{{{card.rd}}}}; width: 18px; height: 18px; border-radius: 9px; background: {{{{card.hue}}}}; color: #0B0D10; font-size: 11px; font-weight: 700; align-items: center; justify-content: center">{{{{card.rank}}}}</span><span style="flex-grow: 1; font-size: 11.5px; font-weight: 700; letter-spacing: 0.06em; color: #B2B5BE">{{{{card.what}}}}</span><button type="button" aria-label="Закрыть" onClick="{{{{card.close}}}}" style="width: 22px; height: 22px; padding: 0px; border: 0px; border-radius: 4px; background: transparent; color: #9598A1; cursor: pointer; display: flex; align-items: center; justify-content: center">{ICON_CLOSE}</button></div>
<div style="font-size: 28px; line-height: 34px; font-weight: 600; color: #FFFFFF; margin: 2px 0px 6px 0px">{{{{card.pct}}}}</div>
{CARD_ROW.format(label='Время', field='time')}
{CARD_ROW.format(label='Цена', field='price')}
{CARD_ROW.format(label='Шкала', field='scale')}
{CARD_ROW.format(label='Сессий', field='count')}
</div></sc-if>'''


def bottom(top, h):
    return f'''<div style="position: absolute; left: 0px; top: {top}px; width: 1920px; height: {h}px; background: #0B0D10; border-top: 1px solid #1E232B">
<sc-for list="{{{{bot.frames}}}}" as="e" hint-placeholder-count="6"><div style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: {{{{e.w}}}}px; height: {{{{e.h}}}}px; box-sizing: border-box; background: #0F1216; border: 1px solid #1B1F26; border-radius: 6px"></div></sc-for>
<sc-for list="{{{{bot.titles}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; font-size: 12.5px; color: #B2B5BE; pointer-events: none; white-space: nowrap">{{{{e.t}}}}</div></sc-for>
<sc-if value="{{{{bot.show}}}}" hint-placeholder-val="{{{{true}}}}"><svg width="{{{{bot.fw}}}}" height="{{{{bot.fh}}}}" style="position: absolute; left: {{{{bot.fx}}}}px; top: {{{{bot.fy}}}}px; overflow: visible; pointer-events: none"><path d="{{{{bot.fanZero}}}}" fill="none" stroke="rgba(209,212,220,0.35)" stroke-width="1" stroke-dasharray="3 3"></path><path d="{{{{bot.fanArea}}}}" fill="rgba(209,212,220,0.10)"></path><path d="{{{{bot.fanMid}}}}" fill="none" stroke="#D1D4DC" stroke-width="1.6"></path></svg></sc-if>
<sc-for list="{{{{bot.cells}}}}" as="e" hint-placeholder-count="0"><div onMouseEnter="{{{{e.enter}}}}" onMouseLeave="{{{{e.leave}}}}" onClick="{{{{e.click}}}}" style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: {{{{e.w}}}}px; height: {{{{e.h}}}}px; background: {{{{e.bg}}}}; outline: {{{{e.bd}}}}; cursor: pointer"></div></sc-for>
<sc-for list="{{{{bot.bars}}}}" as="e" hint-placeholder-count="0"><div onMouseEnter="{{{{e.enter}}}}" onMouseLeave="{{{{e.leave}}}}" onClick="{{{{e.click}}}}" style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: {{{{e.w}}}}px; height: {{{{e.h}}}}px; background: {{{{e.bg}}}}; outline: {{{{e.bd}}}}; border-radius: 1px"></div></sc-for>
<sc-for list="{{{{bot.texts}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; transform: {{{{e.al}}}}; font-size: 11px; line-height: 14px; color: #9598A1; white-space: nowrap; pointer-events: none">{{{{e.t}}}}</div></sc-for>
</div>'''


def page(title, body, script, preview):
    props = json.dumps({"$preview": {"width": preview[0], "height": preview[1]}})
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


def build(name, title, html_file, js_file, g, clusters, extra=None, bottom_frag='', badges=True, toolbar_frag=None):
    body = rd(html_file)
    rep = {
        '__TOOLBAR__': toolbar_frag or toolbar(),
        '__CHART__': chart_base(g, clusters, badges),
        '__SCALE__': scale(g), '__AXIS__': axis(g), '__LEGEND__': LEGEND, '__CARD__': CARD, '__BOTTOM__': bottom_frag,
    }
    rep.update(extra or {})
    for k, v in rep.items():
        body = body.replace(k, v)
    script = ENGINE + '\n' + COMMON + '\n' + rd(js_file)
    text = page(title, body, script, (1920, 1000))
    open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='\n').write(text)
    left = [t for t in ('__TOOLBAR__', '__CHART__', '__SCALE__', '__AXIS__', '__LEGEND__', '__CARD__', '__BOTTOM__', '__CLUSTERS__', '__BARS__') if t in text]
    print(name, len(text), 'bytes', 'LEFT:' if left else '', left)


CL_A = '''<sc-for list="{{cells}}" as="e" hint-placeholder-count="0"><div onMouseEnter="{{e.enter}}" onMouseLeave="{{e.leave}}" onClick="{{e.click}}" style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: {{e.w}}px; height: {{e.h}}px; box-sizing: border-box; border-radius: 2px; background: {{e.bg}}; border: {{e.bd}}; cursor: pointer"></div></sc-for>
<sc-for list="{{zones}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; width: {{e.w}}px; height: {{e.h}}px; box-sizing: border-box; border: {{e.bd}}; background: {{e.bg}}; border-radius: 3px; pointer-events: none"></div></sc-for>'''

def cl_b(g):
    PW, PH = g['PW'], g['PH']
    return f'''<div style="position: absolute; left: {{{{xNow}}}}px; top: 0px; width: {{{{cloudW}}}}px; height: {PH}px; overflow: hidden; pointer-events: none"><div style="position: absolute; left: 0px; top: 0px; width: {{{{cloudW}}}}px; height: {PH}px; filter: blur(9px)"><sc-for list="{{{{cloud}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: {{{{e.w}}}}px; height: {{{{e.h}}}}px; background: {{{{e.bg}}}}"></div></sc-for></div></div>
<svg width="{PW}" height="{PH}" viewBox="0 0 {PW} {PH}" style="position: absolute; left: 0px; top: 0px; pointer-events: none"><path d="{{{{cr0}}}}" fill="none" stroke="rgba(61,155,255,0.3)" stroke-width="1"></path><path d="{{{{cr1}}}}" fill="none" stroke="rgba(61,155,255,0.65)" stroke-width="1.1"></path><path d="{{{{cr2}}}}" fill="none" stroke="rgba(140,195,255,0.95)" stroke-width="1.4"></path><path d="{{{{ce0}}}}" fill="none" stroke="rgba(176,124,255,0.3)" stroke-width="1"></path><path d="{{{{ce1}}}}" fill="none" stroke="rgba(176,124,255,0.65)" stroke-width="1.1"></path><path d="{{{{ce2}}}}" fill="none" stroke="rgba(206,176,255,0.95)" stroke-width="1.4"></path></svg>
<sc-for list="{{{{hits}}}}" as="e" hint-placeholder-count="0"><div onMouseEnter="{{{{e.enter}}}}" onMouseLeave="{{{{e.leave}}}}" onClick="{{{{e.click}}}}" style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; width: {{{{e.w}}}}px; height: {{{{e.h}}}}px; box-sizing: border-box; border: {{{{e.bd}}}}; border-radius: 2px; cursor: pointer"></div></sc-for>
<sc-for list="{{{{zlab}}}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: 0px; top: 0px"><div style="position: absolute; left: {{{{e.bx}}}}px; top: {{{{e.by}}}}px; width: {{{{e.bw}}}}px; height: {{{{e.bh}}}}px; box-sizing: border-box; border: {{{{e.bb}}}}; border-radius: 4px; display: {{{{e.box}}}}; pointer-events: none"></div><div onMouseEnter="{{{{e.enter}}}}" onMouseLeave="{{{{e.leave}}}}" onClick="{{{{e.click}}}}" style="position: absolute; left: {{{{e.x}}}}px; top: {{{{e.y}}}}px; transform: translateX(-50%); height: 20px; box-sizing: border-box; padding: 0px 7px 0px 3px; border-radius: 10px; background: rgba(11,13,16,0.9); border: {{{{e.bd}}}}; display: flex; align-items: center; gap: 5px; cursor: pointer; white-space: nowrap"><span style="width: 14px; height: 14px; border-radius: 7px; background: {{{{e.bg}}}}; color: #0B0D10; font-size: 10px; font-weight: 700; line-height: 14px; text-align: center">{{{{e.t}}}}</span><span style="font-size: 12px; font-weight: 600; color: #E6E8EE">{{{{e.pct}}}}</span></div></div></sc-for>'''



def cl_b2(g):
    PW, PH = g['PW'], g['PH']
    return open(os.path.join(HERE, 'cl_b2.frag.html'), encoding='utf-8').read().replace('__PW__', str(PW)).replace('__PH__', str(PH))

HUD = '''<div style="display: flex; gap: 8px"><sc-for list="{{hud}}" as="h" hint-placeholder-count="4"><div title="{{h.tip}}" onMouseEnter="{{h.enter}}" onMouseLeave="{{h.leave}}" onClick="{{h.click}}" style="height: 34px; box-sizing: border-box; padding: 0px 12px; border-radius: 8px; background: {{h.bg}}; border: {{h.bd}}; display: flex; align-items: center; gap: 8px; cursor: {{h.cur}}; white-space: nowrap"><span style="font-size: 12px; color: #9598A1">{{h.t}}</span><span style="font-size: 15px; font-weight: 600; color: {{h.col}}">{{h.v}}</span></div></sc-for></div>
<div style="flex-grow: 1"></div>'''

CL_C = '''<sc-for list="{{zlab}}" as="e" hint-placeholder-count="0"><div style="position: absolute; left: 0px; top: 0px"><div onMouseEnter="{{e.enter}}" onMouseLeave="{{e.leave}}" onClick="{{e.click}}" style="position: absolute; left: {{e.bx}}px; top: {{e.by}}px; width: {{e.bw}}px; height: {{e.bh}}px; box-sizing: border-box; border: {{e.bb}}; background: {{e.bf}}; border-radius: 3px; cursor: pointer"></div><div onMouseEnter="{{e.enter}}" onMouseLeave="{{e.leave}}" onClick="{{e.click}}" style="position: absolute; left: {{e.x}}px; top: {{e.y}}px; height: 20px; box-sizing: border-box; padding: 0px 8px 0px 3px; border-radius: 10px; background: {{e.pbg}}; border: {{e.bd}}; display: flex; align-items: center; gap: 6px; white-space: nowrap; cursor: pointer; font-size: 12px"><span style="width: 14px; height: 14px; border-radius: 7px; background: {{e.bg}}; color: #0B0D10; font-size: 10px; font-weight: 700; line-height: 14px; text-align: center">{{e.t}}</span><span style="font-weight: 700; color: #FFFFFF">{{e.pct}}</span><span style="color: #B2B5BE">{{e.when}}</span><span style="display: {{e.pxd}}; color: #E6E8EE">{{e.px}}</span></div></div></sc-for>'''


if __name__ == '__main__':
    import sys
    which = sys.argv[1:] or ['A', 'B', 'C', 'B2']
    if 'A' in which:
        gA = dict(W=1568, PW=1372, PH=760, ladderW=88, scaleW=108, axisH=28)
        gA['xs'] = gA['PW'] + gA['ladderW']
        build('Main.dc.html', 'DR Lab · A · Терминал', 'a.html', 'a.js', gA, CL_A, bottom_frag=bottom(832, 168))
    if 'B' in which:
        gB = dict(W=1548, PW=1416, PH=714, ladderW=0, scaleW=132, axisH=28)
        gB['xs'] = gB['PW']
        build('Scenario.dc.html', 'DR Lab · B · Сценарий', 'b.html', 'b.js', gB, cl_b(gB), bottom_frag=bottom(832, 168), badges=False)
    if 'B2' in which:
        gB2 = dict(W=1548, PW=1416, PH=684, ladderW=0, scaleW=132, axisH=28)
        gB2['xs'] = gB2['PW']
        g2 = dict(gB2, PH=714)
        build('ScenarioV2.dc.html', 'DR Lab · B′ · Сценарий (выбран)', 'b2.html', 'b2.js', gB2, cl_b2(gB2), bottom_frag=bottom(832, 168), badges=False,
              extra={'__SCALE__': scale(g2, quiet=True), '__AXIS__': axis(g2)})
    if 'C' in which:
        gC = dict(W=1920, PW=1650, PH=880, ladderW=124, scaleW=146, axisH=28)
        gC['xs'] = gC['PW'] + gC['ladderW']
        g2 = dict(gC, PH=924)
        build('Clean.dc.html', 'DR Lab · C · Чистый график', 'c.html', 'c.js', gC, CL_C, badges=False,
              toolbar_frag=toolbar(48, HUD), extra={'__SCALE__': scale(g2), '__AXIS__': axis(g2)})
