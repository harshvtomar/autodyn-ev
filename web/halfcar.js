"use strict";
/* Chat 3 additive 4-DOF UI. Existing quarter-car logic remains unmodified. */
(() => {
  const el = id => document.getElementById(id);
  const form = el('half-config');
  const defaults = Object.fromEntries(Array.from(form.querySelectorAll('[name]')).map(n=>[n.name,n.value]));
  const defaultOptions={kind:'bump',height:'60',bump:'1.5',speed:'5',sine:'1.5',duration:'5',dt:'0.005',spacing:'1.5',chirpEnd:'4',chirpDuration:'3'};
  let output=null,position=0,playing=true,lastTick=null;
  const value=id=>Number(el(id).value);
  function data(){
    const vehicle=Object.fromEntries(Array.from(form.querySelectorAll('[name]')).map(n=>[n.name,Number(n.value)]));
    return {vehicle,road:{kind:el('half-road-kind').value,height_m:value('half-height')/1000,start_s:.5,
        bump_length_m:value('half-bump-length'),speed_m_s:value('half-speed'),sine_frequency_hz:value('half-sine'),
        bump_spacing_m:value('half-bump-spacing'),chirp_end_frequency_hz:value('half-chirp-end'),chirp_duration_s:value('half-chirp-duration')},
      settings:{duration_s:value('half-duration'),dt_s:value('half-dt')}};
  }
  function setMessage(message,error=false){el('half-status').textContent=message;el('half-status').style.color=error?'#ff9d91':'#91c8bf';}
  function plottable(x,y,mult=1){return x.map((t,i)=>[t,y[i]*mult]);}
  function redraw(){
    if(!output||el('halfcar-lab').hidden)return;
    const ch=output.channels,t=ch.time_s,pi=180/Math.PI;
    seriesChart('half-body-chart',[
      {color:'#66e1cf',points:plottable(t,ch.body_heave_m,1000)},
      {color:'#be9cff',points:plottable(t,ch.body_pitch_rad,pi)}]);
    seriesChart('half-axle-chart',[
      {color:'#fac07a',points:plottable(t,ch.front_road_m,1000)},
      {color:'#f7da9b',points:plottable(t,ch.rear_road_m,1000)},
      {color:'#72a6ff',points:plottable(t,ch.front_wheel_m,1000)},
      {color:'#66e1cf',points:plottable(t,ch.rear_wheel_m,1000)}]);
    seriesChart('half-travel-chart',[
      {color:'#be9cff',points:plottable(t,ch.front_suspension_travel_m,1000)},
      {color:'#66e1cf',points:plottable(t,ch.rear_suspension_travel_m,1000)}]);
    seriesChart('half-accel-chart',[
      {color:'#66e1cf',points:plottable(t,ch.body_heave_acceleration_m_s2)},
      {color:'#be9cff',points:plottable(t,ch.body_pitch_acceleration_rad_s2)}]);
    drawSketch();
  }
  async function simulate(e){
    if(e)e.preventDefault();
    const button=el('half-run');button.disabled=true;setMessage('Integrating the eight-state system…');
    try{
      const r=await fetch('/api/halfcar/simulate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data())});
      const res=await r.json();
      if(!r.ok)throw Error(res.error||`HTTP ${r.status}`);
      output=res;(window.AutoDynVizResults ||= {})["half"]=res;window.dispatchEvent(new CustomEvent("autodyn:result",{detail:{model:"half",data:res}}));position=0;playing=true;lastTick=null;
      const m=res.metrics;
      el('half-rms').textContent=m.body_heave_acceleration_rms_m_s2.toFixed(3);
      el('half-pitch').textContent=m.body_pitch_peak_deg.toFixed(3);
      el('half-travel').textContent=`${m.front_suspension_travel_peak_mm.toFixed(1)} / ${m.rear_suspension_travel_peak_mm.toFixed(1)}`;
      el('half-delay').textContent=res.rear_road_delay_s.toFixed(3);
      el('half-scrub').disabled=false;el('half-play').disabled=false;
      el('half-export-csv').disabled=false;el('half-export-json').disabled=false;
      el('half-play').textContent='Ⅱ';el('half-play').setAttribute('aria-label','Pause half-car animation');
      el('half-scrub').value=0;
      setMessage(`${res.samples.toLocaleString()} samples · ${res.settings.dt_s}s RK4 step · wheelbase ${res.wheelbase_m} m`);
      redraw();
    }catch(err){setMessage('Half-car simulation error: '+err.message,true)}
    finally{button.disabled=false;}
  }
  function drawSketch(){
    if(!output)return;
    const canvas=el('half-sketch'),rect=canvas.getBoundingClientRect();
    if(rect.width<50||rect.height<50)return;
    const dpr=Math.min(window.devicePixelRatio||1,2);
    canvas.width=Math.round(rect.width*dpr);canvas.height=Math.round(rect.height*dpr);
    const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);
    const w=rect.width,h=rect.height,s=Math.min(w/570,h/250);
    const left=w*.23,right=w*.77,middle=(left+right)/2;
    const i=Math.max(0,Math.min(output.samples-1,Math.round(position*(output.samples-1))));
    const c=output.channels;
    const at=key=>c[key][i];
    const bodyY=h*.29-at('body_heave_m')*500*s;
    const exaggeratedPitch=at('body_pitch_rad')*4;
    const a=output.vehicle.cg_to_front_m,b=output.vehicle.cg_to_rear_m;
    const span=a+b;
    const attachmentFront=bodyY-exaggeratedPitch*(right-left)*b/span;
    const attachmentRear=bodyY+exaggeratedPitch*(right-left)*a/span;
    const frontWheelY=h*.65-at('front_wheel_m')*500*s;
    const rearWheelY=h*.65-at('rear_wheel_m')*500*s;
    const frontRoadY=h*.84-at('front_road_m')*500*s;
    const rearRoadY=h*.84-at('rear_road_m')*500*s;
    ctx.clearRect(0,0,w,h);
    ctx.strokeStyle='#254258';ctx.lineWidth=1;
    for(let y=20;y<h;y+=25){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke()}
    for(let x=25;x<w;x+=25){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,h);ctx.stroke()}
    function line(x1,y1,x2,y2,color,width=3){ctx.beginPath();ctx.strokeStyle=color;ctx.lineWidth=width;ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke()}
    // Chassis attachment locations are driven by actual heave/pitch response, with scale magnification.
    line(left-24*s,attachmentRear,right+24*s,attachmentFront,'#66e1cf',10*s);
    line(left,attachmentRear+4*s,left,rearWheelY-20*s,'#a2bacb',2*s);
    line(right,attachmentFront+4*s,right,frontWheelY-20*s,'#a2bacb',2*s);
    // Left is REAR and right is FRONT, matching the nose-up pitch convention.
    const wheel=(x,y,color)=>{ctx.beginPath();ctx.fillStyle='#102435';ctx.strokeStyle=color;ctx.lineWidth=7*s;ctx.arc(x,y,19*s,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.beginPath();ctx.fillStyle='#66e1cf';ctx.arc(x,y,5*s,0,Math.PI*2);ctx.fill()};
    wheel(left,rearWheelY,'#84acc6');wheel(right,frontWheelY,'#84acc6');
    line(left-55*s,rearRoadY,left+55*s,rearRoadY,'#fac07a',5*s);
    line(right-55*s,frontRoadY,right+55*s,frontRoadY,'#fac07a',5*s);
    ctx.font=`${Math.max(10,11*s)}px system-ui`;ctx.fillStyle='#d5e8ef';ctx.textAlign='center';
    ctx.fillText('REAR',left,Math.min(h-9,rearRoadY+22*s));ctx.fillText('FRONT',right,Math.min(h-9,frontRoadY+22*s));
    ctx.fillText('HEAVE / PITCH',middle,Math.max(13,bodyY-22*s));
    el('half-time').textContent=`${at('time_s').toFixed(2)} / ${output.settings.duration_s.toFixed(2)} s`;
  }
  function animate(t){
    if(lastTick===null)lastTick=t;
    const elapsed=Math.min(.1,(t-lastTick)/1000);lastTick=t;
    if(playing&&output&&!el('halfcar-lab').hidden){
      position+=elapsed/output.settings.duration_s;
      if(position>=1){position=1;playing=false;el('half-play').textContent='▶';}
      el('half-scrub').value=Math.round(position*1000);
      drawSketch();
    }
    requestAnimationFrame(animate);
  }
  function toCsv(){
    if(!output)return;
    const fields=Object.keys(output.channels);
    const rows=[fields.join(',')];
    for(let i=0;i<output.samples;i++)rows.push(fields.map(key=>output.channels[key][i].toPrecision(11)).join(','));
    download('autodyn-ev-chat3-halfcar-response.csv','text/csv;charset=utf-8',rows.join('\n')+'\n');
  }
  function summary(){if(!output)return;download('autodyn-ev-chat3-halfcar-engineering-report.json','application/json',JSON.stringify(output,null,2));}
  el('model-select').addEventListener('change',()=>{
    const selection=el('model-select').value;
    const half=selection==='half', braking=selection==='braking', regen=selection==='regen';
    document.querySelector('.app-grid').hidden=half||braking||regen;el('halfcar-lab').hidden=!half;
    el('braking-lab').hidden=!braking;el('regen-lab').hidden=!regen;
    el('model-badge').textContent=half?'4 DOF':braking?'1-D':regen?'EV':'2 DOF';
    el('model-subtitle').textContent=half?'Heave + pitch + two unsprung masses':braking?'Separate longitudinal model':regen?'Energy recovery · separate longitudinal model':'Vertical suspension system';
    if(half){if(!output)simulate();else redraw();}
    else if(!braking&&!regen){drawAll();}
  });
  el('half-config').addEventListener('submit',simulate);
  el('half-reset').addEventListener('click',()=>{
    for(const field of form.querySelectorAll('[name]'))field.value=defaults[field.name];
    const map={'half-road-kind':defaultOptions.kind,'half-height':defaultOptions.height,'half-bump-length':defaultOptions.bump,
      'half-speed':defaultOptions.speed,'half-sine':defaultOptions.sine,'half-duration':defaultOptions.duration,'half-dt':defaultOptions.dt,
      'half-bump-spacing':defaultOptions.spacing,'half-chirp-end':defaultOptions.chirpEnd,'half-chirp-duration':defaultOptions.chirpDuration};
    for(const [id,value] of Object.entries(map))el(id).value=value;
    simulate();
  });
  el('half-play').addEventListener('click',()=>{playing=!playing;if(playing&&position>=1)position=0;el('half-play').textContent=playing?'Ⅱ':'▶';el('half-play').setAttribute('aria-label',playing?'Pause half-car animation':'Play half-car animation');});
  el('half-scrub').addEventListener('input',()=>{position=Number(el('half-scrub').value)/1000;playing=false;el('half-play').textContent='▶';drawSketch();});
  el('half-export-csv').addEventListener('click',toCsv);el('half-export-json').addEventListener('click',summary);
  window.addEventListener('resize',()=>{if(!el('halfcar-lab').hidden)redraw()});
  window.halfCarScenario=data;
  requestAnimationFrame(animate);
})();
