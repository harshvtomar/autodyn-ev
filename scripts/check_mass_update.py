"""Check actual local server mass response independently of any browser UI.

  python3 scripts/check_mass_update.py --port 8775
"""
import argparse
import json
from urllib.request import Request, urlopen


def query(port, mass):
    payload = {"vehicle": {"sprung_mass_kg":mass,"unsprung_mass_kg":40,
                           "suspension_stiffness_n_m":18000,"damping_n_s_m":1500,
                           "tire_stiffness_n_m":190000},
               "road":{"kind":"bump","height_m":0.06,"start_s":0.5,
                       "bump_length_m":1.5,"speed_m_s":5.0},
               "settings":{"duration_s":5.0,"dt_s":0.005}}
    req=Request(f"http://127.0.0.1:{port}/api/simulate",data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type":"application/json"},method="POST")
    with urlopen(req,timeout=20) as response: data=json.load(response)
    if data['vehicle']['sprung_mass_kg']!=mass:
        raise AssertionError(f"Requested {mass} kg, returned {data['vehicle']['sprung_mass_kg']} kg")
    return float(data['metrics']['body_acceleration_rms_m_s2'])

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8775)
    port=parser.parse_args().port
    readings={mass:query(port,mass) for mass in (300,500,300)}
    for mass in (300,500):print(f'{mass} kg → {readings[mass]:.6f} m/s²')
    assert abs(readings[300]-0.9060817384319384)<1e-8
    assert abs(readings[500]-0.5556923125715003)<1e-8
    print('PASS: backend changes acceleration with mass')
