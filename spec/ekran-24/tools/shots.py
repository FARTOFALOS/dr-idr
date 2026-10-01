"""Snapshots of screen 24 for the annotated specification (spec/ekran-24/).

For every state below: a 1920 x 1000 screenshot of the running local screen and the geometry of every layer and block
(the page's own `&geo=1` export, read from the DOM). Both come from the same address, so the markers drawn by
annotate.py land on the elements. History days of NQ only: screenshots of the tool and page geometry, no tape and no
per-session data (AGENTS.md rule 1).

python spec/ekran-24/tools/shots.py        (the server must run: start-dr-lab.cmd -NoBrowser)
python spec/ekran-24/tools/annotate.py     (then: the numbered pictures in spec/ekran-24/img/)
"""
import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / 'img' / 'raw'
PROFILE = HERE / '.chrome'            # a throw-away browser profile (git-ignored)
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
BASE = 'http://127.0.0.1:8767/24/'

# name -> address fragment (a history day of NQ at a slice, with the state shown)
STATES = {
    'obzor':     '#date=2025-12-09&session=RDR&at=11:00',
    'polosa':    '#date=2025-12-09&session=RDR&at=11:00&hov=pcell:X:9',
    'okno':      '#date=2025-12-09&session=RDR&at=11:00&hov=tcell:19',
    'zona':      '#date=2025-12-09&session=RDR&at=11:00&ev=R&zone=2&det=1',
    'sessiya':   '#date=2025-12-09&session=RDR&at=11:00&pt=8',
    'oblast':    '#date=2025-12-09&session=RDR&at=11:00&ev=X&area=8:12:2:5',
    'uroven':    '#date=2025-12-09&session=RDR&at=11:00&lvl=u2',
    'put':       '#date=2025-12-09&session=RDR&at=11:00&mode=path',
    'slom':      '#date=2025-12-10&session=RDR&at=14:30',
}


def run(args):
    return subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                           '--virtual-time-budget=10000', '--user-data-dir=' + str(PROFILE)] + args,
                          capture_output=True, text=True, encoding='utf-8', timeout=120)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for name, frag in STATES.items():
        url = BASE + frag + '&geo=1'
        run(['--window-size=1920,1000', '--screenshot=' + str(RAW / (name + '.png')), url])
        # in --dump-dom the visible area is 16 x 95 px smaller than the window: a larger window gives the same 1920 x 1000
        dom = run(['--window-size=1936,1095', '--dump-dom', url]).stdout
        m = re.search(r'<script type="application/json" id="geo">(.*?)</script>', dom, re.S)
        if not m:
            raise SystemExit('no geometry for ' + name + ' (is the server running?)')
        geo = json.loads(m.group(1))
        if (geo['W'], geo['H']) != (1920, 1000):
            raise SystemExit(f'{name}: the page was {geo["W"]} x {geo["H"]}, not 1920 x 1000')
        (RAW / (name + '.json')).write_text(json.dumps(geo, ensure_ascii=False, indent=1), encoding='utf-8')
        print('img/raw/' + name + '.png + .json')


if __name__ == '__main__':
    main()
