"""Numbered markers on the design 24 snapshots for meaning/10-dizajn-24.md (the numbers are explained there).

python meaning/img/annotate24.py      (after the snapshots in design/sozvezdiya-24/shots/v1, the first look of 24; history days of NQ, screenshots
                                       of the tool, which AGENTS.md rule 1 allows; no tape, no per-session data)
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, '..', '..', 'design', 'sozvezdiya-24', 'shots', 'v1')   # the look before «Окна времени»
FONT = ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf', 15)
P = 1622   # the markers of the right panel stand on its left edge

# source snapshot -> (picture, [(number, marker centre, point it refers to or None)])
MARKS = {
    '1-rdr-otkat.png': ('24-obzor.png', [
        (1, (520, 100), (455, 27)), (2, (650, 100), (640, 27)), (3, (900, 480), (918, 367)), (4, (1000, 66), (1043, 95)),
        (5, (330, 250), (352, 386)), (6, (400, 800), (455, 800)), (7, (1585, 600), (1563, 380)), (8, (1230, 860), (1280, 930)),
        (9, (1400, 870), (1364, 940)), (10, (P, 66), None), (11, (P, 108), None), (12, (P, 160), None), (13, (P, 192), None),
        (14, (P, 262), None), (15, (180, 985), (95, 989)), (16, (1360, 75), (1325, 27))]),
    '2-rdr-rasshirenie-oblast.png': ('24-oblast.png', [
        (1, (950, 545), (950, 592)), (2, (1135, 540), (1072, 572)), (3, (1390, 560), (1312, 606)), (4, (1100, 860), (1153, 805)),
        (5, (1010, 880), (950, 938)), (6, (900, 80), (832, 27)), (7, (P, 411), None), (8, (P, 437), None), (9, (P, 480), None),
        (10, (P, 552), None)]),
    '3-put-semi.png': ('24-put-semi.png', [
        (1, (560, 100), (551, 27)), (2, (700, 100), (690, 27)), (3, (880, 230), (900, 300)), (4, (380, 280), (500, 420)),
        (5, (700, 905), (644, 955)), (6, (1600, 100), (1556, 410)), (7, (P, 140), None), (8, (P, 218), None), (9, (P, 252), None)]),
    '4-semya-sloma.png': ('24-slom.png', [
        (1, (900, 380), (950, 445)), (2, (P, 66), None), (3, (P, 104), None), (4, (664, 110), (664, 27)), (5, (1230, 760), (1279, 647)),
        (6, (1590, 450), (1560, 604))]),
    '5-uroven-detali.png': ('24-uroven.png', [
        (1, (700, 520), (700, 566)), (2, (P, 345), None), (3, (P, 380), None), (4, (P, 424), None), (5, (P, 466), None),
        (6, (230, 790), (150, 868)), (7, (580, 941), (530, 941)), (8, (1300, 860), (1300, 906)), (9, (1500, 855), (1500, 890))]),
    '6-odr-sessiya.png': ('24-sessiya.png', [
        (1, (930, 500), (930, 412)), (2, (1150, 200), (1073, 255)), (3, (760, 500), (821, 445)), (4, (680, 150), (749, 117)),
        (5, (P, 258), None), (6, (P, 325), None)]),
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
    im = Image.open(os.path.join(SHOTS, src)).convert('RGB')
    d = ImageDraw.Draw(im)
    for n, c, p in marks:
        mark(d, n, c, p)
    im = im.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    im.save(os.path.join(HERE, dst), optimize=True)
    print(dst)
