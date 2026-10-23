"""Prepare the separate Time x SD profile approved for implementation on 2026-10-22. Accepted estimands stay 53."""
import copy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'integration/candidates/registry/95-time-sd.yaml'


def main():
    pb=json.loads((ROOT/'integration/candidates/registry/90-pullbacks.yaml').read_text(encoding='utf-8'))
    cont=json.loads((ROOT/'integration/candidates/registry/80-continuations.yaml').read_text(encoding='utf-8'))
    source='SRC:TIME-SD-235';profile='PROFILE:TIME-SD-235';route='/api/integration/time-sd'
    out=dict(registry_part='time-sd-235',source_references=[dict(id=source,sc_ref=['§12.6'],grounds='OPERATOR_REQUIREMENT',role='DECISION',
        document='meaning/lens/2026-10-22-plan-23-5-time-sd.md',locator='Plan presented in this chat on 22.10; direct human response «РЕАЛИЗУЙ» authorizes this implementation. No C2/C3 or perceptual acceptance is inferred.')],
        profiles=[],questions=[],outcomes=[],regions=[],density_algorithms=[],estimands=[],estimators=[],claim_forms=[],fact_forms=[],surfaces=[],encodings=[])
    p=copy.deepcopy(pb['profiles'][0]);p.update(id=profile,version='1.0',title_ru='Время × SD · 23.5',source_refs=[source],
        note='CANDIDATE FOR LOCAL REVIEW; implementation explicitly authorized 22.10. R=PB-L, X=FINAL-X, fixed 0.3 IDR x 15min cores, peak joint-cell projections, full N. Not operator perceptually accepted.')
    out['profiles']=[p]
    out['questions']=[dict(id='Q:TIME-SD-235',version='1',sc_ref=['T0','§12.6'],grounds='OPERATOR_REQUIREMENT',
        text_ru='В какие окна времени и в каких SD-ячейках совпадали события сессий семьи?',scene_ru='совместная область времени и SD, локальное ядро и пиковые проекции; одна F, один N'),
        dict(id='Q:TIME-SD-LINK',version='1',sc_ref=['T0','§12.6'],grounds='OPERATOR_REQUIREMENT',text_ru='Куда и когда шли те же истории после откатов из выбранного ядра?',
        scene_ru='те же эпизоды и их последующие M5 после закрытия M5 дна; посещение области в её собственном окне, одна сессия один голос от полной F')]
    outcome=copy.deepcopy(cont['outcomes'][0]);outcome.update(id='OUT:TS-POST-L',version='1.0',title_ru='Посещение области после дна эпизода из ядра',
        horizon_start='OWN_PB_BOTTOM_CLOSE_EXCLUSIVE',reference_definition='lab/time_sd235_ref.py::following_reference',
        implementations=['lab/time_sd235.py::following'],source_refs=[source],
        statuses='Joint event: a verified PB-L in the source core AND a later M5 of that SAME case visits the target price/time region. Earliest target bar opens at/after the close of the source L M5. Own block end. Full F denominator; uncertain source or missing later bars yields bounds; unrelated FINAL-X and targets before L never establish YES.')
    out['outcomes']=[outcome]
    out['regions']=[dict(id='REG:TIME-SD-CORE',version='1.0',sc_ref=['P2','P3'],grounds='OPERATOR_REQUIREMENT',region_kind='ZONE_MASK',origin='ALGORITHM',
        grid='GRID:K10-J15-1',density_algorithm='ALG:TIME-SD-CORE-1',bounds_rule='exact three adjacent 0.1-IDR cells in one 15-minute window; no temporal growth',title_ru='локальное ядро времени × SD')]
    out['density_algorithms']=[dict(id='ALG:TIME-SD-CORE-1',version='1.0',sc_ref=['P3'],grounds='OPERATOR_REQUIREMENT',title_ru='Локальные ядра 0,3 SD × 15 минут',
        grid='GRID:K10-J15-1',frozen=True,density_rule='unique case IDs in k-1,k,k+1 of the SAME b; M5 witnesses retained',
        region_rule='local maximum against adjacent price centres/time windows; compare neighbours but never join their cells; equal adjacent price peaks in same b: centre nearest u=0 then lower k; equal time peaks remain separate',
        min_support_rule='max(4,ceil(N/20)); unknown is kept in N and in bounds, never used to promote a peak',
        order_rule='time b, descending established support, centre nearest u=0, lower k; separate R and X',seed_rule='deterministic, no random procedure',diagnostics=['local historical support; no inference of predictive advantage'],source_refs=[source])]
    region_tpl=next(x for x in pb['estimands'] if x['id']=='EST:PB-REGION')
    cat_tpl=next(x for x in pb['estimands'] if x['id']=='EST:PB-SESSIONS')
    labels=[dict(surface='INSPECTOR',view='ANY',key=k,text_ru=t) for k,t in {
        'core':'локальное ядро · 15 минут × 0,3 SD','price':'пик этой SD-ячейки в одном окне 15 минут',
        'time':'пик этих 15 минут в одной SD-ячейке','region':'событие в выбранной области времени и цены',
        'R':'локальный откат до обновления','X':'окончательное расширение',
        'earlier':'только ранние установленные события','later':'есть установленное событие позже среза',
        'after':'после откатов из этого ядра','context':'Сейчас · итоговые R/X',
        'none':'нет ядра с достаточной локальной опорой','source':'история тех же эпизодов; доля всей семьи',
        'IN_ZONES':'есть установленное событие в ядрах','OUTSIDE':'установленные только вне ядер',
        'UNKNOWN':'без установленной координаты','NONE':'без события / нет периода',
    }.items()]
    for ev,outcome_id in [('R','OUT:PB-L-1'),('X','OUT:FINAL-X-1')]:
        event_ru='локальный откат до обновления' if ev=='R' else 'окончательное расширение'
        for kind in ('CORE','PEAK','REGION','SESSIONS'):
            eid='EST:TS-'+kind+'-'+ev;est=copy.deepcopy(cat_tpl if kind=='SESSIONS' else region_tpl)
            est.update(id=eid,version='1.0',question='Q:TIME-SD-235',profile=profile,q5_outcome=outcome_id,source_refs=[source],
                q1_formalised_part_ru=event_ru+': '+{'CORE':'доля уникальных сессий в точном ядре 0,3 SD × 15 минут','PEAK':'поддержка выбранной совместной клетки: максимум по времени для фиксированной цены или максимум по цене для фиксированного времени','REGION':'доля уникальных сессий в точной выбранной области','SESSIONS':'в ядрах / установленные только вне ядер / неизвестно / нет события'}[kind],
                q6_time_ru='общие часы ET; события после собственной активации до конца блока; clock разделяет установленные события по open+5 <= cut; повторяемый PB имеет один голос сессии в области')
            if kind!='SESSIONS':est['q5_region']='REG:TIME-SD-CORE' if kind=='CORE' else 'REG:JOINT-1'
            est['parameters']=[dict(name=k,parameter_kind='THRESHOLD',meaning_ru=k+' — объявленная область или правило выбора') for k in ['scale','k0','k1','b0','b1']]
            if kind=='CORE':est['parameters'].append(dict(name='zone_id',parameter_kind='ZONE_ID',meaning_ru='ядро этой версии/снимка/типа'))
            out['estimands'].append(est)
            ert=copy.deepcopy(next(x for x in pb['estimators'] if x['id']==('ESTR:PB-SESSIONS' if kind=='SESSIONS' else 'ESTR:PB-REGION')))
            ert.update(id=eid.replace('EST:','ESTR:'),version='1.0',estimands=[eid],implementations=['lab/time_sd235.py::derive'],reference_definition='lab/time_sd235_ref.py::check')
            out['estimators'].append(ert)
            form=copy.deepcopy(next(x for x in pb['claim_forms'] if x['id']==('CF:PB-SESSIONS' if kind=='SESSIONS' else 'CF:PB-REGION')))
            form.update(id=eid.replace('EST:','CF:'),version='1.0',estimand=eid,subject_ru='вся фиксированная семья F; '+event_ru,
                statement_ru=('Из {N} сессий: в локальных ядрах {in_zones}, установленные только вне ядер {outside}, неизвестно {unknown}, без события {none}.' if kind=='SESSIONS' else
                              'У {yes} из {N} сессий семьи '+event_ru+' находится в указанной совместной области времени и SD; ещё у {unknown} присутствие не установлено.'),
                labels=copy.deepcopy(labels),note='Words for the approved implementation plan; no C2/C3 and no automatic operator perceptual acceptance.')
            out['claim_forms'].append(form)
    est=copy.deepcopy(region_tpl);est.update(id='EST:TS-LINK',version='1.0',question='Q:TIME-SD-LINK',profile=profile,q5_outcome='OUT:TS-POST-L',source_refs=[source],
        q1_formalised_part_ru='доля всей семьи с совместной цепочкой: PB-L в исходном ядре, затем тот же исторический путь посещает выбранную область в её окне',
        q6_time_ru='после закрытия M5 своего L до собственного конца блока, внутри целевого окна; source L принадлежит выбранному ядру')
    out['estimands'].append(est)
    ert=copy.deepcopy(out['estimators'][0]);ert.update(id='ESTR:TS-LINK',estimands=['EST:TS-LINK'],implementations=['lab/time_sd235.py::following'],reference_definition='lab/time_sd235_ref.py::following_reference');out['estimators'].append(ert)
    form=copy.deepcopy(out['claim_forms'][0]);form.update(id='CF:TS-LINK',estimand='EST:TS-LINK',statement_ru='У {yes} из {N} сессий семьи после отката из исходного ядра тот же путь посетил целевую область в её окне; ещё у {unknown} цепочка не установлена.',labels=copy.deepcopy(labels));out['claim_forms'].append(form)
    out['fact_forms']=copy.deepcopy(pb['fact_forms'])
    out['fact_forms']=[] # existing PB fact forms describe the reused H/L/B facts; do not duplicate their IDs
    out['surfaces']=[dict(id='API:'+route,sc_ref=['§12.3','§12.6'],route=route,surface_profile='SC11_TIME_SD_235',definitions=source,
        estimands=[e['id'] for e in out['estimands']]+[e['id'] for e in pb['estimands']],marking='proposed time-SD profile; retained independently verified PB source evidence; no C2/C3')]
    # Source-proof numbers retain exactly their existing declared meanings.
    for i,e in enumerate(pb['encodings']):
        e=copy.deepcopy(e);e.update(id='FE:TS.PB.'+str(i),surface='API:'+route);out['encodings'].append(e)
    def enc(path,kind,target):
        out['encodings'].append(dict(id='FE:TS.'+str(len(out['encodings'])),sc_ref=['§12.3'],surface='API:'+route,path=path,field_kind=kind,target=target))
    enc('proof.time_sd.scale','PARAMETER','PB locality scale; X remains FINAL-X')
    enc('proof.time_sd.definition.{time_minutes,price_cells,price_cell_num,price_cell_den,atom_minutes,min_abs,min_frac_num,min_frac_den}','PARAMETER','ALG:TIME-SD-CORE-1 frozen constants')
    enc('proof.time_sd.maps.{*}.need','PARAMETER','support floor')
    enc('proof.time_sd.maps.{*}.points[*].{i,v,k,b,kt,kn,open}','MEASUREMENT','verified PB-L or accepted FINAL-X coordinates')
    enc('proof.time_sd.maps.{*}.m5[*].{k,open}','MEASUREMENT','M5 x 0.1 IDR cell')
    enc('proof.time_sd.maps.{*}.m5[*].n_known','SUPPORT_COUNT','unique session support in M5 cell')
    for carrier in ('cells','cores','price_peaks','time_peaks','regions'):
        prefix='proof.time_sd.maps.{*}.'+carrier+'[*]'
        enc(prefix+'.{k0,k1,b0,b1,k,b,index}','PARAMETER','exact cell mask / chosen joint cell; original second coordinate is retained')
        enc(prefix+'.{n_known,n_possible,earlier,later}','SUPPORT_COUNT','EST:TS-* same-region unique membership, unknown and nonoverlapping known clock parts')
    enc('proof.time_sd.maps.{*}.cores[*].{apex_D,n_points,n_episodes}','SUPPORT_COUNT','core support and retained witnesses; not additional votes')
    enc('proof.time_sd.maps.{*}.cores[*].{price_low,price_high,time_start,time_end}','MEASUREMENT','fixed core bounds')
    enc('proof.time_sd.maps.{*}.cores[*].anchor[*]','MEASUREMENT','canonical core centre')
    enc('proof.time_sd.maps.{*}.cores[*].cell_mask[*][*]','MEASUREMENT','exact finite mask')
    enc('proof.time_sd.maps.{*}.sessions.{IN_ZONES,OUTSIDE,UNKNOWN,NONE}','SUPPORT_COUNT','EST:TS-SESSIONS-* categories of N')
    enc('proof.time_sd.links[*].{k0,k1,b0,b1}','PARAMETER','target joint region after the source L')
    enc('proof.time_sd.links[*].{n_known,n_possible}','SUPPORT_COUNT','EST:TS-LINK unique cases; full F denominator')
    enc('proof.time_sd.links[*].witnesses[*].{l_open,target_open,target_close}','TIME','same-case chronological witness after L close')
    for group in ('outcomes','estimators'):
        for item in out[group]:item['reference_definition']='lab/contract.py::ref_time_sd235'
    for ev in ('R','X'):
        prefix='proof.time_sd.today.'+ev+'[*]'
        enc(prefix+'.visit.{close,eligible}','TIME','exact current closed-M5 visit; eligible slots distinguish no period')
        enc(prefix+'.completion.{b_close,h_open}','TIME','own completed PB episode, never mere price visit')
    DEST.write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print(DEST.relative_to(ROOT),len(out['estimands']),'new estimands; accepted 53 untouched')


if __name__=='__main__':main()
