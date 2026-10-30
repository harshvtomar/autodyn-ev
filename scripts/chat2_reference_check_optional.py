"""Optional independently implemented SciPy/NumPy state-space reference.

Not part of app runtime; requires scipy & numpy installed on validation machine.
"""
import json
from pathlib import Path
from math import pi
import numpy as np
from scipy.integrate import solve_ivp
from autodyn_ev.physics import Road,SimulationSettings,Vehicle
from autodyn_ev.analysis import damped_modes
from autodyn_ev.simulation import simulate

rng=np.random.default_rng(20261029)
modal_errors=[]
for i in range(100):
    ms=float(rng.uniform(100,1200));mu=float(rng.uniform(15,150))
    ks=float(rng.uniform(5000,120000));c=float(rng.uniform(0,12000));kt=float(rng.uniform(40000,500000))
    v=Vehicle(ms,mu,ks,c,kt)
    A=np.array([[0,0,1,0],[0,0,0,1],[-ks/ms,ks/ms,-c/ms,c/ms],[ks/mu,-(ks+kt)/mu,c/mu,-c/mu]])
    expected=np.linalg.eigvals(A)
    actual=np.array([complex(p['real_s_inv'],p['imag_rad_s']) for p in damped_modes(v)['poles']])
    # nearest assignment across 4 roots by brute-force 24 permutations
    from itertools import permutations
    error=min(max(abs(actual[j]-expected[k]) for j,k in enumerate(order)) for order in permutations(range(4)))
    modal_errors.append(error)

v=Vehicle();r=Road(kind='sine',height_m=.02,start_s=0,sine_frequency_hz=1.2)
s=SimulationSettings(duration_s=4,dt_s=.0025)
result=simulate(v,r,s)

def reference(t,y):
    zs,zu,vs,vu=y
    zr=r.displacement(t)
    fs=v.suspension_stiffness_n_m*(zs-zu)+v.damping_n_s_m*(vs-vu)
    return (vs,vu,-fs/v.sprung_mass_kg,(fs-v.tire_stiffness_n_m*(zu-zr))/v.unsprung_mass_kg)

time=result['channels']['time_s']
sol=solve_ivp(reference,(0,s.duration_s),(0,0,0,0),method='DOP853',t_eval=time,rtol=1e-12,atol=1e-13)
assert sol.success
channels=['sprung_m','unsprung_m','sprung_velocity_m_s','unsprung_velocity_m_s']
errors={ch:float(np.max(np.abs(sol.y[i]-np.asarray(result['channels'][ch])))) for i,ch in enumerate(channels)}
checks={'numpy_modal_max_abs_eigenvalue_error_1_per_s':float(max(modal_errors)),
        'checked_random_vehicle_configurations':100,
        'scipy_dop853_rk4_max_errors_by_channel':errors,
        'damped_modal_tolerance_1_per_s':1e-4,
        'time_domain_max_channel_tolerance_si_units':2e-5,
        'result':'PASS' if max(modal_errors)<1e-4 and max(errors.values())<2e-5 else 'FAIL',
        'scope':'Independent 4x4 NumPy eigenvalues and SciPy DOP853 on sinusoidal road; does not validate real vehicle behavior'}
Path('docs/chat2_reference_results.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks,indent=2))
if checks['result']!='PASS': raise SystemExit(1)
