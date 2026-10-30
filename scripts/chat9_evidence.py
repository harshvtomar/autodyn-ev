"""Reproduce Chat 9 evidence from unchanged accepted model code (stdlib only).

Run from repository root: python3 scripts/chat9_evidence.py --out docs/chat9_evidence
This script does not modify physics modules, start the browser, or require SciPy.
"""
import argparse
import json
import hashlib
from dataclasses import asdict, replace
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from autodyn_ev.physics import Road, SimulationSettings, Vehicle
from autodyn_ev.halfcar import HalfCarVehicle, simulate_half, derivatives_half, ZERO_STATE as HALF_ZERO
from autodyn_ev.simulation import simulate
from autodyn_ev.braking import BrakingScenario, simulate_braking
from autodyn_ev.regen import RegenScenario, simulate_regen
from autodyn_ev.optimization import optimization_request
from autodyn_ev.verification import (independent_pareto_ids, verify_study,
    independent_trapezoidal_rms, constant_braking_reference, max_abs_delta)


def fingerprint(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',',':'), allow_nan=False).encode()).hexdigest()


def aligned_comparison(model, road, duration=3.0):
    run=simulate if model=='quarter' else simulate_half
    vehicle=Vehicle() if model=='quarter' else HalfCarVehicle()
    results={str(dt):run(vehicle, road, SimulationSettings(duration_s=duration, dt_s=dt))
             for dt in (0.01,0.005,0.0025)}
    ch='sprung_m' if model=='quarter' else 'body_heave_m'
    finest=results['0.0025']['channels'][ch]
    diffs={str(dt):max_abs_delta(results[str(dt)]['channels'][ch],finest[::int(round(dt/.0025))])
           for dt in (.01,.005)}
    return {'model':model,'road_kind':road.kind,'duration_s':duration,'channel':ch,
            'reference':'same RK4 implementation, 0.0025 s numerical reference (not ground truth)',
            'max_abs_difference_m':diffs,
            'fine_response_sha256':fingerprint(results['0.0025']),
            'limitation':'Event boundary alignment, discontinuities and sampling can change observed error order'}


def make_evidence():
    from math import sqrt
    cases=[]
    # Force limiting cases through the full solver, using conventional fixed numerical reference.
    for mode in ('quarter','half'):
        runner=simulate if mode=='quarter' else simulate_half
        v=Vehicle() if mode=='quarter' else HalfCarVehicle()
        r=Road(kind='flat')
        raw=runner(v,r,SimulationSettings(duration_s=2,dt_s=.005))
        acc='sprung_acceleration_m_s2' if mode=='quarter' else 'body_heave_acceleration_m_s2'
        cases.append({'id':f'{mode}-flat-equilibrium','passed':max(map(abs,raw['channels'][acc]))==0,
                      'evidence':'zero initial equilibrium + flat road gives exactly zero acceleration'})
    for mode in ('quarter','half'):
        for road in (Road(kind='sine',start_s=0,height_m=.01),Road(kind='bump'),Road(kind='pothole')):
            rows=aligned_comparison(mode,road)
            rows['case_id']=f'{mode}-{road.kind}-refinement'
            cases.append(rows)
    for profile in ('constant','ramp'):
        braking=simulate_braking(BrakingScenario(profile=profile,dt_s=.02))
        cases.append({'id':f'braking-{profile}',
            'stopped':braking['metrics']['stopped'], 'distance_m':braking['metrics']['distance_travelled_m'],
            'end_speed_m_s':braking['metrics']['final_speed_m_s']})
    br=simulate_braking(BrakingScenario())
    expected=constant_braking_reference(1200,20,5,.8)
    cases.append({'id':'braking-closed-form-constant','predicted':expected,
                  'reported':(br['metrics']['stopping_time_s'],br['metrics']['stopping_distance_m']),
                  'passed':all(abs(x-y)<1e-8 for x,y in zip(expected,(br['metrics']['stopping_time_s'],br['metrics']['stopping_distance_m'])))})
    regen=simulate_regen(RegenScenario())
    cases.append({'id':'regen-default', 'energy_metrics':{k:v for k,v in regen['metrics'].items() if 'energy' in k or 'fraction' in k},
                  'result_sha256':fingerprint(regen)})
    studies=[]
    for model in ('quarter','half'):
        base=['damping_n_s_m','suspension_stiffness_n_m'] if model=='quarter' else ['front_damping_n_s_m','rear_spring_n_m']
        for kind,params,constraints in (
            ('seven',[base[0]],{}),
            ('forty_nine',base,{}),
            ('none_feasible',[base[0]],{'max_body_acceleration_rms_m_s2':0.0})):
            request={'model':model,'parameters':params,'constraints':constraints,
                     'settings':{'duration_s':2,'dt_s':.01}}
            first=optimization_request(request)
            second=optimization_request(request)
            assert fingerprint(first)==fingerprint(second)
            details=verify_study(first)
            studies.append({'id':f'{model}-{kind}',**details,'exact_replay_sha256':fingerprint(first),
                            'consistent_replay':True})
    # Probe sensitivity to road surface and discretization without claiming robust rank invariance.
    rankings=[]
    for road in ('bump','sine','pothole'):
        for dt in (.01,.005):
            sample=optimization_request({'model':'quarter','parameters':['damping_n_s_m'],
                'road':{'kind':road},'settings':{'duration_s':3,'dt_s':dt}})
            rankings.append({'road':road,'dt_s':dt,'selected_id':sample['selected_id'],
               'pareto_ids':sample['pareto_ids'],'feasible_count':sample['feasible_count']})
    return {'schema':'chat9-evidence-1.0','software_release':'0.9.0',
            'evidence_type':'simulation and mathematical reference, not physical calibration',
            'cases':cases,'optimization_studies':studies,'rank_sensitivity':rankings,
            'limitations':['The finest RK4 step is a numerical reference, not a measured truth.',
                           'Braking ignores ABS, aerodynamic drag, and real road friction dynamics.',
                           'Tire-deflection proxy is not a tire-contact or road-safety measurement.',
                           'No ISO 2631 certification, globally optimal design or measured EV performance.']}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='docs/chat9_evidence');args=parser.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    result=make_evidence()
    (out/'engineering_matrix.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    lines=['# Chat 9 reproducible numerical verification matrix','','Generated by standard-library `scripts/chat9_evidence.py`.','',
           '**Not physical vehicle validation.**','','## Engineering reference cases','']
    for case in result['cases']:
        label=case.get('case_id',case.get('id'))
        lines.append(f'- **{label}**: {json.dumps({k:v for k,v in case.items() if k not in ("fine_response_sha256","result_sha256")},default=str)}')
    lines+=['','## Optimization replay and constraint checks','']
    for study in result['optimization_studies']:
        lines.append(f'- **{study["id"]}**: {study["case_count"]} candidates, {study["feasible_count"]} feasible, {study["pareto_count"]} Pareto; selected {study["selected_id"]}.')
    lines+=['','## Road and time-step sensitivity (not a guarantee of robust selection)','']
    for item in result['rank_sensitivity']:
        lines.append(f'- **{item["road"]}**, dt={item["dt_s"]} s: selected case {item["selected_id"]}, Pareto {item["pareto_ids"]}.')
    lines+=['','## Limitations','']+[f'- {x}' for x in result['limitations']]
    (out/'engineering_matrix.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'case_count':len(result['cases']),'grid_studies':len(result['optimization_studies']),
                       'sensitivity_cases':len(result['rank_sensitivity']), 'result_sha256':fingerprint(result)},indent=2))

if __name__=='__main__': main()
