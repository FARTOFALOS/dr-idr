  // One source-bound publication, never a join against F.M. The target survives view/cut changes.
  const CS = { target: null, scene: null, key: null, packet: null, previous: null, pending: null, error: null, seq: 0,
    selected: null, drag: null, drawing: null, discarded: 0, verified: 0, last: null, comparison: null,
    history: [], detail: 'question' };
  const continuationMode = () => ICFG.enabled && TRIAL.continuations && st.mode === 'continuations';
  const continuationScene = ctx => [A.inst, ctx.D.iso, ctx.s.k].join('|');
  const cRat = q => q[0] / q[1];
  const cPrice = (t, u) => +t.frame.edge + t.frame.direction * +t.frame.width * u;
  const cCanonical = x => x === null || typeof x !== 'object' ? JSON.stringify(x) : Array.isArray(x) ? '[' + x.map(cCanonical).join(',') + ']' : '{' + Object.keys(x).sort().map(k => JSON.stringify(k) + ':' + cCanonical(x[k])).join(',') + '}';
  async function cHash(x) { const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(cCanonical(x))); return [...new Uint8Array(b)].map(v => v.toString(16).padStart(2,'0')).join(''); }
  function cRequest(ctx) {
    if (!CS.target || CS.scene !== continuationScene(ctx)) return null;
    const cut = Math.floor(ctx.obs / 5) * 5;
    const prefix = ctx.D.bars.filter(b => b.t + 5 <= cut).map(b => [b.t + 5, ...[b.o,b.h,b.l,b.c].map(p => Math.round(p / (A.day.tick || .25)))]);
    return { cut, prefix, key: [IS.epoch,CS.scene, cut, st.scope, JSON.stringify(CS.target), JSON.stringify(prefix)].join('|') };
  }
  function continuationPacket(ctx) { const q=cRequest(ctx); return q && CS.key===q.key ? CS.packet : null; }
  function cVisit(w, p) {
    const q=p.question, t=p.target, lo=t.low.map(BigInt), hi=t.high.map(BigInt); let gap=false;
    for(let j=0;j<p.grid.length;j++) {
      if(p.grid[j]<q.first_close||p.grid[j]>q.last_close)continue;
      const b=w.path[j]; if(!b){gap=true;continue;}
      if(BigInt(b[0])*hi[1]<hi[0]*BigInt(w.w)&&BigInt(b[1])*lo[1]>=lo[0]*BigInt(w.w))return 'YES';
    }
    return gap?'UNKNOWN':'NO';
  }
  async function verifyContinuation(r, q, ctx) {
    if(!r.proof || !r.release_id || r.contract?.status!=='CONFORMANT' || reviewFault(r))throw Error(r.message||'Нет проверенного выпуска');
    const p=r.proof, c=p.context, t=p.target;
    if(c.cut!==q.cut||c.instrument!==A.inst||c.date!==ctx.D.iso||c.block!==ctx.s.k||
       c.base_registry_hash!==SC11.registry_hash||c.registry_hash!==REVIEW.registry_hash||
       JSON.stringify(p.today_prefix)!==JSON.stringify(q.prefix))throw Error('Выпуск относится к другому срезу или версии');
    for(const k of ['low','high','first_close','last_close','created_at'])if(JSON.stringify(t[k])!==JSON.stringify(CS.target[k]))throw Error('Закреплённая цель изменилась');
    if(p.full_path_compared || p.source_kind!=='POSITION_AT_COMMON_CLOCK')throw Error('Положение подменено полным путём');
    if(await cHash(p)!==r.release_id)throw Error('Данные выпуска или пути подменены');
    const risk=new Set(p.risk_ids),pos=new Set(p.position_ids),excluded=p.risk_exclusions,totals={};
    if(!excluded||risk.size!==p.risk_ids.length||pos.size!==p.position_ids.length||
       [...risk].some(id=>!pos.has(id))||Object.keys(excluded).length!==pos.size-risk.size)throw Error('Опора и исключения не составляют набор сопоставимых дней');
    for(const [id,reason] of Object.entries(excluded)){
      if(!pos.has(id)||risk.has(id)||!['WINDOW_ALREADY_VISITED','WINDOW_VISIT_UNKNOWN','NOT_ACTIVE_AT_WINDOW_START'].includes(reason))throw Error('Неизвестная причина исключения');
      totals[reason]=(totals[reason]||0)+1;
    }
    if(cCanonical(totals)!==cCanonical(p.exclusion_counts)||p.counts.position!==pos.size||p.counts.risk!==risk.size)throw Error('Причины исключений не связаны с опорой');
    const active=r.status==='RESEARCH_ONLY', ids=p.witnesses.map(w=>w.id);
    if(new Set(ids).size!==ids.length || active && JSON.stringify(ids)!==JSON.stringify(p.risk_ids) || !active && ids.length)throw Error('Рисунок не содержит точную опору выпуска');
    const counts={YES:0,NO:0,UNKNOWN:0};
    for(const w of p.witnesses){
      if(w.path.length!==p.grid.length||!p.position_ids.includes(w.id)||w.date>=c.date)throw Error('Чужой или неполный путь');
      const raw={...w};delete raw.revision;
      if(await cHash(raw)!==w.revision||cVisit(w,p)!==w.outcome)throw Error('Путь не подтверждает исход');
      counts[w.outcome]++;
    }
    if(active){
      const s=p.support,b=r.contract.bundles.find(b=>b.estimand==='EST:C-WINDOW'),e=b?.estimates.find(e=>e.value_kind==='BOUNDS'),pt=b?.estimates.find(e=>e.value_kind==='POINT');
      const parameters=JSON.parse(b?.parameters||'{}');
      if(!b||b.claim.claim_class!=='ConditionalDescriptiveClaim'||s.n_total!==ids.length||s.n_known!==counts.YES+counts.NO||s.yes!==counts.YES||s.no!==counts.NO||s.unknown!==counts.UNKNOWN||
         parameters.release!==r.release_id||parameters.target!==t.id||parameters.question!==p.question.id||parameters.cut!==c.cut||
         e?.denominator!==s.n_total||Math.abs(e.lower-s.yes/s.n_total)>1e-12||Math.abs(e.upper-(s.yes+s.unknown)/s.n_total)>1e-12||pt?.denominator!==s.n_known||pt.numerator!==s.yes||Math.abs(pt.value-s.yes/s.n_known)>1e-12)throw Error('Число не связано с нарисованными исходами');
    } else if(r.contract.bundles.length)throw Error('Неактивный вопрос содержит свежую долю');
    return r;
  }
  function compareContinuations(before,after){
    if(!before||before.release_id===after.release_id||before.proof.target.id!==after.proof.target.id)return null;
    const a=before.proof,b=after.proof,A=new Set(a.position_ids),B=new Set(b.position_ids);
    return {same_question:a.question.id===b.question.id,entered:[...B].filter(x=>!A.has(x)).length,left:[...A].filter(x=>!B.has(x)).length,
            revision_changed:a.context.history_revision!==b.context.history_revision,backward:b.context.cut<a.context.cut,
            before_cut:a.context.cut,after_cut:b.context.cut,before:before.release_id,after:after.release_id};
  }
  function rememberContinuation(r){
    const p=r.proof,c=p.context;
    // Receipts of actually viewed answers, not a manufactured retrospective forecast series.
    CS.history=CS.history.filter(x=>x.target===p.target.id&&x.history_revision===c.history_revision&&
      x.registry===c.registry_hash&&x.code===c.code_revision&&x.cut!==c.cut);
    CS.history.push({cut:c.cut,target:p.target.id,question:p.question.id,release:r.release_id,
      history_revision:c.history_revision,registry:c.registry_hash,code:c.code_revision,
      value:r.status==='RESEARCH_ONLY'?cValue(r):null,status:r.status,observed:p.observed,
      support:p.support.n_total,first:p.question.first_close,last:p.question.last_close,
      residual:p.question.conditions.length>0});
    CS.history.sort((a,b)=>a.cut-b.cut);
  }
  function requestContinuations(ctx) {
    if(!continuationMode()||!CS.target)return;
    if(CS.scene!==continuationScene(ctx)){CS.target=null;CS.packet=null;CS.key=null;return;}
    const q=cRequest(ctx); if(!q||q.key===CS.key&&(CS.packet||CS.error)||CS.pending===q.key)return;
    const token=++CS.seq, previous=CS.packet?.release_id||CS.previous;
    CS.previous=previous;CS.key=q.key;CS.packet=null;CS.error=null;CS.pending=q.key;CS.drawing=null;
    const body={instrument:A.inst,session:ctx.s.k,at:q.cut,scope:st.scope,target:CS.target,previous};if(A.src==='hist')body.date=A.date;
    fetch('/api/integration/continuations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(async res=>{
      const r=await res.json();if(!res.ok)throw Error(r.message||r.error||'Сервер не ответил');
      if(token!==CS.seq||cRequest(cur())?.key!==q.key){CS.discarded++;return;}
      if(!r.proof)throw Error(r.message||r.status);
      await verifyContinuation(r,q,ctx);
      if(token!==CS.seq||cRequest(cur())?.key!==q.key){CS.discarded++;return;}
      CS.comparison=compareContinuations(CS.last,r);CS.last=r;CS.packet=r;CS.previous=r.release_id;CS.verified++;CS.target={...CS.target,frame:r.proof.target.frame};
      rememberContinuation(r);
      // Equivalent numeric frame strings returned by the server do not create another request.
      CS.key=cRequest(cur()).key;CS.selected=CS.selected&&r.proof.witnesses.some(w=>w.id===CS.selected)?CS.selected:null;
    }).catch(e=>{if(token===CS.seq){CS.error=e.message;CS.packet=null;CS.drawing=null;}})
      .finally(()=>{if(token===CS.seq)CS.pending=null;redraw(true);});
  }
  function pinContinuation(low,high,open,end,ctx=cur()) {
    if(!ctx.s.conf||ctx.s.failed)throw Error('Для новой цели нужен подтверждённый целый DR');
    const cut=Math.floor(ctx.obs/5)*5;if(open<cut||end<=open||end>SESS[ctx.s.k].end)throw Error('Выберите будущее окно внутри блока');
    CS.target={low,high,first_close:open+5,last_close:end,created_at:cut};CS.scene=continuationScene(ctx);
    CS.key=CS.packet=CS.previous=CS.error=CS.pending=CS.selected=CS.last=CS.comparison=null;CS.history=[];CS.detail='question';CS.seq++;st.tool=false;st.pin=st.hover=null;render(true);
  }
  function cValue(r) {
    // an established visit is a fact, marked as «Отсюда» marks a reached place; no number stands for it (handoff 19.10 §1)
    if(r?.proof?.observed.status==='FACT_YES')return '✓';
    if(!r||r.status!=='RESEARCH_ONLY')return '—';
    const s=r.proof.support;
    return s.unknown?lbl('EST:C-WINDOW','bounds',{lo:pct(100*s.yes/s.n_total),hi:pct(100*(s.yes+s.unknown)/s.n_total)}):pct(100*s.yes/s.n_total);
  }
  function cStatus(r) {
    if(CS.error)return CS.error;
    if(!CS.target)return 'Выберите область и будущее окно';
    if(!r)return lbl('EST:C-WINDOW','pending');
    if(r.status==='RESEARCH_ONLY')return '';
    const x=r.proof.observed;
    if(x.status==='FACT_YES')return lbl('EST:C-WINDOW','fact',{time:clk(x.available_at)});
    if(x.status==='FACT_NO')return 'Окно закончилось: посещения не было';
    return ({WITHHELD_SMALL_SUPPORT:'Мало сопоставимых случаев',OBSERVATION_GAP:'В прошедшей части окна есть пропуск',UNKNOWN_FINAL:'Итог окна неизвестен',WITHHELD_NO_PREFIX:'После подтверждения ещё нет закрытой M5',WITHHELD_PREFIX_GAP:'В известном префиксе есть пропуск: сопоставление недоступно',WITHHELD_DR_BROKEN:'DR сломан: свежего условного ответа нет'})[r.status]||'Ответ недоступен';
  }
  function cChange(r){
    if(r?.proof.observed.status.startsWith('FACT'))return lbl('EST:C-WINDOW','resolved');
    if(CS.comparison?.backward)return 'Ранний срез закреплённой цели';
    if(CS.comparison?.revision_changed)return 'Изменились исходные исторические данные';
    return CS.comparison?(CS.comparison.same_question?lbl('EST:C-WINDOW','same_question'):lbl('EST:C-WINDOW','new_question')):lbl('EST:C-WINDOW','selected');
  }
  function cCondition(p){
    const condition=p?.question.conditions.find(x=>x.kind==='WINDOW_NO_VISIT');
    return condition?lbl('EST:C-WINDOW','no_visit_yet',{time:clk(condition.last_close)}):'';
  }
  function cHistory(p){
    const rows=CS.history.filter(x=>x.cut<=p.context.cut).reverse();
    return '<div class="p21-note">'+lbl('EST:C-WINDOW','history_seen')+'</div><div class="c24-history">'+rows.map(x=>{
      const value=x.value??(x.observed.status==='FACT_YES'?lbl('EST:C-WINDOW','history_yes'):x.observed.status==='FACT_NO'?lbl('EST:C-WINDOW','history_no'):lbl('EST:C-WINDOW','absent'));
      const what=x.value?(x.residual?lbl('EST:C-WINDOW','history_rest',{from:clk(x.first-5),to:clk(x.last)}):lbl('EST:C-WINDOW','history_whole')):'';
      return '<button type="button" data-c24-cut="'+x.cut+'" data-c24-release="'+x.release+'"'+(x.cut===p.context.cut?' aria-current="true"':'')+'><span>'+clk(x.cut)+'</span><b>'+value+'</b><small>'+what+(x.value?' · '+lbl('EST:C-WINDOW','support_n',{n:x.support}):'')+'</small></button>';
    }).join('')+'</div>';
  }
  function continuationPanel(ctx) {
    requestContinuations(ctx);const r=continuationPacket(ctx),p=r?.proof;
    const b=r?.contract.bundles.find(b=>b.estimand==='EST:C-WINDOW');
    return '<div class="p21-h"><span class="p24-ht">'+lbl('EST:C-WINDOW','head')+candTag()+'</span></div><div class="p21-note">'+lbl('EST:C-WINDOW','comparison')+'</div>'+
      (p?'<div class="p21-note">'+[cPrice(p.target,cRat(p.target.low)),cPrice(p.target,cRat(p.target.high))].sort((a,b)=>a-b).map(px).join('…')+' · '+clk(p.target.window_open)+'–'+clk(p.target.window_close)+'</div>':'')+
      // the number's own sentence is the published claim of its bundle (CF:C-WINDOW, with its counts) and what it applies to
      '<div class="p21-link c24-answer"'+(b?' data-bundle="'+b.id+'" data-edition="'+REVIEW.edition+'" title="'+esc(b.claim.statement_ru+'\n'+b.claim.applies_to_ru)+'"':'')+'>'+prow(p?.question.conditions.length?lbl('EST:C-WINDOW','residual'):lbl('EST:C-WINDOW','window'),cValue(r))+'</div>'+
      '<div class="p21-note">'+esc(cStatus(r))+'</div>'+(p?'<div class="p21-note">'+esc(cChange(r))+'</div>'+
      (p.question.active&&p.question.conditions.length?'<div class="p21-note">'+cCondition(p)+' · '+lbl('EST:C-WINDOW','history_rest',{from:clk(p.question.first_close-5),to:clk(p.question.last_close)})+'</div>':'')+
      '<button class="p24-btn" type="button" data-c24="history">'+lbl('EST:C-WINDOW','history_head')+'</button>':'');
  }
  function continuationDetail(ctx) {
    const r=continuationPacket(ctx),p=r?.proof,t=p?.target,s=p?.support;
    let body='<div class="c24-tools"><button type="button" data-c24="question">Вопрос</button><button type="button" data-c24="history">'+lbl('EST:C-WINDOW','history_head')+'</button></div>';
    if(!p||CS.detail!=='history')body+='<div class="c24-tools"><button type="button" data-c24="draw">▭ Новая цель</button><button type="button" data-c24="reset">Снять цель</button></div>';
    if(!p)return {head:lbl('EST:C-WINDOW','head'),body:body+'<div class="p21-note">'+esc(cStatus(r))+'</div>'};
    if(CS.detail==='history')return {head:lbl('EST:C-WINDOW','history_head'),body:body+cHistory(p)+'<div class="p21-note">'+lbl('FF:CANDIDATE-STATUS','foot')+'</div>'};
    body+=dRow('Срез знания',clk(p.context.cut))+dRow('Физическая область',[cPrice(t,cRat(t.low)),cPrice(t,cRat(t.high))].sort((a,b)=>a-b).map(px).join('–'))+
      dRow('Цель',clk(t.window_open)+'–'+clk(t.window_close))+dRow('Остаток',p.question.active?clk(p.question.first_close-5)+'–'+clk(p.question.last_close):'вопрос разрешён/недоступен')+
      dRow('Сопоставление','положение ±¼ SD · общие часы');
    if(p.question.active)body+=dRow('История / пригодны',p.counts.G+' / '+p.counts.eligible)+
      dRow('По положению / опора вопроса',p.counts.position+' / '+p.counts.risk)+dRow('В исходной F / вне F',p.counts.in_F+' / '+p.counts.outside_F)+
      dRow('YES / NO / UNKNOWN',s.yes+' / '+s.no+' / '+s.unknown)+dRow('Известны / всего',s.n_known+' / '+s.n_total)+
      dRow('Ответ',r.status==='RESEARCH_ONLY'?cValue(r):esc(cStatus(r)));
    else body+=dRow('Факт',esc(cStatus(r)));
    if(p.question.active&&p.question.conditions.length){
      body+=dRow('Условие',cCondition(p));
      for(const [reason,n] of Object.entries(p.exclusion_counts))body+=dRow(lbl('EST:C-WINDOW','exclude_'+reason),String(n));
    }
    if(CS.comparison)body+=dRow('Новые / вышедшие аналоги',CS.comparison.entered+' / '+CS.comparison.left)+
      dRow('Изменение',CS.comparison.backward?'обратный просмотр':CS.comparison.revision_changed?'исходные данные изменились':CS.comparison.same_question?'новый выпуск прежнего вопроса':'та же цель; изменился остаток/применимость');
    if(p.witnesses.length)body+='<label class="c24-case">Путь случая <select id="c24case"><option value="">Все случаи опоры</option>'+p.witnesses.map(w=>'<option value="'+esc(w.id)+'"'+(CS.selected===w.id?' selected':'')+'>'+esc(w.date+' · '+w.outcome)+'</option>').join('')+'</select></label>';
    body+='<div class="p21-note">'+lbl('EST:C-WINDOW','selected')+' · '+lbl('EST:C-WINDOW','extension')+'</div><div class="p21-note">'+lbl('FF:CANDIDATE-STATUS','foot')+'</div>';
    body+=dRow('Выпуск',r.release_id.slice(0,12))+dRow('Данные',p.context.history_revision.slice(0,12));
    return {head:lbl('EST:C-WINDOW','head'),body};
  }
  function continuationInspector(ctx){
    const r=continuationPacket(ctx),p=r?.proof;
    if(!p)return '<div class="ih">'+lbl('EST:C-WINDOW','head')+'</div><div class="is">'+esc(cStatus(r))+'</div><div class="is">'+lbl('FF:CANDIDATE-STATUS','foot')+'</div>';
    const t=p.target,s=p.support;
    return '<div class="ih">'+(r.status==='RESEARCH_ONLY'?cValue(r):esc(cStatus(r)))+'</div>'+
      '<div class="is">'+sd(cRat(t.low))+'…'+sd(cRat(t.high))+' SD · '+clk(t.window_open)+'–'+clk(t.window_close)+' · срез '+clk(p.context.cut)+'</div>'+
      (r.status==='RESEARCH_ONLY'?'<div class="is">Опора '+s.n_total+' · YES '+s.yes+' / NO '+s.no+' / UNKNOWN '+s.unknown+'</div>':'')+
      '<div class="is">'+esc(cChange(r))+
      (p.question.active&&p.question.conditions.length?' · остаток '+clk(p.question.first_close-5)+'–'+clk(p.question.last_close)+'</div><div class="is">'+cCondition(p):'')+'</div>'+
      // the residual support and the reasons that make it (81 → 39: 42 already in the window) stand together; the change
      // of the position set since the previous M5 is another operation and comes last, so two different counts are never
      // read as one cause (handoff 19.10 §3; meaning/13 entry 55)
      (p.question.active&&p.question.conditions.length?'<div class="is">'+lbl('EST:C-WINDOW','support_chain',{position:p.counts.position,risk:p.counts.risk})+'</div>':'')+
      (p.question.active&&p.question.conditions.length?'<div class="is">'+Object.entries(p.exclusion_counts).map(([reason,n])=>lbl('EST:C-WINDOW','exclude_'+reason)+' '+n).join(' · ')+'</div>':'')+
      (p.question.active&&CS.comparison&&!CS.comparison.backward&&!CS.comparison.revision_changed?'<div class="is">'+lbl('EST:C-WINDOW','membership_change',{time:clk(CS.comparison.before_cut),entered:CS.comparison.entered,left:CS.comparison.left})+'</div>':'')+
      '<div class="is">'+lbl('FF:CANDIDATE-STATUS','foot')+'</div>';
  }
  function continuationDraw(c,ctx) {
    CS.drawing=null;requestContinuations(ctx);const r=continuationPacket(ctx),p=r?.proof;
    if(p){
      const t=p.target,pp=u=>cPrice(t,u),cut=p.context.cut,points=[];
      if(r.status==='RESEARCH_ONLY')for(const w of p.witnesses){
        const selected=CS.selected===w.id, color=selected?'#EDF1F5':cfg.path;
        c.lineWidth=selected?1.7:.65;c.setLineDash(w.outcome==='UNKNOWN'?[3,3]:[]);let last=null;
        for(let j=0;j<p.grid.length;j++){
          const T=p.grid[j],row=w.path[j];if(!row||T<=w.activation){last=null;continue;}
          const x=V.X(T),y=V.Y(pp(row[2]/w.w)),past=T<=cut,beyond=T>t.last_close;
          c.strokeStyle=rgba(color,selected ? .8 : (past||beyond ? .035 : .15));
          if(last&&T-last.T===5){c.beginPath();c.moveTo(last.x,last.y);c.lineTo(x,y);c.stroke();}
          if(!past&&!beyond){c.beginPath();c.moveTo(x,V.Y(pp(row[0]/w.w)));c.lineTo(x,V.Y(pp(row[1]/w.w)));c.stroke();}
          points.push([w.id,j,row[0],row[1],row[2]]);last={T,x,y};
        }
      }
      c.setLineDash([]);
      const pa=pp(cRat(t.low)),pb=pp(cRat(t.high)),x0=V.X(t.window_open),x1=V.X(t.window_close),ya=V.Y(pa),yb=V.Y(pb);
      const split=clamp(V.X(cut),x0,x1),top=Math.min(ya,yb),height=Math.abs(ya-yb);
      c.fillStyle=rgba('#8F98A6',.055);c.fillRect(x0,top,split-x0,height);
      if(p.question.active){c.fillStyle=rgba(cfg.path,.12);c.fillRect(split,top,x1-split,height);}
      c.strokeStyle=rgba(cfg.path,.9);c.lineWidth=1.4;c.strokeRect(x0,top,x1-x0,height);
      if(p.question.active&&split>x0&&split<x1){c.setLineDash([3,3]);c.strokeStyle=rgba(cfg.path,.6);c.beginPath();c.moveTo(split,top);c.lineTo(split,top+height);c.stroke();c.setLineDash([]);}
      V.win={pA:pa,pB:pb,t0:t.window_open,t1:t.window_close,col:cfg.path};
      if(p.observed.witness_bar){const b=ctx.D.bars.find(b=>b.t===p.observed.witness_bar[0]);if(b){c.strokeStyle='#DDE9ED';c.lineWidth=1.5;c.strokeRect(V.X(b.t),V.Y(b.h)-3,V.bs,V.Y(b.l)-V.Y(b.h)+6);}}
      CS.drawing={release:r.release_id,history_revision:p.context.history_revision,ids:r.status==='RESEARCH_ONLY'?p.witnesses.map(w=>w.id):[],points,target:t.id,question:p.question.id,
        elapsed:[t.window_open,Math.min(t.window_close,Math.max(t.window_open,cut))],remaining:p.question.active?[p.question.first_close-5,p.question.last_close]:null};
    }
    if(CS.drag){const d=CS.drag;c.setLineDash([4,3]);c.strokeStyle=cfg.path;c.strokeRect(d.x,d.y,d.x1-d.x,d.y1-d.y);c.setLineDash([]);}
  }
  function continuationToolbar(ctx) {
    const b=dom('mode').querySelector('[data-m="continuations"]');if(b){b.hidden=!ICFG.enabled||!TRIAL.continuations;if(!b.hidden&&!b.title){b.title=lbl('FF:CANDIDATE-STATUS','mode_title');b.classList.add('cand');}}
    if(!continuationMode())return;
    const ab=dom('areab');ab.textContent='▭ Область · окно';ab.title='Закрепить физическую область и абсолютное будущее окно';
    dom('ev').innerHTML='';
  }
  root.addEventListener('click',e=>{
    const entry=e.target.closest('[data-c24-cut]');
    if(entry){const cut=Number(entry.dataset.c24Cut);if(CS.history.some(x=>x.cut===cut&&x.release===entry.dataset.c24Release)){st.rp=cut;st.pin=st.hover=null;render(true);}return;}
    const b=e.target.closest('[data-c24]');if(!b)return;
    if(b.dataset.c24==='draw')st.tool=true;
    else if(['question','history'].includes(b.dataset.c24)){CS.detail=b.dataset.c24;st.detPin=true;dom('detg')._k='';}
    else{CS.target=null;CS.packet=null;CS.key=null;CS.error=null;CS.drawing=null;CS.last=null;CS.comparison=null;CS.history=[];CS.selected=null;CS.previous=null;CS.seq++;}
    render(true);
  });
  root.addEventListener('change',e=>{if(e.target.id==='c24case'){CS.selected=e.target.value||null;redraw();}});
  cv.addEventListener('mousedown',e=>{
    if(!continuationMode()||!(st.tool||e.shiftKey))return;const[x,y]=local(e);if(x<0||x>V.plot.w||y<0||y>V.plot.h)return;
    e.stopImmediatePropagation();e.preventDefault();CS.drag={x,y,x1:x,y1:y};
  },true);
  cv.addEventListener('mousemove',e=>{if(!CS.drag)return;const[x,y]=local(e);CS.drag.x1=clamp(x,0,V.plot.w);CS.drag.y1=clamp(y,0,V.plot.h);e.stopImmediatePropagation();redraw();},true);
  window.addEventListener('mouseup',e=>{if(!CS.drag)return;e.stopImmediatePropagation();const d=CS.drag;CS.drag=null;
    try{const ctx=cur(),s=ctx.s,edge=s.side===1?s.idrH:s.idrL,w=s.idrH-s.idrL,u=y=>s.side*(V.P(y)-edge)/w;
      const k0=Math.floor(Math.min(u(d.y),u(d.y1))*10),k1=Math.max(k0+1,Math.ceil(Math.max(u(d.y),u(d.y1))*10));
      const open=Math.max(Math.floor(ctx.obs/5)*5,Math.floor(Math.min(V.T(d.x),V.T(d.x1))/5)*5),end=Math.min(SESS[s.k].end,Math.ceil(Math.max(V.T(d.x),V.T(d.x1))/5)*5);
      pinContinuation([k0,10],[k1,10],open,end,ctx);
    }catch(err){CS.error=err.message;render(true);}
  },true);
  const cFragment=new URLSearchParams(location.hash.slice(1));
  if(ICFG.enabled&&cFragment.get('mode')==='continuations'){TRIAL.continuations=true;st.mode='continuations';}
  function continuationSeed(ctx){
    if(CS.target||!continuationMode()||!ctx.s.conf)return;
    const seed=cFragment.get('cont');if(!seed||CS.seeded)return;CS.seeded=true;
    const [a,b,open,end,created]=seed.split(',').map(Number);
    CS.target={low:[a,10],high:[b,10],first_close:open+5,last_close:end,created_at:created};CS.scene=continuationScene(ctx);
  }
