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
        (1, (1394, 212), (1345, 246)), (2, (1196, 186), (1250, 250)), (3, (862, 592), (905, 522)),
        (4, (1071, 356), (1071, 392)), (5, (903, 404), (930, 452)), (6, (1598, 570), (1560, 520)),
        (7, (958, 880), (985, 926)), (8, (1624, 60), None), (9, (1624, 272), None),
        (10, (1624, 484), None), (11, (1624, 596), None), (12, (1624, 707), None)]),
    'brk.png': ('22-bez-sopostavleniya.png', [
        (1, (1624, 86), None), (2, (1624, 247), None), (3, (1624, 348), None), (4, (1624, 494), None),
        (5, (1085, 610), (1133, 672)), (6, (470, 690), (527, 646))]),
    'wait.png': ('22-do-podtverzhdeniya.png', [
        (1, (1624, 84), None), (2, (1624, 122), None), (3, (1392, 305), (1345, 337)), (4, (1624, 330), None)]),
    'conf_hl_4.png': ('22-mesto-navedenie.png', [
        (1, (1394, 212), (1345, 246)), (2, (1150, 170), (1235, 238)), (3, (1175, 880), (1218, 958)), (4, (820, 330), (880, 297))]),
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
