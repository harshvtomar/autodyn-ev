"""OPTIONAL independent numerical cross-check. Not needed to run AutoDyn EV.

Requires SciPy. Compares custom fixed-step RK4 with high-accuracy DOP853
on a smooth sinusoidal road that starts at t=0, avoiding event discontinuities.
"""
import json
from pathlib import Path
from math import sqrt
from autodyn_ev.physics import Vehicle, Road, SimulationSettings, derivatives
from autodyn_ev.simulation import simulate
from scipy.integrate import solve_ivp

v=Vehicle(); road=Road(kind='sine', height_m=.02, start_s=0, sine_frequency_hz=1.2)
settings=SimulationSettings(duration_s=5,dt_s=.005)
ours=simulate(v,road,settings)
t=ours['channels']['time_s']
reference=solve_ivp(lambda ti,yi:derivatives(ti,tuple(yi),v,road),[t[0],t[-1]],[0,0,0,0],method='DOP853',t_eval=t,atol=1e-12,rtol=1e-11)
assert reference.success
errors={}
for name,axis in [('sprung_displacement_m',0),('unsprung_displacement_m',1),('sprung_velocity_m_s',2),('unsprung_velocity_m_s',3)]:
    ours_key=['sprung_m','unsprung_m','sprung_velocity_m_s','unsprung_velocity_m_s'][axis]
    errors[name]=float(max(abs(a-b) for a,b in zip(ours['channels'][ours_key],reference.y[axis])))
assert max(errors.values())<5e-5, errors
result={ 'reference':'SciPy solve_ivp DOP853, atol 1e-12, rtol 1e-11', 'duration_s':5,'dt_s':.005,'max_absolute_error_by_channel':errors,'acceptance_threshold':5e-5,'status':'PASS','note':'Smooth sine input only; not evidence for discontinuous road profiles or real-world validation' }
print(json.dumps(result,indent=2))
(Path(__file__).resolve().parent.parent/'docs/scipy_reference_results.json').write_text(json.dumps(result,indent=2)+'\n')
