"""Chat 5 independent physics, boundary and legacy separation regressions."""
import json
import math
import unittest
from dataclasses import replace
from autodyn_ev.braking import (BrakingScenario, GRAVITY, actual_at, axle_loads,
                                demand_at, scenario_from_mapping, simulate_braking)
from autodyn_ev.simulation import simulate
from autodyn_ev.physics import Road, Vehicle, SimulationSettings


class TestBrakingPhysics(unittest.TestCase):
    def setUp(self):
        self.sc=BrakingScenario()

    def test_default_analytic_stop(self):
        r=simulate_braking(self.sc)
        self.assertTrue(r['metrics']['stopped'])
        self.assertAlmostEqual(r['metrics']['stopping_time_s'],4,places=11)
        self.assertAlmostEqual(r['metrics']['stopping_distance_m'],40,places=11)

    def test_non_grid_stop_exact(self):
        s=replace(self.sc,initial_speed_m_s=17,dt_s=.08)
        r=simulate_braking(s)
        self.assertAlmostEqual(r['metrics']['stopping_time_s'],3.4,places=11)
        self.assertAlmostEqual(r['metrics']['stopping_distance_m'],28.9,places=10)
        self.assertAlmostEqual(r['channels']['time_s'][-1],3.4,places=10)

    def test_zero_braking_constant_speed(self):
        s=replace(self.sc,demanded_decel_m_s2=0,duration_s=2)
        r=simulate_braking(s);self.assertFalse(r['metrics']['stopped'])
        self.assertIsNone(r['metrics']['stopping_distance_m'])
        self.assertAlmostEqual(r['metrics']['distance_travelled_m'],40,places=10)
        self.assertEqual(set(r['channels']['speed_m_s']),{20.})

    def test_zero_initial_speed(self):
        r=simulate_braking(replace(self.sc,initial_speed_m_s=0))
        self.assertEqual(r['samples'],1)
        self.assertEqual(r['metrics']['stopping_time_s'],0)
        self.assertEqual(r['metrics']['stopping_distance_m'],0)

    def test_available_traction_bounds_actual(self):
        r=simulate_braking(replace(self.sc,demanded_decel_m_s2=12))
        self.assertTrue(r['metrics']['traction_limited'])
        for force in r['channels']['actual_brake_force_n']:
            self.assertLessEqual(force, r['metrics']['available_traction_n']+1e-9)

    def test_coefficient_reduces_stop(self):
        s=replace(self.sc,demanded_decel_m_s2=12)
        d1=simulate_braking(replace(s,friction_coefficient=.3))['metrics']['stopping_distance_m']
        d2=simulate_braking(replace(s,friction_coefficient=.7))['metrics']['stopping_distance_m']
        self.assertGreater(d1,d2)

    def test_all_speeds_nonnegative_and_distance_monotone(self):
        for profile in ('constant','ramp'):
            r=simulate_braking(replace(self.sc,profile=profile))
            for v in r['channels']['speed_m_s']:self.assertGreaterEqual(v,0)
            x=r['channels']['distance_m'];self.assertTrue(all(x[i]<=x[i+1]+1e-10 for i in range(len(x)-1)))
            self.assertEqual(r['channels']['speed_m_s'][-1],0)

    def test_front_rear_normal_balance(self):
        r=simulate_braking(replace(self.sc,profile='ramp'))
        c=r['channels']
        for front,rear in zip(c['front_normal_n'],c['rear_normal_n']):
            self.assertAlmostEqual(front+rear,self.sc.mass_kg*GRAVITY,places=8)
            self.assertGreaterEqual(rear,0)

    def test_braking_front_increases_rear_decreases(self):
        f0,r0=axle_loads(0,self.sc);f1,r1=axle_loads(5,self.sc)
        self.assertGreater(f1,f0);self.assertLess(r1,r0)
        self.assertAlmostEqual(f1-f0,r0-r1,places=8)

    def test_zero_height_no_transfer(self):
        s=replace(self.sc,cg_height_m=0)
        self.assertEqual(axle_loads(0,s),axle_loads(5,s))

    def test_mu_g_analytic(self):
        s=replace(self.sc,demanded_decel_m_s2=12)
        r=simulate_braking(s)
        d=s.friction_coefficient*GRAVITY
        self.assertAlmostEqual(r['metrics']['stopping_time_s'],s.initial_speed_m_s/d,places=11)
        self.assertAlmostEqual(r['metrics']['stopping_distance_m'],s.initial_speed_m_s**2/(2*d),places=11)

    def test_ramp_unlimited_analytic(self):
        s=replace(self.sc,profile='ramp',ramp_s=1)
        r=simulate_braking(s)
        # after 1s, v=17.5m/s; distance in ramp=20-5/6.
        self.assertAlmostEqual(r['metrics']['stopping_time_s'],4.5,places=10)
        self.assertAlmostEqual(r['metrics']['stopping_distance_m'],49.7916666666667,places=9)

    def test_ramp_through_traction_saturation(self):
        s=replace(self.sc,profile='ramp',demanded_decel_m_s2=12,ramp_s=2,dt_s=.08)
        a=simulate_braking(s)
        b=simulate_braking(replace(s,dt_s=.01))
        self.assertTrue(a['metrics']['traction_limited'])
        self.assertAlmostEqual(a['metrics']['stopping_time_s'],b['metrics']['stopping_time_s'],places=9)
        self.assertAlmostEqual(a['metrics']['stopping_distance_m'],b['metrics']['stopping_distance_m'],places=9)

    def test_event_time_step_independence(self):
        for profile in ('constant','ramp'):
            base=replace(self.sc,profile=profile,initial_speed_m_s=18.81)
            a=simulate_braking(replace(base,dt_s=.09))['metrics']
            b=simulate_braking(replace(base,dt_s=.003))['metrics']
            self.assertAlmostEqual(a['stopping_time_s'],b['stopping_time_s'],places=9)
            self.assertAlmostEqual(a['stopping_distance_m'],b['stopping_distance_m'],places=9)

    def test_short_window_reports_not_stopped(self):
        s=replace(self.sc,duration_s=1)
        r=simulate_braking(s)
        self.assertIsNone(r['metrics']['stopping_time_s']);self.assertFalse(r['metrics']['stopped'])
        self.assertGreater(r['metrics']['final_speed_m_s'],0)
        self.assertIn('not stopping distance',' '.join(r['warnings']))

    def test_last_sample_load_static_after_stop(self):
        r=simulate_braking(self.sc)
        self.assertEqual(r['channels']['actual_decel_m_s2'][-1],0)
        self.assertAlmostEqual(r['channels']['front_normal_n'][-1],r['metrics']['static_front_normal_n'])

    def test_returned_outputs_finite(self):
        for p in ('constant','ramp'):
            r=simulate_braking(replace(self.sc,profile=p))
            self.assertEqual(len({len(ch) for ch in r['channels'].values()}),1)
            self.assertTrue(all(math.isfinite(v) for arr in r['channels'].values() for v in arr))
            json.dumps(r,allow_nan=False)

    def test_schema_version_and_provenance(self):
        r=simulate_braking()
        self.assertEqual(r['version'],'0.5.0')
        self.assertEqual(r['model'],'independent-longitudinal-braking')
        self.assertIn('gravity_m_s2',r['provenance'])
        self.assertEqual(r['provenance']['units']['actual_decel_m_s2'],'m/s²')
        self.assertIn('none',r['provenance']['suspension_coupling'])

    def test_no_legacy_physics_mutation(self):
        vehicle,road,settings=Vehicle(),Road(),SimulationSettings()
        before=simulate(vehicle,road,settings)['metrics']['body_acceleration_rms_m_s2']
        simulate_braking()
        after=simulate(vehicle,road,settings)['metrics']['body_acceleration_rms_m_s2']
        self.assertEqual(before,after)
        self.assertAlmostEqual(before,.906,delta=.002)

    def test_zero_demand_ramp(self):
        r=simulate_braking(replace(self.sc,profile='ramp',demanded_decel_m_s2=0))
        self.assertFalse(r['metrics']['stopped']);self.assertEqual(r['metrics']['peak_deceleration_m_s2'],0)

    def test_requested_greater_than_actual(self):
        r=simulate_braking(replace(self.sc,demanded_decel_m_s2=12))
        self.assertGreater(r['channels']['requested_force_n'][0],r['channels']['actual_brake_force_n'][0])

    def test_ramp_t0_zero(self):
        s=replace(self.sc,profile='ramp');self.assertEqual(demand_at(0,s),0)
        self.assertEqual(actual_at(0,s),0)

    def test_gravity_dependent_loads(self):
        s=self.sc
        f,r=axle_loads(0,s)
        self.assertAlmostEqual(f/s.mass_kg,GRAVITY*s.cg_to_rear_m/(s.cg_to_front_m+s.cg_to_rear_m))


class TestBrakingValidation(unittest.TestCase):
    def test_defaults_mapping(self):self.assertEqual(scenario_from_mapping({}),BrakingScenario())
    def test_nested_mapping(self):self.assertEqual(scenario_from_mapping({'scenario':{'mass_kg':1000}}).mass_kg,1000)
    def test_non_object(self):
        for v in ([],None,1,True):
            with self.assertRaises(ValueError):scenario_from_mapping(v)
    def test_unknown_field(self):
        with self.assertRaisesRegex(ValueError,'unknown braking'):scenario_from_mapping({'abs':True})
    def test_bad_profile(self):
        with self.assertRaisesRegex(ValueError,'profile'):scenario_from_mapping({'profile':'abs'})
    def test_bad_number(self):
        for v in ('bad',None,True,float('nan'),float('inf')):
            with self.subTest(v=v),self.assertRaises(ValueError):scenario_from_mapping({'mass_kg':v})
    def test_invalid_range_all_fields(self):
        for name in ('mass_kg','cg_height_m','cg_to_front_m','cg_to_rear_m','initial_speed_m_s','friction_coefficient','demanded_decel_m_s2','ramp_s','duration_s','dt_s'):
            with self.subTest(name=name),self.assertRaises(ValueError):scenario_from_mapping({name:-1})
    def test_rear_negative_rejected(self):
        with self.assertRaisesRegex(ValueError,'rear axle'):scenario_from_mapping({'cg_to_front_m':.4,'cg_height_m':2,'demanded_decel_m_s2':12})
    def test_high_resolution_limit(self):
        with self.assertRaisesRegex(ValueError,'10,000'):scenario_from_mapping({'duration_s':40,'dt_s':.002})
    def test_boundaries_allowed(self):
        sc=scenario_from_mapping({'demanded_decel_m_s2':0,'cg_height_m':0,'initial_speed_m_s':0});self.assertEqual(sc.initial_speed_m_s,0)
    def test_long_wheelbase_rejected(self):
        with self.assertRaisesRegex(ValueError,'wheelbase'):scenario_from_mapping({'cg_to_front_m':4,'cg_to_rear_m':4})

if __name__=='__main__':unittest.main()
