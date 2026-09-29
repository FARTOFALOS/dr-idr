"""Numbered markers on the design 22 snapshots for meaning/04-dizajn-22.md (the numbers are explained there).

python meaning/img/annotate.py      (after design/sozvezdiya-22/src/shots.sh; synthetic mockup pictures only)
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(HERE, '..', '..', 'design', 'sozvezdiya-22', 'snap')
FONT = ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf', 15)

# (number, marker centre, point it refers to or None)
MARKS = {
    'conf.png': ('22-obzor.png', [
        (1, (1395, 200), (1313, 232)), (2, (1000, 195), (1000, 262)), (3, (905, 635), (1000, 697)),
        (4, (960, 775), (1060, 812)), (5, (1000, 575), (1050, 505)), (6, (1600, 305), (1567, 265)),
        (7, (1180, 870), (1175, 918)), (8, (330, 800), (262, 800)), (9, (560, 670), (560, 632)),
        (10, (1624, 60), None), (11, (1624, 176), None), (12, (1624, 453), None), (13, (1624, 577), None)]),
    'brk.png': ('22-bez-sopostavleniya.png', [
        (1, (1624, 72), None), (2, (1624, 118), None), (3, (1624, 240), None), (4, (1624, 493), None),
        (5, (960, 420), (962, 478)), (6, (470, 760), (527, 716))]),
    'wait.png': ('22-do-podtverzhdeniya.png', [
        (1, (1624, 84), None), (2, (1624, 122), None), (3, (1392, 295), (1345, 331)), (4, (1624, 268), None),
        (5, (480, 290), (480, 350))]),
    'conf_hl_3.png': ('22-mesto-navedenie.png', [
        (1, (1624, 247), None), (2, (700, 230), (778, 268)), (3, (1150, 880), (1225, 958)), (4, (1180, 205), (1100, 262))]),
}


def mark(d, n, c, p):
    if p:
        d.line([c, p], fill=(247, 201, 72), width=2)
        d.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3], fill=(247, 201, 72))
    r = 13
    d.ellipse([c[0] - r, c[1] - r, c[0] + r, c[1] + r], fill=(247, 201, 72), outline=(11, 12, 16), width=2)
    t = str(n)
    w = d.textlength(t, font=FONT)
    d.text((c[0] - w / 2, c[1] - 9), t, font=FONT, fill=(11, 12, 16))


for src, (dst, marks) in MARKS.items():
    im = Image.open(os.path.join(SNAP, src)).convert('RGB')
    d = ImageDraw.Draw(im)
    for n, c, p in marks:
        mark(d, n, c, p)
    im.save(os.path.join(HERE, dst), optimize=True)
    print(dst)
