"""Publish comparison evidence without exporting the private market records collected by the stand."""
import hashlib
import html
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
PACKAGE=ROOT/'meaning/lens/2026-10-14-integration'
LOCAL=ROOT/'lab/.runtime/integration-spec'

LABELS={
 'FOCUS':'Скрытая сводка: свечи и созвездия',
 'WAIT':'До подтверждения',
 'CONF':'Закрытие подтверждающей M5; ещё нет полного остаточного префикса',
 'OPEN':'Открытый вопрос: до середины IDR, все дни',
 'FEW':'Тот же рынок: weekday, мало аналогов ARRIVE',
 'PULL':'NOW R до следующей свечи',
 'REACHED':'Следующая M5: место уже достигнуто',
 'BREAK':'Семья слома и малая опора',
 'ORIGINAL':'Возврат к исходной семье после слома',
 'PATHS':'Старый вид частот и кандидат с отдельными путями',
}

def dump(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

def main():
    rows=json.loads((LOCAL/'comparison.raw.local.json').read_text(encoding='utf-8'))
    public=[]
    for r in rows:
        a,b=r['A'],r['B']
        eq=dict(same_market_cut=a['scene']==b['scene'],same_closed_observations=a['observed']==b['observed'],
                same_base_snapshot_members_extremes_cells_counts=a['base']==b['base'],same_now_values_support_status=a['now']==b['now'],
                checked_passports=all(not v['contract']['unchecked'] for v in (a,b)),
                no_contract_violation=all(not v['contract']['violations'] for v in (a,b)),
                no_page_scroll=all(v['geometry']['no_page_scroll'] for v in (a,b)),
                same_chart_geometry=a['geometry']['canvas']==b['geometry']['canvas'])
        assert all(eq.values()), (r['id'],r['viewport'],eq)
        assert a['summary_hidden']==b['summary_hidden']==(r['id']=='FOCUS')
        stem=r['id'].lower()+'-'+str(r['viewport'][0])
        imgs={v:'img/'+stem+'.'+v+'.png' for v in ('A','B')}
        digests={v:hashlib.sha256((PACKAGE/'comparison'/p).read_bytes()).hexdigest() for v,p in imgs.items()}
        public.append(dict(scene_id=r['id'],label=LABELS[r['id']],instrument='NQ',session='RDR',date=b['scene']['date'],
            cut=b['scene']['cut'],scope='weekday' if r['id'] in ('WAIT','CONF','FEW','BREAK','ORIGINAL') else 'all',
            viewport=r['viewport'],checks=eq,summary_hidden=b['summary_hidden'],
            candidate_routine_counter_policy='CONFLICT_PRE_COUNTS' if b['panel_counters'] else 'NO_ROUTINE_COUNTS_DETECTED_IN_SCANNED_FIELDS',
            candidate_arrive_status=(b['arrive'] or {}).get('status'),
            candidate_now_status=(b['now'] or {}).get('status'),images=imgs,image_sha256=digests))
    checks=[]
    if (LOCAL/'branch-checks.raw.local.json').exists():
        for r in json.loads((LOCAL/'branch-checks.raw.local.json').read_text(encoding='utf-8')):
            checks.append(dict(scene=r['scene'],viewport=r['viewport'],variant=r['variant'],test=r['test'],
                               problems=r['result']['problems'],note='frozen branch check rerun, not operator acceptance'))
    report=dict(version='I24-PAIR-1',source='two frozen git archives on own local servers; shared existing CDP harness',
        pairs=len(public),rendered_screens=2*len(public),human_acceptance='NOT_RUN',
        baseline='2672841da928f7379e5d7bc27eef8ff3e0fa5738',
        candidate='0f1ae26828db402f203660b6deab14d15262c185 + preview-definition.json',
        selection='preserve accepted composition; transfer only individually verified relations, not wholesale B',
        scenes=public,branch_checks=checks,
        coverage_boundary=['declared NQ/RDR scenes only; not the whole market history','comparison is not a new predictor validation',
                           'PRE/ARRIVE and new labels/paths are candidates','raw OHLC/case paths remain in lab/.runtime',
                           'mutations, live return, cold boot and all H tasks belong to implementation acceptance, not screenshot parity'])
    dump(PACKAGE/'comparison/report.json',report)
    options=''.join('<option value="'+s+'">'+html.escape(LABELS[s])+'</option>' for s in LABELS)
    data=json.dumps(public,ensure_ascii=False)
    page='''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DR Lab · одинаковые реальные сцены A/B</title><style>
body{margin:0;background:#111820;color:#e5edf5;font:15px system-ui,sans-serif}header{padding:14px 20px;background:#1a2633;position:sticky;top:0;z-index:2}h1{font-size:20px;margin:0 0 8px}p{margin:7px 0;max-width:1100px;line-height:1.45}select,button{font:inherit;background:#26384b;color:#fff;border:1px solid #607086;border-radius:5px;padding:6px;margin:5px 6px 0 0}button.active{border-color:#efb376;background:#4b3b2d}main{padding:12px 20px}#facts{padding:8px 0}figure{margin:8px 0}figcaption{padding:7px 0;color:#efb376}img{display:block;width:100%;height:auto;border:1px solid #394958}#images.side{display:grid;grid-template-columns:1fr 1fr;gap:12px}a{color:#b9d8ff}small{color:#afc1d4}#warning{color:#ffd5a5}
</style><header><h1>DR Lab: один рынок, два представления</h1>
<p>A — рабочий экран из принятого main. B — сравнительный кандидат на основе PR #9 с ограниченными поправками сводки. Новые профили и визуальные решения не приняты.</p>
<label>Сцена <select id="scene">OPTIONS</select></label><label>Размер <select id="size"><option>1600</option><option>1920</option></select></label>
<button id="a">A · принятый</button><button id="b">B · кандидат</button><button id="both">Рядом</button>
<p><small>Переключение A/B сохраняет сцену и размер. Снимки получены на локальной истории 2006–2025. Проверка совпадения данных не доказывает лучшего чтения человеком.</small></p></header>
<main><div id="facts"></div><p id="warning"></p><div id="images"></div><p><a href="README.md">Различия и границы проверки</a> · <a href="../preview-definition.json">Точный состав B</a> · <a href="report.json">Машинный протокол</a></p></main>
<script>const rows=DATA;let mode='both';const $=id=>document.getElementById(id);function show(){const r=rows.find(x=>x.scene_id===$('scene').value&&x.viewport[0]===+$('size').value);$('facts').textContent=`NQ · RDR · ${r.date} · срез ${Math.floor(r.cut/60)}:${String(r.cut%60).padStart(2,'0')} ET · ${r.scope} · ${r.viewport.join('×')}. Совпали: закрытый рынок, семья, R/X и NOW; паспорта проверены.`;$('warning').textContent=r.scene_id==='WAIT'?'В B до подтверждения остаётся конфликт счётчиков с правилами сводки. Этот вид целиком не рекомендован к переносу.':r.scene_id==='PATHS'?'A показывает частоты закрытий, B — отдельные пути и выбранные случаи: это разные представления, новая подмена главного вида не разрешена.':'Новые карточки R/X, свёрнутые семейные подробности и дополнительные маркеры B остаются кандидатными.';const vs=mode==='both'?['A','B']:[mode];$('images').className=mode==='both'?'side':'';$('images').innerHTML=vs.map(v=>`<figure><figcaption>${v==='A'?'A · принятый main':'B · кандидат, не принят'}</figcaption><img src="${r.images[v]}" alt="${v}: ${r.label}"></figure>`).join('');for(const [id,v] of [['a','A'],['b','B'],['both','both']])$(id).classList.toggle('active',mode===v);}for(const [id,v] of [['a','A'],['b','B'],['both','both']])$(id).onclick=()=>{mode=v;show()};$('scene').onchange=$('size').onchange=show;show();</script></html>'''.replace('OPTIONS',options).replace('DATA',data)
    (PACKAGE/'comparison/index.html').write_text(page,encoding='utf-8')
    print('REPORT',len(public),'pairs;',2*len(public),'screens; numeric parity and checked passports; human acceptance NOT RUN',flush=True)

if __name__=='__main__': main()
