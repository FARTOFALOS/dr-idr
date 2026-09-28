"""Collects every DR Lab screen design so far into this folder and writes ИСТОРИЯ.html: one page, top to bottom, numbered,
every design running live inside it (the same interaction as on its canvas).

python make_history.py            rebuild interactive/ and the page (fast)
python make_history.py --shots    also re-take the snapshots in images/ (headless Chrome, a few minutes)

The .dc.html designs run on the Claude Design runtime, copied from the canvas as interactive/support.js (not ours, kept
out of git; if it is missing, read artifact-type/dc-runtime.js of the canvas CANVAS_NEW with the Artifact tool and save it
there). Sources that exist nowhere else in the repo live in sources/ (8-10 and 17-19). Every design is a synthetic
mockup: no market data anywhere.
"""
import html
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
CHROME = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
RENDER = os.path.join(REPO, 'design', 'clusters-2026-09-28', 'src', 'render.js')
IMG, INTER, TMP, SRC = (os.path.join(HERE, d) for d in ('images', 'interactive', '_tmp', 'sources'))
for d in (IMG, INTER, TMP):
    os.makedirs(d, exist_ok=True)
SHOTS = '--shots' in sys.argv

CANVAS_OLD = 'https://claude.ai/artifact/Hyhworqk9xqZtmWqbV4ev2'
CANVAS_NEW = 'https://claude.ai/artifact/9NTzLxzdq8qiBRDjpqoDR7'
STATES = {'conf': '{}', 'wait': '{"scene":"wait","rp":{"sess":"RDR","at":640}}', 'brk': '{"scene":"brk"}'}


def shot(html_path, png, w=1920, h=1000, extra=()):
    if not SHOTS and os.path.exists(png):
        return True
    prof = os.path.join(TMP, 'chrome-profile')
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
                    '--window-size=%d,%d' % (w, h), '--user-data-dir=' + prof, *extra, '--screenshot=' + png,
                    'file:///' + html_path.replace('\\', '/')], capture_output=True, timeout=90)
    return os.path.exists(png)


def dc_shot(dc_file, state, png):
    if not SHOTS and os.path.exists(png):
        return True
    tmp = os.path.join(TMP, os.path.basename(png).replace('.png', '.html'))
    subprocess.run(['node', RENDER, dc_file, STATES[state], tmp], capture_output=True, check=True, timeout=120)
    return shot(tmp, png)


def copy(src, dst):
    if os.path.exists(src):
        shutil.copyfile(src, dst)
        return True
    return False


# ---------- the runtime of the Claude Design canvas: lets a .dc.html run on its own ----------
if not os.path.exists(os.path.join(INTER, 'support.js')):
    print('WARNING: interactive/support.js is missing, designs 1-4 and 8-16 will not run: read artifact-type/dc-runtime.js of ' + CANVAS_NEW)

# ---------- 1-4: the redesign of 24-25 September ----------
red = os.path.join(REPO, 'design', 'redesign-2026-09')
for src, dst in [('Main', '01-terminal'), ('Scenario', '02-scenariy'), ('Clean', '03-chistyy-grafik'), ('ScenarioV2', '04-b-prime')]:
    copy(os.path.join(red, 'built', src + '.dc.html'), os.path.join(INTER, dst + '.dc.html'))
for a, b in [('A_live', '01-terminal'), ('B_live', '02-scenario'), ('C_live', '03-clean'),
             ('B2_live', '04-b-prime-live'), ('B2_scrub', '04-b-prime-scrub'), ('B2_col', '04-b-prime-column'), ('B2_odr', '04-b-prime-odr')]:
    copy(os.path.join(red, 'snapshots', a + '.png'), os.path.join(IMG, b + '.png'))

# ---------- 5-7: the semantic architecture prototype (another session), one page with three layouts ----------
proto = open(os.path.join(REPO, 'design', 'semantic-2026-09', 'prototype.html'), encoding='utf-8').read()
live57 = ('<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>DR Lab · смысловая архитектура</title>'
          '<style>:root{color-scheme:dark}html,body{margin:0;background:#0c1015}body{padding:12px}</style></head><body>' + proto +
          '<script>setTimeout(function(){var l=(location.hash.match(/[ABC]/)||[])[0];'
          'var b=l&&document.querySelector(\'[data-layout="\'+l+\'"]\');if(b)b.click();},200);</script></body></html>')
open(os.path.join(INTER, '05-07-smyslovaya-arkhitektura.html'), 'w', encoding='utf-8').write(live57)
for lay, name in [('A', '05-pole-ceny'), ('B', '06-scenariy'), ('C', '07-dve-distancii')]:
    p = os.path.join(TMP, name + '.html')
    open(p, 'w', encoding='utf-8').write(live57.replace('location.hash', "'#%s'" % lay))
    shot(p, os.path.join(IMG, name + '.png'), 1920, 1080, ('--force-dark-mode', '--virtual-time-budget=4000'))

# ---------- 8-10: this session, version 1 (smoothed clusters), from the copy of the canvas saved before it changed ----------
v1src = os.path.join(SRC, 'v1-sglazhennye')   # the canvas as it was before version 2 replaced it
for f, n in [('Main', '08-v1-klastery'), ('Summary', '09-v1-svodka'), ('Projections', '10-v1-proekcii')]:
    copy(os.path.join(v1src, f + '.dc.html'), os.path.join(INTER, n + '.dc.html'))
for n, states in [('08-v1-klastery', ('conf', 'wait', 'brk')), ('09-v1-svodka', ('conf',)), ('10-v1-proekcii', ('conf',))]:
    for s in states:
        dc_shot(os.path.join(INTER, n + '.dc.html'), s, os.path.join(IMG, '%s-%s.png' % (n, s)))

# ---------- 11-16: this session, version 2 (one glyph per 5-minute cell) and the density row ----------
built = os.path.join(REPO, 'design', 'clusters-2026-09-28', 'built', 'project')
V2 = [('Main', '11-v2-klastery', ('conf', 'wait', 'brk')), ('Summary', '12-v2-svodka', ('conf', 'brk')),
      ('Projections', '13-v2-proekcii', ('conf', 'brk')), ('Solid', '14-nadezhnost', ('conf', 'wait', 'brk')),
      ('Units', '15-edinicy', ('conf', 'wait', 'brk')), ('Mosaic', '16-mozaika', ('conf', 'wait', 'brk'))]
for f, n, states in V2:
    copy(os.path.join(built, f + '.dc.html'), os.path.join(INTER, n + '.dc.html'))
    for s in states:
        dc_shot(os.path.join(INTER, n + '.dc.html'), s, os.path.join(IMG, '%s-%s.png' % (n, s)))

# ---------- 17-19: the fresh-eyes variants (a separate agent that saw only the meaning and the strategy) ----------
fresh = os.path.join(SRC, '17-19-svezhiy-vzglyad')   # the separate agent's page, notes and brief
copy(os.path.join(fresh, 'index.html'), os.path.join(INTER, '17-19-svezhiy-vzglyad.html'))
copy(os.path.join(fresh, 'NOTES.md'), os.path.join(INTER, '17-19-svezhiy-vzglyad-NOTES.md'))

# ---------- 20: the synthesis of the operator's picks of 28 September («Созвездия») ----------
sz = os.path.join(REPO, 'design', 'sozvezdiya-2026-09-28')
copy(os.path.join(sz, 'built', 'index.html'), os.path.join(INTER, '20-sozvezdiya.html'))
for s in ('conf', 'wait', 'brk'):
    copy(os.path.join(sz, 'snap', s + '.png'), os.path.join(IMG, '20-sozvezdiya-%s.png' % s))

# ---------- 21: design 20 with the right panel reworked (the second agent's variant, then the operator's rules) ----------
copy(os.path.join(REPO, 'design', 'sozvezdiya-21', 'built', 'index.html'), os.path.join(INTER, '21-sozvezdiya-panel.html'))

# ---------- the page ----------
STAGES = [
    ('s1', '24.09 · первые три варианта', 'Claude, сессия редизайна. Они же на холсте ' + CANVAS_OLD + ' (второй ряд).'),
    ('s2', '25.09 · выбранный B′', 'Выбран вами на холсте ' + CANVAS_OLD + ' (первый ряд). Описание: docs/DESIGN.md.'),
    ('s3', '25.09 · «смысловая архитектура»', 'Другая сессия (смысловой архитектор): design/semantic-2026-09/CONCEPT.md. Это один прототип с тремя раскладками: кнопки A / B / C над ним, «Следующая сцена» внизу.'),
    ('s4', '28.09 · версия 1: сглаженные кластеры', 'Эта сессия, первая публикация. Вы отклонили: «треугольник должен быть один на клетку, с пустотами между ними». Состояния — переключатель «Пример» вверху макета.'),
    ('s5', '28.09 · версия 2: один знак = одна клетка 5 минут', 'Эта сессия, сейчас на холсте ' + CANVAS_NEW + ' (первый ряд). Состояния — переключатель «Пример» вверху макета.'),
    ('s6', '28.09 · как показать силу кластера', 'Та же раскладка 1, четыре способа отрисовки (холст ' + CANVAS_NEW + ', второй ряд). «Ступени» — это дизайн 11.'),
    ('s7', '28.09 · свежий взгляд', 'Отдельный агент видел только смысл и стратегию, без наших макетов. Общее у всех трёх: «место» = область 15 мин × 0,1 W с долей k из N; сильное / заметное / слабое по доле, числу сессий и тому, держится ли доля во всех трёх эпохах (пороги — его выбор); продолжение — янтарь, откат — синий. Вариант и состояние — переключатели вверху справа (варианты 1 / 2 / 3 в одном файле). Его заметки: interactive/17-19-svezhiy-vzglyad-NOTES.md.'),
    ('s8', '28.09 · 20: сборка по вашим пометкам', 'Из ваших пометок: веер и типичный путь (1), уровни как в 1 и раздельные, навигация TradingView (5–6, 11–16), проекции у шкалы (3, 10, 13), полоса времени снизу (4, 8) — выше и раскрывается, звёздное небо (18), созвездия-плотности вместо квадратов (8–9), клик по свече — как было в тот момент (1), панель с процентами (17–19), шесть графиков истории (1). Исходники: design/sozvezdiya-2026-09-28/. Адрес состояния: #conf, #wait, #brk, &pin=pull:1, &strip=1, &at=11:35.'),
    ('s9', '28.09 · 21: рабочий экран DR Lab (панель — только то, что заслужило место)', 'Тот же график, что в 20. Панель справа: второй агент предложил смысловую панель, вы оставили только «Дальше по похожим» и «Места» — проценты, без числа сессий, и каждая строка — ссылка: наведение зажигает на графике уровень, место, его самую плотную цену и время. Исходники: design/sozvezdiya-21/.'),
]
FR = '17-19-svezhiy-vzglyad.html#v=%s&s=conf'
# (number, title, stage, file in interactive/, frame w, h, what differs)
D = [
    (1, 'A · «Терминал»', 's1', '01-terminal.dc.html', 1920, 1000, ['график + «лесенка» касаний у шкалы цены (проценты у уровней)', 'колонка справа: «DR удержится», зоны отката и экстремума 1–3, сессии дня, DR/IDR', 'кластеры — синие клетки, зоны пунктиром с номерами, веер', 'внизу ряд из шести графиков истории']),
    (2, 'B · «Сценарий»', 's1', '02-scenariy.dc.html', 1920, 1000, ['колонка справа: инспектор, РИСК / ВХОД / ЦЕЛЬ', 'кластеры — мягкие облака с изолиниями', 'внизу ряд графиков истории']),
    (3, 'C · «Чистый график»', 's1', '03-chistyy-grafik.dc.html', 1920, 1000, ['без боковой колонки: главные числа в строке сверху', 'зоны 1–3 подписаны прямо на графике (доля и время)', 'профиль по цене у шкалы']),
    (4, 'B′ · «Сценарий» — выбран', 's2', '04-b-prime.dc.html', 1920, 1000, ['продолжение — зелёные облака с изолиниями, откат — красные треугольники по ходу отката', 'тихие проценты без рамок; весь торговый день, колесо и перетаскивание', 'полоса над осью времени: по прошлому — прогноз того момента, по будущему — кластеры этого времени', 'колонка РИСК / ВХОД / ЦЕЛЬ, внизу ряд истории, полоса дня; клик по свече — повтор']),
    (5, 'A · «Поле цены»', 's3', '05-07-smyslovaya-arkhitektura.html#A', 1920, 1080, ['максимум места для свечей, справа только шкала и узкий профиль', 'облака отката («пыльная роза») и расширения («нефрит»), без треугольников', 'подробности — компактная карточка по выбору']),
    (6, 'B · «Сценарий» (инспектор события)', 's3', '05-07-smyslovaya-arkhitektura.html#B', 1920, 1080, ['справа узкий инспектор: состояние → текущая зона → барьер → отмена', 'модели дня строкой над графиком, фазы дня меняют акцент', 'распределения — выдвижная вкладка']),
    (7, 'C · «Две дистанции» (M5 + M1)', 's3', '05-07-smyslovaya-arkhitektura.html#C', 1920, 1080, ['слева M5 с контекстом, справа увеличенная M1 выбранной области', 'под M1: событие, VIB, две исходные свечи и время теста']),
    (8, '1 · «Кластеры на графике» (сглаженные)', 's4', '08-v1-klastery.dc.html', 1920, 1000, ['график во всю ширину, у каждого кластера подпись «доля · время»', 'откат — полутон из треугольников по сглаженной плотности, продолжение — ступенчатые области с контурами', 'кластер = обведённый контур (плотность ≥ половины пика)']),
    (9, '2 · «График + сводка» (сглаженные)', 's4', '09-v1-svodka.dc.html', 1920, 1000, ['справа колонка: день, модели, факты сессии, кластеры строками', 'на графике у кластеров только номера']),
    (10, '3 · «Проекции» (сглаженные)', 's4', '10-v1-proekcii.dc.html', 1920, 1000, ['на графике кластеры без чисел', 'те же экстремумы полосками: по цене у шкалы и по времени над осью']),
    (11, '1 · «Кластеры на графике» (клетки 5 мин, ступени)', 's5', '11-v2-klastery.dc.html', 1920, 1000, ['один знак = одна клетка 5 мин × 0,1 IDR, между знаками пустоты, без сглаживания', 'четыре ступени размера и яркости: самые частые клетки крупные, единичные — точка', 'треугольник — откат, кружок — продолжение, до подтверждения серые «Верх» и «Низ»', 'кластер = соседние клетки самой частой ступени, подпись «доля · время»']),
    (12, '2 · «График + сводка» (клетки 5 мин)', 's5', '12-v2-svodka.dc.html', 1920, 1000, ['та же отрисовка, справа колонка сводки и кластеры строками']),
    (13, '3 · «Проекции» (клетки 5 мин)', 's5', '13-v2-proekcii.dc.html', 1920, 1000, ['та же отрисовка, полоски по цене и по времени с процентами']),
    (14, 'Плотность · «Надёжность»', 's6', '14-nadezhnost.dc.html', 1920, 1000, ['размер треугольника — доля клетки', 'заливка — сколько сессий за ним: сплошной ≥ 8, полупрозрачный 4–7, контур 2–3, точка — одна', 'сильные места видны по сплошным знакам']),
    (15, 'Плотность · «Единицы»', 's6', '15-edinicy.dc.html', 1920, 1000, ['блоки 15 мин × 0,2 IDR от текущего момента', 'каждый маленький знак = 1% похожих сессий — сколько знаков, столько процентов']),
    (16, 'Плотность · «Мозаика клеток»', 's6', '16-mozaika.dc.html', 1920, 1000, ['клетки нарисованы плитками: плотная — самые частые, светлая — частые, контур — реже, точка — единичные', 'читается как тепловая карта с явными ступенями']),
    (17, '1 · «Профиль» — где по цене', 's7', FR % 'profile', 1920, 1000, ['время свёрнуто: справа от свечей полосы «мест» от общей нулевой линии, длина полосы = доля (k из N)', 'рядом «ворс» — по штриху на каждую похожую сессию', 'сильное место — сплошная полоса и жирная цифра, заметное — полупрозрачная, слабое — пунктир', 'график показывает весь день; время места — только цифрой и мини-линейкой']),
    (18, '2 · «Рой» — вот сами сессии', 's7', FR % 'swarm', 1920, 1000, ['будущее до 16:00 открыто: каждая похожая сессия — точка в своём времени и цене экстремума', 'места — рамки поверх точек с чипом «доля · k из N»; сильное — густая яркая толпа и толстая рамка, слабое — пунктир', 'серые точки — разброс «вне мест»', 'до подтверждения — «Верх» и «Низ» и доли первого подтверждения ↑ / ↓ / не будет']),
    (20, '«Созвездия» — сборка по вашим пометкам (рабочий вариант)', 's8', '20-sozvezdiya.html#conf', 1920, 1000, ['звёздное небо: каждая похожая сессия — две тусклые точки (продолжение и откат)', 'по три места на сторону: откат — от верхней границы / от центра / retirement setup; продолжение — до следующей ступени / до второй / дальше; доля места маленькой фоновой цифрой, форма — где в нём плотнее всего', 'наведение на созвездие: подсвечивается квадрат 15 минут под курсором и уходит вниз к оси времени, со своими временем и ценами', 'веер 20–80 % и его медиана штрихом, как в 1', 'уровни: DR сплошная, IDR штрих, mid точки, STD тонкие; прошлые сессии — такие же белые линии тише; VIB; подпись справа', 'плотность по цене справа от шкалы, ярче где больше; полоса времени снизу; шесть графиков истории выезжают снизу при наведении', 'панель: день сейчас, дальше по похожим, места (три на сторону); «⚙ Настройки» — все цвета, яркости и линии; клик по свече — как было в тот момент']),
    (21, 'Рабочий экран: панель-ссылки, цели, время, риск', 's9', '21-sozvezdiya-panel.html#conf', 1920, 1000, ['с 28.09 это главный экран DR Lab на рыночных данных (http://127.0.0.1:8767); здесь — его макет на синтетических днях', 'ниже «Мест»: цели (дошли · обычно к), время (половина и 70 % откатов и экстремумов), где сценарий сломан (DR удержится, retirement −0,75 и DR после касания, пустой интервал для стопа)', 'справа только «Дальше по похожим» (следующая ступень, DR удержится, где чаще всего продолжение и откат, первые 15 минут) и «Места» по три на сторону: процент, самая плотная цена и её время', 'наведение на строку: ступень — линия и когда до неё обычно доходили; место — его границы, созвездие и самый плотный кусок со временем на оси', 'до подтверждения: ↑ / ↓ / нет и до DR high / low', 'полоски плотности справа контрастнее: самая плотная — ярче всех и в белой рамке', 'кнопки −5м / +5м, «Сводка» — скрыть панель; контуры на момент подтверждения — в «Слои»']),
    (19, '3 · «Табло» — рейтинг мест с доказательствами', 's7', FR % 'board', 1920, 1000, ['под графиком строки мест по рангу: доля, k из N, цена, «у +1,0», окно времени на общей с графиком оси', 'столбики по трём эпохам 2006–12 / 2013–19 / 2020–25: серый — место в этой эпохе проседает', 'слабые места свёрнуты в одну строку, на графике только тонкие рамки с номерами']),
]
for d in D:
    if not os.path.exists(os.path.join(INTER, d[3].split('#')[0])):
        sys.exit('missing interactive/' + d[3])


def linkify(s):
    return re.sub(r'(https://\S+?)(?=[\s,)]|$)', r'<a href="\1" target="_blank" rel="noopener">\1</a>', html.escape(s))


rail, body = [], []
for sid, stitle, snote in STAGES:
    items = [d for d in D if d[2] == sid]
    rail.append('<div class="rs">%s</div>' % html.escape(stitle))
    body.append('<section class="stage"><h2>%s</h2><p class="note">%s</p>' % (html.escape(stitle), linkify(snote)))
    for n, t, _, f, w, h, bullets in items:
        src = 'interactive/' + f
        rail.append('<a href="#d%d" data-n="%d"><b>%d</b>%s</a>' % (n, n, n, html.escape(t)))
        body.append(
            '<article id="d%d"><div class="head"><span class="num">%d</span><h3>%s</h3>'
            '<a class="open" href="%s" target="_blank">открыть отдельно ↗</a></div><ul>%s</ul>'
            '<div class="live" style="aspect-ratio:%d/%d" data-src="%s" data-w="%d" data-h="%d"><span class="wait">макет загружается…</span></div></article>' % (
                n, n, html.escape(t), html.escape(src), ''.join('<li>%s</li>' % html.escape(b) for b in bullets), w, h, html.escape(src), w, h))
    body.append('</section>')

page = '''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>DR Lab · история дизайнов</title>
<style>
:root{--bg:#0B0D10;--panel:#11151B;--line:#232A33;--text:#D1D4DC;--dim:#9AA1AD;--acc:#F7C948;--rail:236px;color-scheme:dark}
html,body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Trebuchet MS",Roboto,Ubuntu,sans-serif}
a{color:#8FB8E8}
nav{position:fixed;left:0;top:0;bottom:0;width:var(--rail);overflow-y:auto;box-sizing:border-box;padding:16px 10px 30px 14px;background:#0F1216;border-right:1px solid var(--line)}
nav h1{font-size:16px;margin:0 0 4px;color:#fff}nav .sub{font-size:12px;color:var(--dim);margin:0 0 10px}
nav .rs{font-size:11px;letter-spacing:.4px;color:var(--dim);margin:14px 0 4px;text-transform:uppercase}
nav a{display:flex;gap:8px;align-items:baseline;padding:4px 6px;border-radius:6px;color:var(--text);text-decoration:none;font-size:13px;line-height:1.3}
nav a b{flex:0 0 22px;color:var(--acc);text-align:right}nav a:hover{background:#1A1F27}nav a.on{background:#232A33;color:#fff}
main{margin-left:var(--rail);padding:22px 22px 80px}
.lead{color:var(--dim);margin:0 0 6px;max-width:1100px}
h2{font-size:21px;margin:0 0 4px;color:#fff}h3{font-size:18px;margin:0}
.stage{margin:34px 0 0;padding-top:16px;border-top:2px solid var(--line)}.note{color:var(--dim);margin:0 0 14px;overflow-wrap:anywhere}
article{margin:18px 0 32px}
.head{display:flex;align-items:center;gap:12px;margin-bottom:6px}.head .open{margin-left:auto;font-size:14px;white-space:nowrap}
.num{display:inline-flex;align-items:center;justify-content:center;min-width:44px;height:44px;border-radius:22px;background:var(--acc);color:#0B0D10;font-size:22px;font-weight:800}
ul{margin:4px 0 10px 22px;padding:0;color:#C3C8D1;columns:2;column-gap:36px}li{break-inside:avoid}
.live{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:6px;background:#0B0D10}
.live iframe{position:absolute;left:0;top:0;border:0;transform-origin:0 0;background:#0B0D10}
.wait{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);color:var(--dim)}
@media (max-width:900px){:root{--rail:0px}nav{display:none}ul{columns:1}}
</style></head><body>
<nav><h1>DR Lab · дизайны</h1><p class="sub">все варианты по порядку, каждый живой</p>__RAIL__</nav>
<main>
<p class="lead">Каждый макет ниже работает так же, как на своём холсте: наведение, клики, колесо — масштаб, перетаскивание — сдвиг, клик по свече — повтор. Колесо над макетом двигает макет, а не страницу: листайте колесом над текстом или над списком слева. «Открыть отдельно ↗» — тот же макет во всю вкладку. Свечи и все числа синтетические.</p>
__BODY__
</main>
<script>
(function () {
  // Each design is a heavy page on the same thread as this one: load them one at a time, nearest first,
  // and drop the ones far away so the page stays responsive.
  var boxes = [].slice.call(document.querySelectorAll('.live')), queue = [], busy = false;
  function fit(b) {
    var f = b.querySelector('iframe');
    if (f) f.style.transform = 'scale(' + (b.clientWidth / +b.dataset.w) + ')';
  }
  function pump() {
    if (busy) return;
    var b = queue.shift();
    if (!b) return;
    if (!b.want || b.querySelector('iframe')) return pump();
    busy = true;
    var f = document.createElement('iframe'), done = false;
    function next() { if (done) return; done = true; setTimeout(function () { busy = false; pump(); }, 120); }
    f.onload = next; setTimeout(next, 5000);
    f.width = b.dataset.w; f.height = b.dataset.h; f.src = b.dataset.src;
    b.appendChild(f); fit(b);
  }
  function want(b) { b.want = true; if (queue.indexOf(b) < 0) queue.push(b); pump(); }
  function drop(b) { b.want = false; var f = b.querySelector('iframe'); if (f) f.remove(); }
  window.addEventListener('resize', function () { boxes.forEach(fit); });
  var near = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) want(e.target); });
  }, { rootMargin: '400px 0px' });
  var far = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (!e.isIntersecting) drop(e.target); });
  }, { rootMargin: '2200px 0px' });
  boxes.forEach(function (b) { near.observe(b); far.observe(b); });
  var nav = document.querySelector('nav'), links = {};
  [].forEach.call(document.querySelectorAll('nav a[data-n]'), function (a) { links[a.dataset.n] = a; });
  var seen = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      for (var k in links) links[k].classList.remove('on');
      var a = links[e.target.id.slice(1)];
      if (!a) return;
      a.classList.add('on');
      var r = a.getBoundingClientRect();
      if (r.top < 60 || r.bottom > innerHeight - 20) nav.scrollTop += r.top - innerHeight / 2;
    });
  }, { rootMargin: '-45% 0px -50% 0px' });
  [].forEach.call(document.querySelectorAll('article'), function (a) { seen.observe(a); });
})();
</script>
</body></html>'''.replace('__RAIL__', ''.join(rail)).replace('__BODY__', '\n'.join(body))
open(os.path.join(HERE, 'ИСТОРИЯ.html'), 'w', encoding='utf-8').write(page)
print('designs', len(D), 'page', round(len(page) / 1e3), 'kB', 'shots' if SHOTS else '(snapshots kept)')
