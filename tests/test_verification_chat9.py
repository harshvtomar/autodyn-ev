"""Chat 9: separate algebraic reference, limiting cases, event and grid robustness.

These tests never edit the accepted physical solvers or historical test cases.
"""
from dataclasses import asdict,replace
from math import isclose, isfinite
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen, Request
from http.server import ThreadingHTTPServer

from autodyn_ev.physics import Vehicle,Road,SimulationSettings,derivatives
from autodyn_ev.halfcar import HalfCarVehicle,derivatives_half,simulate_half,axle_roads
from autodyn_ev.simulation import simulate
from autodyn_ev.braking import BrakingScenario,simulate_braking,GRAVITY
from autodyn_ev.regen import RegenScenario,simulate_regen
from autodyn_ev.optimization import optimization_request
from autodyn_ev.server import Handler
from autodyn_ev.verification import (quarter_force_reference,half_force_reference,
    quarter_free_energy, half_free_energy, independent_trapezoidal_rms,
    independent_pareto_ids, constant_braking_reference, max_abs_delta,verify_study)


class Chat9Forces(unittest.TestCase):
    def setUp(self):
        self.q=Vehicle();self.h=HalfCarVehicle();self.flat=Road(kind='flat')

    def hp(self,v):
        return (v.body_mass_kg,v.pitch_inertia_kg_m2,v.cg_to_front_m,v.cg_to_rear_m,
                v.front_unsprung_mass_kg,v.rear_unsprung_mass_kg,v.front_spring_n_m,
                v.rear_spring_n_m,v.front_damping_n_s_m,v.rear_damping_n_s_m,
                v.front_tire_n_m,v.rear_tire_n_m)

    def test_quarter_independent_upward_road(self):
        y=(.003,-.004,.1,-.03)
        expected=quarter_force_reference((300,40),(18000,1500,190000),y,0)
        actual=derivatives(0,y,self.q,self.flat)[2:]
        for a,b in zip(expected,actual):self.assertAlmostEqual(a,b,places=12)

    def test_quarter_sign_spring(self):
        a=quarter_force_reference((300,40),(18000,1500,190000),(.01,0,0,0),0)
        self.assertLess(a[0],0);self.assertGreater(a[1],0)

    def test_quarter_sign_damper(self):
        a=quarter_force_reference((300,40),(18000,1500,190000),(0,0,.1,0),0)
        self.assertLess(a[0],0);self.assertGreater(a[1],0)

    def test_quarter_sign_road(self):
        a=quarter_force_reference((300,40),(18000,1500,190000),(0,0,0,0),.01)
        self.assertEqual(a[0],0);self.assertGreater(a[1],0)

    def test_quarter_mass_scaling(self):
        state=(.01,0,0,0)
        a=quarter_force_reference((300,40),(18000,1500,190000),state,0)
        b=quarter_force_reference((600,40),(18000,1500,190000),state,0)
        self.assertEqual(a[0]/2,b[0])

    def test_quarter_free_energy_nonnegative(self):
        self.assertGreaterEqual(quarter_free_energy((300,40),(18000,190000),(.01,-.02,.2,-.1)),0)

    def test_half_reference_arbitrary_state(self):
        state=(.02,-.008,.003,-.004,.3,-.01,-.1,.08)
        expected=half_force_reference(self.hp(self.h),state,0,0)
        actual=derivatives_half(0,state,self.h,self.flat)[4:]
        for a,b in zip(expected,actual):self.assertAlmostEqual(a,b,places=12)

    def test_half_nose_up_convention(self):
        state=(0,.01,0,0,0,0,0,0)
        acc=half_force_reference(self.hp(self.h),state,0,0)
        self.assertLess(acc[1],0)

    def test_half_rear_tire_road_force(self):
        acc=half_force_reference(self.hp(self.h),(0,)*8,0,.01)
        self.assertEqual(acc[0],0);self.assertGreater(acc[3],0)

    def test_half_energy_nonnegative(self):
        self.assertGreaterEqual(half_free_energy(self.hp(self.h),(.01,.01,.004,-.003,.3,.02,.04,-.05)),0)

    def test_half_axle_delay_exact_kinematic_relation(self):
        road=Road(kind='step',start_s=.5,height_m=.04,speed_m_s=5)
        self.assertEqual(axle_roads(.6,self.h,road),(0.04,0))
        self.assertEqual(axle_roads(1.01,self.h,road),(0.04,0.04))

    def test_zero_input_quarter(self):
        out=simulate(self.q,self.flat,SimulationSettings(duration_s=1,dt_s=.005))
        self.assertEqual(max(map(abs,out['channels']['sprung_acceleration_m_s2'])),0)

    def test_zero_input_half(self):
        out=simulate_half(self.h,self.flat,SimulationSettings(duration_s=1,dt_s=.005))
        self.assertEqual(max(map(abs,out['channels']['body_heave_acceleration_m_s2'])),0)

    def test_pothole_negative_at_peak(self):
        r=Road(kind='pothole',start_s=.5,bump_length_m=1.5,speed_m_s=5,height_m=.06)
        self.assertAlmostEqual(r.displacement(.65),-.06)


class Chat9Numerics(unittest.TestCase):
    def test_independent_rms_constant(self):
        self.assertAlmostEqual(independent_trapezoidal_rms([0,.1,.3,1],[3,3,3,3]),3)

    def test_independent_rms_trapezoids(self):
        self.assertAlmostEqual(independent_trapezoidal_rms([0,.25,1],[0,2,0]),(2.0)**0.5)

    def test_bad_times_rejected(self):
        for t,y in [([0,0],[0,1]),([0],[1]),([0,1],[0])]:
            with self.subTest(t=t),self.assertRaises(ValueError):independent_trapezoidal_rms(t,y)

    def test_aligned_rk4_convergence_quarter_sine(self):
        from autodyn_ev.verification import max_abs_delta
        road=Road(kind='sine',height_m=.01,start_s=0)
        samples=[simulate(Vehicle(),road,SimulationSettings(duration_s=2,dt_s=d))['channels']['sprung_m']
                 for d in (.01,.005,.0025)]
        coarse=max_abs_delta(samples[0],samples[2][::4]);medium=max_abs_delta(samples[1],samples[2][::2])
        self.assertGreater(coarse,medium);self.assertLess(medium,1e-3)

    def test_aligned_rk4_convergence_half_sine(self):
        road=Road(kind='sine',height_m=.01,start_s=0)
        samples=[simulate_half(HalfCarVehicle(),road,SimulationSettings(duration_s=2,dt_s=d))['channels']['body_heave_m']
                 for d in (.01,.005,.0025)]
        coarse=max_abs_delta(samples[0],samples[2][::4]);medium=max_abs_delta(samples[1],samples[2][::2])
        self.assertGreater(coarse,medium);self.assertLess(medium,1e-3)

    def test_braking_constant_analytic_stop(self):
        for request,mu in [(5,.8),(12,.3),(2,.9)]:
            sc=BrakingScenario(demanded_decel_m_s2=request,friction_coefficient=mu)
            out=simulate_braking(sc)['metrics']
            t,d=constant_braking_reference(sc.mass_kg,sc.initial_speed_m_s,request,mu)
            self.assertAlmostEqual(out['stopping_time_s'],t,places=8)
            self.assertAlmostEqual(out['stopping_distance_m'],d,places=8)

    def test_braking_stop_independent_of_sample_step(self):
        vals=[simulate_braking(BrakingScenario(dt_s=dt))['metrics'] for dt in (.1,.02,.005)]
        for x in vals:self.assertAlmostEqual(x['stopping_distance_m'],40,places=8)

    def test_braking_ramp_no_negative_speed(self):
        for dt in (.1,.02,.005):
            out=simulate_braking(BrakingScenario(profile='ramp',dt_s=dt))
            self.assertTrue(all(x>=0 for x in out['channels']['speed_m_s']))
            self.assertGreaterEqual(out['metrics']['distance_travelled_m'],0)

    def test_incomplete_stop_not_confused_with_stopping_distance(self):
        m=simulate_braking(BrakingScenario(duration_s=1))['metrics']
        self.assertFalse(m['stopped']);self.assertIsNone(m['stopping_distance_m'])
        self.assertGreater(m['final_speed_m_s'],0)

    def test_zero_regeneration_no_battery_energy(self):
        for sc in (RegenScenario(motor_max_torque_nm=0),RegenScenario(battery_charge_limit_w=0)):
            result=simulate_regen(sc)
            self.assertEqual(result['metrics']['battery_energy_stored_j'],0)

    def test_regen_trajectory_equal_braking(self):
        regen=simulate_regen(RegenScenario());brake=simulate_braking(BrakingScenario())
        for channel in ('time_s','speed_m_s','distance_m'):
            self.assertEqual(regen['channels'][channel],brake['channels'][channel])


class Chat9Optimization(unittest.TestCase):
    def test_independent_pareto_dominated(self):
        cases=[{'id':1,'feasible':True,'metrics':{'body_acceleration_rms_m_s2':1,'suspension_travel_peak_to_peak_mm':2}},
               {'id':2,'feasible':True,'metrics':{'body_acceleration_rms_m_s2':2,'suspension_travel_peak_to_peak_mm':3}},
               {'id':3,'feasible':True,'metrics':{'body_acceleration_rms_m_s2':2,'suspension_travel_peak_to_peak_mm':1}},
               {'id':4,'feasible':False,'metrics':{'body_acceleration_rms_m_s2':0,'suspension_travel_peak_to_peak_mm':0}}]
        self.assertEqual(independent_pareto_ids(cases),[1,3])

    def test_quarter_grid_7(self):
        o=optimization_request({'model':'quarter','settings':{'duration_s':2,'dt_s':.01}})
        self.assertEqual(verify_study(o)['case_count'],7)

    def test_quarter_grid_49(self):
        o=optimization_request({'model':'quarter','parameters':['damping_n_s_m','suspension_stiffness_n_m'],
                                'settings':{'duration_s':2,'dt_s':.01}})
        self.assertEqual(verify_study(o)['case_count'],49)

    def test_half_grid_7(self):
        o=optimization_request({'model':'half','settings':{'duration_s':2,'dt_s':.01}})
        self.assertEqual(verify_study(o)['case_count'],7)

    def test_half_grid_49(self):
        o=optimization_request({'model':'half','parameters':['front_damping_n_s_m','rear_spring_n_m'],
                                'settings':{'duration_s':2,'dt_s':.01}})
        self.assertEqual(verify_study(o)['case_count'],49)

    def test_no_feasible(self):
        o=optimization_request({'constraints':{'max_body_acceleration_rms_m_s2':0},
                                'settings':{'duration_s':2,'dt_s':.01}})
        self.assertEqual(o['feasible_count'],0);self.assertIsNone(o['selected_id'])
        self.assertEqual(verify_study(o)['pareto_count'],0)

    def test_deterministic_studies(self):
        cfg={'model':'half','settings':{'duration_s':2,'dt_s':.01}}
        self.assertEqual(optimization_request(cfg),optimization_request(cfg))

    def test_expected_metric_independent_rms(self):
        o=optimization_request({'settings':{'duration_s':2,'dt_s':.01}})
        v=Vehicle(damping_n_s_m=o['candidates'][0]['parameters']['damping_n_s_m'])
        raw=simulate(v,settings=SimulationSettings(duration_s=2,dt_s=.01))
        expected=independent_trapezoidal_rms(raw['channels']['time_s'],raw['channels']['sprung_acceleration_m_s2'])
        self.assertAlmostEqual(expected,o['candidates'][0]['metrics']['body_acceleration_rms_m_s2'],places=10)

    def test_invalid_limits_rejected(self):
        for obj in ({'constraints':{'max_body_acceleration_rms_m_s2':-1}},
                    {'parameters':['damping_n_s_m','damping_n_s_m']},
                    {'points_per_axis':8}):
            with self.assertRaises(ValueError):optimization_request(obj)


class Chat9API(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.root=f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2)

    def request(self,path,payload=None,ctype='application/json'):
        request=Request(self.root+path,method='POST' if payload is not None else 'GET',
           data=json.dumps(payload).encode() if payload is not None else None,
           headers={'Content-Type':ctype} if payload is not None else {})
        try:
            with urlopen(request,timeout=10) as response:return response.status,json.load(response)
        except HTTPError as exc:return exc.code,json.load(exc)

    def test_health_compatibility(self):
        s,x=self.request('/api/health');self.assertEqual(s,200)
        self.assertEqual(x['version'],'0.4.0');self.assertEqual(x['current_release_version'],'0.8.0')
        self.assertEqual(x['active_application_version'],'0.9.0')

    def test_study_api_success(self):
        s,x=self.request('/api/optimization/study',{'settings':{'duration_s':2,'dt_s':.01}})
        self.assertEqual(s,200);self.assertEqual(x['grid']['run_count'],7)

    def test_invalid_api(self):
        for body in ({'points_per_axis':49},{'parameters':['invalid']},{'constraints':{'bogus':1}}):
            s,x=self.request('/api/optimization/study',body)
            self.assertEqual(s,400);self.assertIn('error',x)

    def test_unknown_endpoint(self):
        s,x=self.request('/api/fake',{});self.assertEqual(s,404)

    def test_legacy_api_remains(self):
        for endpoint in ('/api/simulate','/api/halfcar/simulate','/api/braking/simulate','/api/regen/simulate'):
            s,x=self.request(endpoint,{})
            self.assertEqual(s,200,endpoint);self.assertIn('channels',x)

    def test_security_headers(self):
        with urlopen(self.root+'/',timeout=10) as response:
            self.assertEqual(response.headers['X-Content-Type-Options'],'nosniff')
            self.assertIn("default-src 'self'",response.headers['Content-Security-Policy'])


if __name__=='__main__':unittest.main()
