  // Approved plan 22.10: one time x SD table, finite local cores and peak-cell projections.
  // Rendering functions keep their existing geometry. Every new number has an EST:TS-* bundle and exact region.
  const tsData = ctx => pbPacket(ctx)?.proof.time_sd || null;
  const tsLabel = key => lbl('EST:TS-CORE-R', key);
  const tsFields = ['k0','k1','b0','b1'];
  const tsSame = (a,b) => tsFields.every(k=>a[k]===b[k]);
  const tsBox = (bounds,time,F) => ({k0:Number.isFinite(bounds?.[0])?bounds[0]:null,k1:Number.isFinite(bounds?.[1])?bounds[1]:null,
    b0:time?(time[0]-F.f)/15:null,b1:time?(time[1]-F.f)/15:null});
  const tsInside = (q,v) => (v.k0==null||q.k>=v.k0)&&(v.k1==null||q.k<v.k1)&&(v.b0==null||q.b>=v.b0)&&(v.b1==null||q.b<v.b1);
  const tsMember = (z,q) => z.cell_mask.some(([k,b])=>q.k===k&&q.b===b);
  const TS_TRACE = [];

  async function tsVerify(r,q,ctx,F) {
    const p=r.proof,t=p.time_sd;
    if(!t||t.version!=='DR-LAB-TIME-SD-1.0'||t.scale!==PB.scale)throw Error('Нет выпуска времени × SD выбранного масштаба');
    const want={time_minutes:15,price_cells:3,price_cell_num:1,price_cell_den:10,atom_minutes:5,min_abs:4,min_frac_num:1,min_frac_den:20,projection:'MAX_KNOWN_JOINT_CELL',temporal_growth:false};
    if(JSON.stringify(t.definition)!==JSON.stringify(want))throw Error('Другая геометрия времени × SD');
    const source={...p};delete source.time_sd;delete source.time_sd_source;
    if(await cHash(source)!==p.time_sd_source)throw Error('Изменён исходный выпуск эпизодов');
    const known=new Set(F.M.map(m=>m.id)),w=new Map(p.sessions.map(s=>[s.id,s.w]));
    for(const ev of ['R','X']) {
      const m=t.maps?.[ev];if(!m||m.event!==(ev==='R'?'PB_L':'FINAL_X'))throw Error('Подменён тип события '+ev);
      const expected=ev==='R'?p.points.filter(v=>v.kt>=PB.scale):F.M.filter(v=>v.X.s==='known').map(v=>({id:v.id+'|FINAL-X',case:v.id,v:v.X.v,open:v.X.t,k:Math.floor(10*v.X.v/v.w),b:Math.floor((v.X.t-F.f)/15),episodes:[]}));
      if(JSON.stringify(m.points)!==JSON.stringify(expected))throw Error('Точки '+ev+' не совпадают с исходными событиями');
      const cellKeys=[...new Set(expected.map(v=>v.k+'|'+v.b))].sort();
      if(JSON.stringify(m.cells.map(v=>v.k+'|'+v.b).sort())!==JSON.stringify(cellKeys))throw Error('Неполная совместная таблица '+ev);
      const checkRegion=v=>{
        const qs=expected.filter(pt=>tsInside(pt,v)),ids=[...new Set(qs.map(pt=>pt.case))].sort(),later=new Set(qs.filter(pt=>pt.open+5>q.cut).map(pt=>pt.case)).size;
        if(JSON.stringify(ids)!==JSON.stringify(v.members)||v.n_known!==ids.length||v.earlier!==ids.length-later||v.later!==later||
           v.n_possible!==v.possible.length||new Set(v.possible).size!==v.possible.length||v.possible.some(id=>!known.has(id)||ids.includes(id)))throw Error('Состав/часы области '+ev+' не совпадают');
      };
      for(const v of [...m.cells,...m.cores,...m.price_peaks,...m.time_peaks,...m.regions])checkRegion(v);
      if(m.need!==Math.max(4,Math.ceil(F.N/20)))throw Error('Другая минимальная опора');
      const densityCache=new Map(),support=(k,b)=>{const key=k+'|'+b;if(!densityCache.has(key))densityCache.set(key,new Set(expected.filter(v=>v.b===b&&v.k>=k-1&&v.k<=k+1).map(v=>v.case)).size);return densityCache.get(key);};
      const candidates=new Map();
      for(const v of expected)for(const off of [-1,0,1]){
        const k=v.k+off,b=v.b,n=support(k,b);
        if(n<m.need)continue;
        if([-1,0,1].some(dk=>[-1,0,1].some(db=>support(k+dk,b+db)>n)))continue;
        candidates.set(k+'|'+b,{k,b,n});
      }
      const sorted=[...candidates.values()].sort((a,b)=>a.b-b.b||a.k-b.k),runs=[];
      for(const c of sorted){const last=runs.at(-1),tail=last?.at(-1);if(tail&&tail.b===c.b&&tail.n===c.n&&tail.k+1===c.k)last.push(c);else runs.push([c]);}
      const anchors=runs.map(a=>a.sort((p,q)=>Math.abs(2*p.k+1)-Math.abs(2*q.k+1)||p.k-q.k)[0]).sort((a,b)=>a.b-b.b||b.n-a.n||Math.abs(2*a.k+1)-Math.abs(2*b.k+1)||a.k-b.k);
      if(JSON.stringify(anchors.map(a=>[a.k,a.b,a.n]))!==JSON.stringify(m.cores.map(z=>[...z.anchor,z.apex_D])))throw Error('Ядра не являются локальными максимумами '+ev);
      for(const z of m.cores){const [k,b]=z.anchor;if(z.time_end-z.time_start!==15||z.price_high-z.price_low!==3||JSON.stringify(z.cell_mask)!==JSON.stringify([[k-1,b],[k,b],[k+1,b]])||z.n_known!==z.apex_D)throw Error('Ядро выросло за свой локальный масштаб');}
      for(const axis of ['price','time'])for(const v of m[axis+'_peaks']){
        const pool=m.cells.filter(c=>axis==='price'?c.k===v.index:c.b===v.index).sort((a,b)=>b.n_known-a.n_known||(axis==='price'?a.b-b.b:Math.abs(2*a.k+1)-Math.abs(2*b.k+1)||a.k-b.k));
        if(!pool.length||!tsSame(pool[0],v))throw Error('Проекция потеряла вторую координату');
      }
      for(const [kind,items]of [['CORE',m.cores],['PEAK',[...m.price_peaks,...m.time_peaks]],['REGION',[...m.cells,...m.regions]]])for(const v of items){
        const b=tsBundle(r,ev,kind,v),pt=b?.estimates.find(e=>e.value_kind==='POINT'),bd=b?.estimates.find(e=>e.value_kind==='BOUNDS');
        if(!pt||pt.numerator!==v.n_known||pt.denominator!==F.N||Math.abs(pt.value-v.n_known/F.N)>1e-12||(v.n_possible&&(!bd||Math.abs(bd.upper-(v.n_known+v.n_possible)/F.N)>1e-12)))throw Error('Нет собственного паспорта числа времени × SD');
      }
      if(q.region&&!m.regions.some(v=>tsFields.every((k,i)=>v[k]===q.region[i])))throw Error('Не опубликована выбранная область '+ev);
      const cats=m.sessions,catBundle=pbBundle(r,'EST:TS-SESSIONS-'+ev,p=>p.scale===PB.scale);
      if(Object.values(cats).reduce((a,b)=>a+b,0)!==F.N||!catBundle||catBundle.estimates[0].denominator!==F.N||catBundle.estimates[0].categories.some(c=>cats[c.category]!==c.count))throw Error('Категории не сохраняют N или собственный паспорт');
      if(t.today?.[ev]?.length!==m.cores.length)throw Error('Нет сегодняшних фактов каждого ядра');
    }
    // Every established post-L vote has its own chronological path witness; no unrelated terminal X is substituted.
    const pts=new Map(t.maps.R.points.map(v=>[v.id,v])),ws=new Map(p.sessions.map(v=>[v.id,v]));
    for(const v of t.links){
      const z=t.maps.R.cores.find(z=>z.zone_id===v.source_id),ids=[];
      if(!z)throw Error('Продолжение без исходного ядра');
      for(const hit of v.witnesses){
        const pt=pts.get(hit.point_id),s=ws.get(hit.case),j=p.grid.indexOf(hit.target_close),bar=s?.bars[j],b=(hit.target_open-F.f)/15;
        if(!pt||pt.case!==hit.case||!tsInside(pt,z)||hit.target_open<pt.open+5||hit.l_open!==pt.open||!bar||hit.target_close!==hit.target_open+5||
          (v.b0!=null&&Math.floor(b)<v.b0)||(v.b1!=null&&Math.floor(b)>=v.b1)||(v.k0!=null&&10*bar[1]<v.k0*s.w)||(v.k1!=null&&10*bar[2]>=v.k1*s.w))throw Error('Подменена связь после локального отката');
        ids.push(hit.case);
      }
      if(JSON.stringify([...new Set(ids)].sort())!==JSON.stringify(v.members)||v.n_known!==v.members.length)throw Error('Повторный голос связанного пути');
    }
    return r;
  }

  function tsBundle(r,ev,kind,v) {
    const est='EST:TS-'+kind+(kind==='LINK'?'':'-'+ev);
    return pbBundle(r,est,p=>p.scale===PB.scale&&(kind==='CORE'?p.zone_id===v.zone_id:kind==='PEAK'?p.axis===v.axis&&p.index===v.index&&tsSame(p,v):kind==='LINK'?p.source_id===v.source_id&&p.target_id===v.target_id:tsSame(p,v)));
  }
  function tsPass(F,ev,kind,v) {
    const r=F._pb,b=v&&tsBundle(r,ev,kind,v),pt=b?.estimates.find(e=>e.value_kind==='POINT'),bd=b?.estimates.find(e=>e.value_kind==='BOUNDS');
    const p={candidate:true,estimand:'EST:TS-'+kind+(kind==='LINK'?'':'-'+ev),event_id:ev==='R'?'PB_L':'FINAL_X',pct:pt?100*pt.value:null,pctHi:bd?100*bd.upper:null,
      yes_count:pt?.numerator||0,unknown_count:v?.n_possible||0,N:F.N,phrase:b?.claim.statement_ru||'Число ещё не опубликовано',horizon:'собственная активация → конец блока; указанное окно ET',bundle:b,region:v};
    if(b&&!TS_TRACE.some(q=>q.bundle===b.id))TS_TRACE.push({estimand:p.estimand,bundle:b.id,ev,kind,region:v,yes:p.yes_count,N:F.N});
    return p;
  }
  function tsFind(F,ev,kind,bounds,time,outframe=false) {
    const m=F._ts?.maps?.[ev];if(!m)return null;
    if(kind==='price_cell')return m.price_peaks.find(v=>v.index===bounds?.[0])||null;
    if(kind==='time_cell')return m.time_peaks.find(v=>v.index===(time[0]-F.f)/15)||null;
    const box=tsBox(bounds,time,F);let v=[...m.regions,...m.cells].find(v=>tsSame(v,box));
    if(!v&&outframe){const ks=m.points.map(q=>q.k);if(box.k0<=Math.min(...ks))v=m.regions.find(v=>v.k0==null&&v.k1===box.k1&&v.b0==null&&v.b1==null);else if(box.k1>Math.max(...ks))v=m.regions.find(v=>v.k0===box.k0&&v.k1==null&&v.b0==null&&v.b1==null);}
    return v||null;
  }
  function tsRegionPass(F,ev,kind,bounds,time,outframe=false) {
    const v=tsFind(F,ev,kind,bounds,time,outframe);return tsPass(F,ev,kind==='price_cell'||kind==='time_cell'?'PEAK':'REGION',v);
  }
  function tsZoneHeld(F,ev,i){const z=F.zones[ev]?.zones[i];return !z||!tsBundle(F._pb,ev,'CORE',z);}
  function tsCategories(F,ev) {
    const est='EST:TS-SESSIONS-'+ev,b=pbBundle(F._pb,est,p=>p.scale===PB.scale);
    if(b&&!TS_TRACE.some(q=>q.bundle===b.id))TS_TRACE.push({estimand:est,bundle:b.id,ev,kind:'SESSIONS',N:F.N});
    return b;
  }
  function tsProjectionHeld(F,est,params) {
    const ev=est.at(-1),price='k0'in params;
    return tsRegionPass(F,ev,price?'price_cell':'time_cell',price?[params.k0,params.k1]:null,price?null:[F.f+15*params.b0,F.f+15*params.b1]).pct==null;
  }

  pbMapContext = function(ctx) {
    if(ctx.F?._ts)return ctx;
    if(!pullbackMode()||!ctx.F)return ctx;
    if(PB.model?.base&&PB.model.base.r.family_id!==ctx.F.r.family_id){st.area=null;if(/^pb/.test(st.pin?.k||''))st.pin=null;st.hover=null;}
    requestPullbacks(ctx);const r=pbPacket(ctx),t=r?.proof.time_sd,F=ctx.F,key=r&&r.release_id;
    if(PB.model?.key===key&&PB.model?.base===F)return {...ctx,F:PB.model.F};
    const mi=new Map(F.M.map((m,i)=>[m.id,i])),ws=new Map((r?.proof.sessions||[]).map(w=>[w.id,w]));
    const ev={},zones={},zcell={};
    for(const e of ['R','X']) {
      const m=t?.maps[e],pts=(m?.points||[]).map(q=>({ev:e,i:mi.get(q.case),m:F.M[mi.get(q.case)],pbid:e==='R'?q.id:null,source_id:q.id,t:q.open,k:q.k,b:q.b,p:F.u2p(q.v/ws.get(q.case).w)}));
      const cells=new Map((m?.cells||[]).map(c=>[c.k+'|'+c.b,{k:c.k,b:c.b,list:c.members.map(id=>mi.get(id))}]));
      ev[e]={event_id:e==='R'?'PB_L':'FINAL_X',pts,cells,P:new Map((m?.price_peaks||[]).map(v=>[v.index,v.n_known])),T:new Map((m?.time_peaks||[]).map(v=>[v.index,v.n_known])),
        known:new Set(pts.map(q=>q.m.id)).size,unknown:m?.sessions.UNKNOWN||0,none:m?.sessions.NONE||0};
      const zs=(m?.cores||[]).map(z=>({...z,event_id:e,n_zone:z.n_known,p_snapshot:z.n_known/F.N,member_session_ids:z.members}));
      zones[e]={zones:zs,unknown_count:ev[e].unknown,no_event_count:ev[e].none};zcell[e]=new Map();
      zs.forEach((z,i)=>z.cell_mask.forEach(([k,b])=>{if(!zcell[e].has(k+'|'+b))zcell[e].set(k+'|'+b,i);}));
    }
    const view={...F,_pb:r||{loading:true},_ts:t||{loading:true},_cl:null,ev,zones,zcell,what:{...F.what,R:'Дна локальных откатов до обновления'},names:{...F.names}};
    PB.model={key,base:F,F:view};TS_TRACE.length=0;return {...ctx,F:view};
  };
  pbCloudContext = function(ctx) {
    const F=ctx.F;if(!F?._ts?.maps)return ctx;if(PB.model.cloud)return {...ctx,F:PB.model.cloud};
    const ev={};
    for(const e of ['R','X']){
      const groups=new Map();for(const q of F.ev[e].pts){if(!F.zones[e].zones.some(z=>tsMember(z,q)))continue;const key=q.k+'|'+q.t;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(q);}
      const pts=[...groups.values()].map(qs=>{const avg=qs.reduce((n,q)=>n+q.p,0)/qs.length;return qs.slice().sort((a,b)=>Math.abs(a.p-avg)-Math.abs(b.p-avg)||a.source_id.localeCompare(b.source_id))[0];});
      ev[e]={...F.ev[e],pts};
    }
    PB.model.cloud={...F,_cl:null,ev};return {...ctx,F:PB.model.cloud};
  };
  pbProjectionContext = function(ctx) {
    const F=ctx.F;if(!F?._ts?.maps)return ctx;const ev={};
    for(const e of ['R','X']){const by=new Map();for(const q of F.ev[e].pts){const peak=F._ts.maps[e].price_peaks.find(v=>v.index===q.k);if(!peak||!tsInside(q,peak))continue;const key=q.k+'|'+q.m.id,old=by.get(key);if(!old||old.t<q.t)by.set(key,q);}ev[e]={...F.ev[e],pts:[...by.values()]};}
    return {...ctx,F:{...F,ev}};
  };
  pbRange = function(ctx,lo,hi) {
    const t=tsData(ctx),F=ctx.F;if(!t||!F)return [lo,hi];
    for(const e of ['R','X'])t.maps[e].cores.forEach((z,i)=>{const rel=t.today[e][i];if(rel.clock==='PAST'&&!(e==='X'&&rel.status==='HOLDS'))return;if(e==='X'&&rel.status==='IMPOSSIBLE')return;const a=F.u2p(z.price_low/10),b=F.u2p(z.price_high/10);lo=Math.min(lo,a,b);hi=Math.max(hi,a,b);});
    return [lo,hi];
  };
  pbVisualHover = function(h) {
    if(!h)return h;
    if(h.k==='pbzone')return {...h,k:'zone',ev:h.ev||'R'};
    if(h.k==='pbpcell')return {...h,k:'pcell',ev:h.ev||'R'};
    if(h.k==='pbtcell')return {...h,k:'tcell'};
    if(h.k==='pbarea')return {...h,k:'area'};
    if(h.k==='pbpt'){const q=PB.model?.F.ev.R.pts.find(q=>q.pbid===h.id);return q?{...h,k:'pt',ev:'R',i:q.i,q}:h;}
    return h;
  };
  pbSemanticHit = function(h) {
    if(!pullbackMode()||!h)return h;
    if(h.k==='zone')return {...h,k:'pbzone'};
    if(h.k==='pcell')return {...h,k:'pbpcell'};
    if(h.k==='tcell'){const up=V.ctx.F.d0>0?'X':'R';return {...h,k:'pbtcell',ev:h.ev||(st.my<V.bandCy?up:up==='R'?'X':'R')};}
    if(h.k==='unk')return {...h,k:'pbunk'};
    if(h.k==='area')return {...h,k:'pbarea'};
    if(h.k==='pt'&&h.q?.pbid)return {k:'pbpt',id:h.q.pbid,same:new Set(h.same).size,ev:'R'};
    return h;
  };
  pbZonePass = (F,z)=>tsPass(F,'R','CORE',z);
  pbRegionPass = (F,bounds,time,outframe)=>tsRegionPass(F,'R','region',bounds,time,outframe);

  function tsPlace(F,v){if(!v)return '';return (v.k0!=null?band(v.k0,v.k1)+' SD':'вся цена')+' · '+(v.b0!=null?clk(F.f+15*v.b0)+'–'+clk(F.f+15*v.b1):'весь горизонт');}
  function tsRows(F,ev,kind,v){const p=tsPass(F,ev,kind,v);return '<div class="is" data-ts-est="'+p.estimand+'" data-ts-bundle="'+(p.bundle?.id||'')+'"><b class="big" style="color:'+cfg[ev]+'">'+ppTxt(p,true)+'</b> · '+esc(tsPlace(F,v))+'</div><div class="is">'+esc(p.phrase)+'</div>'+(v?'<div class="is k">'+tsLabel('earlier')+': '+pct(100*v.earlier/F.N)+' · '+tsLabel('later')+': '+pct(100*v.later/F.N)+'</div>':'');}
  function tsZoneInspector(ctx,h) {
    const F=pbMapContext(ctx).F,ev=h.ev||'R',z=F?.zones[ev]?.zones[h.i];if(!z)return '<div class="is">'+esc(pbStatus(ctx))+'</div>';
    const rel=F._ts.today[ev][h.i],v=rel.visit,visit={...v,t:v.close,start:z.time_start,end:z.time_end};
    let html='<div class="ih" style="color:'+cfg[ev]+'">'+z.label+' · '+tsLabel(ev)+'</div>'+tsRows(F,ev,'CORE',z);
    html+='<div class="is">'+tsLabel('core')+' · '+lbl('FF:PB-TODAY',rel.clock)+'</div><div class="is">'+visitWords(visit)+'</div>';
    if(ev==='R'){
      const w=pbW(F),c=rel.completion;
      html+='<div class="is">'+(c.state==='COMPLETED'?lbl('FF:PB-TODAY','COMPLETED',{top:w.top,h:clk(c.h_open),t:clk(c.b_close)}):c.state==='IN_ZONE_NOT_UPDATED'?lbl('FF:PB-TODAY','IN_ZONE_NOT_UPDATED',{top:w.top,h:clk(c.h_open)}):lbl('FF:PB-TODAY','NONE'))+'</div>';
      const links=F._ts.links.filter(v=>v.source_id===z.zone_id&&v.n_known+v.n_possible>0);
      if(links.length)html+='<div class="ih">'+tsLabel('after')+'</div>'+links.map(v=>{const p=tsPass(F,'R','LINK',v),target=F.zones.X.zones.find(q=>q.zone_id===v.target_id);return '<div class="is" data-ts-est="EST:TS-LINK" data-ts-bundle="'+(p.bundle?.id||'')+'">'+esc((target?.label||'область')+' · '+tsPlace(F,v))+' · <b>'+ppTxt(p,true)+'</b></div>';}).join('')+'<div class="is k">'+tsLabel('source')+'</div>';
    }else html+='<div class="is">'+zst(rel.status)+'</div>';
    return html;
  }
  const tsOldInspector=pbInspector;
  pbInspector=function(ctx,h){if(h?.k==='pbpt')return tsOldInspector(ctx,h);if(h?.k==='pbzone')return tsZoneInspector(ctx,h);if(h?.k==='pbunk')return pbUnknownHtml(ctx);return pbRegionInspector(ctx,h);};
  pbUnknownHtml=function(ctx){const F=pbMapContext(ctx).F;if(!F?._ts?.maps)return '<div class="is">'+esc(pbStatus(ctx))+'</div>';
    return '<div class="ih">Не распределено по координатам</div>'+['R','X'].map(ev=>{const b=tsCategories(F,ev);return (b?.estimates[0].categories||[]).filter(c=>['UNKNOWN','NONE'].includes(c.category)).map(c=>'<div class="is" data-ts-est="'+b.estimand+'" data-ts-bundle="'+b.id+'">'+ev+' · '+tsLabel(c.category)+' · '+pct(100*c.count/F.N)+'</div>').join('');}).join('');};
  pbJointXTip=(ctx,h)=>tsZoneInspector(ctx,{...h,ev:'X'});
  pbRegionInspector=function(ctx,h){
    const F=pbMapContext(ctx).F;if(!F?._ts?.maps)return '<div class="is">'+esc(pbStatus(ctx))+'</div>';
    if(h?.k==='pbarea'){const a=st.area,ev=a?.ev||st.ev;if(!a)return '';const v=tsFind(F,ev,'region',[a.k0,a.k1],a.b0!=null?[F.f+15*a.b0,F.f+15*a.b1]:null);return '<div class="ih">'+tsLabel('region')+'</div>'+tsRows(F,ev,'REGION',v);}
    const isTime=h?.k==='pbtcell'||h?.k==='tcell',ev=h?.ev||st.ev,axis=isTime?'time':'price',index=isTime?h.b0:h.k0;
    const v=F._ts.maps[ev][axis+'_peaks'].find(v=>v.index===index);
    return '<div class="ih" style="color:'+cfg[ev]+'">'+ev+' · '+tsLabel(axis)+'</div>'+tsRows(F,ev,'PEAK',v);
  };
  pbCombinedZones=function(ctx){
    requestPullbacks(ctx);const F=pbMapContext(ctx).F,t=F?._ts;
    let out='<div class="p21-h second"><span>Зоны по времени</span>'+scopeSwitch()+'</div>';
    if(!t?.maps)return out+'<div class="p21-note">'+esc(pbStatus(ctx))+'</div>';
    const all=['R','X'].flatMap(ev=>F.zones[ev].zones.map((z,i)=>({ev,z,i}))).sort((a,b)=>a.z.time_start-b.z.time_start||b.z.n_known-a.z.n_known),sl=sliceOf(ctx);let sep=false;
    for(const {ev,z,i}of all){
      if(!sep&&z.time_end>sl){out+='<div class="p24-now"><span></span>сейчас '+clk(sl)+'<span></span></div>';sep=true;}
      const p=tsPass(F,ev,'CORE',z),rel=t.today[ev][i],status=ev==='R'?lbl('FF:PB-TODAY',rel.clock):zst(rel.status);
      const look=ev==='R'?(rel.clock==='PAST'?'IMPOSSIBLE':'POSSIBLE'):rel.status;
      out+=link({k:'pbzone',ev,i},'<span class="t"><span><span class="zt">'+clk(z.time_start)+'–'+clk(z.time_end)+'</span> <i class="zn" style="color:'+cfg[ev]+'">'+z.label+'</i></span><span class="p21-sub">'+band(z.price_low,z.price_high)+' SD · '+status+'</span></span><b class="zp">'+ppTxt(p,true)+'</b>','mc zst-'+look,null,p.phrase).replace('data-l21=','data-ts-est="'+p.estimand+'" data-ts-bundle="'+p.bundle.id+'" data-l21=');
    }
    if(!sep)out+='<div class="p24-now"><span></span>'+(sl>=F.end?'блок закончен':'сейчас '+clk(sl))+'<span></span></div>';
    if(!all.length)out+='<div class="p21-note">'+tsLabel('none')+'</div>';
    for(const ev of ['R','X']){const b=tsCategories(F,ev);if(b)for(const c of b.estimates[0].categories.filter(c=>c.category!=='IN_ZONES'))out+='<div class="p21-link dim" data-ts-est="'+b.estimand+'" data-ts-bundle="'+b.id+'">'+prow('<i style="color:'+cfg[ev]+'">'+ev+'</i> '+tsLabel(c.category),pct(100*c.count/F.N))+'</div>';}
    return out;
  };
  pbAreaHtml=function(ctx){const F=pbMapContext(ctx).F,a=st.area,ev=a.ev||st.ev,v=tsFind(F,ev,'region',[a.k0,a.k1],a.b0!=null?[F.f+15*a.b0,F.f+15*a.b1]:null),p=tsPass(F,ev,'REGION',v);return '<div class="p21-h second p24-sel">Выбранная область <span><button class="p24-x" data-clear="area" title="Снять выбор (Esc)">✕</button></span></div>'+link({k:'pbarea',ev},prow('<i style="color:'+cfg[ev]+'">'+ev+'</i> '+esc(tsPlace(F,v)),ppTxt(p,true)),'',null,p.phrase);};

  pbGeom=function(ctx,r){const F=pbMapContext(ctx).F,p=r.proof;return {W:new Map(p.sessions.map(w=>[w.id,w])),E:new Map(p.episodes.map(e=>[e.id,e])),P:new Map(p.points.map(q=>[q.id,q])),zones:(F._ts?.maps?.R.cores||[]).map((z,i)=>({z,i,pts:p.points.filter(q=>q.kt>=PB.scale&&tsInside(q,z)).map(q=>({q,x:V.X(q.open+2.5),y:V.Y(F.u2p(q.v/p.sessions.find(w=>w.id===q.case).w))}))}))};};
  const tsOldDetail=pbDetail;
  pbDetail=function(ctx,h){if(h.k==='pbpt')return tsOldDetail(ctx,h);if(h.k==='pbunk')return {head:'Не распределено по координатам',body:pbUnknownHtml(ctx)};const F=pbMapContext(ctx).F,ev=h.ev||st.ev;
    if(h.k==='pbzone'){const z=F.zones[ev].zones[h.i];if(!z)return {head:'Время × SD',body:''};let body=tsZoneInspector(ctx,h);
      body+='<div class="dt">Истории этого ядра</div>'+F._ts.maps[ev].points.filter(q=>tsInside(q,z)).map(q=>ev==='R'?'<div class="is" data-pbpt="'+esc(q.id)+'">'+esc(pbDate(q.case))+' · '+clk(q.open)+' · '+sd(q.v/rWidth(F,q.case))+'</div>':'<div class="is">'+esc(pbDate(q.case))+' · '+clk(q.open)+' · '+sd(q.v/rWidth(F,q.case))+'</div>').join('');
      return {head:z.label+' · '+tsLabel(ev),body};}
    return {head:'Время × SD',body:pbRegionInspector(ctx,h)};
  };
  function rWidth(F,id){return F._pb.proof.sessions.find(w=>w.id===id).w;}
  pbCards=function(g,ctx){if(!pullbackMode())return false;const F=pbMapContext(ctx).F;if(!F?._ts?.maps)return false;drawHeat('dcR',F,ctx,'R');drawHeat('dcX',F,ctx,'X');return true;};
  function tsHills(F,ev){return F.zones[ev].zones.map((z,i)=>{const cases=new Map();for(const q of F.ev[ev].pts)if(tsMember(z,q)){if(!cases.has(q.m.id))cases.set(q.m.id,new Set());cases.get(q.m.id).add(q.t+2.5);}const pts=[];let pk=0,pkT=z.time_start;for(let t=z.time_start;t<=z.time_end+.01;t+=1.5){let d=0;for(const times of cases.values())d+=Math.max(...[...times].map(u=>Math.exp(-((t-u)**2)/(2*7**2))));pts.push([t,d]);if(d>pk){pk=d;pkT=t;}}return {z,i,pts,pk,pkT,b0:z.b0,b1:z.b1,cases:cases.size};});}
  const tsOldLink=linkOf;
  linkOf=function(ctx){const F=ctx.F,h=hv();if(!F?._ts?.maps||!h||!['pcell','tcell'].includes(h.k))return tsOldLink(ctx);
    V.lk=null;const ev=h.ev||st.ev,axis=h.k==='pcell'?'price':'time',index=h.k==='pcell'?h.k0:h.b0,v=F._ts.maps[ev][axis+'_peaks'].find(v=>v.index===index);if(!v)return;
    const target={event_id:ev,cell_mask:[[v.k0,v.b0]],time_start:F.f+15*v.b0,time_end:F.f+15*v.b1};
    V.lk={ev,src:'pcell',x:V.X(F.f+15*v.b0+7.5),y:V.Y(F.u2p((v.k0+v.k1)/20)),b:v.b0,k0:v.k0,k1:v.k1,n:v.n_known,past:v.later===0,marker:targetMarker(F,ctx,ev,target)};
    V.win={pA:null,pB:null,t0:target.time_start,t1:target.time_end,col:V.lk.marker.paint.color};
  };
  const tsOldTip=tipHtml;
  const tsFinalFamily=F=>({...F,names:{...F.names,R:'Окончательный откат',X:'Окончательное расширение'}});
  tipHtml=function(h,ctx){if(pullbackMode()&&h?.k==='hcell'){const F=pbMapContext(ctx).F,v=tsFind(F,h.ev,'region',[h.kk,h.kk+1],[F.f+15*h.b,F.f+15*(h.b+1)]);return '<div class="ih">'+h.ev+' · время × SD</div>'+tsRows(F,h.ev,'REGION',v);}if(pullbackMode()&&h?.k==='pt')return tsOldTip(h,{...ctx,F:tsFinalFamily(ctx.F)});return tsOldTip(h,ctx);};
  const tsOldZoneTip=zoneTip;
  zoneTip=function(F,ctx,h){return pullbackMode()?tsZoneInspector(ctx,h):tsOldZoneTip(F,ctx,h);};
  // These function bindings are hoisted from panel.js; numerical BASE/NOW passports are kept as final-extreme context.
  const tsOldNowHtml=nowHtml;
  nowHtml=function(F,ctx){const html=tsOldNowHtml(F,ctx);return pullbackMode()?html.replace('Сейчас',tsLabel('context')):html;};
  const tsOldDetBody=detBody;
  detBody=function(ctx,o){if(pullbackMode()&&o&&['zone','pcell','tcell','area'].includes(o.k))return pbDetail(ctx,pbSemanticHit(o));if(pullbackMode()&&o?.k==='pt')return tsOldDetBody({...ctx,F:tsFinalFamily(ctx.F)},o);return tsOldDetBody(ctx,o);};
  const tsOldMember=memberHtml;
  memberHtml=function(F,m){return tsOldMember(pullbackMode()?tsFinalFamily(F):F,m);};
