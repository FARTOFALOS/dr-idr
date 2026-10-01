"""Numbered markers on the snapshots of screen 24 for spec/ekran-24/*.md (the numbers are explained there).

Every marker points at an element by the page's own geometry (img/raw/<state>.json, made by shots.py with `&geo=1`),
never by hand-measured pixels, so a new snapshot after a change of the screen re-annotates itself.

python spec/ekran-24/tools/annotate.py
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / 'img' / 'raw'
OUT = HERE.parent / 'img'
FONT = ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf', 15)
YELLOW, INK = (247, 201, 72), (11, 12, 16)


def ctr(r):
    return (r[0] + r[2] / 2, r[1] + r[3] / 2)


def left(r, dx=10):
    return (r[0] + dx, r[1] + r[3] / 2)


def right(r, dx=10):
    return (r[0] + r[2] - dx, r[1] + r[3] / 2)


def block(G, text):
    for b in G['panel']['blocks'] + G['panel']['links']:
        if b['r'] and text in b['text']:
            return b['r']
    raise KeyError('no panel block with «' + text + '»')


def zone(G, label):
    return next(z for z in G['chart']['zones'] if z['label'] == label)


def cap(G, ev, i):
    return next(c for c in G['chart']['caps'] if c['ev'] == ev and c['i'] == i)['box']


def hill(G, ev, i):
    return next(h for h in G['chart']['hills'] if h['ev'] == ev and h['i'] == i)['top']


def add(p, d):
    return (p[0] + d[0], p[1] + d[1])


# picture -> (state, [(number, target(G) -> (x, y), marker offset from the target)])
C = lambda k: (lambda G: tuple(G['chart'][k]))
D = lambda k, f=ctr: (lambda G: f(G['dom'][k]))
MARKS = {
    'obzor-grafik': ('obzor', [
        (1, lambda G: add(G['chart']['legend'], (430, 0)), (26, 0)),
        (2, lambda G: add(G['chart']['status'], (150, 0)), (26, 0)),
        (3, lambda G: ctr(G['chart']['box']), (-50, -70)),
        (4, C('fracs'), (-4, 34)),
        (5, C('drH'), (0, -24)),
        (6, C('idrH'), (-30, 24)),
        (7, C('mid'), (40, 22)),
        (8, C('std'), (0, -22)),
        (9, C('pill'), (-34, -22)),
        (10, C('slice'), (24, 130)),
        (11, lambda G: add(G['chart']['end'], (0, 14)), (26, 22)),
        (12, lambda G: ctr(zone(G, 'X2')['bb']), (0, 0)),
        (13, lambda G: ctr(zone(G, 'X2')['labelBox']), (-70, -12)),
        (14, lambda G: ctr(zone(G, 'R2')['bb']), (0, 0)),
        (15, lambda G: ctr(zone(G, 'R1')['labelBox']), (24, 22)),
        (16, lambda G: tuple(G['chart']['stars']['Xzone']), (24, -24)),
        (17, lambda G: tuple(G['chart']['stars']['Rres']), (24, -24)),
        (18, lambda G: tuple(G['chart']['stars']['ring']), (24, -24)),
        (19, C('axisDR'), (-64, 30)),
        (20, C('priceNow'), (-64, -18)),
        (21, lambda G: tuple(G['chart']['projRow']['R']), (0, -26)),
        (22, lambda G: tuple(G['chart']['projRow']['X']), (0, -26)),
        (23, lambda G: ctr(cap(G, 'X', 1)), (0, 0)),
        (24, lambda G: hill(G, 'X', 0), (26, -6)),
        (25, C('column'), (0, 0)),
        (26, C('unk'), (22, -16)),
        (27, lambda G: ctr(G['chart']['taxis']), (0, 0)),
        (28, lambda G: (G['chart']['axis'][0] + 70, G['chart']['bandCy']), (0, -40)),
    ]),
    'obzor-panel': ('obzor', [
        (1, D('inst'), (0, 30)), (2, D('sess'), (0, 30)), (3, D('date'), (0, 30)), (4, D('mode'), (0, 30)),
        (5, D('ev'), (0, 30)), (6, D('areab'), (0, 30)), (7, D('dayb'), (0, 30)), (8, D('step21'), (0, 30)),
        (9, D('lay'), (0, 30)), (10, D('cfgb'), (0, 30)), (11, D('clock'), (0, 30)),
        (12, lambda G: left(block(G, 'Семья ·')), (-24, 0)),
        (13, lambda G: left(G['panel']['bar']), (-24, 0)),
        (14, lambda G: left(G['panel']['out']), (-24, 0)),
        (15, lambda G: left(block(G, 'Зоны по времени')), (-24, 0)),
        (16, lambda G: ctr(G['panel']['now']), (0, 0)),
        (17, lambda G: left(block(G, 'X2')), (-24, 0)),
        (18, lambda G: left(block(G, 'X вне зон')), (-24, 0)),
        (19, lambda G: left(block(G, 'X не определено')), (-24, 0)),
        (20, lambda G: left(G['panel']['notes'][-1]), (-24, 0)),
        (21, lambda G: left(G['dom']['insp'], 20), (-34, 0)),
        (22, lambda G: left(G['dom']['det'], 640), (0, 0)),
    ]),
    'polosa': ('polosa', [
        (1, C('hovRow'), (0, -28)),
        (2, C('hovBand'), (0, -26)),
        (3, lambda G: tuple(G['chart']['link']['spot']), (-30, -24)),
        (4, lambda G: tuple(G['chart']['link']['line']), (26, 0)),
        (5, lambda G: tuple(G['chart']['link']['pill']), (-40, -10)),
        (6, C('pricePill'), (-66, 0)),
        (7, lambda G: (G['chart']['link']['line'][0], G['chart']['bandCy'] + 30), (40, 10)),
        (8, lambda G: left(G['dom']['insp'], 20), (-34, 0)),
    ]),
    'okno': ('okno', [
        (1, C('hovCol'), (34, -20)),
        (2, C('hovColChart'), (34, 0)),
        (3, lambda G: (G['chart']['hovCol'][0], G['chart']['taxis'][1] + 14), (-60, -12)),
        (4, lambda G: left(G['dom']['insp'], 20), (-34, 0)),
    ]),
    'zona': ('zona', [
        (1, lambda G: ctr(zone(G, 'R2')['bb']), (-90, -40)),
        (2, C('zoneCells'), (-30, 26)),
        (3, lambda G: tuple(G['chart']['link']['spot']), (30, -26)),
        (4, lambda G: tuple(G['chart']['link']['line']), (30, 0)),
        (5, lambda G: left(block(G, 'R2')), (-24, 0)),
        (6, lambda G: left(G['dom']['insp'], 20), (-34, 0)),
        (7, lambda G: left(G['dom']['deth'], 220), (0, -24)),
    ] + [(8 + j, (lambda j: (lambda G: (G['det']['cards'][j]['r'][0] + G['det']['cards'][j]['r'][2] - 26, G['det']['cards'][j]['r'][1] + 14)))(j), (0, 0)) for j in range(6)]),
    'sessiya': ('sessiya', [
        (1, lambda G: tuple(G['chart']['pair']['X']), (28, -24)),
        (2, lambda G: tuple(G['chart']['pair']['R']), (28, 26)),
        (3, lambda G: tuple(G['chart']['pair']['path']), (0, -30)),
        (4, lambda G: left(block(G, 'Сессия семьи')), (-24, 0)),
        (5, lambda G: left(G['dom']['insp'], 20), (-34, 0)),
    ]),
    'oblast': ('oblast', [
        (1, lambda G: ctr(next(a for a in G['chart']['area'] if a['part'] == 'frame')['box']), (0, 50)),
        (2, lambda G: ctr(next(a for a in G['chart']['area'] if a['part'] == 'window')['box']), (0, -28)),
        (3, lambda G: ctr(next(a for a in G['chart']['area'] if a['part'] == 'band')['box']), (34, 0)),
        (4, lambda G: left(block(G, 'Выбранная область')), (-24, 0)),
        (5, lambda G: left(block(G, 'X в полосе за всю сессию')), (-24, 0)),
        (6, lambda G: left(block(G, 'заходили в полосу · вся сессия')), (-24, 0)),
    ]),
    'uroven': ('uroven', [
        (1, C('level'), (0, -24)),
        (2, lambda G: left(block(G, 'Уровень')), (-24, 0)),
        (3, lambda G: left(block(G, 'дальше по подтверждению · вся сессия')), (-24, 0)),
        (4, lambda G: left(block(G, 'дальше по подтверждению · после')), (-24, 0)),
    ]),
    'put': ('put', [
        (1, D('mode'), (0, 30)),
        (2, C('filmCell'), (0, -28)),
        (3, C('filmCol'), (0, -28)),
        (4, lambda G: left(block(G, 'Путь семьи')), (-24, 0)),
    ]),
    'slom': ('slom', [
        (1, C('brkPill'), (34, -22)),
        (2, lambda G: left(G['panel']['seg']), (-24, 0)),
        (3, lambda G: left(block(G, 'Семья слома ·')), (-24, 0)),
        (4, lambda G: (G['chart']['proj'][0] + 30, G['chart']['proj'][1] + 10), (0, 26)),
        (5, lambda G: left(block(G, 'зон нет')), (-24, 0)),
        (6, lambda G: (G['chart']['band'][0] + G['chart']['band'][2] * 0.7, G['chart']['bandCy']), (0, -40)),
    ]),
}


def main():
    for out, (state, marks) in MARKS.items():
        G = json.loads((RAW / (state + '.json')).read_text(encoding='utf-8'))
        im = Image.open(RAW / (state + '.png')).convert('RGB')
        d = ImageDraw.Draw(im)
        for n, target, off in marks:
            tx, ty = target(G)
            mx, my = tx + off[0], ty + off[1]
            if off != (0, 0):
                d.line([(tx, ty), (mx, my)], fill=YELLOW, width=2)
                d.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], outline=YELLOW, width=2)
            d.ellipse([mx - 13, my - 13, mx + 13, my + 13], fill=YELLOW, outline=INK, width=2)
            t = str(n)
            w = d.textlength(t, font=FONT)
            d.text((mx - w / 2, my - 9), t, fill=INK, font=FONT)
        im.save(OUT / (out + '.png'), optimize=True)
        print('img/' + out + '.png', len(marks), 'markers')


if __name__ == '__main__':
    main()
