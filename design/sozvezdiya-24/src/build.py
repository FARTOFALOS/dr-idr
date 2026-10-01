"""Builds design 24 «Границы хода» into the running tool: lab/dist/24/index.html + d24.js.

Design 24 = design 22's working screen (design/sozvezdiya-22) with its statistical layer replaced by the semantic
specification DR-LAB-SEM-1.0 (meaning/lens/2026-10-01-specifikaciya-v1.md); data from lab/scene24.py (/api/d24/*).
Design 22 stays the working screen at http://127.0.0.1:8767/ and is not touched; design 24 opens at /24/ (the desktop
shortcut «DR Lab 24», start-dr-lab-24.cmd). There is no synthetic mockup: a date of 2006-2025 opens as if it were today.

python build.py        (from this folder)
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(REPO, 'lab', 'dist', '24')


def read(name):
    return open(os.path.join(HERE, name), encoding='utf-8').read()


page = read('page.html').replace('/*__PANEL24CSS__*/', read('panel.css'))
app = read('app.js').replace('  /*__PANEL24__*/\n', read('panel.js'))
assert '/*__PANEL24CSS__*/' not in page and '/*__PANEL24__*/' not in app, 'template changed: update build.py'
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8', newline='\n').write(page)
open(os.path.join(OUT, 'd24.js'), 'w', encoding='utf-8', newline='\n').write(
    '// Built from design/sozvezdiya-24/src (app.js + panel.js) by its build.py: edit there.\n' + app)
print('lab/dist/24/index.html', round(len(page) / 1e3), 'kB · d24.js', round(len(app) / 1e3), 'kB')
