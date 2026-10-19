"""Define the continuation candidate using existing SC record classes, separate from accepted semantics."""
import copy
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / 'integration/candidates/registry'


def records(name):
    return yaml.safe_load((REG / name).read_text(encoding='utf-8'))


def main():
    q = records('30-questions-estimands.yaml')
    c = records('20-cases-outcomes.yaml')
    forms = records('40-claims.yaml')
    old = lambda coll, key: copy.deepcopy(next(x for x in coll if x['id'] == key))
    profile = old(records('00-editions.yaml')['profiles'], 'PROFILE:ARRIVE-24')
    profile.update(id='PROFILE:CONTINUATIONS-24', title_ru='Продолжения: закреплённая область и окно',
                   grounds='PROPOSAL', source_refs=['SRC:CANDIDATES-1'],
                   note='CANDIDATE FOR LOCAL REVIEW; fixed physical target, common-clock POS_GEO and explicit residual no-visit condition. UI acceptance and predictive admission pending.')
    question = old(q['questions'], 'Q:K-ARRIVE')
    question.update(id='Q:C-WINDOW', grounds='PROPOSAL')
    question['text_ru']='Посещали ли закреплённую область в оставшихся M5 её абсолютного окна?'
    question['scene_ru']='Одна физическая цель, текущий известный префикс, самостоятельный POS_GEO и явное условие остатка; не доля исходной F'
    for key in ('title_ru', 'question_ru', 'trader_words_ru'):
        if key in question: question[key] = 'Где бывала цена в закреплённой области и окне после выбранной M5?'
    est = old(q['estimands'], 'EST:K-ARRIVE')
    est.update(id='EST:C-WINDOW', grounds='PROPOSAL', question=question['id'], profile=profile['id'],
               q1_formalised_part_ru='доля уникальных случаев POS_GEO, чьи действительные M5-диапазоны посетили фиксированную полосу в оставшихся M5 абсолютного окна; внутри окна — при явном условии известного непосещения его прошедшей части',
               q4_case_set=['CS:C-RISK'], q5_outcome='OUT:C-WINDOW', q5_region='REG:C-BAND',
               q6_time_ru='только закрытые M5 после cut и внутри закреплённого абсолютного окна; собственная активация каждого аналога уже наступила',
               q8_order_ru='YES/NO/UNKNOWN; n_total и n_known не меньше 20; при UNKNOWN первичны границы по всему набору, иначе точная доля; не прогноз сегодняшнего исхода',
               parameters=[dict(name='target', parameter_kind='EVENT', meaning_ru='неизменная физическая область, исходная рамка и абсолютное окно'),
                           dict(name='cut', parameter_kind='CUT', meaning_ru='закрытая M5 текущего знания')])
    estimator = old(q['estimators'], 'ESTR:K-POINT-BOUNDS-1')
    estimator.update(id='ESTR:C-WINDOW', grounds='PROPOSAL', estimands=[est['id']],
                     implementations=['lab/continuity24.py::release'], reference_definition='lab/contract.py::ref_continuation')
    sets = []
    for ident, role, parent, title in [('CS:C-G','HISTORICAL_UNIVERSE',None,'Подтверждённая история инструмента и блока'),
                                      ('CS:C-POS','MATCHED_AT_CUT','CS:C-G','Близкое положение на общих часах'),
                                      ('CS:C-RISK','MATCHED_AT_CUT','CS:C-POS','Опора конкретного остаточного вопроса')]:
        s = old(c['case_sets'], 'CS:K-ARRIVE-ALL-1')
        s.update(id=ident, grounds='PROPOSAL', role=role, title_ru=title, profile=profile['id'],
                 key_fields=['INSTRUMENT','BLOCK','DATE_BEFORE_TARGET'], source_refs=['SRC:CANDIDATES-1'])
        if role=='MATCHED_AT_CUT': s['comparison']='CMP:C-POS'
        else: s.pop('comparison',None)
        if parent: s['parent']=[parent]
        else: s.pop('parent', None)
        s['history_rule']='G: strictly earlier dates <=2025, same instrument/block, both directions/windows in own directed IDR frame; POS: own complete alive prefix at common cut, close within 1/4 IDR; RISK: explicit question conditions only, no future labels in selection'
        s['condition_ru']=title+'; сравнивалось положение, не полный путь; условие непосещения части окна объявлено отдельно'
        s['undetermined_rule']='Unknown outcome stays in the support; fewer than 20 total or known outcomes withholds number and conditional geometry'
        sets.append(s)
    outcome = old(c['outcomes'], 'OUT:VISIT-FULL-1')
    outcome.update(id='OUT:C-WINDOW', grounds='PROPOSAL', event='VISIT', projection='BAND_VISIT',
                   title_ru='Посещение выбранной области в оставшейся части абсолютного окна',
                   horizon_start='COMMON_CUT_EXCLUSIVE',
                   statuses='Within (cut, block end] intersected with REG:C-BAND absolute window: YES if an actual M5 range overlaps; NO if all required M5 known without overlap; UNKNOWN otherwise; first time is not inferred inside M5',
                   implementations=['lab/continuity24.py::visit'],source_refs=['SRC:CANDIDATES-1'],
                   reference_definition='lab/contract.py::ref_continuation')
    for key in ('definition_ru','rule_ru','horizon_ru'):
        if key in outcome: outcome[key]='Union of actual M5 ranges in the fixed future window: YES if any observed overlap, NO if all required M5 are known without overlap, UNKNOWN otherwise.'
    region = old(c['regions'], 'REG:PRICE-BAND-1')
    region.pop('grid',None)
    region.update(id='REG:C-BAND', grounds='PROPOSAL',region_kind='JOINT_PRICE_TIME',origin='OPERATOR_SELECTION',
                  bounds_rule='Directed [low,high) fixed through the original physical IDR frame; absolute window of complete M5, first_close..last_close inclusive. Moving cut clips the remaining bars, never translates price or window.')
    for key in ('definition_ru','rule_ru'):
        if key in region: region[key]='Directed half-open band [low,high), fixed through the original physical frame; fixed absolute M5 window'
    form = old(forms['claim_forms'], 'CF:K-ARRIVE')
    form.update(id='CF:C-WINDOW', grounds='PROPOSAL', estimand=est['id'], acceptance='PROPOSED_BY_EXECUTOR',
                statement_ru='На срезе {cut}, среди {n} исторических случаев с близким положением и указанным условием {yes} посетили область в оставшемся окне {window}; исход неизвестен у {unknown}.',
                condition_ru=sets[-1]['condition_ru'],
                forbidden_readings_ru=['шанс сделки сегодня','совпадение полного пути','доля исходной F','один прогноз с неизменной опорой'])
    form['labels']=[dict(surface='PANEL',view='ANY',key=k,text_ru=v) for k,v in {
        'head':'Продолжения','comparison':'Близкое положение · общие часы','window':'Закреплённое окно',
        'original':'Исходная F','residual':'Остаток · до этого не посещали','same_question':'Та же цель и будущее окно',
        'new_question':'Та же цель · новый остаточный вопрос','fact':'Посещение установлено в {time}','resolved':'Вопрос разрешён фактом',
        'unknown':'Неизвестно','absent':'Ответ не опубликован','pending':'Сопоставляю историю…',
        'paths':'Действительные пути опоры','selected':'Сопоставлялось положение, не полный путь',
        'extension':'Закреплённое/остаточное окно: калибровка отдельно','point':'{pct}','bounds':'{lo}–{hi}'}.items()]
    route='/api/integration/continuations'
    enc=[]
    fields=[('proof.context.{cut,today_w,today_close,tick_num,tick_den}','PREFIX_STATE'),
            ('proof.context.conditions[*].{first_close,last_close}','PARAMETER'),
            ('proof.today_prefix[*][*]','OBSERVATION'),('proof.grid[*]','TIME'),
            ('proof.target.frame.{activation,end,direction}','STRATEGY_OBJECT'),
            ('proof.target.{first_close,last_close,created_at,window_open,window_close}','TIME'),
            ('proof.target.{low,high,physical_edges}[*]','PARAMETER'),('proof.target.physical_edges[*][*]','PARAMETER'),
            ('proof.question.{first_close,last_close}','TIME'),
            ('proof.question.conditions[*].{first_close,last_close}','PARAMETER'),
            ('proof.observed.available_at','TIME'),('proof.observed.witness_bar[*]','TIME'),
            ('proof.counts.{G,eligible,position,risk,in_F,outside_F}','SUPPORT_COUNT'),
            ('proof.support.{n_total,n_known,yes,no,unknown}','SUPPORT_COUNT'),
            ('proof.witnesses[*].{w,activation,direction,edge_ticks}','CASE_RECORD'),('proof.witnesses[*].path[*][*]','CASE_RECORD'),
            ('comparison.{entered,left}','SUPPORT_COUNT')]
    for i,(path,kind) in enumerate(fields):
        enc.append(dict(id='FE:C.'+str(i),sc_ref=['§12.3'],surface='API:'+route,path=path,field_kind=kind,
                        target='EST:C-WINDOW fixed-target scene; context, exact source records and declared support'))
    data=dict(registry_part='continuations-candidate', profiles=[profile], questions=[question], estimands=[est],
              estimators=[estimator], case_sets=sets, outcomes=[outcome], regions=[region], claim_forms=[form],
              surfaces=[dict(id='API:'+route,sc_ref=['§12.3'],route=route,surface_profile='SC11_CONTINUATIONS_0_1',
                             definitions='SRC:CANDIDATES-1',estimands=[est['id']],marking='separate proposed ContractEnvelope; no C2/C3')],encodings=enc)
    cmp_collection, cmp_source=next((k,x) for k,items in c.items() if isinstance(items,list) for x in items if x.get('id')=='CMP:K-POS-1')
    cmp=copy.deepcopy(cmp_source);cmp['id']='CMP:C-POS';cmp['grounds']='PROPOSAL'
    data[cmp_collection]=[cmp]
    (REG/'80-continuations.yaml').write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')


if __name__=='__main__': main()
