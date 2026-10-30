"""Chat 6 regression and mathematical checks; deliberately do not change inherited tests."""
import json
import math
import threading
import unittest
from dataclasses import replace, asdict
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from autodyn_ev.braking import BrakingScenario, GRAVITY, simulate_braking
from autodyn_ev.regen import RegenScenario, allocate, scenario_from_mapping, simulate_regen
from autodyn_ev.server import Handler


def close(a,b,absolute=1e-7,relative=1e-9):
    return abs(a-b) <= max(absolute,relative*max(abs(a),abs(b)))


class TestRegenMath(unittest.TestCase):
    def setUp(self): self.s=RegenScenario()

    def test_defaults_valid(self): self.s.validate()
    def test_braking_stopping_unchanged(self):
        r=simulate_regen(self.s); b=simulate_braking(BrakingScenario())
        for key in b['channels']: self.assertEqual(b['channels'][key],r['channels'][key])
        self.assertEqual(r['metrics']['stopping_time_s'],4.0)
        self.assertAlmostEqual(r['metrics']['stopping_distance_m'],40.0,places=9)
    def test_initial_kinetic_budget(self): self.assertEqual(simulate_regen(self.s)['metrics']['initial_kinetic_energy_j'],240000.)
    def test_energy_conservation_complete(self):
        m=simulate_regen(self.s)['metrics'];self.assertTrue(close(m['kinetic_energy_reduction_j'],m['battery_energy_stored_j']+m['conversion_loss_j']+m['friction_dissipation_j']))
    def test_energy_conservation_incomplete(self):
        r=simulate_regen(replace(self.s,duration_s=1));m=r['metrics'];self.assertFalse(m['stopped']);self.assertTrue(close(m['kinetic_energy_reduction_j'],m['battery_energy_stored_j']+m['conversion_loss_j']+m['friction_dissipation_j']))
    def test_energy_conservation_ramp(self):
        for dur in [1,4,20]:
            r=simulate_regen(replace(self.s,profile='ramp',ramp_s=2,duration_s=dur));m=r['metrics']
            self.assertAlmostEqual(m['energy_balance_residual_j'],0,places=6)
    def test_zero_torque_no_regen(self): self.assertEqual(simulate_regen(replace(self.s,motor_max_torque_nm=0))['metrics']['battery_energy_stored_j'],0)
    def test_zero_motor_power_no_regen(self): self.assertEqual(simulate_regen(replace(self.s,motor_max_mech_power_w=0))['metrics']['battery_energy_stored_j'],0)
    def test_zero_battery_power_no_regen(self): self.assertEqual(simulate_regen(replace(self.s,battery_charge_limit_w=0))['metrics']['battery_energy_stored_j'],0)
    def test_zero_efficiency_no_regen(self): self.assertEqual(simulate_regen(replace(self.s,conversion_efficiency=0))['metrics']['battery_energy_stored_j'],0)
    def test_full_regen_ideal(self):
        s=replace(self.s,motor_max_torque_nm=1500,gear_ratio=30,driven_wheel_radius_m=.1,motor_max_mech_power_w=400000,battery_charge_limit_w=400000,conversion_efficiency=1)
        m=simulate_regen(s)['metrics'];self.assertAlmostEqual(m['battery_energy_stored_j'],240000.,places=2);self.assertAlmostEqual(m['friction_dissipation_j'],0,places=2)
    def test_full_regen_with_losses(self):
        s=replace(self.s,motor_max_torque_nm=1500,gear_ratio=30,driven_wheel_radius_m=.1,motor_max_mech_power_w=400000,battery_charge_limit_w=400000,conversion_efficiency=.75)
        m=simulate_regen(s)['metrics'];self.assertAlmostEqual(m['battery_energy_stored_j'],180000.,places=2);self.assertAlmostEqual(m['conversion_loss_j'],60000.,places=2)
    def test_grip_limit(self):
        s=replace(self.s,friction_coefficient=.3,demanded_decel_m_s2=7)
        r=simulate_regen(s);c=r['channels'];self.assertTrue(r['metrics']['traction_limited'])
        for f in c['actual_brake_force_n']: self.assertLessEqual(f,s.mass_kg*s.friction_coefficient*GRAVITY+1e-8)
        for f,g,h in zip(c['actual_brake_force_n'],c['regen_force_n'],c['friction_force_n']):self.assertTrue(close(f,g+h))
    def test_torque_limit(self):
        s=replace(self.s,motor_max_torque_nm=25)
        r=simulate_regen(s)
        self.assertTrue(all(f<=25*s.gear_ratio/s.driven_wheel_radius_m+1e-8 for f in r['channels']['regen_force_n']))
    def test_motor_power_limit(self):
        r=simulate_regen(replace(self.s,motor_max_mech_power_w=4000));self.assertLessEqual(r['metrics']['peak_motor_mechanical_power_w'],4000+1e-9)
    def test_charge_power_limit(self):
        r=simulate_regen(replace(self.s,battery_charge_limit_w=3000));self.assertLessEqual(r['metrics']['peak_battery_charge_power_w'],3000+1e-9)
    def test_no_power_after_stop(self):
        r=simulate_regen(self.s);self.assertEqual(r['channels']['battery_charge_power_w'][-1],0.0);self.assertEqual(r['channels']['regen_force_n'][-1],0.)
    def test_no_negative_speed(self): self.assertTrue(all(x>=0 for x in simulate_regen(self.s)['channels']['speed_m_s']))
    def test_monotonic_speed(self):
        v=simulate_regen(self.s)['channels']['speed_m_s'];self.assertTrue(all(y<=x+1e-11 for x,y in zip(v,v[1:])))
    def test_monotonic_distance(self):
        d=simulate_regen(self.s)['channels']['distance_m'];self.assertTrue(all(y>=x-1e-11 for x,y in zip(d,d[1:])))
    def test_monotonic_cumulative_energy(self):
        c=simulate_regen(self.s)['channels'];
        for key in ['cumulative_motor_energy_j','cumulative_battery_energy_j','cumulative_friction_energy_j','cumulative_conversion_loss_j']:
            a=c[key];self.assertTrue(all(y>=x-1e-8 for x,y in zip(a,a[1:])),key)
    def test_channel_shapes(self):
        r=simulate_regen(self.s);self.assertEqual({len(v) for v in r['channels'].values()},{r['samples']})
    def test_no_regen_below_cutoff(self):
        r=simulate_regen(replace(self.s,low_speed_cutoff_m_s=5));c=r['channels'];
        for v,f in zip(c['speed_m_s'],c['regen_force_n']):
            if v<5:self.assertEqual(f,0)
    def test_cutoff_reduces_recovery(self):
        base=simulate_regen(self.s);cut=simulate_regen(replace(self.s,low_speed_cutoff_m_s=5));self.assertLess(cut['metrics']['battery_energy_stored_j'],base['metrics']['battery_energy_stored_j'])
    def test_zero_speed(self):
        r=simulate_regen(replace(self.s,initial_speed_m_s=0));m=r['metrics'];self.assertTrue(m['stopped']);self.assertEqual(m['battery_energy_stored_j'],0);self.assertEqual(r['samples'],1)
    def test_zero_demand(self):
        r=simulate_regen(replace(self.s,demanded_decel_m_s2=0,duration_s=2));m=r['metrics'];self.assertFalse(m['stopped']);self.assertEqual(m['battery_energy_stored_j'],0)
    def test_energy_below_kinetic_drop(self):
        for s in [self.s,replace(self.s,duration_s=1),replace(self.s,profile='ramp',ramp_s=5)]:
            m=simulate_regen(s)['metrics'];self.assertLessEqual(m['battery_energy_stored_j'],m['kinetic_energy_reduction_j']+1e-8)
    def test_charge_energy_below_power_time(self):
        s=replace(self.s,battery_charge_limit_w=1700);r=simulate_regen(s);self.assertLessEqual(r['metrics']['battery_energy_stored_j'],1700*r['metrics']['elapsed_s']+1e-3)
    def test_load_conservation(self):
        c=simulate_regen(self.s)['channels'];self.assertTrue(all(close(f+r,self.s.mass_kg*GRAVITY) for f,r in zip(c['front_normal_n'],c['rear_normal_n'])))
    def test_json_serializable_finite(self): json.dumps(simulate_regen(self.s),allow_nan=False)
    def test_provenance_keys(self):
        r=simulate_regen(self.s);self.assertEqual(r['version'],'0.6.0');self.assertIn('battery',r['provenance']);self.assertIn('regen_force_n',r['provenance']['units'])
    def test_incomplete_warning(self):self.assertTrue(any('did not reach' in s for s in simulate_regen(replace(self.s,duration_s=1))['warnings']))
    def test_ramp_does_not_change_legacy(self):
        s=replace(self.s,profile='ramp',ramp_s=3)
        r=simulate_regen(s);b=simulate_braking(BrakingScenario(**{k:v for k,v in asdict(s).items() if k in BrakingScenario.__dataclass_fields__}))
        self.assertEqual(r['channels']['speed_m_s'],b['channels']['speed_m_s'])
    def test_constant_total_reduction(self): self.assertTrue(close(simulate_regen(self.s)['metrics']['kinetic_energy_reduction_j'],240000))
    def test_increase_efficiency_increases_storage(self):
        a=simulate_regen(replace(self.s,conversion_efficiency=.5))['metrics']['battery_energy_stored_j'];b=simulate_regen(replace(self.s,conversion_efficiency=.9))['metrics']['battery_energy_stored_j'];self.assertGreater(b,a)
    def test_zero_regen_means_all_friction(self):
        r=simulate_regen(replace(self.s,battery_charge_limit_w=0));m=r['metrics'];self.assertAlmostEqual(m['friction_dissipation_j'],m['kinetic_energy_reduction_j'],places=6)
    def test_small_time_step_consistency(self):
        a=simulate_regen(replace(self.s,dt_s=.04))['metrics']['battery_energy_stored_j'];b=simulate_regen(replace(self.s,dt_s=.01))['metrics']['battery_energy_stored_j'];self.assertLess(abs(a-b),.3)
    def test_force_split_nonnegative(self):
        c=simulate_regen(self.s)['channels'];self.assertTrue(all(x>=0 for x in c['regen_force_n']+c['friction_force_n']))
    def test_very_low_speed(self):
        s=replace(self.s,initial_speed_m_s=.001);r=simulate_regen(s);self.assertTrue(r['metrics']['stopped']);self.assertLess(r['metrics']['battery_energy_stored_j'],.01)

class TestMappingAndValidation(unittest.TestCase):
    def test_default_mapping(self):self.assertEqual(scenario_from_mapping({}),RegenScenario())
    def test_nested_mapping(self):self.assertEqual(scenario_from_mapping({'scenario':{'motor_max_torque_nm':0}}).motor_max_torque_nm,0)
    def test_unknown_field_rejected(self):
        with self.assertRaisesRegex(ValueError,'unknown'):scenario_from_mapping({'scenario':{'invented':1}})
    def test_non_object_rejected(self):
        for x in [[],None,2,'str']:
            with self.subTest(x=x),self.assertRaises(ValueError):scenario_from_mapping(x)
    def test_nested_invalid_rejected(self):
        with self.assertRaises(ValueError):scenario_from_mapping({'scenario':[]})
    def test_each_bound_rejected(self):
        fields={'motor_max_torque_nm':(-1,1501),'gear_ratio':(0,31),'driven_wheel_radius_m':(0,1.1),
            'motor_max_mech_power_w':(-1,400001),'battery_charge_limit_w':(-1,400001),
            'conversion_efficiency':(-.01,1.01),'low_speed_cutoff_m_s':(-1,11)}
        for key,bounds in fields.items():
            for v in bounds:
                with self.subTest(field=key,value=v),self.assertRaises(ValueError):replace(RegenScenario(),**{key:v}).validate()
    def test_nan_inf_rejected(self):
        for v in [float('nan'),float('inf'),float('-inf')]:
            with self.subTest(value=v),self.assertRaises(ValueError):replace(RegenScenario(),battery_charge_limit_w=v).validate()
    def test_bool_rejected(self):
        with self.assertRaises(ValueError):replace(RegenScenario(),conversion_efficiency=True).validate()
    def test_invalid_mass_legacy_guard(self):
        with self.assertRaises(ValueError):replace(RegenScenario(),mass_kg=-2).validate()
    def test_negative_rear_load_rejected(self):
        with self.assertRaises(ValueError):replace(RegenScenario(),cg_to_front_m=.4,cg_height_m=2,demanded_decel_m_s2=12).validate()
    def test_allocate_zero_speed(self):self.assertEqual(allocate(6000,0,RegenScenario()),(0,6000))
    def test_allocate_force_zero(self):self.assertEqual(allocate(0,20,RegenScenario()),(0,0))
    def test_allocate_split_sum(self):
        for v in [.1,2,10,30]:
            a,b=allocate(4000,v,RegenScenario());self.assertAlmostEqual(a+b,4000)

class TestRegenAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True);cls.thread.start()
        cls.host=f'http://127.0.0.1:{cls.http.server_port}'
    @classmethod
    def tearDownClass(cls): cls.http.shutdown();cls.http.server_close();cls.thread.join(timeout=2)
    def request(self,path,payload=None):
        body=json.dumps(payload).encode() if payload is not None else None
        headers={'Content-Type':'application/json'} if payload is not None else {}
        req=Request(self.host+path,body,headers)
        try:
            with urlopen(req,timeout=6) as r:return r.status,json.loads(r.read()) if path.startswith('/api/') else r.read()
        except HTTPError as exc:return exc.code,json.loads(exc.read())
    def test_new_endpoint(self):
        code,r=self.request('/api/regen/simulate',{'scenario':{}});self.assertEqual(code,200);self.assertEqual(r['version'],'0.6.0');self.assertGreater(r['metrics']['battery_energy_stored_j'],0)
    def test_new_js_route(self):
        req=Request(self.host+'/regen.js')
        with urlopen(req,timeout=6) as r:self.assertEqual(r.status,200);self.assertIn(b'regen-form',r.read())
    def test_page_selector(self):
        with urlopen(self.host+'/',timeout=6) as r:self.assertIn(b'value="regen"',r.read())
    def test_bad_input_400(self):
        code,data=self.request('/api/regen/simulate',{'scenario':{'conversion_efficiency':-1}});self.assertEqual(code,400);self.assertIn('conversion_efficiency',data['error'])
    def test_legacy_health_version_preserved(self):
        code,r=self.request('/api/health');self.assertEqual(code,200);self.assertEqual(r['application_version'],'0.5.0');self.assertEqual(r['release_version'],'0.6.0')
    def test_legacy_braking_still_responds(self):
        code,r=self.request('/api/braking/simulate',{'scenario':{}});self.assertEqual(code,200);self.assertAlmostEqual(r['metrics']['stopping_distance_m'],40.0,places=9)
    def test_bad_path_404(self):
        code,r=self.request('/api/regen/unknown',{});self.assertEqual(code,404)
    def test_invalid_json_400(self):
        req=Request(self.host+'/api/regen/simulate',b'{bad',{'Content-Type':'application/json'})
        with self.assertRaises(HTTPError) as cm:urlopen(req,timeout=6)
        self.assertEqual(cm.exception.code,400)

if __name__=='__main__':unittest.main()
