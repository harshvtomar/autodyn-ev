"use strict";
/* Chat 4: additive interface; baseline comparison is strictly within one model. */
(() => {
  const $ = id => document.getElementById(id);
  const store = {quarter:{baseline:null,result:null},half:{baseline:null,result:null}};
  const clone = v => JSON.parse(JSON.stringify(v));
  const getScenario = model => clone(model === 'half' ? window.halfCarScenario() : scenario());
  function notice(model, msg, error=false) {const node=$(model+'-ride-status');node.textContent=msg;node.style.color=error?'#ff9c90':'#a5d7d1';}
  function f(n,d=3){return Number(n).toFixed(d)}
  function xy(ch, key, scale=1) {return ch.time_s.map((t,i)=>[t,ch[key][i]*scale]);}
  function graph(id, list){seriesChart(id,list)}
  function present(model, result){
    const d=result.current,metrics=d.metrics, ch=d.waveforms;
    const base=result.baseline?.waveforms;
    const accel=model==='half'?'body_heave_acceleration_m_s2':'sprung_acceleration_m_s2';
    const tColor='#67e2d0',bColor='#a389f5';
    graph(model+'-ride-accel',[
      {color:tColor,points:xy(ch,accel)},
      ...(base?[{color:bColor,points:xy(base,accel)}]:[])]);
    if(model==='half'){
      graph(model+'-ride-road',[
        {color:'#fabc77',points:xy(ch,'front_road_m',1000)},
        {color:'#72a6ff',points:xy(ch,'rear_road_m',1000)}]);
      graph(model+'-ride-travel',[
        {color:'#a389f5',points:xy(ch,'front_suspension_travel_m',1000)},
        {color:tColor,points:xy(ch,'rear_suspension_travel_m',1000)}]);
    }else{
      graph(model+'-ride-road',[{color:'#fabc77',points:xy(ch,'road_m',1000)}]);
      graph(model+'-ride-travel',[
        {color:tColor,points:xy(ch,'suspension_travel_m',1000)},
        ...(base?[{color:bColor,points:xy(base,'suspension_travel_m',1000)}]:[])]);
    }
    const vals=[
      ['Body acceleration · time-weighted RMS',`${f(metrics.body_acceleration_rms_si)} m/s²`],
      ['Body acceleration · peak abs',`${f(metrics.body_acceleration_peak_abs_si)} m/s²`],
      ...(model==='half'?[['Front travel · peak-to-peak',`${f(metrics.front_suspension_travel_peak_to_peak_si*1000,2)} mm`],
       ['Rear travel · peak-to-peak',`${f(metrics.rear_suspension_travel_peak_to_peak_si*1000,2)} mm`]]:
       [['Suspension travel · peak-to-peak',`${f(metrics.suspension_travel_peak_to_peak_si*1000,2)} mm`]]),
      ...(model==='half'?[['Front tire deflection proxy · peak',`${f(metrics.front_tire_deflection_peak_abs_si*1000,2)} mm`],
       ['Rear tire deflection proxy · peak',`${f(metrics.rear_tire_deflection_peak_abs_si*1000,2)} mm`]]:
       [['Tire deflection proxy · peak',`${f(metrics.tire_deflection_peak_abs_si*1000,2)} mm`]]),
      ['Settling after last excitation',metrics.settling_after_last_excitation_s===null?'Not defined / not reached':`${f(metrics.settling_after_last_excitation_s)} s`],
      ['Post-event analysis window',d.windows.post_event?`${f(d.windows.post_event.start_s)}–${f(d.windows.post_event.end_s)} s`:'Not applicable'],
      ...(d.windows.post_event?[['Post-event body accel. RMS',`${f(d.windows.post_event.channels.body_acceleration.rms)} m/s²`]]:[])
    ];
    const summary=$(model+'-ride-summary');summary.replaceChildren();
    for(const [label,value] of vals){let card=document.createElement('div');
      let title=document.createElement('span');title.textContent=label;let line=document.createElement('b');line.textContent=' '+value;
      card.append(title,document.createElement('div'),line);summary.append(card);}
    const warning = d.warnings.join(' ');
    notice(model,`Study complete · ${d.samples} samples · ${d.scenario.road.kind} road · ${result.baseline?'baseline overlaid in purple · ':''}${warning}`);
  }
  async function execute(model,comparison=false){
    const button=$(model+'-ride-'+(comparison?'compare':'run'));
    const saved=store[model].baseline;
    if(comparison&&!saved){notice(model,'Save a baseline first.',true);return;}
    button.disabled=true;notice(model,'Calculating engineering response and time-weighted metrics…');
    try{
      const body={model,scenario:getScenario(model)};
      if(comparison)body.baseline=clone(saved);
      const r=await fetch('/api/ride/study',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
      const data=await r.json();if(!r.ok)throw Error(data.error||`HTTP ${r.status}`);
      store[model].result=data;
      $(model+'-ride-csv').disabled=false;$(model+'-ride-json').disabled=false;present(model,data);
    }catch(e){notice(model,'Study error: '+e.message,true)}finally{button.disabled=false;}
  }
  function downloadCSV(model){
    const d=store[model].result;if(!d)return;
    const vehicleKeys=Object.keys(d.current.scenario.vehicle);
    const columns=['model','case','release','road_kind','road_height_m','road_start_s',
      'road_bump_length_m','road_speed_m_s','road_sine_frequency_hz',
      'road_bump_spacing_m','road_chirp_end_frequency_hz','road_chirp_duration_s',
      'integration_dt_s',...vehicleKeys.map(k=>'vehicle_'+k),
      'time_s','body_acceleration_m_s2','road_front_or_single_m','road_rear_m',
      'travel_front_or_single_m','travel_rear_m','body_pitch_rad'];
    const lines=[columns.join(',')];
    for(const item of [['current',d.current],['baseline',d.baseline]]){
      const [caseName,result]=item;if(!result)continue;
      const c=result.waveforms,half=model==='half',time=c.time_s,r=result.scenario.road;
      const metadata=[model,caseName,d.release,r.kind,r.height_m,r.start_s,r.bump_length_m,
        r.speed_m_s,r.sine_frequency_hz,r.bump_spacing_m,r.chirp_end_frequency_hz,
        r.chirp_duration_s,result.scenario.settings.dt_s,
        ...vehicleKeys.map(k=>result.scenario.vehicle[k])];
      for(let i=0;i<time.length;i++)lines.push([...metadata,
        time[i],c[half?'body_heave_acceleration_m_s2':'sprung_acceleration_m_s2'][i],
        c[half?'front_road_m':'road_m'][i],half?c.rear_road_m[i]:'',
        c[half?'front_suspension_travel_m':'suspension_travel_m'][i],
        half?c.rear_suspension_travel_m[i]:'',half?c.body_pitch_rad[i]:''].join(','));
    }
    download('autodyn-ev-chat4-'+model+'-ride.csv','text/csv;charset=utf-8',lines.join('\n')+'\n');
  }
  for(const model of ['quarter','half']){
    $(model+'-ride-run').addEventListener('click',()=>execute(model));
    $(model+'-ride-save').addEventListener('click',()=>{store[model].baseline=getScenario(model);notice(model,'Baseline saved. Change vehicle parameters only; keep road and time settings identical for comparison.');});
    $(model+'-ride-compare').addEventListener('click',()=>execute(model,true));
    $(model+'-ride-json').addEventListener('click',()=>{
      if(store[model].result)download('autodyn-ev-chat4-'+model+'-ride.json','application/json',JSON.stringify(store[model].result,null,2));
    });
    $(model+'-ride-csv').addEventListener('click',()=>downloadCSV(model));
  }
})();
