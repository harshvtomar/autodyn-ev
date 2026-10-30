"use strict";
/* Optional software-projected 3D renderer. It reads authoritative response arrays;
   no integration, solver, API or export modifications occur here. */
(()=>{
 const $=id=>document.getElementById(id), M=window.AutoDynVizMath;
 const canvas=$('viz-canvas'),fallback=$('viz-fallback'),control=$('viz-mode'),timeline=$('viz-timeline');
 const dataByModel={quarter:null,half:null,braking:null,regen:null};
 let active=$('model-select').value,clock=0,playing=false,lastTick=null,threeD=true,ctx=null;
 let camera={yaw:0.68,elevation:0.34,zoom:100},dragging=null;
 const reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)');
 const s=(v,d=2)=>Number(v).toFixed(d);
 const hasResult=()=>!!dataByModel[active];
 const announce=msg=>{$('viz-status').textContent=msg};
 try{ctx=canvas.getContext('2d',{alpha:false});}catch(_){ctx=null}
 const duration=()=>hasResult()?dataByModel[active].channels.time_s.at(-1):0;
 function switchMode(force2d=false){
   threeD=!force2d&&control.value==='3d'&&!!ctx;
   canvas.hidden=!threeD;fallback.hidden=threeD;
   if(!threeD){announce(ctx?'2D fallback selected. Existing 2D engineering charts remain available.':'Canvas unavailable: 2D SVG fallback active. All physics and exports remain available.');}
   else announce('Projected 3D active: drag or use arrow keys to orbit. All geometry is schematic.');
   draw();
 }
 function setPlay(on){playing=!!on&&hasResult();lastTick=null;$('viz-play').textContent=playing?'Ⅱ Pause':'▶ Play';$('viz-play').setAttribute('aria-label',playing?'Pause 3D animation':'Play 3D animation');}
 function setTime(sec){const d=duration();clock=M.clamp(Number(sec)||0,0,d);timeline.value=d?String(Math.round(clock/d*1000)):'0';draw();}
 function updateModel(){active=$('model-select').value;setPlay(false);clock=0;const ok=hasResult();timeline.disabled=!ok;$('viz-play').disabled=!ok;$('viz-restart').disabled=!ok;timeline.value='0';
   announce(ok?'Viewing '+active+' response from previously computed, read-only samples.':'Waiting for '+active+' model results; run this model to enable timeline.');draw();}
 function register(e){const {model,data}=e.detail||{};if(!Object.hasOwn(dataByModel,model)||!data?.channels?.time_s)return;
   // Keep original output object read-only and preserve its original samples/keys.
   dataByModel[model]=data;
   if(model===active){setPlay(false);clock=0;timeline.disabled=false;$('viz-play').disabled=false;$('viz-restart').disabled=false;timeline.value='0';announce('New '+model+' response loaded · '+data.channels.time_s.length+' authoritative samples.');draw();}
 }
 function line(a,b,color='#597f95',width=2){let A=M.project(a,camera,W,H),B=M.project(b,camera,W,H);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(A.x,A.y);ctx.lineTo(B.x,B.y);ctx.stroke();}
 let W=640,H=340;
 function polygon(points,fill,stroke='#416179'){ctx.beginPath();points.forEach((pt,i)=>{const q=M.project(pt,camera,W,H);if(!i)ctx.moveTo(q.x,q.y);else ctx.lineTo(q.x,q.y)});ctx.closePath();ctx.fillStyle=fill;ctx.fill();ctx.strokeStyle=stroke;ctx.lineWidth=1.2;ctx.stroke();}
 function box(cx,cy,cz,l,h,w,colors,pitch=0){const vertices=[];for(const x of [-1,1])for(const y of [-1,1])for(const z of [-1,1]){const dx=x*l/2,dy=y*h/2;vertices.push([cx+dx*Math.cos(pitch)-dy*Math.sin(pitch),cy+dx*Math.sin(pitch)+dy*Math.cos(pitch),cz+z*w/2]);}
   const faces=[[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]];
   const surfaces=faces.map((ids,k)=>({points:ids.map(i=>vertices[i]),fill:colors[k%colors.length],depth:ids.reduce((v,i)=>v+M.project(vertices[i],camera,W,H).depth,0)/4}));
   surfaces.sort((a,b)=>a.depth-b.depth);surfaces.forEach(f=>polygon(f.points,f.fill));
 }
 function wheel(x,y,z,r){const steps=18;
   for(const offset of [-0.13,0.13]){
     const ring=Array.from({length:steps},(_,k)=>[x+r*Math.cos(k/steps*Math.PI*2),y+r*Math.sin(k/steps*Math.PI*2),z+offset]);
     polygon(ring,'#0d2436','#85aec7');for(let k=0;k<steps;k+=3)line([x,y,z+offset],ring[k],'#557f9b',1);
   }
   line([x,y,z-0.13],[x,y,z+0.13],'#8cbfd4',3);
 }
 function spring(x,y0,y1,z){const n=8,points=[];for(let i=0;i<=n;i++)points.push([x+(i===0||i===n?0:(i%2?0.085:-0.085)),y0+(y1-y0)*i/n,z]);
    for(let i=1;i<points.length;i++)line(points[i-1],points[i],'#be9cff',2);
 }
 function arrow(x,y,z,len,color){line([x,y,z],[x,y+len,z],color,4);line([x,y+len,z],[x-0.065,y+len-Math.sign(len)*0.11,z],color,3);line([x,y+len,z],[x+0.065,y+len-Math.sign(len)*0.11,z],color,3);}
 function draw3d(state){
   const rect=canvas.getBoundingClientRect();W=rect.width||650;H=rect.height||350;if(W<8||H<8)return;
   const ratio=Math.min(devicePixelRatio||1,2),rw=Math.round(W*ratio),rh=Math.round(H*ratio);
   if(canvas.width!==rw||canvas.height!==rh){canvas.width=rw;canvas.height=rh}
   ctx.setTransform(ratio,0,0,ratio,0,0);ctx.fillStyle='#0d2030';ctx.fillRect(0,0,W,H);
   // 3D grid is illustrative road plane, not a tire contact calculation.
   for(let x=-4;x<=4;x+=0.5)line([x,0,-1.8],[x,0,1.8],'#254155',.8);
   for(let z=-1.5;z<=1.5;z+=0.5)line([-4,0,z],[4,0,z],'#254155',.8);
   line([-3.7,0,0],[3.7,0,0],'#dca865',3);
   const stopped=state.speed_m_s!==null;
   const heave=stopped?0:M.clamp(state.body_m*18,-0.38,0.38);
   const front=stopped?0:M.clamp(state.front_wheel_m*18,-0.34,0.34);
   const rear=stopped?0:M.clamp(state.rear_wheel_m*18,-0.34,0.34);
   const pitch=stopped?0:M.clamp(state.pitch_rad*4,-.38,.38);
   const r=.28,baseBody=1.14;
   const isQuarter=active==='quarter',frontX=isQuarter?0:1.18,rearX=-1.18;
   const bodies=stopped?[-.88,.88]:isQuarter?[0]:[rearX,frontX];
   for(const x of bodies){const y=r+(x===frontX?front:rear);for(const z of (stopped?[-0.55,.55]:[0]))wheel(x,y,z,r);
      if(!stopped){const attach=baseBody+heave+x*Math.sin(pitch)-.17;spring(x,y+.27,attach,0);}}
   if(stopped){box(0,baseBody,0,3.0,.52,1.35,['#226477','#307f86','#235a69','#3ba59e','#1f6770','#2b8284']);
     const frontN=state.front_normal_n||0,rearN=state.rear_normal_n||0,max=Math.max(frontN,rearN,1);
     arrow(frontX,1.60,.80,.62*frontN/max,'#6fe1cc');arrow(rearX,1.60,.80,.62*rearN/max,'#c0a0ff');
     if(active==='regen'){const regen=Math.max(0,state.regen_force_n||0),friction=Math.max(0,state.friction_force_n||0),total=Math.max(1,regen+friction);
       box(0,1.73,-.17,1.6,.13,.45,['#117e79','#198f86']);
       arrow(frontX,1.62,-.5,.45*regen/total,'#5ce5ce');arrow(rearX,1.62,-.5,.45*friction/total,'#fac07a');}
   }else box(0,baseBody+heave,0,isQuarter?1.45:3.0,.48,1.20,['#226477','#307f86','#235a69','#3ba59e','#1f6770','#2b8284'],pitch);
   ctx.fillStyle='#b9d4dd';ctx.font='11px system-ui';ctx.fillText(stopped?'Longitudinal schematic · no calculated pitch motion':(isQuarter?'Single axle · static-relative body/wheel':'Front +X · nose-up pitch positive'),14,22);
 }
 function draw2d(state){const body=$('viz-fallback-body'),front=$('viz-fallback-front'),rear=$('viz-fallback-rear');
   const h=M.clamp((state.body_m||0)*380,-38,38),p=M.clamp(state.pitch_rad*180/Math.PI*4,-24,24);
   body.setAttribute('transform',`translate(0 ${-h}) rotate(${-p} 310 110)`);
   const wheelF=M.clamp((state.front_wheel_m||0)*380,-36,36),wheelR=M.clamp((state.rear_wheel_m||0)*380,-36,36);
   front.setAttribute('cy',String(181-wheelF));rear.setAttribute('cy',String(181-wheelR));
 }
 function draw(){const data=dataByModel[active];if(!data){$('viz-time').textContent='No '+active+' results';$('viz-readings').textContent='Run the selected simulation to see physical state channels.';return}
   const state=M.stateAt(active,data,clock),e=state.time_s,d=state.duration_s;
   $('viz-time').textContent=`${s(e)} / ${s(d)} s`;
   const parts=[`Model: ${active}`,`t: ${s(e,3)} s`];
   if(state.speed_m_s!==null){parts.push(`speed: ${s(state.speed_m_s,3)} m/s`,`travel: ${s(state.distance_m,3)} m`,`front load: ${s(state.front_normal_n,1)} N`,`rear load: ${s(state.rear_normal_n,1)} N`);
     if(active==='regen')parts.push(`battery: ${s(state.battery_j/1000,2)} kJ`,`regen: ${s(state.regen_force_n,1)} N`,`friction: ${s(state.friction_force_n,1)} N`);
   }else{parts.push(`heave: ${s(state.body_m*1000,3)} mm`,`front wheel: ${s(state.front_wheel_m*1000,3)} mm`);
     if(active==='half')parts.push(`pitch: ${s(state.pitch_rad*180/Math.PI,4)}°`,`rear wheel: ${s(state.rear_wheel_m*1000,3)} mm`);
   }
   $('viz-readings').replaceChildren(...parts.map(str=>{const node=document.createElement('span');node.textContent=str;return node}));
   if(threeD){try{draw3d(state)}catch(err){control.value='2d';switchMode(true);announce('3D draw failed: '+err.message+'; showing 2D fallback.');}}
   if(!threeD)draw2d(state);
 }
 function animate(t){if(lastTick===null)lastTick=t;const delta=Math.max(0,Math.min((t-lastTick)/1000,.1));lastTick=t;
   if(playing&&hasResult()&&!document.hidden){const speed=Number($('viz-speed').value);const d=duration();clock=Math.min(d,clock+delta*speed);timeline.value=d?Math.round(clock/d*1000):0;draw();if(clock>=d)setPlay(false)}
   requestAnimationFrame(animate);
 }
 $('model-select').addEventListener('change',updateModel);
 window.addEventListener('autodyn:result',register);
 for(const [model,data] of Object.entries(window.AutoDynVizResults||{}))register({detail:{model,data}});
 control.addEventListener('change',()=>switchMode());
 $('viz-play').addEventListener('click',()=>{if(clock>=duration())setTime(0);setPlay(!playing)});
 $('viz-restart').addEventListener('click',()=>{setPlay(false);setTime(0)});
 timeline.addEventListener('input',()=>{setPlay(false);setTime(duration()*Number(timeline.value)/1000)});
 $('viz-reset-camera').addEventListener('click',()=>{camera={yaw:.68,elevation:.34,zoom:100};$('viz-zoom').value=100;draw()});
 $('viz-zoom').addEventListener('input',()=>{camera.zoom=Number($('viz-zoom').value);draw()});
 canvas.addEventListener('pointerdown',e=>{dragging={x:e.clientX,y:e.clientY};canvas.setPointerCapture?.(e.pointerId)});
 canvas.addEventListener('pointermove',e=>{if(!dragging)return;camera.yaw+=M.clamp((e.clientX-dragging.x)*.008,-.2,.2);camera.elevation=M.clamp(camera.elevation+(e.clientY-dragging.y)*.006,-.2,1.15);dragging={x:e.clientX,y:e.clientY};draw()});
 canvas.addEventListener('pointerup',()=>dragging=null);canvas.addEventListener('pointercancel',()=>dragging=null);
 canvas.addEventListener('keydown',e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','-','=','Home'].includes(e.key)){e.preventDefault();if(e.key==='ArrowLeft')camera.yaw-=.12;if(e.key==='ArrowRight')camera.yaw+=.12;if(e.key==='ArrowUp')camera.elevation=M.clamp(camera.elevation+.10,-.2,1.15);if(e.key==='ArrowDown')camera.elevation=M.clamp(camera.elevation-.10,-.2,1.15);if(e.key==='+'||e.key==='=')camera.zoom=M.clamp(camera.zoom+10,60,155);if(e.key==='-')camera.zoom=M.clamp(camera.zoom-10,60,155);if(e.key==='Home'){camera.yaw=.68;camera.elevation=.34;camera.zoom=100}$('viz-zoom').value=camera.zoom;draw()}});
 window.addEventListener('resize',draw);
 if(reduced){reduced.addEventListener?.('change',()=>{if(reduced.matches)setPlay(false)})}
 // Test-only inspection interface contains presentation state, never a reference to writable solver channels.
 window.AutoDynVizDebug=Object.freeze({getState:()=>hasResult()?M.stateAt(active,dataByModel[active],clock):null,setTime,hasResult:()=>hasResult(),getCamera:()=>({...camera}),getMode:()=>threeD?'3d':'2d'});
 $('viz-play').disabled=true;$('viz-restart').disabled=true;switchMode(!ctx);updateModel();if(reduced?.matches)announce('Reduced motion preference: playback remains paused until explicitly started.');requestAnimationFrame(animate);
})();
