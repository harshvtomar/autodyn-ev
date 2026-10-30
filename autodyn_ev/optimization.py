"""Chat 8 deterministic, bounded trade-off exploration of unchanged ride simulators.

No new dynamics and no vehicle-validated optimum. Two objectives, no hidden score.
"""
from dataclasses import asdict, replace
from itertools import product
from math import isfinite
from typing import Any

from .physics import Road, SimulationSettings, Vehicle
from .simulation import scenario_from_mapping, simulate
from .halfcar import HalfCarVehicle, scenario_half_from_mapping, simulate_half
from .ride import _window

RELEASE = '0.8.0'
SCHEMA = 'optimization-study-1.0'
FIELDS = {
    'quarter': {
        'suspension_stiffness_n_m': (5000.0, 120000.0, 'N/m'),
        'damping_n_s_m': (0.0, 12000.0, 'N·s/m'),
    },
    'half': {
        'front_spring_n_m': (5000.0, 120000.0, 'N/m'),
        'rear_spring_n_m': (5000.0, 120000.0, 'N/m'),
        'front_damping_n_s_m': (0.0, 12000.0, 'N·s/m'),
        'rear_damping_n_s_m': (0.0, 12000.0, 'N·s/m'),
    },
}
CONSTRAINTS = ('max_body_acceleration_rms_m_s2', 'max_suspension_travel_peak_to_peak_mm',
               'max_tire_deflection_peak_abs_mm')
UNITS = {
    'body_acceleration_rms_m_s2': 'm/s²',
    'suspension_travel_peak_to_peak_mm': 'mm',
    'tire_deflection_peak_abs_mm': 'mm',
    'front_suspension_travel_peak_to_peak_mm': 'mm',
    'rear_suspension_travel_peak_to_peak_mm': 'mm',
    'front_tire_deflection_peak_abs_mm': 'mm',
    'rear_tire_deflection_peak_abs_mm': 'mm',
    'body_pitch_peak_deg': 'degrees',
}


def _finite_number(value: Any, name: str, lo: float, hi: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    if not lo <= value <= hi:
        raise ValueError(f'{name} must be between {lo} and {hi}')
    return float(value)


def _grid(center: float, lo: float, hi: float) -> list[float]:
    lower = max(lo, center*0.8)
    upper = min(hi, center*1.2)
    values = [lower + (upper-lower)*i/6 for i in range(7)]
    if len({round(v, 10) for v in values}) != 7:
        raise ValueError('parameter span collapses to duplicate grid points; select a positive nonzero baseline')
    return values


def _metrics(raw: dict, model: str) -> dict[str, float]:
    ch = raw['channels']; time = ch['time_s']; end = time[-1]
    acc = 'sprung_acceleration_m_s2' if model == 'quarter' else 'body_heave_acceleration_m_s2'
    result = {'body_acceleration_rms_m_s2': _window(time, ch[acc], 0, end)['rms']}
    if model == 'quarter':
        travel = ch['suspension_travel_m']; tire = ch['tire_deflection_m']
        result.update(suspension_travel_peak_to_peak_mm=1000*(max(travel)-min(travel)),
                      tire_deflection_peak_abs_mm=1000*max(abs(x) for x in tire))
    else:
        for name in ('front', 'rear'):
            travel = ch[f'{name}_suspension_travel_m']; tire = ch[f'{name}_tire_deflection_m']
            result[f'{name}_suspension_travel_peak_to_peak_mm'] = 1000*(max(travel)-min(travel))
            result[f'{name}_tire_deflection_peak_abs_mm'] = 1000*max(abs(x) for x in tire)
        result['suspension_travel_peak_to_peak_mm'] = max(result[f'{name}_suspension_travel_peak_to_peak_mm'] for name in ('front','rear'))
        result['tire_deflection_peak_abs_mm'] = max(result[f'{name}_tire_deflection_peak_abs_mm'] for name in ('front','rear'))
        result['body_pitch_peak_deg'] = max(abs(x) for x in ch['body_pitch_rad'])*180/3.141592653589793
    return result


def _pareto(candidates: list[dict]) -> list[int]:
    """IDs of feasible nondominated cases, minimizing RMS and peak-to-peak travel."""
    feasible = [c for c in candidates if c['feasible']]
    objectives = ('body_acceleration_rms_m_s2', 'suspension_travel_peak_to_peak_mm')
    return [p['id'] for p in feasible if not any(
        all(q['metrics'][k] <= p['metrics'][k] for k in objectives)
        and any(q['metrics'][k] < p['metrics'][k] for k in objectives)
        for q in feasible if q['id'] != p['id'])]


def optimization_request(body: Any) -> dict:
    if not isinstance(body, dict):
        raise ValueError('optimization request must be a JSON object')
    accepted = {'model','vehicle','road','settings','parameters','points_per_axis','constraints'}
    if set(body)-accepted:
        raise ValueError(f'unknown optimization fields: {sorted(set(body)-accepted)}')
    model = body.get('model', 'quarter')
    if model not in FIELDS:
        raise ValueError('model must be quarter or half')
    params = body.get('parameters', ['damping_n_s_m'] if model=='quarter' else ['front_damping_n_s_m'])
    if not isinstance(params, list) or not 1 <= len(params) <= 2 or len(set(map(str,params))) != len(params):
        raise ValueError('parameters must be a unique list containing one or two names')
    if any(not isinstance(p,str) or p not in FIELDS[model] for p in params):
        raise ValueError('selected parameters are not supported for this model')
    points = body.get('points_per_axis', 7)
    if type(points) is not int or points != 7:
        raise ValueError('points_per_axis must be exactly 7 (maximum 49 candidates)')
    constraints = body.get('constraints', {})
    if not isinstance(constraints,dict) or set(constraints)-set(CONSTRAINTS):
        raise ValueError('constraints must contain only supported maximum threshold fields')
    limits = {}
    for key,value in constraints.items():
        if value is not None:
            limits[key] = _finite_number(value,key,0.0,1e5)
    mapping = {k:body[k] for k in ('vehicle','road','settings') if k in body}
    if model=='quarter':
        vehicle,road,settings = scenario_from_mapping(mapping)
        simulate_fn = simulate
    else:
        vehicle,road,settings = scenario_half_from_mapping(mapping)
        simulate_fn = simulate_half
    if round(settings.duration_s/settings.dt_s) > 3000:
        raise ValueError('optimization duration/dt exceeds 3000 steps per case; use a coarser step or shorter duration')
    base = simulate_fn(vehicle, road, settings)
    baseline_metrics = _metrics(base,model)
    grids = {p:_grid(float(getattr(vehicle,p)),*FIELDS[model][p][:2]) for p in params}
    cases = []
    for idx,values in enumerate(product(*(grids[p] for p in params))):
        updates = dict(zip(params,values))
        candidate_vehicle = replace(vehicle,**updates)
        raw = simulate_fn(candidate_vehicle,road,settings)
        metrics = _metrics(raw,model)
        failed = [key for key,limit in limits.items()
                  if metrics[key.removeprefix('max_')] > limit]
        cases.append({'id':idx+1,'parameters':updates,'metrics':metrics,
                      'feasible':not failed,'failed_constraints':failed})
    pareto = _pareto(cases)
    feasible = [c for c in cases if c['feasible']]
    selected = min(feasible, key=lambda c:(c['metrics']['body_acceleration_rms_m_s2'],
                                         c['metrics']['suspension_travel_peak_to_peak_mm'],
                                         c['metrics']['tire_deflection_peak_abs_mm'],c['id'])) if feasible else None
    return {
        'schema_version': SCHEMA,'application_version':RELEASE,'study_type':'bounded-deterministic-parameter-grid',
        'model':model,'baseline':{'vehicle':asdict(vehicle),'metrics':baseline_metrics},
        'scenario':{'road':asdict(road),'settings':{'duration_s':settings.duration_s,'dt_s':base['settings']['dt_s']},
                    'initial_state':'zero static-equilibrium-relative'},
        'grid':{'parameters':params,'points_per_axis':points,'values':grids,
                'hard_cap':49,'run_count':len(cases),'bounds':{p:{'min':FIELDS[model][p][0],
                   'max':FIELDS[model][p][1],'unit':FIELDS[model][p][2]} for p in params}},
        'constraints':limits,'objectives':[
            {'key':'body_acceleration_rms_m_s2','direction':'min','unit':'m/s²',
             'method':'trapezoidal time-weighted unweighted RMS'},
            {'key':'suspension_travel_peak_to_peak_mm','direction':'min','unit':'mm',
             'method':'sampled peak-to-peak; half-car uses worse of front and rear'}],
        'units':UNITS,'candidates':cases,'feasible_count':len(feasible),'pareto_ids':pareto,
        'selected_id': selected['id'] if selected else None,
        'selection_rule':'Among feasible cases: smallest RMS, then smallest peak-to-peak travel, then smallest tire proxy, then grid ID',
        'warnings':[
            'Discrete fixed-grid comparison only. No globally optimal or physically validated design is claimed.',
            'Unweighted acceleration RMS is not an ISO 2631 comfort certification.',
            'Tire deflection is a linear always-contact force-variation proxy, not a real grip or contact measurement.',
            'No combined braking, regeneration, suspension, vehicle safety or battery range score.',
            'All cases use identical road forcing, duration, zero initial conditions and integration settings.',
        ],
    }
