"""Build the separate working view 23.5 to lab/dist/23-5. Keeps the source and build of screen 24 separate.
The main map is the final R / X of screen 24; the local layer «Съёмы лоу» is sweeps235.js (operator 2026-10-26).
See docs/DR-LAB-23-5-SWEEPS.md before altering the mapping or the appearance.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(REPO, 'lab', 'dist', '23-5')


def read(name):
    return open(os.path.join(HERE, name), encoding='utf-8').read()


page = read('page.html').replace('/*__PANEL24CSS__*/', read('panel.css'))
app = read('app.js').replace('  /*__INTEGRATION24__*/\n', read('integration.js') + '\n' + read('continuations.js') + '\n' + read('pullbacks.js') + '\n' + read('time_sd235.js') + '\n' + read('sweeps235.js')).replace('  /*__PANEL24__*/\n', read('panel.js'))
# DR-LAB-SC-1.1: the page embeds the page registry of the machine contract (estimands, claim forms with their labels,
# fact forms), built by contract/tools/build.py; the page renders only these labels and checks its registry hash
# against the server's envelopes (a contract rebuilt without rebuilding this page is reported, never ignored)
sc11 = open(os.path.join(REPO, 'contract', 'build', 'page_registry.json'), encoding='utf-8').read().strip()
app = app.replace('/*__SC11__*/null', sc11)
assert '/*__PANEL24CSS__*/' not in page and '/*__PANEL24__*/' not in app and '/*__SC11__*/' not in app, 'template changed: update build.py'
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8', newline='\n').write(page)
open(os.path.join(OUT, 'd24.js'), 'w', encoding='utf-8', newline='\n').write(
    '// Built from design/sozvezdiya-23-5/src (app.js + panel.js) by its build.py: edit there.\n' + app)
print('lab/dist/23-5/index.html', round(len(page) / 1e3), 'kB · d24.js', round(len(app) / 1e3), 'kB')
