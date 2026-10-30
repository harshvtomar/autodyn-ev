"use strict";
/* Chat 8: UI is read-only with respect to authoritative physics and 3D data. */
(() => {
  const $ = id => document.getElementById(id);
  const fields = {
    quarter: [['damping_n_s_m','Damper (N·s/m)'],['suspension_stiffness_n_m','Spring (N/m)']],
    half: [['front_damping_n_s_m','Front damper (N·s/m)'],['rear_damping_n_s_m','Rear damper (N·s/m)'],
      ['front_spring_n_m','Front spring (N/m)'],['rear_spring_n_m','Rear spring (N/m)']]
  };
  let latest=null, highlighted=null, requestToken=0;
  function refreshParameters(){
    const model=$('opt-model').value;
    for(const id of ['opt-p1','opt-p2']){
      const select=$(id);select.replaceChildren();
      if(id==='opt-p2'){const none=document.createElement('option');none.value='';none.textContent='None · 7 cases';select.appendChild(none);}
      for(const [val,label] of fields[model]){const o=document.createElement('option');o.value=val;o.textContent=label;select.appendChild(o);}
    }
    $('opt-status').textContent=`${model==='quarter'?'Quarter-car':'Half-car'} parameter choices ready. All scenarios use matching road and time settings.`;
  }
  const num = id => Number($(id).value);
  function scenario(){
    const model=$('opt-model').value;
    if(model==='quarter'){
      const keys=['sprung_mass_kg','unsprung_mass_kg','suspension_stiffness_n_m','damping_n_s_m','tire_stiffness_n_m'];
      return {vehicle:Object.fromEntries(keys.map(k=>[k,num(k)])),road:{kind:$('road_kind').value,
        height_m:num('height_mm')/1000,start_s:0.5,bump_length_m:num('bump_length_m'),
        speed_m_s:num('speed_m_s'),sine_frequency_hz:num('sine_frequency_hz'),
        bump_spacing_m:num('bump_spacing_m'),chirp_end_frequency_hz:num('chirp_end_frequency_hz'),
        chirp_duration_s:num('chirp_duration_s')},settings:{duration_s:num('duration_s'),dt_s:num('dt_s')}};
    }
    const vehicle=Object.fromEntries(Array.from($('half-config').querySelectorAll('[name]')).map(n=>[n.name,Number(n.value)]));
    return {vehicle,road:{kind:$('half-road-kind').value,height_m:num('half-height')/1000,
      start_s:0.5,bump_length_m:num('half-bump-length'),speed_m_s:num('half-speed'),
      sine_frequency_hz:num('half-sine'),bump_spacing_m:num('half-bump-spacing'),
      chirp_end_frequency_hz:num('half-chirp-end'),chirp_duration_s:num('half-chirp-duration')},
      settings:{duration_s:num('half-duration'),dt_s:num('half-dt')}};
  }
  function constraints(){
    const limits={};
    for(const [name,id] of [['max_body_acceleration_rms_m_s2','opt-limit-rms'],
                            ['max_suspension_travel_peak_to_peak_mm','opt-limit-travel'],
                            ['max_tire_deflection_peak_abs_mm','opt-limit-tire']]){
      const raw=$(id).value.trim();if(raw!==''){
        const v=Number(raw);if(!Number.isFinite(v)||v<0)throw Error(`${name} must be a finite nonnegative number`);
        limits[name]=v;
      }
    }
    return limits;
  }
  const fmt=(x,n=3)=>Number(x).toFixed(n);
  const add=(parent,tag,value)=>{const n=document.createElement(tag);n.textContent=value;parent.appendChild(n);return n;};
  async function run(){
    const token=++requestToken;
    latest=null; highlighted=null; $('opt-run').disabled=true;
    ['opt-csv','opt-json','opt-report'].forEach(id=>$(id).disabled=true);
    $('opt-status').textContent='Running bounded study against the accepted physics engine…';
    try {
      const params=[$('opt-p1').value,$('opt-p2').value].filter(Boolean);
      if(new Set(params).size!==params.length)throw Error('Choose two different parameters or select None for the second parameter');
      const body={model:$('opt-model').value,...scenario(),parameters:params,points_per_axis:7,constraints:constraints()};
      const response=await fetch('/api/optimization/study',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const result=await response.json();
      if(!response.ok)throw Error(result.error||`HTTP ${response.status}`);
      if(token!==requestToken)return;
      latest=result; highlighted=result.selected_id;
      render();['opt-csv','opt-json','opt-report'].forEach(id=>$(id).disabled=false);
    }catch(err){if(token===requestToken){$('opt-status').textContent=`Study rejected: ${err.message}`;$('opt-summary').replaceChildren();$('opt-table-body').replaceChildren();}}
    finally{if(token===requestToken)$('opt-run').disabled=false;}
  }
  function render(){
    const r=latest;if(!r)return;
    $('opt-status').textContent=`${r.grid.run_count} deterministic cases · ${r.feasible_count} feasible · ${r.pareto_ids.length} non-dominated · selected: ${r.selected_id??'none'}`;
    const summary=$('opt-summary');summary.replaceChildren();
    const base=r.baseline.metrics;
    for(const [title,content] of [
      ['Baseline RMS',`${fmt(base.body_acceleration_rms_m_s2)} m/s²`],
      ['Baseline travel',`${fmt(base.suspension_travel_peak_to_peak_mm,2)} mm`],
      ['Feasible',`${r.feasible_count} / ${r.grid.run_count}`],
      ['Selected case',r.selected_id===null?'None':`#${r.selected_id} · minimum RMS among feasible`],
    ]){const div=document.createElement('div');add(div,'b',`${title}: `);add(div,'span',content);summary.appendChild(div);}
    const body=$('opt-table-body');body.replaceChildren();
    for(const c of r.candidates){
      const tr=document.createElement('tr');tr.tabIndex=0;tr.setAttribute('aria-label',`Inspect case ${c.id}`);
      if(c.id===highlighted)tr.classList.add('opt-selected');
      const entries=[`#${c.id}`,Object.entries(c.parameters).map(([k,v])=>`${k}=${fmt(v,2)}`).join(' · '),
        fmt(c.metrics.body_acceleration_rms_m_s2,4),fmt(c.metrics.suspension_travel_peak_to_peak_mm,2),
        fmt(c.metrics.tire_deflection_peak_abs_mm,2),c.feasible?'Feasible':c.failed_constraints.join(', '),
        r.pareto_ids.includes(c.id)?'Yes':'—'];
      entries.forEach(v=>add(tr,'td',v));
      const select=()=>{highlighted=c.id;render();};
      tr.addEventListener('click',select);tr.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select();}});
      body.appendChild(tr);
    }
    const selected=r.candidates.find(c=>c.id===highlighted);
    $('opt-selection').textContent=selected?`Viewing case #${selected.id}: ${Object.entries(selected.parameters).map(([k,v])=>`${k}=${fmt(v,2)} ${r.grid.bounds[k].unit}`).join(' · ')} · RMS ${fmt(selected.metrics.body_acceleration_rms_m_s2,4)} m/s² · travel ${fmt(selected.metrics.suspension_travel_peak_to_peak_mm,2)} mm${selected.feasible?' · feasible':' · infeasible'}`:'No selected candidate; constraints may exclude every case.';
    drawPlot(r);
  }
  function drawPlot(r){
    const canvas=$('opt-plot');const bounds=canvas.getBoundingClientRect();if(bounds.width<5)return;
    const dpr=Math.min(window.devicePixelRatio||1,2);canvas.width=Math.round(bounds.width*dpr);canvas.height=Math.round(bounds.height*dpr);
    const ctx=canvas.getContext('2d');if(!ctx)return;ctx.scale(dpr,dpr);
    const w=bounds.width,h=bounds.height,L=64,R=22,T=23,B=49,P=w-L-R,Q=h-T-B;
    const xs=r.candidates.map(c=>c.metrics.body_acceleration_rms_m_s2),ys=r.candidates.map(c=>c.metrics.suspension_travel_peak_to_peak_mm);
    let xlo=Math.min(...xs),xhi=Math.max(...xs),ylo=Math.min(...ys),yhi=Math.max(...ys);
    const xp=Math.max((xhi-xlo)*.1,.001),yp=Math.max((yhi-ylo)*.1,.1);
    xlo-=xp;xhi+=xp;ylo=Math.max(0,ylo-yp);yhi+=yp;
    const X=v=>L+(v-xlo)/(xhi-xlo)*P,Y=v=>h-B-(v-ylo)/(yhi-ylo)*Q;
    ctx.clearRect(0,0,w,h);ctx.font='11px system-ui';ctx.fillStyle='#bed6e1';ctx.strokeStyle='#355467';ctx.lineWidth=1;
    for(let j=0;j<=4;j++){const x=L+j*P/4,y=T+j*Q/4;ctx.beginPath();ctx.moveTo(L,y);ctx.lineTo(w-R,y);ctx.stroke();ctx.fillText(fmt(yhi-j*(yhi-ylo)/4,1),8,y+3);ctx.fillText(fmt(xlo+j*(xhi-xlo)/4,2),Math.max(L-12,x-14),h-B+17);}
    ctx.fillText('Acceleration RMS (m/s²) →',L+P*.35,h-8);
    // The vertical-axis unit is spelled out above the canvas; avoid colliding with ticks on narrow screens.
    for(const c of r.candidates){const x=X(c.metrics.body_acceleration_rms_m_s2),y=Y(c.metrics.suspension_travel_peak_to_peak_mm);
      ctx.beginPath();ctx.arc(x,y,c.id===highlighted?7:4.5,0,Math.PI*2);
      ctx.fillStyle=c.id===highlighted?'#fac07a':!c.feasible?'#7f8d9a':r.pareto_ids.includes(c.id)?'#66e1cf':'#72a6ff';ctx.fill();
      if(c.id===highlighted){ctx.strokeStyle='#fff';ctx.lineWidth=1.5;ctx.stroke();}
    }
  }
  function download(name,type,data){
    const url=URL.createObjectURL(new Blob([data],{type}));const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function csv(){if(!latest)return;const r=latest;
    const names=r.grid.parameters;const keys=Object.keys(r.candidates[0].metrics);
    const meta=['schema_version','application_version','model','road_kind','road_height_m','road_speed_m_s',
      'duration_s','dt_s','baseline_vehicle_json','constraints_json'];
    const headers=[...meta,'id',...names,...keys,'feasible','failed_constraints','pareto','selected'];
    const quote=v=>{const str=String(v??'');return /[",\n\r]/.test(str)?'"'+str.replace(/"/g,'""')+'"':str;};
    const lines=[headers.map(quote).join(',')];
    for(const c of r.candidates){const values=[r.schema_version,r.application_version,r.model,r.scenario.road.kind,
      r.scenario.road.height_m,r.scenario.road.speed_m_s,r.scenario.settings.duration_s,r.scenario.settings.dt_s,
      JSON.stringify(r.baseline.vehicle),JSON.stringify(r.constraints),c.id,...names.map(k=>c.parameters[k]),
      ...keys.map(k=>c.metrics[k]),c.feasible,c.failed_constraints.join('|'),r.pareto_ids.includes(c.id),
      c.id===r.selected_id];lines.push(values.map(quote).join(','));}
    download('autodyn-chat8-optimization.csv','text/csv;charset=utf-8',lines.join('\n')+'\n');
  }
  function report(){if(!latest)return;const r=latest;
    const chosen=r.candidates.find(c=>c.id===r.selected_id);
    const lines=[`AutoDyn EV v${r.application_version} — Bounded Engineering Study`,
      `Schema: ${r.schema_version}`,`Model: ${r.model}`,`Grid: ${JSON.stringify(r.grid)}`,
      `Road and solver: ${JSON.stringify(r.scenario)}`,`Baseline: ${JSON.stringify(r.baseline)}`,
      `Limits: ${JSON.stringify(r.constraints)}`,`Objectives: ${JSON.stringify(r.objectives)}`,
      `Feasible: ${r.feasible_count}/${r.grid.run_count}; Pareto IDs: ${r.pareto_ids.join(', ')||'none'}`,
      `Selected: ${chosen?JSON.stringify(chosen):'No feasible candidate'}`,
      `Selection rule: ${r.selection_rule}`,'','Warnings:',...r.warnings.map(w=>'- '+w)];
    download('autodyn-chat8-engineering-report.txt','text/plain;charset=utf-8',lines.join('\n')+'\n');
  }
  $('opt-model').addEventListener('change',refreshParameters);
  $('opt-use-current').addEventListener('click',()=>{$('opt-model').value=$('model-select').value==='half'?'half':'quarter';refreshParameters();});
  $('opt-run').addEventListener('click',run);
  $('opt-csv').addEventListener('click',csv);
  $('opt-json').addEventListener('click',()=>latest&&download('autodyn-chat8-optimization.json','application/json',JSON.stringify(latest,null,2)));
  $('opt-report').addEventListener('click',report);
  window.addEventListener('resize',()=>latest&&drawPlot(latest));
  refreshParameters();
})();
