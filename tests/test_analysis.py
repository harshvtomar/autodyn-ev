"""Chat 2 validations on top of all unmodified Chat 1 tests."""
import math
import random
import unittest
from dataclasses import replace

from autodyn_ev.analysis import (BOUNDS, METRICS, compare, convergence, damped_modes,
                                 provenance, sweep, _roots_quartic)
from autodyn_ev.physics import Road, SimulationSettings, Vehicle
from autodyn_ev.simulation import simulate


def base():
    return {'vehicle':{'sprung_mass_kg':300,'unsprung_mass_kg':40,
                       'suspension_stiffness_n_m':18000,'damping_n_s_m':1500,
                       'tire_stiffness_n_m':190000},
            'road':{'kind':'bump','height_m':.06,'start_s':.5,'bump_length_m':1.5,
                    'speed_m_s':5,'sine_frequency_hz':1.5},
            'settings':{'duration_s':3,'dt_s':.005}}


class TestDampedModal(unittest.TestCase):
    def test_undamped_poles_are_imaginary(self):
        v=Vehicle(damping_n_s_m=0)
        d=damped_modes(v)
        self.assertEqual(len(d['oscillatory_modes']),2)
        self.assertEqual(len(d['real_nonoscillatory_poles']),0)
        for got,expected in zip(d['oscillatory_modes'], v.undamped_frequencies_hz):
            self.assertAlmostEqual(got['damped_frequency_hz'],expected,places=8)
            self.assertAlmostEqual(got['damping_ratio'],0,places=10)

    def test_standard_damping_positive(self):
        result=damped_modes(Vehicle())
        self.assertEqual(len(result['oscillatory_modes']),2)
        self.assertTrue(all(0<p['damping_ratio']<1 for p in result['oscillatory_modes']))
        self.assertTrue(all(p['decay_rate_s_inv']>0 for p in result['oscillatory_modes']))

    def test_high_damping_shows_nonoscillatory_poles(self):
        d=damped_modes(Vehicle(damping_n_s_m=12000))
        self.assertEqual(len(d['real_nonoscillatory_poles']),2)
        self.assertEqual(len(d['oscillatory_modes']),1)
        self.assertTrue(all(p['decay_rate_s_inv']>0 for p in d['real_nonoscillatory_poles']))

    def test_polynomial_coefficient_formula(self):
        v=Vehicle()
        a=damped_modes(v)['characteristic_polynomial']
        self.assertEqual(a,[12000,1500*340,300*(18000+190000)+40*18000,1500*190000,18000*190000])

    def test_all_roots_satisfy_characteristic_equation(self):
        for c in [0,100,1500,3000,5000,8000,12000]:
            d=damped_modes(Vehicle(damping_n_s_m=c))
            p=d['characteristic_polynomial']
            self.assertEqual(len(d['poles']),4)
            for pole in d['poles']:
                z=complex(pole['real_s_inv'],pole['imag_rad_s'])
                residual=abs(sum(a*z**(4-i) for i,a in enumerate(p)))
                divisor=sum(abs(a*z**(4-i)) for i,a in enumerate(p))
                self.assertLess(residual/divisor,1e-8)

    def test_random_valid_vehicle_root_residuals(self):
        rng=random.Random(24019)
        for _ in range(120):
            v=Vehicle(**{k:rng.uniform(*bounds) for k,bounds in BOUNDS.items()})
            d=damped_modes(v)
            poly=d['characteristic_polynomial']
            for pole in d['poles']:
                z=complex(pole['real_s_inv'],pole['imag_rad_s'])
                error=abs(sum(a*z**(4-i) for i,a in enumerate(poly)))
                scale=sum(abs(a*z**(4-i)) for i,a in enumerate(poly))
                self.assertLess(error/scale,1e-8)

    def test_invalid_mass_is_rejected(self):
        with self.assertRaises(ValueError):damped_modes(Vehicle(sprung_mass_kg=0))


class TestComparison(unittest.TestCase):
    def test_identical_scenarios_have_zero_deltas(self):
        sc=base();result=compare({'baseline':sc,'variant':sc})
        self.assertTrue(result['same_road_input'])
        for k in METRICS:self.assertAlmostEqual(result['metric_deltas'][k]['absolute'],0,places=11)
        self.assertEqual(result['baseline']['channels'],result['variant']['channels'])

    def test_mass_change_alters_response(self):
        a=base();b=base();b['vehicle']=dict(b['vehicle'],sprung_mass_kg=500)
        result=compare({'baseline':a,'variant':b})
        self.assertTrue(result['same_road_input'])
        self.assertGreater(abs(result['metric_deltas']['body_acceleration_rms_m_s2']['absolute']),.01)
        self.assertEqual(result['baseline']['samples'],result['variant']['samples'])

    def test_road_change_caution(self):
        a=base();b=base();b['road']=dict(b['road'],kind='flat')
        result=compare({'baseline':a,'variant':b})
        self.assertFalse(result['same_road_input'])
        self.assertIn('cannot be attributed',result['caution'])

    def test_zero_reference_has_undefined_percentage(self):
        a=base();b=base();a['road']=dict(a['road'],kind='flat')
        d=compare({'baseline':a,'variant':b})['metric_deltas']['body_acceleration_rms_m_s2']
        self.assertIsNone(d['percent'])

    def test_rejects_different_time_grids(self):
        a=base();b=base();b['settings']=dict(b['settings'],dt_s=.002)
        with self.assertRaisesRegex(ValueError,'identical integration'):compare({'baseline':a,'variant':b})

    def test_rejects_extra_keys(self):
        with self.assertRaises(ValueError):compare({'baseline':base(),'variant':base(),'other':1})

    def test_computational_limit(self):
        a=base();a['settings']={'duration_s':15,'dt_s':.001}
        with self.assertRaisesRegex(ValueError,'7,500'):compare({'baseline':a,'variant':a})


class TestSweep(unittest.TestCase):
    def payload(self,**extra):
        return {'scenario':base(),'parameter':'damping_n_s_m','start':1000.,'stop':2000.,'count':5}|extra

    def test_single_variable_and_endpoints(self):
        d=sweep(self.payload())
        self.assertEqual(len(d['points']),5)
        self.assertEqual([p['parameter_value'] for p in d['points']],[1000,1250,1500,1750,2000])
        self.assertAlmostEqual(d['points'][2]['metrics']['body_acceleration_rms_m_s2'],d['reference_metrics']['body_acceleration_rms_m_s2'])

    def test_every_parameter_has_valid_sweep(self):
        for field,limits in BOUNDS.items():
            d=sweep(self.payload(parameter=field,start=limits[0],stop=limits[1],count=3))
            self.assertEqual(len(d['points']),3)

    def test_canonical_reference_unchanged(self):
        d=sweep(self.payload())
        s=base()
        expected=simulate(Vehicle(**s['vehicle']),Road(**s['road']),SimulationSettings(**s['settings']))
        for k in METRICS:self.assertEqual(d['reference_metrics'][k],expected['metrics'][k])

    def test_rejects_bad_parameter(self):
        with self.assertRaises(ValueError):sweep(self.payload(parameter='braking'))

    def test_rejects_invalid_bounds(self):
        with self.assertRaises(ValueError):sweep(self.payload(start=-10))

    def test_rejects_boolean_count(self):
        with self.assertRaises(ValueError):sweep(self.payload(count=True))

    def test_rejects_excess_count(self):
        with self.assertRaises(ValueError):sweep(self.payload(count=12))

    def test_rejects_nonfinite(self):
        with self.assertRaises(ValueError):sweep(self.payload(stop=float('inf')))

    def test_budget(self):
        sc=base();sc['settings']={'duration_s':15,'dt_s':.001}
        with self.assertRaisesRegex(ValueError,'budget'):sweep(self.payload(scenario=sc,count=11))


class TestConvergence(unittest.TestCase):
    def test_finest_reference_zero_error(self):
        result=convergence({'scenario':base(),'steps_s':[.01,.005,.0025]})
        self.assertEqual(len(result['results']),3)
        self.assertTrue(all(e==0 for e in result['results'][-1]['max_abs_state_error_vs_finest'].values()))
        self.assertTrue(result['results'][0]['max_abs_state_error_vs_finest']['sprung_m']>=0)
        self.assertIn('boundaries',result['interpretation'])

    def test_sine_refinement_improves_consistently(self):
        sc=base();sc['road']=dict(sc['road'],kind='sine',height_m=.02,start_s=0,sine_frequency_hz=1)
        result=convergence({'scenario':sc,'steps_s':[.01,.005,.0025]})
        errors=[r['max_abs_state_error_vs_finest']['sprung_m'] for r in result['results']]
        self.assertGreater(errors[0],errors[1]);self.assertEqual(errors[-1],0)

    def test_rejects_wrong_order(self):
        with self.assertRaises(ValueError):convergence({'scenario':base(),'steps_s':[.002,.005,.01]})

    def test_rejects_duplicate(self):
        with self.assertRaises(ValueError):convergence({'scenario':base(),'steps_s':[.01,.005,.005]})

    def test_rejects_bad_type(self):
        with self.assertRaises(ValueError):convergence({'scenario':base(),'steps_s':[.01,.005,'bad']})

    def test_rejects_budget(self):
        sc=base();sc['settings']={'duration_s':15,'dt_s':.005}
        with self.assertRaisesRegex(ValueError,'35,000'):convergence({'scenario':sc,'steps_s':[.003,.002,.0015,.001]})


class TestProvenance(unittest.TestCase):
    def test_all_legacy_channels_and_metrics_stay_in_place(self):
        result=simulate()
        self.assertEqual(result['schema_version'],'1.0')
        self.assertEqual(result['samples'],1001)
        self.assertEqual(len(result['channels']),12)
        self.assertAlmostEqual(result['metrics']['body_acceleration_rms_m_s2'],.906082,places=5)
        self.assertEqual(result['provenance']['model_revision'],'quarter-car-2dof-v0.2.0')
        self.assertEqual(result['provenance']['solver'],'fixed-step-classical-RK4')

    def test_scenario_provenance_contains_units_and_model(self):
        result=simulate()
        p=result['provenance']
        self.assertEqual(p['vehicle']['sprung_mass_kg'],300)
        self.assertEqual(p['units']['acceleration'],'m/s^2')
        self.assertIn('not empirical',p['data_kind'])
        self.assertEqual(p['road']['kind'],'bump')

    def test_repeatable_provenance(self):
        self.assertEqual(simulate()['provenance'],simulate()['provenance'])


if __name__=='__main__':unittest.main()
