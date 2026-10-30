"use strict";
/* Chat 7 pure read-only presentation mathematics. Safe under Node and browsers. */
(function (root) {
  const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
  function sampleAt(ch,seconds){
    if(!ch||!Array.isArray(ch.time_s)||!ch.time_s.length)throw new Error('Missing authoritative time series');
    const t=ch.time_s,now=clamp(Number(seconds)||0,t[0],t[t.length-1]);
    let lo=0,hi=t.length-1;
    while(lo<hi){const mid=(lo+hi)>>1;if(t[mid]<now)lo=mid+1;else hi=mid}
    const j=lo,i=Math.max(0,j-1),gap=t[j]-t[i],a=gap>0?(now-t[i])/gap:0;
    const result={time_s:now};
    for(const [key,arr] of Object.entries(ch)){
      if(key==='time_s')continue;
      if(!Array.isArray(arr)||arr.length!==t.length)continue;
      result[key]=arr[i]+a*(arr[j]-arr[i]);
    }
    return result;
  }
  function stateAt(model,data,seconds){
    if(!['quarter','half','braking','regen'].includes(model))throw new Error('Unknown model');
    const s=sampleAt(data.channels,seconds),dur=data.channels.time_s.at(-1);
    const state={model,time_s:s.time_s,duration_s:dur,body_m:0,pitch_rad:0,front_wheel_m:0,rear_wheel_m:0,front_road_m:0,rear_road_m:0,speed_m_s:null,distance_m:null,front_normal_n:null,rear_normal_n:null,battery_j:null,regen_force_n:null,friction_force_n:null};
    if(model==='quarter'){
      state.body_m=s.sprung_m;state.front_wheel_m=s.unsprung_m;state.front_road_m=s.road_m;
    }else if(model==='half'){
      state.body_m=s.body_heave_m;state.pitch_rad=s.body_pitch_rad;
      state.front_wheel_m=s.front_wheel_m;state.rear_wheel_m=s.rear_wheel_m;
      state.front_road_m=s.front_road_m;state.rear_road_m=s.rear_road_m;
    }else{
      state.speed_m_s=s.speed_m_s;state.distance_m=s.distance_m;
      state.front_normal_n=s.front_normal_n;state.rear_normal_n=s.rear_normal_n;
      if(model==='regen'){
        state.battery_j=s.cumulative_battery_energy_j;
        state.regen_force_n=s.regen_force_n;state.friction_force_n=s.friction_force_n;
      }
    }
    return state;
  }
  function project(point,camera,width,height){
    const {yaw,elevation,zoom}=camera,[x,y,z]=point;
    const xr=x*Math.cos(yaw)-z*Math.sin(yaw);
    const d=x*Math.sin(yaw)+z*Math.cos(yaw);
    const scale=Math.min(width/7.1,height/3.8)*(zoom/100);
    return {x:width/2+xr*scale,y:height*0.60-(y*Math.cos(elevation)-d*Math.sin(elevation))*scale,depth:d*Math.cos(elevation)+y*Math.sin(elevation)};
  }
  const api={clamp,sampleAt,stateAt,project};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.AutoDynVizMath=api;
})(typeof window!=='undefined'?window:globalThis);
