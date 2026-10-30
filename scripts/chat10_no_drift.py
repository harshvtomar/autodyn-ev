"""Compare exact authoritative physics outputs from accepted pristine Chat 9 and final Chat 10.

Usage: python3 scripts/chat9_no_drift.py /path/to/pristine-chat9 --out docs/chat9_no_drift.json
Uses a clean subprocess for each source tree to avoid Python module caching.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

COLLECT='''
import json
from autodyn_ev.simulation import simulate,scenario_from_mapping
from autodyn_ev.halfcar import simulate_half,scenario_half_from_mapping
from autodyn_ev.braking import simulate_braking, scenario_from_mapping as bm
from autodyn_ev.regen import simulate_regen, scenario_from_mapping as rm
cases=[
 ('quarter',{}),
 ('quarter',{'road':{'kind':'flat'}}),
 ('quarter',{'vehicle':{'damping_n_s_m':2300},'road':{'kind':'sine'}}),
 ('quarter',{'road':{'kind':'pothole'},'settings':{'dt_s':.01}}),
 ('half',{}),
 ('half',{'road':{'kind':'double_bump'},'vehicle':{'pitch_inertia_kg_m2':2000}}),
 ('half',{'road':{'kind':'sine'},'settings':{'dt_s':.01}}),
 ('braking',{}),
 ('braking',{'scenario':{'profile':'ramp','ramp_s':1}}),
 ('braking',{'scenario':{'friction_coefficient':.3}}),
 ('regen',{}),
 ('regen',{'scenario':{'motor_max_torque_nm':0}}),
 ('regen',{'scenario':{'battery_charge_limit_w':3000}}),
 ('regen',{'scenario':{'profile':'ramp','ramp_s':1}}),
]
result=[]
for model,scenario in cases:
 if model=='quarter': output=simulate(*scenario_from_mapping(scenario))
 elif model=='half': output=simulate_half(*scenario_half_from_mapping(scenario))
 elif model=='braking': output=simulate_braking(bm(scenario))
 else: output=simulate_regen(rm(scenario))
 payload=json.dumps(output,sort_keys=True,separators=(',',':'),allow_nan=False)
 result.append({'model':model,'scenario':scenario,'payload':payload})
print(json.dumps(result))
'''


def collect(root):
    proc=subprocess.run([sys.executable,'-c',COLLECT],cwd=root,capture_output=True,text=True,timeout=90)
    if proc.returncode:raise RuntimeError(proc.stderr[-2000:])
    return json.loads(proc.stdout)


def main():
    p=argparse.ArgumentParser();p.add_argument('pristine_baseline');p.add_argument('--out',default='docs/CHAT10_NO_DRIFT.json');args=p.parse_args()
    root=Path(__file__).resolve().parents[1];base=Path(args.pristine_baseline).resolve()
    before=collect(base);after=collect(root)
    entries=[]
    for a,b in zip(before,after):
        same=(a['model']==b['model'] and a['scenario']==b['scenario'] and a['payload']==b['payload'])
        entries.append({'model':a['model'],'scenario':a['scenario'],'exact_json_identical':same,
                        'bytes_before':len(a['payload'].encode()),'bytes_after':len(b['payload'].encode()),
                        'before_sha256':hashlib.sha256(a['payload'].encode()).hexdigest(),
                        'after_sha256':hashlib.sha256(b['payload'].encode()).hexdigest()})
    if len(entries)!=14 or not all(x['exact_json_identical'] for x in entries):
        raise AssertionError('authoritative numerical drift or missing output detected')
    result={'baseline':'accepted v0.9.0','new_release':'Chat 10 v1.0.0',
            'comparison':'exact independently executed sorted serialized output JSON',
            'count':len(entries),'identical_count':sum(x['exact_json_identical'] for x in entries),
            'cases':entries}
    output=Path(args.out);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2)+'\n');print(f"No drift: {len(entries)}/{len(entries)} exact output matches")

if __name__=='__main__':main()
