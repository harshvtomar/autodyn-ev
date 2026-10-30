"use strict";
/* A separate independent Chat 5 screen. No dependencies and no suspension coupling. */
(() => {
 const $=id=>document.getElementById(id),form=$('braking-form');
 const defaultValues=Object.fromEntries([...form.elements].filter(n=>n.name).map(n=>[n.name,n.value]));
 let result=null;
 function scenario(){
   const obj={};for(const element of form.elements){if(element.name)obj[element.name]=element.name==='profile'?element.value:Number(element.value);}
   return obj;
 }
 function message(text,error=false){$('braking-status').textContent=text;$('braking-status').style.color=error?'#ffb0a0':'#91c8bf';}
 function box(title,value){return `<div class="card"><span>${title}</span><strong>${value}</strong></div>`}
 function showResults(data){
   const m=data.metrics;
   const fmt=(n,d=2)=>Number(n).toLocaleString('en-US',{maximumFractionDigits:d,minimumFractionDigits:d});
   $('braking-metrics').innerHTML=box('Stopped',m.stopped?'Yes':'No — window ended')+
      box('Stopping time',m.stopped?`${fmt(m.stopping_time_s)} s`:'Not reached')+
      box('Stopping distance',m.stopped?`${fmt(m.stopping_distance_m)} m`:'Not reached')+
      box('Peak deceleration',`${fmt(m.peak_deceleration_m_s2)} m/s²`)+
      box('Average deceleration',`${fmt(m.average_deceleration_m_s2)} m/s²`)+
      box('Final speed',`${fmt(m.final_speed_m_s)} m/s`)+
      box('Peak front axle load',`${fmt(m.peak_front_normal_n,0)} N`)+
      box('Minimum rear axle load',`${fmt(m.min_rear_normal_n,0)} N`);
   $('braking-warnings').replaceChildren(...data.warnings.map(w=>{const p=document.createElement('p');p.textContent='• '+w;return p}));
   const ch=data.channels;
   const graphs=[['braking-speed',[['Speed',ch.speed_m_s,'#66e1cf']]],
      ['braking-distance',[['Distance',ch.distance_m,'#72a6ff']]],
      ['braking-decel',[['Demanded',ch.demanded_decel_m_s2,'#fac07a'],['Actual',ch.actual_decel_m_s2,'#66e1cf']]],
      ['braking-load',[['Front',ch.front_normal_n,'#be9cff'],['Rear',ch.rear_normal_n,'#72a6ff']]],
      ['braking-force',[['Requested',ch.requested_force_n,'#fac07a'],['Capacity',ch.traction_limit_n,'#be9cff'],['Actual',ch.actual_brake_force_n,'#66e1cf']]]];
   for(const [id,values] of graphs)draw(id,ch.time_s,values);
   $('braking-export-csv').disabled=false;$('braking-export-json').disabled=false;
   message(`${data.samples.toLocaleString()} output points · ${m.traction_limited?'Demand capped by aggregate friction':'Demand within assumed traction cap'} · ${m.stopped?'Stopped':'Not stopped'}`);
 }
 function draw(id,t,series){
   const canvas=$(id),wrap=canvas.parentElement,rect=wrap.getBoundingClientRect();if(rect.width<30)return;
   const w=rect.width,h=rect.height,dpr=Math.min(window.devicePixelRatio||1,2);
   canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);
   ctx.clearRect(0,0,w,h);const l=48,r=12,top=12,b=28,ww=w-l-r,hh=h-top-b;
   const all=series.flatMap(s=>s[1]),min0=Math.min(...all),max0=Math.max(...all),pad=(max0-min0||1)*.1;
   const min=Math.min(0,min0-pad),max=max0+pad;const xmax=t[t.length-1]||1;
   const x=v=>l+v/xmax*ww,y=v=>top+(max-v)/(max-min)*hh;
   ctx.font='10px system-ui';ctx.textAlign='right';
   for(let k=0;k<=4;k++){const value=min+(max-min)*k/4,py=y(value);ctx.strokeStyle='#294458';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(l,py);ctx.lineTo(w-r,py);ctx.stroke();ctx.fillStyle='#a2b9c9';ctx.fillText(value.toFixed(Math.abs(value)<10?2:0),l-7,py+3);}
   ctx.textAlign='center';for(let k=0;k<=4;k++)ctx.fillText((xmax*k/4).toFixed(1),x(xmax*k/4),h-8);
   for(const [label,arr,color] of series){ctx.strokeStyle=color;ctx.lineWidth=1.9;ctx.beginPath();for(let i=0;i<t.length;i++){if(i===0)ctx.moveTo(x(t[i]),y(arr[i]));else ctx.lineTo(x(t[i]),y(arr[i]));}ctx.stroke();}
   let legend=canvas.parentElement.nextElementSibling;
   if(!legend||!legend.classList.contains('plot-legend')){legend=document.createElement('div');legend.className='plot-legend';canvas.parentElement.after(legend)}
   legend.replaceChildren(...series.map(s=>{const span=document.createElement('span'),i=document.createElement('i');i.style.background=s[2];span.append(i,document.createTextNode(s[0]));return span}));
 }
 function download(name,type,body){const blob=new Blob([body],{type}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)}
 function escapeCSV(v){const str=String(v??'');return /[\n",]/.test(str)?'"'+str.replaceAll('"','""')+'"':str;}
 function csv(){if(!result)return;const c=result.channels,sc=result.scenario;const cols=Object.keys(c),keys=Object.keys(sc);
   const header=['model','version',...keys,...cols];const rows=[header.join(',')];
   for(let i=0;i<c.time_s.length;i++)rows.push(['independent-longitudinal-braking',result.version,...keys.map(k=>sc[k]),...cols.map(k=>c[k][i])].map(escapeCSV).join(','));
   download('autodyn-ev-chat5-braking-v0.5.0.csv','text/csv;charset=utf-8',rows.join('\n')+'\n');}
 async function run(e){if(e)e.preventDefault();const btn=$('braking-run');btn.disabled=true;message('Calculating braking event…');
   try{const response=await fetch('/api/braking/simulate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scenario:scenario()})});const data=await response.json();if(!response.ok)throw Error(data.error||`HTTP ${response.status}`);result=data;(window.AutoDynVizResults ||= {})["braking"]=data;window.dispatchEvent(new CustomEvent("autodyn:result",{detail:{model:"braking",data}}));showResults(result)}
   catch(err){message('Braking scenario rejected: '+err.message,true)}finally{btn.disabled=false;}}
 form.addEventListener('submit',run);
 $('braking-reset').addEventListener('click',()=>{for(const e of form.elements){if(e.name)e.value=defaultValues[e.name]}run()});
 $('braking-export-csv').addEventListener('click',csv);
 $('braking-export-json').addEventListener('click',()=>result&&download('autodyn-ev-chat5-braking-v0.5.0.json','application/json',JSON.stringify(result,null,2)));
 $('model-select').addEventListener('change',()=>{if($('model-select').value==='braking'){if(!result)run();else showResults(result);}});
 window.addEventListener('resize',()=>{if(!$('braking-lab').hidden&&result)showResults(result)});
 window.brakingScenario=scenario;
})();
