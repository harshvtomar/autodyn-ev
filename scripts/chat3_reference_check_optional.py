"""Optional independent SciPy/NumPy verification; not application requirements."""
from __future__ import annotations
import json,random
from dataclasses import replace
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
from autodyn_ev.halfcar import HalfCarVehicle,simulate_half,derivatives_half,half_energy
from autodyn_ev.physics import Road,SimulationSettings

seed=20261029
random.seed(seed)
max_matrix_residual=0.
max_energy_derivative_residual=0.
for i in range(150):
    v=HalfCarVehicle(
      body_mass_kg=random.uniform(200,1200),pitch_inertia_kg_m2=random.uniform(200,3000),
      cg_to_front_m=random.uniform(.7,2),cg_to_rear_m=random.uniform(.7,2),
      front_unsprung_mass_kg=random.uniform(20,90),rear_unsprung_mass_kg=random.uniform(20,90),
      front_spring_n_m=random.uniform(8000,60000),rear_spring_n_m=random.uniform(8000,60000),
      front_damping_n_s_m=random.uniform(0,5000),rear_damping_n_s_m=random.uniform(0,5000),
      front_tire_n_m=random.uniform(80000,350000),rear_tire_n_m=random.uniform(80000,350000))
    y=np.array([random.uniform(-.04,.04) for _ in range(4)]+[random.uniform(-.3,.3) for _ in range(4)])
    B=np.array([[1.,v.cg_to_front_m,-1,0],[1.,-v.cg_to_rear_m,0,-1],[0,0,1,0],[0,0,0,1]])
    mass=np.diag([v.body_mass_kg,v.pitch_inertia_kg_m2,v.front_unsprung_mass_kg,v.rear_unsprung_mass_kg])
    stiffness=B.T@np.diag([v.front_spring_n_m,v.rear_spring_n_m,v.front_tire_n_m,v.rear_tire_n_m])@B
    damping=B.T@np.diag([v.front_damping_n_s_m,v.rear_damping_n_s_m,0,0])@B
    expected=np.concatenate([y[4:],np.linalg.solve(mass,-stiffness@y[:4]-damping@y[4:])])
    actual=np.array(derivatives_half(0,tuple(y),v,Road(kind='flat')))
    max_matrix_residual=max(max_matrix_residual,float(np.max(np.abs(actual-expected))))
    vv=y[4:]
    dE=-float(vv@damping@vv)
    from autodyn_ev.halfcar import half_energy_rate_flat
    max_energy_derivative_residual=max(max_energy_derivative_residual,abs(dE-half_energy_rate_flat(tuple(y),v)))

r=Road(kind='sine',height_m=.012,start_s=.4,sine_frequency_hz=.8)
s=SimulationSettings(duration_s=2.0,dt_s=.0025)
v=HalfCarVehicle()
actual=simulate_half(v,r,s)
ref=solve_ivp(lambda t,y:derivatives_half(t,tuple(y),v,r),(0,2.0),[0]*8,t_eval=np.array(actual['channels']['time_s']),method='DOP853',rtol=2e-11,atol=1e-12,max_step=.0004)
assert ref.success,ref.message
compare_keys=['body_heave_m','body_pitch_rad','front_wheel_m','rear_wheel_m','body_heave_velocity_m_s','body_pitch_rate_rad_s','front_wheel_velocity_m_s','rear_wheel_velocity_m_s']
max_per_channel={key:float(np.max(np.abs(ref.y[i]-actual['channels'][key]))) for i,key in enumerate(compare_keys)}
assert max_matrix_residual < 1e-10,max_matrix_residual
assert max_energy_derivative_residual < 1e-10,max_energy_derivative_residual
assert all(max_per_channel[k]<2e-5 for k in compare_keys),max_per_channel
result={'independent_reference':'NumPy direct M,C,K state assembly; SciPy DOP853 high-resolution comparison','random_cases':150,'seed':seed,'max_matrix_acceleration_error':max_matrix_residual,'max_energy_rate_error':max_energy_derivative_residual,'max_abs_scipy_channel_error_SI':max_per_channel,'threshold_each_channel':2e-5,'status':'PASS','scope':'smooth sinusoidal road excitation; no empirical vehicle validation'}
Path('docs/chat3_reference_results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
