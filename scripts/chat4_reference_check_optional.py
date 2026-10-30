"""Independent SciPy DOP853 numerical oracle for new Chat 4 road scenarios.

SciPy and NumPy are OPTIONAL development-only tools, not runtime requirements.
This constructs equations independently from the application's derivatives.
"""
import json
import math
from pathlib import Path
from dataclasses import asdict

from autodyn_ev.physics import Road, SimulationSettings, Vehicle
from autodyn_ev.halfcar import HalfCarVehicle, simulate_half
from autodyn_ev.simulation import simulate


def reference_road(t, road):
    if road.kind=='flat' or t < road.start_s:return 0.
    q=t-road.start_s
    d=road.bump_length_m/road.speed_m_s
    def pulse(x):return 0 if x<0 or x>=d else road.height_m*(1-math.cos(2*math.pi*x/d))/2
    if road.kind=='pothole':return -pulse(q)
    if road.kind=='double_bump':return pulse(q)+pulse(q-d-road.bump_spacing_m/road.speed_m_s)
    if road.kind=='bump':return pulse(q)
    if road.kind=='step':return road.height_m
    if road.kind=='sine':return road.height_m*math.sin(2*math.pi*road.sine_frequency_hz*q)
    if road.kind=='chirp':
        u=min(q,road.chirp_duration_s)
        phase=road.sine_frequency_hz*u + .5*(road.chirp_end_frequency_hz-road.sine_frequency_hz)*u*u/road.chirp_duration_s + road.chirp_end_frequency_hz*(q-u)
        return road.height_m*math.sin(2*math.pi*phase)
    raise AssertionError('unknown road')


def main():
    import numpy as np
    from scipy.integrate import solve_ivp
    dt=.005;duration=5.;times=np.linspace(0,duration,1001)
    settings=SimulationSettings(duration_s=duration,dt_s=dt)
    comparisons=[]
    for kind,model in [('pothole','quarter'),('double_bump','half'),('chirp','quarter'),('chirp','half')]:
        road=Road(kind=kind)
        if model=='quarter':
            v=Vehicle();res=simulate(v,road,settings)
            def dydt(t,y):
                zs,zu,vs,vu=y
                f=v.suspension_stiffness_n_m*(zs-zu)+v.damping_n_s_m*(vs-vu)
                ft=v.tire_stiffness_n_m*(zu-reference_road(t,road))
                return [vs,vu,-f/v.sprung_mass_kg,(f-ft)/v.unsprung_mass_kg]
            channels=['sprung_m','unsprung_m','sprung_velocity_m_s','unsprung_velocity_m_s'];refs=[0,1,2,3]
            ref=solve_ivp(dydt,[0,duration],[0]*4,t_eval=times,rtol=1e-10,atol=1e-12,method='DOP853',max_step=.001)
        else:
            v=HalfCarVehicle();res=simulate_half(v,road,settings)
            def dydt(t,y):
                z,theta,uf,ur,vz,w,vuf,vur=y
                ff=-v.front_spring_n_m*(z+v.cg_to_front_m*theta-uf)-v.front_damping_n_s_m*(vz+v.cg_to_front_m*w-vuf)
                fr=-v.rear_spring_n_m*(z-v.cg_to_rear_m*theta-ur)-v.rear_damping_n_s_m*(vz-v.cg_to_rear_m*w-vur)
                qf=reference_road(t,road);qr=reference_road(t-v.wheelbase_m/road.speed_m_s,road)
                return [vz,w,vuf,vur,(ff+fr)/v.body_mass_kg,
                        (v.cg_to_front_m*ff-v.cg_to_rear_m*fr)/v.pitch_inertia_kg_m2,
                        (-ff-v.front_tire_n_m*(uf-qf))/v.front_unsprung_mass_kg,
                        (-fr-v.rear_tire_n_m*(ur-qr))/v.rear_unsprung_mass_kg]
            channels=['body_heave_m','body_pitch_rad','front_wheel_m','rear_wheel_m',
                      'body_heave_velocity_m_s','body_pitch_rate_rad_s','front_wheel_velocity_m_s','rear_wheel_velocity_m_s']
            refs=list(range(8))
            ref=solve_ivp(dydt,[0,duration],[0]*8,t_eval=times,rtol=1e-10,atol=1e-12,method='DOP853',max_step=.001)
        if not ref.success:raise RuntimeError(ref.message)
        errors={k:float(np.max(np.abs(np.asarray(res['channels'][k])-ref.y[index]))) for k,index in zip(channels,refs)}
        peak=max(errors.values())
        if peak>2e-4:raise AssertionError(f'{kind} {model} exceeds tolerance {peak}: {errors}')
        comparisons.append({'kind':kind,'model':model,'max_absolute_error_across_selected_states':peak,
                            'channel_errors':errors,'oracle':'SciPy DOP853 max_step=.001; independent equations and road profile',
                            'tolerance':2e-4})
    output={'passed':True,'source':'optional independent high-accuracy DOP853 numerical oracle',
            'runtime_scipy_required':False,'cases':comparisons}
    p=Path(__file__).resolve().parent.parent/'docs/chat4_reference_results.json'
    p.write_text(json.dumps(output,indent=2))
    print(json.dumps(output,indent=2))

if __name__=='__main__':main()
