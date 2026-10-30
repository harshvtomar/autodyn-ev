"""Optional independent SciPy/NumPy checks; neither is a required app dependency."""
from dataclasses import replace
from math import isfinite
from pathlib import Path
from random import Random
import json
from scipy.integrate import quad, solve_ivp
from autodyn_ev.regen import RegenScenario, simulate_regen
from autodyn_ev.braking import GRAVITY

ROOT=Path(__file__).resolve().parents[1]
rng=Random(20261029)
results=[]
for j in range(100):
    sc=RegenScenario(mass_kg=rng.uniform(800,2300),initial_speed_m_s=rng.uniform(5,32),
        friction_coefficient=rng.uniform(.35,1.15),demanded_decel_m_s2=rng.uniform(.7,8),
        profile='ramp' if j%2 else 'constant',ramp_s=rng.uniform(.4,3),
        duration_s=rng.uniform(1.5,13),dt_s=rng.choice([.005,.01,.02,.04]),
        motor_max_torque_nm=rng.uniform(0,350),gear_ratio=rng.uniform(2,15),
        driven_wheel_radius_m=rng.uniform(.22,.45),motor_max_mech_power_w=rng.uniform(500,85000),
        battery_charge_limit_w=rng.uniform(200,50000),conversion_efficiency=rng.uniform(.25,1),
        low_speed_cutoff_m_s=(rng.uniform(.1,3) if j%9==0 else 0.0))
    sc.validate()
    app=simulate_regen(sc)
    m=sc.mass_kg
    mu_cap=sc.friction_coefficient*GRAVITY
    def decel(t):
        requested=sc.demanded_decel_m_s2 if sc.profile=='constant' else sc.demanded_decel_m_s2*min(max(0,t/sc.ramp_s),1)
        return min(requested,mu_cap)
    # Reference numerics use only the public scenario parameters and SciPy ODEs;
    # not the Chat 6 allocator, work-integrator or Chat 5 speed arrays.
    def f(t,y):
        vel=max(0,y[0]);a=decel(t)
        force=m*a
        if vel==0 or vel<sc.low_speed_cutoff_m_s or sc.conversion_efficiency==0 or sc.battery_charge_limit_w==0:
            regen=0
        else:
            regen=min(force,sc.motor_max_torque_nm*sc.gear_ratio/sc.driven_wheel_radius_m,
                sc.motor_max_mech_power_w/vel,sc.battery_charge_limit_w/(sc.conversion_efficiency*vel))
        return [-a if vel>0 else 0,vel,regen*vel]
    def event(t,y): return y[0]
    event.terminal=True;event.direction=-1
    solution=solve_ivp(f,(0,sc.duration_s),(sc.initial_speed_m_s,0,0),method='DOP853',events=event,rtol=2e-9,atol=3e-9,max_step=.03)
    if not solution.success:raise AssertionError('reference solver failed')
    stop=bool(len(solution.t_events[0]));appmetrics=app['metrics']
    tdiff=abs(solution.t[-1]-appmetrics['elapsed_s'])
    xdiff=abs(solution.y[1,-1]-appmetrics['distance_travelled_m'])
    energydiff=abs(solution.y[2,-1]-appmetrics['motor_mechanical_recovered_j'])
    # Tight absolute tolerances for smooth cases; finite cutoff event near a
    # quadrature node allows sub-joule energy error from this independent ODE.
    energy_tol=max(1.0,sc.mass_kg*sc.initial_speed_m_s**2*2e-5)
    if stop!=appmetrics['stopped'] or tdiff>2e-4 or xdiff>2e-3 or energydiff>energy_tol:
        raise AssertionError(f'case={j} time_error={tdiff} distance_error={xdiff} motor_energy_error={energydiff} limit={energy_tol} stopped={stop,appmetrics["stopped"]}')
    residual=appmetrics['energy_balance_residual_j']
    if not isfinite(residual) or abs(residual)>1e-6:raise AssertionError('energy balance failed')
    results.append({'case':j,'profile':sc.profile,'stopped':stop,'time_error_s':tdiff,
            'distance_error_m':xdiff,'mechanical_energy_error_j':energydiff,'energy_balance_residual_j':residual})
summary={'cases':len(results),'reference':'independent SciPy DOP853 ODE for speed, distance and regenerative mechanical work; bounded motor and battery outputs',
 'max_time_error_s':max(r['time_error_s'] for r in results),
 'max_distance_error_m':max(r['distance_error_m'] for r in results),
 'max_mechanical_energy_error_j':max(r['mechanical_energy_error_j'] for r in results),
 'max_energy_residual_j':max(abs(r['energy_balance_residual_j']) for r in results),
 'stopped_cases':sum(r['stopped'] for r in results),
 'ramped_cases':sum(r['profile']=='ramp' for r in results),
 'motor_work_tolerance_j':'max(1.0, mass*initial_speed^2*2e-5) per case',
 'time_tolerance_s':2e-4,'distance_tolerance_m':2e-3}
(ROOT/'docs'/'chat6_scipy_reference_results.json').write_text(json.dumps({'summary':summary,'cases':results},indent=2))
print(json.dumps(summary,indent=2))
