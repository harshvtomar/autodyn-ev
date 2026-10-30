"use strict";

const $ = id => document.getElementById(id);
const VEHICLE_FIELDS = ["sprung_mass_kg", "unsprung_mass_kg", "suspension_stiffness_n_m", "damping_n_s_m", "tire_stiffness_n_m"];
const FORM_FIELDS = [...VEHICLE_FIELDS, "height_mm", "bump_length_m", "speed_m_s", "sine_frequency_hz", "bump_spacing_m", "chirp_end_frequency_hz", "chirp_duration_s", "duration_s"];
const PALETTE = {road: "#fac07a", wheel: "#72a6ff", body: "#66e1cf", travel: "#be9cff", grid: "#294157", label: "#9bb2c3"};
let current = null;
let cursorFraction = null;
let playing = true;
let playClock = 0;
let lastFrame = null;
let previousRun = 0;
const plotConfigs = [
  {id: "displacement", series: [{key:"road_m",scale:1000,color:PALETTE.road},{key:"unsprung_m",scale:1000,color:PALETTE.wheel},{key:"sprung_m",scale:1000,color:PALETTE.body}]},
  {id: "acceleration", series: [{key:"sprung_acceleration_m_s2",scale:1,color:PALETTE.body}]},
  {id: "travel", series: [{key:"suspension_travel_m",scale:1000,color:PALETTE.travel}]},
];

function readableValue(id, number) {
  switch (id) {
    case "sprung_mass_kg": case "unsprung_mass_kg": return `${number} kg`;
    case "suspension_stiffness_n_m": case "tire_stiffness_n_m": return `${Number(number).toLocaleString()} N/m`;
    case "damping_n_s_m": return `${Number(number).toLocaleString()} N·s/m`;
    case "height_mm": return `${number} mm`;
    case "bump_length_m": return `${Number(number).toFixed(1)} m`;
    case "speed_m_s": return `${(number * 3.6).toFixed(1).replace(/\.0$/, "")} km/h`;
    case "sine_frequency_hz": return `${Number(number).toFixed(1)} Hz`;
    case "bump_spacing_m": return `${Number(number).toFixed(1)} m`;
    case "chirp_end_frequency_hz": return `${Number(number).toFixed(1)} Hz`;
    case "chirp_duration_s": return `${Number(number).toFixed(1)} s`;
    case "duration_s": return `${Number(number).toFixed(1)} s`;
    default: return String(number);
  }
}
function updateLabels() {
  FORM_FIELDS.forEach(id => { $(id + "_value").textContent = readableValue(id, Number($(id).value)); });
  const kind = $("road_kind").value;
  document.querySelectorAll(".road-bump").forEach(n=>n.hidden=!["bump","pothole","double_bump"].includes(kind));
  document.querySelectorAll(".road-sine").forEach(n=>n.hidden=!["sine","chirp"].includes(kind));
  $("quarter-spacing-field").hidden = kind !== "double_bump";
  $("quarter-chirp-field").hidden = kind !== "chirp";
  $("quarter-chirp-duration-field").hidden = kind !== "chirp";
  $("height_mm").disabled = kind === "flat";
  if (current) {
    // A changed control must never leave a previous RMS value looking current.
    $("metric-rms").closest(".metric-grid").classList.add("stale-results");
    for (const id of ["metric-rms", "metric-accel", "metric-travel", "metric-mode"]) $(id).textContent = "—";
    for (const id of ["csv", "report", "provenance"]) $(id).disabled = true;
    status(`Inputs changed (sprung mass ${Number($("sprung_mass_kg").value)} kg). Results need a new simulation.`);
    $("status-light").style.background = "#ffca7a";
    if ($("modal-output")) $("modal-output").textContent = "Inputs changed — click Run simulation to refresh the pole diagnostics.";
  }
}
function scenario() {
  const vehicle = Object.fromEntries(VEHICLE_FIELDS.map(k => [k, Number($(k).value)]));
  return {vehicle, road: {kind:$("road_kind").value, height_m:Number($("height_mm").value)/1000, start_s:0.5,
    bump_length_m:Number($("bump_length_m").value), speed_m_s:Number($("speed_m_s").value), sine_frequency_hz:Number($("sine_frequency_hz").value),
    bump_spacing_m:Number($("bump_spacing_m").value),chirp_end_frequency_hz:Number($("chirp_end_frequency_hz").value),chirp_duration_s:Number($("chirp_duration_s").value)},
    settings:{duration_s:Number($("duration_s").value), dt_s:Number($("dt_s").value)} };
}
function status(message,error=false) {
  $("status").textContent=message;
  $("status-light").style.background=error?"#ff907c":"#66e1cf";
}
function fmt(x,precision=2){return Number(x).toFixed(precision)}
function showMetrics(data){
  const m=data.metrics;
  $("metric-rms").textContent=fmt(m.body_acceleration_rms_m_s2,3);
  $("metric-accel").textContent=fmt(m.body_acceleration_peak_m_s2,3);
  $("metric-travel").textContent=fmt(m.suspension_travel_peak_mm,2);
  $("metric-mode").textContent=fmt(m.body_mode_undamped_hz,2);
  $("samples").textContent=data.samples.toLocaleString();
}
async function run(e){
  if(e) e.preventDefault();
  const token=++previousRun;
  const requested = scenario();
  $("run").disabled=true;
  status(`Calculating sprung mass ${requested.vehicle.sprung_mass_kg} kg…`);
  try {
    const response = await fetch("/api/simulate", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(requested)});
    const data = await response.json();
    if(!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    if(token!==previousRun) return;
    if (!data.vehicle || VEHICLE_FIELDS.some(k => Number(data.vehicle[k]) !== requested.vehicle[k])) {
      throw new Error("The response used different vehicle parameters. Results were NOT updated.");
    }
    if (JSON.stringify(scenario()) !== JSON.stringify(requested)) {
      throw new Error("Inputs changed while calculating; run the simulation again.");
    }
    current=data; (window.AutoDynVizResults ||= {})["quarter"]=data;window.dispatchEvent(new CustomEvent("autodyn:result",{detail:{model:"quarter",data}})); cursorFraction=null; playClock=0; lastFrame=null; playing=true;
    $("play").textContent="Ⅱ"; $("play").setAttribute("aria-label","Pause animation");
    for(const id of ["csv","report","play"]) $(id).disabled=false;
    $("scrubber").value=0;
    showMetrics(data); $("metric-rms").closest(".metric-grid").classList.remove("stale-results"); updateMechanism(); drawAll();
    status(`Verified run: sprung mass ${fmt(data.vehicle.sprung_mass_kg,0)} kg · RMS ${fmt(data.metrics.body_acceleration_rms_m_s2,3)} m/s² · ${data.samples.toLocaleString()} points`);
    $("provenance").disabled=false;
    updateModal();
  } catch(err){status(`Simulation error: ${err.message}`,true)}
  finally {if(token===previousRun) $("run").disabled=false}
}
function download(filename,mime,contents){
  const blob = new Blob([contents],{type:mime});
  const url=URL.createObjectURL(blob);
  const a=document.createElement("a");a.href=url;a.download=filename;document.body.appendChild(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function exportCSV(){
  if(!current)return;
  const keys=Object.keys(current.channels);const n=current.samples;
  const lines=[keys.join(",")];
  for(let i=0;i<n;i++)lines.push(keys.map(k=>current.channels[k][i].toPrecision(10)).join(","));
  download("autodyn-ev-session1-response.csv","text/csv;charset=utf-8",lines.join("\n")+"\n");
}
function exportSummary(){
  if(!current)return;
  const {channels,...summary}=current;
  download("autodyn-ev-session1-summary.json","application/json",JSON.stringify(summary,null,2));
}
function plot(config){
  const canvas=$(config.id); if(!canvas || !current)return;
  const rect=canvas.getBoundingClientRect();if(rect.width<5||rect.height<5)return;
  const ratio=Math.min(window.devicePixelRatio||1,2);
  canvas.width=Math.round(rect.width*ratio);canvas.height=Math.round(rect.height*ratio);
  const ctx=canvas.getContext("2d");ctx.scale(ratio,ratio);
  const w=rect.width,h=rect.height; const L=46,R=14,T=19,B=31,plotW=w-L-R,plotH=h-T-B;
  const series=config.series.map(s=>({...s,values:current.channels[s.key]}));
  let ymin=0, ymax=0;
  for(const s of series){for(const value of s.values){const scaled=value*s.scale;if(scaled<ymin)ymin=scaled;if(scaled>ymax)ymax=scaled;}}
  // Keep axes meaningful for a perfectly flat response.
  if(ymax-ymin<1e-8){ymin=-1;ymax=1}
  const pad=(ymax-ymin)*.12;ymin-=pad;ymax+=pad;
  const X = idx => L+idx/(current.samples-1)*plotW;
  const Y = value => T+(ymax-value)/(ymax-ymin)*plotH;
  ctx.clearRect(0,0,w,h);ctx.font="10px Inter, system-ui";ctx.textBaseline="middle";
  ctx.lineWidth=1;
  for(let j=0;j<=4;j++){
    const y=T+j*plotH/4;
    ctx.strokeStyle=PALETTE.grid;ctx.beginPath();ctx.moveTo(L,y);ctx.lineTo(w-R,y);ctx.stroke();
    const value=ymax-j*(ymax-ymin)/4;
    ctx.fillStyle=PALETTE.label;ctx.textAlign="right";
    ctx.fillText(Math.abs(value)>=100?value.toFixed(0):Math.abs(value)>=10?value.toFixed(1):value.toFixed(2),L-9,y);
  }
  const total=current.settings.duration_s;
  ctx.textBaseline="top";ctx.textAlign="center";
  for(let j=0;j<=5;j++){
    ctx.fillStyle=PALETTE.label;ctx.fillText((total*j/5).toFixed(1),L+j*plotW/5,h-B+10);
  }
  ctx.textAlign="right";ctx.fillStyle=PALETTE.label;ctx.fillText("time (s)",w-R,h-8);
  ctx.save();ctx.beginPath();ctx.rect(L,T,plotW,plotH);ctx.clip();
  for(const s of series){
    ctx.lineWidth=2;ctx.strokeStyle=s.color;ctx.beginPath();
    const stride=Math.max(1,Math.floor(current.samples/2000));
    for(let i=0;i<current.samples;i+=stride){
      if(i===0)ctx.moveTo(X(i),Y(s.values[i]*s.scale));else ctx.lineTo(X(i),Y(s.values[i]*s.scale));
    }
    ctx.lineTo(X(current.samples-1),Y(s.values[current.samples-1]*s.scale));ctx.stroke();
  }
  if(cursorFraction!==null){
    const index=Math.min(current.samples-1,Math.max(0,Math.round(cursorFraction*(current.samples-1))));
    ctx.strokeStyle="#b9cbdd99";ctx.lineWidth=1;ctx.setLineDash([4,4]);ctx.beginPath();ctx.moveTo(X(index),T);ctx.lineTo(X(index),T+plotH);ctx.stroke();ctx.setLineDash([]);
    let tooltip=`${fmt(current.channels.time_s[index],2)}s`;
    for(const s of series)tooltip+=`  ${fmt(s.values[index]*s.scale,2)}`;
    const width=Math.min(w-L-R,ctx.measureText(tooltip).width+18);
    const xx=Math.min(w-R-width,Math.max(L,X(index)-width/2));
    ctx.fillStyle="#0b1a2ced";ctx.fillRect(xx,T+5,width,24);ctx.fillStyle="#d9f0f4";ctx.font="10px system-ui";ctx.textBaseline="middle";ctx.textAlign="center";ctx.fillText(tooltip,xx+width/2,T+17);
  }
  ctx.restore();
}
function drawAll(){plotConfigs.forEach(plot)}
function updateMechanism(){
  if(!current)return;
  const total=current.settings.duration_s;
  const index=Math.min(current.samples-1,Math.max(0,Math.round(playClock/total*(current.samples-1))));
  const ch=current.channels;const amplify=300; // diagrammatic, not to scale
  $("body-mass").style.transform=`translateY(${-amplify*ch.sprung_m[index]}px)`;
  $("wheel").style.transform=`translateY(${-amplify*ch.unsprung_m[index]}px)`;
  $("ground").style.transform=`translateY(${-amplify*ch.road_m[index]}px)`;
  $("clock").textContent=`${fmt(playClock,2)} / ${fmt(total,2)} s`;
  $("scrubber").value=Math.round(playClock/total*1000);
}
function animate(timestamp){
  if(current && playing){
    if(lastFrame!==null)playClock+=(timestamp-lastFrame)/1000;
    if(playClock>current.settings.duration_s)playClock=0;
    updateMechanism();
  }
  lastFrame=timestamp;requestAnimationFrame(animate);
}
async function init(){
  for(const id of FORM_FIELDS) $(id).addEventListener("input",updateLabels);
  $("road_kind").addEventListener("change",updateLabels);
  // Recalculate when a mass slider is released, even if Run was missed.
  // Explicit Run simulation continues to work for every parameter.
  $("sprung_mass_kg").addEventListener("change",()=>{if(current && $("model-select").value==="quarter") run();});
  $("config").addEventListener("submit",run);
  $("csv").addEventListener("click",exportCSV);
  $("report").addEventListener("click",exportSummary);
  $("play").addEventListener("click",()=>{
    playing=!playing;lastFrame=null;$("play").textContent=playing?"Ⅱ":"▶";
    $("play").setAttribute("aria-label",playing?"Pause animation":"Play animation");
  });
  $("scrubber").addEventListener("input",e=>{if(!current)return;playClock=Number(e.target.value)/1000*current.settings.duration_s;playing=false;lastFrame=null;$("play").textContent="▶";$("play").setAttribute("aria-label","Play animation");updateMechanism()});
  $("reset").addEventListener("click",()=>{ $("config").reset();updateLabels();run() });
  for(const cfg of plotConfigs){
    $(cfg.id).addEventListener("pointermove",e=>{
      const r=e.target.getBoundingClientRect();cursorFraction=Math.min(1,Math.max(0,((e.clientX-r.left)-46)/(r.width-60)));drawAll();
    });
    $(cfg.id).addEventListener("pointerleave",()=>{cursorFraction=null;drawAll()});
  }
  let resizeDebounce;
  new ResizeObserver(()=>{clearTimeout(resizeDebounce);resizeDebounce=setTimeout(drawAll,45)}).observe(document.querySelector(".results"));
  updateLabels();requestAnimationFrame(animate);await run();
}
init();

// Chat 2 additive engineering study tools; Chat 1 charts, equations and exports unchanged.
let savedBaseline = null;
let lastAnalysis = null;
let lastStudyType = null;
const PARAM_BOUNDS = {
  sprung_mass_kg: [100,1200], unsprung_mass_kg: [15,150],
  suspension_stiffness_n_m:[5000,120000], damping_n_s_m:[0,12000], tire_stiffness_n_m:[40000,500000]
};
function defaultBaseline(){
  return {vehicle:{sprung_mass_kg:300,unsprung_mass_kg:40,suspension_stiffness_n_m:18000,damping_n_s_m:1500,tire_stiffness_n_m:190000},
    road:{kind:'bump',height_m:.06,start_s:.5,bump_length_m:1.5,speed_m_s:5,sine_frequency_hz:1.5},
    settings:{duration_s:5,dt_s:.005}};
}
function labMessage(id,html){$(id).textContent=html}
async function study(endpoint,payload){
  const response=await fetch('/api/'+endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  const value=await response.json();
  if(!response.ok)throw new Error(value.error||`HTTP ${response.status}`);
  return value;
}
function seriesChart(id,series){
  const canvas=$(id);const rect=canvas.getBoundingClientRect();
  if(rect.width<15||rect.height<15 || !series.length)return;
  const scale=Math.min(window.devicePixelRatio||1,2);
  canvas.width=Math.round(rect.width*scale);canvas.height=Math.round(rect.height*scale);
  const ctx=canvas.getContext('2d');ctx.scale(scale,scale);
  const w=rect.width,h=rect.height,L=51,R=15,T=16,B=32;
  const points=series.flatMap(x=>x.points);
  if(!points.length)return;
  let xmin=Math.min(...points.map(x=>x[0])),xmax=Math.max(...points.map(x=>x[0]));
  let ymin=Math.min(0,...points.map(x=>x[1])),ymax=Math.max(0,...points.map(x=>x[1]));
  if(xmax===xmin){xmax+=1};if(ymax===ymin){ymin-=1;ymax+=1};
  const margin=(ymax-ymin)*.1;ymin-=margin;ymax+=margin;
  const X=x=>L+(x-xmin)/(xmax-xmin)*(w-L-R);
  const Y=y=>T+(ymax-y)/(ymax-ymin)*(h-T-B);
  ctx.clearRect(0,0,w,h);ctx.font='10px system-ui';ctx.lineWidth=1;
  for(let i=0;i<=4;i++){
    const y=T+i*(h-T-B)/4;
    ctx.strokeStyle='#294157';ctx.beginPath();ctx.moveTo(L,y);ctx.lineTo(w-R,y);ctx.stroke();
    ctx.fillStyle='#9bb2c3';ctx.textAlign='right';ctx.fillText((ymax-i*(ymax-ymin)/4).toPrecision(3),L-7,y+3);
  }
  for(let i=0;i<=4;i++){
    const x=L+i*(w-L-R)/4;ctx.fillStyle='#9bb2c3';ctx.textAlign='center';
    ctx.fillText((xmin+(xmax-xmin)*i/4).toPrecision(3),x,h-8);
  }
  ctx.save();ctx.beginPath();ctx.rect(L,T,w-L-R,h-T-B);ctx.clip();
  for(const s of series){
    ctx.strokeStyle=s.color;ctx.lineWidth=2;ctx.beginPath();
    const jump=Math.max(1,Math.floor(s.points.length/1200));
    for(let i=0;i<s.points.length;i+=jump){const [x,y]=s.points[i];if(i===0)ctx.moveTo(X(x),Y(y));else ctx.lineTo(X(x),Y(y))}
    const last=s.points[s.points.length-1];ctx.lineTo(X(last[0]),Y(last[1]));ctx.stroke();
  }
  ctx.restore();
}
function xy(a,b){return a.map((x,i)=>[x,b[i]])}
function setLastAnalysis(type,result){
  lastStudyType=type;lastAnalysis=result;
  $('analysis-csv').disabled=false;$('analysis-json').disabled=false;
  $('analysis-status').textContent=`${type} completed · reproducible simulation results`;
}
function numberOrNull(x,n=3){return x==null?'not defined':Number(x).toFixed(n)}
async function updateModal(){
  try{
    const modal=await study('modal',{vehicle:scenario().vehicle});
    let parts=modal.oscillatory_modes.map((p,i)=>`Mode ${i+1}: ${numberOrNull(p.damped_frequency_hz)} Hz · ζ=${numberOrNull(p.damping_ratio)}`);
    if(modal.real_nonoscillatory_poles.length)parts.push(`${modal.real_nonoscillatory_poles.length} real decay poles (no oscillatory frequency)`);
    labMessage('modal-output',parts.join('  |  ') || 'No oscillatory poles.');
  }catch(e){labMessage('modal-output','Modal calculation: '+e.message)}
}
async function runComparison(){
  const button=$('compare-run');button.disabled=true;labMessage('compare-output','Computing both scenarios…');
  try{
    const result=await study('compare',{baseline:savedBaseline,variant:scenario()});
    const a=result.baseline.metrics,b=result.variant.metrics;
    const pct=result.metric_deltas.body_acceleration_rms_m_s2.percent;
    labMessage('compare-output',`Body acceleration RMS: ${numberOrNull(a.body_acceleration_rms_m_s2)} → ${numberOrNull(b.body_acceleration_rms_m_s2)} m/s² (${pct===null?'percentage undefined for zero reference':numberOrNull(pct,1)+'% change'}). ${result.caution}`);
    const channels=['baseline','variant'].map((name,i)=>{
      const ch=result[name].channels;
      return {color:i?'#66e1cf':'#72a6ff',points:xy(ch.time_s,ch.sprung_acceleration_m_s2)};
    });
    seriesChart('compare-plot',channels);setLastAnalysis('comparison',result);
  }catch(e){labMessage('compare-output','Error: '+e.message)}finally{button.disabled=false}
}
async function runSweep(){
  const button=$('sweep-run');button.disabled=true;labMessage('sweep-output','Running seven simulation points…');
  try{
    const base=scenario();const field=$('sweep-parameter').value;const value=base.vehicle[field];
    const [minimum,maximum]=PARAM_BOUNDS[field];
    const start=Math.max(minimum,value===0?0:value*.8);
    const stop=Math.min(maximum,value===0?maximum*.15:value*1.2);
    if(!(start<stop))throw new Error('Cannot construct a bounded sweep. Change parameter first.');
    const result=await study('sweep',{scenario:base,parameter:field,start,stop,count:7});
    const ys=result.points.map(p=>p.metrics.body_acceleration_rms_m_s2);
    const minIndex=ys.indexOf(Math.min(...ys));
    labMessage('sweep-output',`7 controlled runs · lowest sampled RMS ${numberOrNull(ys[minIndex])} m/s² at ${numberOrNull(result.points[minIndex].parameter_value,1)} ${result.units}. This does not establish an overall optimum.`);
    seriesChart('sweep-plot',[{color:'#66e1cf',points:result.points.map(p=>[p.parameter_value,p.metrics.body_acceleration_rms_m_s2])}]);
    setLastAnalysis('parameter-sweep',result);
  }catch(e){labMessage('sweep-output','Error: '+e.message)}finally{button.disabled=false}
}
async function runConvergence(){
  const button=$('convergence-run');button.disabled=true;labMessage('convergence-output','Computing three numerical resolutions…');
  try{
    const result=await study('convergence',{scenario:scenario(),steps_s:[.01,.005,.0025]});
    const line=result.results.map(x=>`${x.requested_dt_s}s: ${(1000*x.max_abs_state_error_vs_finest.sprung_m).toExponential(2)} mm`).join(' · ');
    labMessage('convergence-output',`Maximum body displacement difference vs finest: ${line}. ${result.interpretation}`);
    seriesChart('convergence-plot',[{color:'#be9cff',points:result.results.map(p=>[p.actual_dt_s,1000*p.max_abs_state_error_vs_finest.sprung_m])}]);
    setLastAnalysis('time-step',result);
  }catch(e){labMessage('convergence-output','Error: '+e.message)}finally{button.disabled=false}
}
function csvCell(v){const str=v==null?'':typeof v==='object'?JSON.stringify(v):String(v);return /[",\n\r]/.test(str)?'"'+str.replaceAll('"','""')+'"':str}
function csvRows(rows){return rows.map(row=>row.map(csvCell).join(',')).join('\n')+'\n'}
function analysisCSV(){
  if(!lastAnalysis)return;
  const v=lastAnalysis;let table=[];
  if(lastStudyType==='comparison'){
    table=[['scenario','time_s','road_m','body_acceleration_m_s2','suspension_travel_m','model_revision','solver']];
    for(const key of ['baseline','variant']){
      const ch=v[key].channels,p=v[key].provenance;
      for(let i=0;i<v[key].samples;i++)table.push([key,ch.time_s[i],ch.road_m[i],ch.sprung_acceleration_m_s2[i],ch.suspension_travel_m[i],p.model_revision,p.solver]);
    }
  }else if(lastStudyType==='parameter-sweep'){
    table=[['parameter','value','units','body_accel_rms_m_s2','peak_body_accel_m_s2','peak_travel_mm','rms_delta_percent_vs_reference','model_revision','solver']];
    for(const p of v.points)table.push([v.parameter,p.parameter_value,v.units,p.metrics.body_acceleration_rms_m_s2,p.metrics.body_acceleration_peak_m_s2,p.metrics.suspension_travel_peak_mm,p.rms_delta_percent,v.provenance.model_revision,v.provenance.solver]);
  }else{
    table=[['requested_dt_s','actual_dt_s','samples','max_abs_error_sprung_m','max_abs_error_unsprung_m','max_abs_error_sprung_velocity_m_s','max_abs_error_unsprung_velocity_m_s','model_revision','solver']];
    for(const p of v.results)table.push([p.requested_dt_s,p.actual_dt_s,p.samples,p.max_abs_state_error_vs_finest.sprung_m,p.max_abs_state_error_vs_finest.unsprung_m,p.max_abs_state_error_vs_finest.sprung_velocity_m_s,p.max_abs_state_error_vs_finest.unsprung_velocity_m_s,v.provenance.model_revision,v.provenance.solver]);
  }
  download('autodyn-ev-chat2-'+lastStudyType+'.csv','text/csv;charset=utf-8',csvRows(table));
}
function initLab(){
  savedBaseline=defaultBaseline();
  $('save-baseline').addEventListener('click',()=>{savedBaseline=scenario();labMessage('baseline-label','Baseline saved from current controls. Change inputs then compare.');});
  $('compare-run').addEventListener('click',runComparison);
  $('sweep-run').addEventListener('click',runSweep);
  $('convergence-run').addEventListener('click',runConvergence);
  $('analysis-csv').addEventListener('click',analysisCSV);
  $('analysis-json').addEventListener('click',()=>{if(lastAnalysis)download('autodyn-ev-chat2-'+lastStudyType+'.json','application/json',JSON.stringify(lastAnalysis,null,2))});
  $('provenance').addEventListener('click',()=>{if(current)download('autodyn-ev-response-provenance.json','application/json',JSON.stringify({...current.provenance,legacy_csv_columns:Object.keys(current.channels),legacy_csv_filename:'autodyn-ev-session1-response.csv',csv_note:'Use together with the unchanged 12-column legacy CSV. Model/units and scenario parameters live in this sidecar.'},null,2))});
}
initLab();
