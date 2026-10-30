"""Chat 2 engineering studies. Pure standard library; no changes to Chat 1 ODE.

Damped poles are solutions to det(lambda^2 M + lambda C + K) = 0.
Non-proportional damping can yield nonoscillatory real poles: do not assign those
an invented oscillation frequency or canonical undamped mode labels.
"""
from dataclasses import asdict, replace
from math import hypot, isfinite, pi
from typing import Any

from .physics import Road, SimulationSettings, Vehicle
from .simulation import simulate, scenario_from_mapping

MODEL_REVISION = 'quarter-car-2dof-v0.2.0'
SOLVER = 'fixed-step-classical-RK4'
BOUNDS = {
    'sprung_mass_kg': (100.0, 1200.0),
    'unsprung_mass_kg': (15.0, 150.0),
    'suspension_stiffness_n_m': (5000.0, 120000.0),
    'damping_n_s_m': (0.0, 12000.0),
    'tire_stiffness_n_m': (40000.0, 500000.0),
}
METRICS = ('body_acceleration_rms_m_s2', 'body_acceleration_peak_m_s2',
           'suspension_travel_peak_mm', 'body_displacement_peak_mm',
           'tire_deflection_peak_mm', 'tire_force_variation_peak_n')


def _unit_metadata() -> dict[str, str]:
    return {'time': 's', 'displacement': 'm', 'velocity': 'm/s',
            'acceleration': 'm/s^2', 'force_variation': 'N',
            'reported_peak_displacement_and_travel': 'mm',
            'sprung_and_unsprung_mass': 'kg', 'spring_and_tire_stiffness': 'N/m',
            'damping': 'N*s/m'}


def provenance(vehicle: Vehicle, road: Road, settings: SimulationSettings, analysis: str) -> dict[str, Any]:
    """Deterministic recipe for reproducing a run; does not invent measurement provenance."""
    return {'model_revision': MODEL_REVISION,
            'model': 'linear-2dof-quarter-car-static-equilibrium-deviations',
            'analysis': analysis, 'solver': SOLVER,
            'coordinates': 'positive-up; static-equilibrium-relative',
            'units': _unit_metadata(),
            'vehicle': asdict(vehicle), 'road': asdict(road),
            'requested_settings': asdict(settings),
            'data_kind': 'simulated; not empirical vehicle measurements',
            'versioned_output': '2.0-additive; existing 1.0 keys preserved'}


def _poly(coeff: list[complex], z: complex) -> complex:
    out = complex(0)
    for c in coeff:
        out = out * z + c
    return out


def _roots_quartic(coeff: list[float]) -> list[complex]:
    """Scale the monic quartic and solve all roots with Aberth iteration.

    Separate simultaneous updates, an analytic derivative and collision jitter
    avoid accidental repeated-root division; residuals are checked after solve.
    """
    # Normalized coefficients must already be scale-free and monic.
    starts = [complex(0.83, 0.41), complex(-0.67, 0.95),
              complex(-1.02, -0.53), complex(0.57, -0.87)]
    roots = starts
    deriv = [4.0, 3 * coeff[1], 2 * coeff[2], coeff[3]]
    for _ in range(550):
        candidates = []
        for i, z in enumerate(roots):
            f = _poly(coeff, z)
            fp = _poly(deriv, z)
            if abs(fp) < 1e-16:
                z += complex(1e-7 * (i+1), 1e-7)
                f, fp = _poly(coeff, z), _poly(deriv, z)
            newton = f / fp
            interaction = 0j
            for j, other in enumerate(roots):
                if i != j:
                    distance = z - other
                    if abs(distance) < 1e-12:
                        distance += complex(1e-7*(i+1), 1e-7*(j+1))
                    interaction += 1 / distance
            denominator = 1 - newton * interaction
            update = newton / denominator if abs(denominator) > 1e-12 else newton
            candidates.append(z - update)
        roots = candidates
        if max(abs(_poly(coeff, z)) for z in roots) < 2e-11:
            break
    residual = max(abs(_poly(coeff, z)) for z in roots)
    if residual > 5e-8 or any(not isfinite(z.real) or not isfinite(z.imag) for z in roots):
        raise ValueError('damped pole solver could not resolve nearly repeated poles; modify parameters')
    return roots


def damped_modes(vehicle: Vehicle) -> dict[str, Any]:
    """Exact linearized 2-DOF characteristic polynomial, not SDOF approximation."""
    vehicle.validate()
    ms, mu = vehicle.sprung_mass_kg, vehicle.unsprung_mass_kg
    ks, kt, c = vehicle.suspension_stiffness_n_m, vehicle.tire_stiffness_n_m, vehicle.damping_n_s_m
    # det(lambda^2 M + lambda C + K):
    # ms mu l^4 + c (ms+mu) l^3 + [ms (ks+kt)+mu ks] l^2 + c kt l + ks kt
    a4, a3 = ms*mu, c*(ms+mu)
    a2, a1, a0 = ms*(ks+kt)+mu*ks, c*kt, ks*kt
    # lambda = scale * x, with scale = largest undamped omega
    scale = max(1.0, vehicle.undamped_frequencies_hz[1] * 2*pi)
    coeff = [1.0, a3/(a4*scale), a2/(a4*scale**2),
             a1/(a4*scale**3), a0/(a4*scale**4)]
    poles = sorted((z*scale for z in _roots_quartic(coeff)), key=lambda z:(z.imag,z.real))
    pairs = []
    for pole in poles:
        if pole.imag > 1e-6:
            omega_n = abs(pole)
            pairs.append({'pole_real_s_inv': pole.real,
                          'pole_imag_rad_s': pole.imag,
                          'damped_frequency_hz': pole.imag/(2*pi),
                          'pole_magnitude_hz': omega_n/(2*pi),
                          'damping_ratio': -pole.real/omega_n,
                          'decay_rate_s_inv': -pole.real})
    real_poles = [{'decay_rate_s_inv':-z.real} for z in poles if abs(z.imag) <= 1e-6]
    return {'undamped_frequencies_hz': list(vehicle.undamped_frequencies_hz),
            'oscillatory_modes': sorted(pairs, key=lambda x:x['damped_frequency_hz']),
            'real_nonoscillatory_poles': sorted(real_poles, key=lambda x:x['decay_rate_s_inv']),
            'poles': [{'real_s_inv': z.real, 'imag_rad_s': z.imag} for z in poles],
            'interpretation': 'Damped frequencies and ratios describe oscillatory state-space poles only. Real poles have decay rates, not oscillatory frequency. With non-proportional damping, mode labels are not presumed to map one-to-one to undamped body/wheel modes.',
            'characteristic_polynomial': [a4,a3,a2,a1,a0],
            'provenance': {'model_revision': MODEL_REVISION, 'method': 'quartic determinant + scaled simultaneous complex pole solve',
                           'pole_units':'1/s (real), rad/s (imaginary)', 'damping_ratio_units':'dimensionless'}}


def _as_scenario(payload: Any):
    return scenario_from_mapping(payload)


def _delta(a: float | None, b: float | None) -> dict[str, float | None]:
    if a is None or b is None:
        return {'absolute':None,'percent':None}
    return {'absolute': b-a, 'percent': None if abs(a)<1e-12 else (b-a)*100/abs(a)}


def compare(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {'baseline','variant'}:
        raise ValueError('comparison requires exactly baseline and variant scenario objects')
    v0,r0,s0 = _as_scenario(payload['baseline'])
    v1,r1,s1 = _as_scenario(payload['variant'])
    if s0 != s1:
        raise ValueError('comparison requires identical integration settings and time grid')
    if round(s0.duration_s/s0.dt_s)>7500:
        raise ValueError('comparison limit is 7,500 time steps per scenario')
    a,b = simulate(v0,r0,s0), simulate(v1,r1,s1)
    controlled = r0==r1
    return {'kind':'comparison', 'schema_version':'2.0',
            'baseline':a, 'variant':b,
            'metric_deltas':{k:_delta(a['metrics'][k], b['metrics'][k]) for k in METRICS},
            'same_road_input': controlled,
            'caution': ('Identical road and time grid: response differences are associated with vehicle parameter differences in this mathematical model.'
                        if controlled else 'Road input differs: response changes cannot be attributed solely to vehicle design.'),
            'provenance':{'baseline':provenance(v0,r0,s0,'baseline'), 'variant':provenance(v1,r1,s1,'variant')}}


def _finite_number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value,(int,float)) or not isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    return float(value)


def sweep(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload,dict) or set(payload)!={'scenario','parameter','start','stop','count'}:
        raise ValueError('sweep requires exactly scenario, parameter, start, stop, count')
    v,r,s = _as_scenario(payload['scenario'])
    field = payload['parameter']
    if not isinstance(field,str) or field not in BOUNDS:
        raise ValueError('sweep parameter must be a recognized vehicle parameter')
    start, stop = _finite_number(payload['start'],'start'), _finite_number(payload['stop'],'stop')
    minimum,maximum = BOUNDS[field]
    if not minimum <= start < stop <= maximum:
        raise ValueError(f'sweep requires {minimum} <= start < stop <= {maximum}')
    n = payload['count']
    if isinstance(n,bool) or not isinstance(n,int) or not 3<=n<=11:
        raise ValueError('count must be an integer between 3 and 11')
    steps = round(s.duration_s/s.dt_s)
    if steps * (n+1)>75000:
        raise ValueError('sweep computational budget exceeded: max 75,000 integration steps')
    reference = simulate(v,r,s)
    rows=[]
    for i in range(n):
        value=start+(stop-start)*i/(n-1)
        test_vehicle=replace(v,**{field:value})
        metrics=simulate(test_vehicle,r,s)['metrics']
        rows.append({'parameter_value':value,'metrics':{key:metrics[key] for key in METRICS},
                     'rms_delta_percent':_delta(reference['metrics']['body_acceleration_rms_m_s2'],metrics['body_acceleration_rms_m_s2'])['percent']})
    return {'kind':'sweep','schema_version':'2.0','parameter':field,
            'units':{'sprung_mass_kg':'kg','unsprung_mass_kg':'kg',
                     'suspension_stiffness_n_m':'N/m','damping_n_s_m':'N*s/m',
                     'tire_stiffness_n_m':'N/m'}[field],
            'reference_parameter_value':getattr(v,field),
            'reference_metrics':{k:reference['metrics'][k] for k in METRICS},
            'points':rows, 'interpretation':'One variable varied at a time; other vehicle, road and solver inputs fixed. Metrics are sample-based; the sweep does not optimize or certify performance.',
            'provenance':provenance(v,r,s,'one-at-a-time-parameter-sweep')}


def _interp(times: list[float], values: list[float], t: float) -> float:
    # O(1) uniform grid indexing; protect last endpoint.
    pos = min(len(times)-1,max(0.0,t / times[-1] * (len(times)-1)))
    i=min(len(times)-2,int(pos))
    weight=pos-i
    return values[i]*(1-weight)+values[i+1]*weight


def convergence(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload,dict) or set(payload)!={'scenario','steps_s'}:
        raise ValueError('convergence requires exactly scenario and steps_s')
    v,r,s = _as_scenario(payload['scenario'])
    steps = payload['steps_s']
    if not isinstance(steps,list) or not 3<=len(steps)<=5:
        raise ValueError('steps_s must be a list with 3 to 5 time steps')
    values=[_finite_number(x,'step') for x in steps]
    if not all(0.001<=dt<=0.02 for dt in values) or len(set(values))!=len(values) or values!=sorted(values,reverse=True):
        raise ValueError('steps must be distinct, descending, between 0.001 and 0.02 s')
    if sum(round(s.duration_s/dt) for dt in values)>35000:
        raise ValueError('convergence computational budget exceeded (35,000 steps)')
    simulations=[simulate(v,r,replace(s,dt_s=dt)) for dt in values]
    ref=simulations[-1]
    tracks=('sprung_m','unsprung_m','sprung_velocity_m_s','unsprung_velocity_m_s')
    results=[]
    for result in simulations:
        errors={}
        for channel in tracks:
            if result is ref:
                errors[channel]=0.0
                continue
            coarse=result['channels'][channel]
            fine=ref['channels'][channel]
            fine_times=ref['channels']['time_s']
            errors[channel]=max(abs(val-_interp(fine_times,fine,t)) for val,t in zip(coarse,result['channels']['time_s']))
        results.append({'requested_dt_s':values[len(results)], 'actual_dt_s':result['settings']['dt_s'],
                        'samples':result['samples'],
                        'max_abs_state_error_vs_finest':errors,
                        'body_acceleration_rms_m_s2':result['metrics']['body_acceleration_rms_m_s2'],
                        'rms_difference_vs_finest_m_s2':result['metrics']['body_acceleration_rms_m_s2']-ref['metrics']['body_acceleration_rms_m_s2']})
    smooth=('sine','flat')
    return {'kind':'convergence','schema_version':'2.0','results':results,
            'reference':'finest tested fixed RK4 step; not an exact or independent solution',
            'interpretation':('Smooth road between onset events: errors may show RK4 refinement behavior, but this is not a proof of stability.'
                if r.kind in smooth else 'Bump onset/end and step onset create derivative/discontinuity events; apparent observed convergence order may be reduced or non-monotonic when steps straddle boundaries. Numerical convergence is not a proof of physical accuracy.'),
            'provenance':provenance(v,r,s,'fixed-step-sensitivity')}


def analysis_request(kind: str, payload: Any) -> dict[str,Any]:
    if kind=='modal':
        if not isinstance(payload,dict) or set(payload)!={'vehicle'}:
            raise ValueError('modal request requires exactly vehicle')
        v,_,_ = scenario_from_mapping({'vehicle':payload['vehicle']})
        return damped_modes(v)
    if kind=='compare':return compare(payload)
    if kind=='sweep':return sweep(payload)
    if kind=='convergence':return convergence(payload)
    raise ValueError('unknown analysis')
