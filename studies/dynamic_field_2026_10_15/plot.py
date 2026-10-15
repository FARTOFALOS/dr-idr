"""Aggregate research figure; no tape, dates of cases, prices or UI changes."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
a=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
b=json.loads((HERE/'ranking-results.json').read_text(encoding='utf-8'))
names={'CLOCK_ALL':'Только часы · семья','POS_ALL':'Позиция SD · семья','POS_GEO':'Позиция SD · широкий пул',
       'STATE_K50_ALL':'Состояние · 50 соседей семьи'}
colors={'CLOCK_ALL':'#8f98a5','POS_ALL':'#d59344','POS_GEO':'#2188b5','STATE_K50_ALL':'#8b66b7'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
fig,ax=plt.subplots(1,2,figsize=(13.8,6),gridspec_kw={'width_ratios':[1,1.1]})
ax[0].plot([0,1],[0,1],color='#c2c7cd',ls='--',lw=1,label='Точное соответствие')
for method in ('CLOCK_ALL','POS_ALL','POS_GEO'):
    rows=sorted([r for r in a['calibration'] if r['kind']=='WINDOW_VISIT' and r['method']==method and r['n']>=1000],key=lambda r:r['predicted'])
    x=np.array([r['predicted'] for r in rows])*100;y=np.array([r['observed'] for r in rows])*100
    ax[0].plot(x,y,'o-',lw=1.8,ms=4,color=colors[method],label=names[method])
    if method=='POS_GEO':
        lo=np.array([r['ci95'][0] for r in rows])*100;hi=np.array([r['ci95'][1] for r in rows])*100
        ax[0].fill_between(x,lo,hi,color=colors[method],alpha=.12)
ax[0].set(xlim=(0,100),ylim=(0,100),xlabel='Посчитанная историческая доля, %',ylabel='Реальное посещение в воспроизведении, %',
          title='Насколько цифра соответствует частоте\nКорзины не меньше 1000 вопросов')
ax[0].legend(loc='upper left',fontsize=8,frameon=False)
ms=('POS_ALL','POS_GEO','STATE_K50_ALL')
for i,method in enumerate(ms):
    r=next(r for r in b['results'] if r['kind']=='WINDOW_VISIT' and r['method']==method and
           r['comparison']=='opposite_sides_same_window' and r['probability_scope']=='both_20_to_40')
    v=r['realised_high_minus_low'];mean=v['mean']*100;lo,hi=np.array(v['ci95'])*100
    ax[1].errorbar(mean,i,xerr=[[mean-lo],[hi-mean]],fmt='o',color=colors[method],capsize=4,ms=7,lw=2)
    ax[1].text(hi+.15,i,f'{mean:+.2f}',va='center',fontsize=9,color=colors[method])
ax[1].axvline(0,color='#9da6b0',lw=1)
ax[1].set(yticks=range(3),yticklabels=[names[m] for m in ms],ylim=(2.5,-.6),xlim=(-2,7),
          xlabel='Преимущество большей цифры по факту, п.п.\nРавный вес целевых дней; 95 % интервал по неделям',
          title='Приоритет между сторонами при долях 20–40 %\nПоказанная разница не меньше 5 п.п.')
for q in ax:
    q.grid(alpha=.18);q.spines[['top','right']].set_visible(False)
fig.suptitle('Будущие посещения областей · историческое воспроизведение 2016–2025\nNQ / ES / YM · ODR / RDR · одинаковые размеры цены и времени',fontsize=13,y=.98)
fig.tight_layout(rect=(0,.01,1,.88),w_pad=3)
fig.savefig(HERE/'calibration.png',dpi=150,facecolor='white')
print('saved calibration.png')
