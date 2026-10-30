"""Chat 9 independent verification references for the accepted solvers.

No authoritative model imports/functions are used to calculate expected accelerations,
energy, brake stopping, time-weighted RMS or the Pareto reference classification.
References are algebraically derived from force balance or elementary kinematics.
This module is optional quality assurance; the running application does not import it.
"""
from math import fsum, sqrt, isfinite


def quarter_force_reference(masses, stiffnesses, state, road_height):
    """Independent Newton force balance; return body and wheel accelerations (m/s²)."""
    ms, mu = masses
    ks, cs, kt = stiffnesses
    zs, zu, vs, vu = state
    spring_force = ks * (zu-zs)
    damper_force = cs * (vu-vs)
    tire_force = kt * (road_height-zu)
    return (spring_force+damper_force)/ms, (-spring_force-damper_force+tire_force)/mu


def half_force_reference(properties, state, front_road, rear_road):
    """Independent small-angle D'Alembert force/moment balance. Returns four accelerations."""
    m, iy, a, b, muf, mur, kf, kr, cf, cr, ktf, ktr = properties
    z, pitch, uf, ur, vz, omega, vuf, vur = state
    front_extension = (z-uf) + a*pitch
    rear_extension = (z-ur) - b*pitch
    front_speed = (vz-vuf) + a*omega
    rear_speed = (vz-vur) - b*omega
    force_f = -kf*front_extension-cf*front_speed
    force_r = -kr*rear_extension-cr*rear_speed
    tire_f = ktf*(front_road-uf)
    tire_r = ktr*(rear_road-ur)
    return ((force_f+force_r)/m, (a*force_f-b*force_r)/iy,
            (tire_f-force_f)/muf, (tire_r-force_r)/mur)


def quarter_free_energy(masses, stiffnesses, state):
    ms,mu=masses; ks,kt=stiffnesses
    zs,zu,vs,vu=state
    return 0.5*fsum((ms*vs*vs,mu*vu*vu,ks*(zs-zu)**2,kt*zu*zu))


def half_free_energy(properties, state):
    m,iy,a,b,muf,mur,kf,kr,cf,cr,ktf,ktr=properties
    z,theta,uf,ur,vz,omega,vuf,vur=state
    return .5*fsum((m*vz*vz,iy*omega*omega,muf*vuf*vuf,mur*vur*vur,
                     kf*(z+a*theta-uf)**2,kr*(z-b*theta-ur)**2,ktf*uf*uf,ktr*ur*ur))


def independent_trapezoidal_rms(t, signal):
    """Direct definition of time-weighted unweighted RMS, independent of ride._window."""
    if len(t)<2 or len(t)!=len(signal) or any(t[i+1]<=t[i] for i in range(len(t)-1)):
        raise ValueError('strictly increasing equal-length arrays required')
    total = fsum((signal[i]**2+signal[i+1]**2)*(t[i+1]-t[i])*0.5 for i in range(len(t)-1))
    return sqrt(total/(t[-1]-t[0]))


def independent_pareto_ids(cases):
    """All-pairs reference classifier including only feasible cases; no model _pareto call."""
    passed=[x for x in cases if x['feasible']]
    answer=[]
    for candidate in passed:
        r=candidate['metrics']['body_acceleration_rms_m_s2']
        d=candidate['metrics']['suspension_travel_peak_to_peak_mm']
        beaten=False
        for rival in passed:
            if rival['id']==candidate['id']:
                continue
            rr=rival['metrics']['body_acceleration_rms_m_s2']
            dd=rival['metrics']['suspension_travel_peak_to_peak_mm']
            if rr<=r and dd<=d and (rr<r or dd<d):
                beaten=True
                break
        if not beaten:
            answer.append(candidate['id'])
    return answer


def verify_study(study):
    """Check grid coverage, constraint decisions, Pareto, and deterministic selection.

    Raises AssertionError on discrepancies rather than silently repairing output.
    """
    cases=study['candidates']; grid=study['grid']; params=grid['parameters']
    expected_count=7**len(params)
    assert expected_count == grid['run_count'] == len(cases)
    assert [x['id'] for x in cases] == list(range(1, expected_count+1))
    for i,c in enumerate(cases):
        assert all(isfinite(value) for value in c['metrics'].values())
        for axis,param in enumerate(params):
            expected_index=(i // (7**(len(params)-1-axis)))%7
            assert c['parameters'][param] == grid['values'][param][expected_index]
        failed=[name for name,limit in study['constraints'].items()
                if c['metrics'][name.removeprefix('max_')] > limit]
        assert failed==c['failed_constraints']
        assert c['feasible']==(not failed)
    assert study['feasible_count']==sum(x['feasible'] for x in cases)
    assert study['pareto_ids']==independent_pareto_ids(cases)
    feasible=[x for x in cases if x['feasible']]
    chosen=min(feasible,key=lambda x:(x['metrics']['body_acceleration_rms_m_s2'],
        x['metrics']['suspension_travel_peak_to_peak_mm'],
        x['metrics']['tire_deflection_peak_abs_mm'],x['id'])) if feasible else None
    assert study['selected_id']==(chosen['id'] if chosen else None)
    return {'case_count':len(cases),'feasible_count':len(feasible),
            'pareto_count':len(study['pareto_ids']), 'selected_id':study['selected_id']}


def constant_braking_reference(mass, speed, requested_decel, mu, g=9.80665):
    """Elementary v² relation for level-road constant deceleration (not stopping code)."""
    decel=min(requested_decel,mu*g)
    if speed==0:
        return 0.0,0.0
    if decel<=0:
        return None,None
    return speed/decel,speed**2/(2*decel)


def max_abs_delta(a,b):
    if len(a)!=len(b):
        raise ValueError('sample channels have different lengths')
    return max((abs(x-y) for x,y in zip(a,b)), default=0.0)
