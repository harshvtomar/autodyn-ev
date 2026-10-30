"use strict";
/* Chat 6 standalone EV regeneration visualization, no external packages. */
(()=>{
 const $=id=>document.getElementById(id), form=$('regen-form');
 const defaults=Object.fromEntries([...form.elements].filter(e=>e.name).map(e=>[e.name,e.value]));
 let output=null;
 const fmt=(v,d=2)=>Number(v).toLocaleString('en-US',{maximumFractionDigits:d,minimumFractionDigits:d});
 function scenario(){return Object.fromEntries([...form.elements].filter(e=>e.name).map(e=>[e.name,e.name==='profile'?e.value:Number(e.value)]));}
 function status(v,bad=false){$('regen-status').textContent=v;$('regen-status').style.color=bad?'#ffad9f':'#8ce1d5';}
 function metric(label,value){const el=document.createElement('div');el.className='card';const span=document.createElement('span');span.textContent=label;const strong=document.createElement('strong');strong.textContent=value;el.append(span,strong);return el;}
 function plot(id,t,series){const canvas=$(id),rect=canvas.parentElement.getBoundingClientRect();if(rect.width<20)return;
   const w=rect.width,h=rect.height,dpr=Math.min(window.devicePixelRatio||1,2);
   canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);
   ctx.clearRect(0,0,w,h);const left=54,right=10,top=12,bottom=29,iw=Math.max(1,w-left-right),ih=Math.max(1,h-top-bottom);
   let lo=Infinity,hi=-Infinity;for(const [,arr] of series){for(const value of arr){if(value<lo)lo=value;if(value>hi)hi=value;}}
   const pad=(hi-lo||1)*0.08;lo=Math.min(0,lo-pad);hi+=pad;const xt=t[t.length-1]||1;
   const x=q=>left+(q/xt)*iw,y=q=>top+(hi-q)/(hi-lo)*ih;
   ctx.font='10px system-ui';ctx.textAlign='right';for(let k=0;k<=4;k++){const v=lo+(hi-lo)*k/4,py=y(v);ctx.strokeStyle='#2a4257';ctx.beginPath();ctx.moveTo(left,py);ctx.lineTo(w-right,py);ctx.stroke();ctx.fillStyle='#b1c6d4';ctx.fillText(Math.abs(v)>100?Math.round(v).toLocaleString():v.toFixed(1),left-6,py+3);}
   ctx.textAlign='center';for(let k=0;k<=4;k++)ctx.fillText((xt*k/4).toFixed(1),x(xt*k/4),h-8);
   for(const [,arr,color] of series){ctx.strokeStyle=color;ctx.lineWidth=2;ctx.beginPath();for(let i=0;i<t.length;i++){if(!i)ctx.moveTo(x(t[i]),y(arr[i]));else ctx.lineTo(x(t[i]),y(arr[i]));}ctx.stroke();}
   let legend=canvas.parentElement.nextElementSibling;if(!legend||!legend.classList.contains('plot-legend')){legend=document.createElement('div');legend.className='plot-legend';canvas.parentElement.after(legend);}
   legend.replaceChildren(...series.map(([label,,color])=>{const s=document.createElement('span'),mark=document.createElement('i');mark.style.background=color;s.append(mark,document.createTextNode(label));return s;}));
 }
 function render(){if(!output)return;const d=output,m=d.metrics,c=d.channels;
  $('regen-metrics').replaceChildren(
   metric('Stopped',m.stopped?'Yes':'Window ended'),metric('Stopping time',m.stopped?`${fmt(m.stopping_time_s)} s`:'Not reached'),
   metric('Stopping distance',m.stopped?`${fmt(m.stopping_distance_m)} m`:'Not reached'),metric('Kinetic energy lost',`${fmt(m.kinetic_energy_reduction_j/1000)} kJ`),
   metric('Battery energy stored',`${fmt(m.battery_energy_stored_j/1000)} kJ`),metric('Friction heat',`${fmt(m.friction_dissipation_j/1000)} kJ`),
   metric('Conversion losses',`${fmt(m.conversion_loss_j/1000)} kJ`),metric('Battery recovery ratio',`${fmt(100*m.recovery_fraction_of_kinetic_reduction,1)}%`),
   metric('Peak motor mechanical power',`${fmt(m.peak_motor_mechanical_power_w/1000)} kW`),metric('Peak battery charging power',`${fmt(m.peak_battery_charge_power_w/1000)} kW`),
   metric('Energy budget residual',`${fmt(m.energy_balance_residual_j,6)} J`),metric('Final speed',`${fmt(m.final_speed_m_s)} m/s`));
  const graphs=[['regen-speed',[['Speed',c.speed_m_s,'#66e1cf']]],
   ['regen-force',[['Total',c.actual_brake_force_n,'#fac07a'],['Regen',c.regen_force_n,'#66e1cf'],['Friction',c.friction_force_n,'#be9cff']]],
   ['regen-power',[['Motor',c.motor_mechanical_power_w,'#66e1cf'],['Battery',c.battery_charge_power_w,'#72a6ff'],['Friction heat',c.friction_dissipation_power_w,'#fac07a']]],
   ['regen-energy',[['Battery',c.cumulative_battery_energy_j,'#66e1cf'],['Friction',c.cumulative_friction_energy_j,'#fac07a'],['Conversion loss',c.cumulative_conversion_loss_j,'#be9cff']]],
   ['regen-balance',[['Kinetic decrease',c.kinetic_energy_reduction_j,'#72a6ff'],['Allocated total',c.cumulative_battery_energy_j.map((x,i)=>x+c.cumulative_friction_energy_j[i]+c.cumulative_conversion_loss_j[i]),'#66e1cf']]],
   ['regen-load',[['Front',c.front_normal_n,'#be9cff'],['Rear',c.rear_normal_n,'#72a6ff']]]];
  for(const [id,values] of graphs)plot(id,c.time_s,values);
  $('regen-warnings').replaceChildren(...d.warnings.map(w=>{const p=document.createElement('p');p.textContent='• '+w;return p;}));
  $('regen-csv').disabled=false;$('regen-json').disabled=false;
  status(`${fmt(m.battery_energy_stored_j/1000)} kJ stored · ${d.samples} samples · ${m.stopped?'Stopped':'Incomplete stop'}`);
 }
 async function run(e){e?.preventDefault();const btn=$('regen-run');btn.disabled=true;status('Calculating energy accounting…');
  try{const res=await fetch('/api/regen/simulate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scenario:scenario()})});const data=await res.json();if(!res.ok)throw Error(data.error||`HTTP ${res.status}`);output=data;(window.AutoDynVizResults ||= {})["regen"]=data;window.dispatchEvent(new CustomEvent("autodyn:result",{detail:{model:"regen",data}}));render();}
  catch(err){status('Scenario rejected: '+err.message,true);output=null;$('regen-csv').disabled=true;$('regen-json').disabled=true;}finally{btn.disabled=false;}}
 function download(name,content,type){const blob=new Blob([content],{type}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 function esc(x){const v=String(x??'');return /[,"\n]/.test(v)?'"'+v.replaceAll('"','""')+'"':v;}
 function csv(){if(!output)return;const c=output.channels,keys=Object.keys(c),sc=output.scenario,sk=Object.keys(sc),fields=['model','version',...sk,...keys],lines=[fields.join(',')];for(let i=0;i<output.samples;i++)lines.push([output.model,output.version,...sk.map(k=>sc[k]),...keys.map(k=>c[k][i])].map(esc).join(','));download('autodyn-ev-chat6-regen-v0.6.0.csv',lines.join('\n')+'\n','text/csv;charset=utf-8');}
 form.addEventListener('submit',run);$('regen-reset').addEventListener('click',()=>{for(const e of form.elements){if(e.name)e.value=defaults[e.name];}run();});
 $('regen-csv').addEventListener('click',csv);$('regen-json').addEventListener('click',()=>{if(output)download('autodyn-ev-chat6-regen-v0.6.0.json',JSON.stringify(output,null,2),'application/json');});
 $('model-select').addEventListener('change',()=>{if($('model-select').value==='regen'){if(!output)run();else render();}});
 window.addEventListener('resize',()=>{if(!$('regen-lab').hidden&&output)render();});
 window.regenScenario=scenario;
})();
