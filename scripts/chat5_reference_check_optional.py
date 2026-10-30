"""Independent SciPy quadrature reference for commanded deceleration and distance.
Optional development check. Does not ship as an app runtime dependency.
"""
from dataclasses import replace
from math import isfinite
import json,random
from pathlib import Path
from autodyn_ev.braking import BrakingScenario,GRAVITY,simulate_braking

def main():
    from scipy.integrate import quad
    from scipy.optimize import brentq
    random.seed(20261029)
    cases=[]
    for i in range(120):
        mu=random.uniform(.25,1.0);demand=random.uniform(2,12)
        s=BrakingScenario(profile='ramp' if i%2 else 'constant',
          initial_speed_m_s=random.uniform(5,35),friction_coefficient=mu,
          demanded_decel_m_s2=demand,ramp_s=random.uniform(.25,3),
          dt_s=[.005,.01,.04,.09][i%4], duration_s=40,
          cg_to_front_m=1.4,cg_height_m=.3)
        # Reference computed separately using SciPy adaptive quadrature of the
        # externally specified deceleration schedule, followed by root solving.
        def decel(time):
            d=demand*(min(1.0,time/s.ramp_s) if s.profile=='ramp' else 1.0)
            return min(d,mu*GRAVITY)
        def v(time):return s.initial_speed_m_s-quad(decel,0,time,epsabs=1e-10,epsrel=1e-10,points=[s.ramp_s,mu*GRAVITY*s.ramp_s/demand] if s.profile=='ramp' else None)[0]
        if v(40)<0:
            tstar=brentq(v,0,40,xtol=1e-12)
            xstar=quad(lambda t:max(0,v(t)),0,tstar,epsabs=1e-8,epsrel=1e-8)[0]
            actual=simulate_braking(s)['metrics']
            dt=abs(actual['stopping_time_s']-tstar);dx=abs(actual['stopping_distance_m']-xstar)
            cases.append({'case':i,'profile':s.profile,'time_error_s':dt,'distance_error_m':dx,'is_finite':isfinite(dx+dt)})
        else:
            raise AssertionError('reference horizon too short')
    maxt=max(c['time_error_s'] for c in cases);maxx=max(c['distance_error_m'] for c in cases)
    result={'reference':'SciPy quad + Brent root, independent continuous deceleration integration',
      'seed':20261029,'cases':len(cases),'max_stop_time_error_s':maxt,'max_stop_distance_error_m':maxx,
      'threshold_stop_time_s':1e-7,'threshold_stop_distance_m':1e-6,'passed':maxt<1e-7 and maxx<1e-6,
      'individual_cases':cases}
    path=Path(__file__).resolve().parent.parent/'docs/chat5_reference_results.json'
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='individual_cases'},indent=2))
    if not result['passed']:raise SystemExit(1)
if __name__=='__main__':main()
