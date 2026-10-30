import math
import unittest
from dataclasses import replace

from autodyn_ev.physics import (
    Road, SimulationSettings, Vehicle, derivatives, mechanical_energy, rk4_step
)
from autodyn_ev.simulation import scenario_from_mapping, simulate, CHANNELS


class VehicleTests(unittest.TestCase):
    def test_default_values_are_valid(self):
        Vehicle().validate()

    def test_road_defaults_are_valid(self):
        Road().validate()

    def test_default_settings_valid(self):
        SimulationSettings().validate()

    def test_natural_modes_positive_and_ordered(self):
        a, b = Vehicle().undamped_frequencies_hz
        self.assertGreater(a, 0)
        self.assertGreater(b, a)
        self.assertLess(a, 3)
        self.assertGreater(b, 6)

    def test_natural_modes_match_eigenvalue_invariants(self):
        v = Vehicle()
        a, b = v.undamped_frequencies_hz
        la, lb = (2 * math.pi * a)**2, (2 * math.pi * b)**2
        self.assertAlmostEqual(la+lb, v.suspension_stiffness_n_m/v.sprung_mass_kg+(v.suspension_stiffness_n_m+v.tire_stiffness_n_m)/v.unsprung_mass_kg, places=7)
        self.assertAlmostEqual(la*lb, v.suspension_stiffness_n_m*v.tire_stiffness_n_m/(v.sprung_mass_kg*v.unsprung_mass_kg), places=5)

    def test_zero_equilibrium_rhs(self):
        self.assertEqual(derivatives(0, (0,0,0,0), Vehicle(), Road(kind="flat")), (0,0,0,0))

    def test_suspension_spring_reaction_opposite(self):
        v=Vehicle()
        _,_,a_s,a_u=derivatives(0,(.05,0,0,0),v,Road(kind="flat"))
        self.assertAlmostEqual(v.sprung_mass_kg*a_s+v.unsprung_mass_kg*a_u,0)
        self.assertLess(a_s,0)
        self.assertGreater(a_u,0)

    def test_tire_force_changes_only_wheel_mass(self):
        v=Vehicle()
        _,_,a_s,a_u=derivatives(0,(0,0,0,0),v,Road(kind="step",height_m=.05,start_s=0))
        self.assertAlmostEqual(a_s,0)
        self.assertAlmostEqual(a_u,v.tire_stiffness_n_m*.05/v.unsprung_mass_kg)

    def test_damping_opposes_relative_velocity(self):
        v=Vehicle()
        _,_,a_s,a_u=derivatives(0,(0,0,1,0),v,Road(kind="flat"))
        self.assertLess(a_s,0)
        self.assertGreater(a_u,0)

    def test_bump_starts_and_ends_at_zero(self):
        r=Road(start_s=.4,bump_length_m=2,speed_m_s=4,height_m=.06)
        for t in [0,.4,.9,1.01]:
            self.assertAlmostEqual(r.displacement(t),0,places=13)
        self.assertAlmostEqual(r.displacement(.65),.06,places=12)

    def test_step_nonzero_after_start(self):
        r=Road(kind="step",height_m=.04,start_s=.3)
        self.assertEqual(r.displacement(.29),0)
        self.assertEqual(r.displacement(.3),.04)
        self.assertEqual(r.displacement(20),.04)

    def test_flat_never_moves(self):
        self.assertEqual(Road(kind="flat").displacement(5),0)

    def test_sine_sign_and_amplitude(self):
        r=Road(kind="sine",height_m=.04,start_s=.5,sine_frequency_hz=1)
        self.assertAlmostEqual(r.displacement(.75),.04)
        self.assertAlmostEqual(r.displacement(1),0,places=14)
        self.assertAlmostEqual(r.displacement(1.25),-.04)

    def test_negative_damping_rejected(self):
        with self.assertRaises(ValueError): replace(Vehicle(),damping_n_s_m=-1).validate()

    def test_nonfinite_mass_rejected(self):
        for x in [float('nan'),float('inf'),float('-inf')]:
            with self.assertRaises(ValueError): replace(Vehicle(),sprung_mass_kg=x).validate()

    def test_bool_not_a_mass(self):
        with self.assertRaises(ValueError): replace(Vehicle(),sprung_mass_kg=True).validate()

    def test_nonfinite_road_rejected(self):
        with self.assertRaises(ValueError): Road(height_m=float('nan')).validate()

    def test_bad_road_kind_rejected(self):
        with self.assertRaises(ValueError): Road(kind="ramp").validate()

    def test_bad_time_step_rejected(self):
        with self.assertRaises(ValueError): SimulationSettings(dt_s=.05).validate()

    def test_too_many_steps_rejected(self):
        # limits ensure at most 15,000 steps
        self.assertEqual(round(15/.001),15000)
        SimulationSettings(duration_s=15,dt_s=.001).validate()

    def test_dissipation_rate_nonpositive(self):
        v=Vehicle()
        state=(.03,-.01,.4,-.2)
        rhs=derivatives(0,state,v,Road(kind="flat"))
        zs,zu,vs,vu=state
        dE=(v.sprung_mass_kg*vs*rhs[2] + v.unsprung_mass_kg*vu*rhs[3]
           +v.suspension_stiffness_n_m*(zs-zu)*(vs-vu) +v.tire_stiffness_n_m*zu*vu)
        self.assertAlmostEqual(dE,-v.damping_n_s_m*(vs-vu)**2,places=8)

    def test_rk4_step_returns_finite_state(self):
        s=rk4_step(0,(.04,0,0,0),.005,Vehicle(),Road(kind="flat"))
        self.assertEqual(len(s),4)
        self.assertTrue(all(math.isfinite(x) for x in s))


class SimulatorTests(unittest.TestCase):
    def test_default_run_has_all_channels(self):
        result=simulate()
        self.assertEqual(result["samples"],1001)
        self.assertEqual(tuple(result["channels"]),CHANNELS)
        self.assertTrue(all(len(a)==1001 for a in result["channels"].values()))
        self.assertEqual(result["channels"]["time_s"][-1],5)
        self.assertTrue(result["metrics"]["body_acceleration_peak_m_s2"]>0)

    def test_no_road_no_motion(self):
        r=simulate(road=Road(kind="flat"),settings=SimulationSettings(duration_s=2))
        self.assertTrue(all(x==0 for k,v in r['channels'].items() if k!='time_s' for x in v))
        self.assertEqual(r['metrics']['body_acceleration_rms_m_s2'],0)
        self.assertIsNone(r['metrics']['post_bump_settling_s'])

    def test_initial_state_free_vibration_energy_decreases(self):
        v=Vehicle()
        road=Road(kind="flat")
        state=(.04,0,0,0)
        prev=mechanical_energy(state,v)
        for i in range(4000):
            state=rk4_step(i*.0025,state,.0025,v,road)
            now=mechanical_energy(state,v)
            self.assertLessEqual(now,prev+1e-10)
            prev=now
        self.assertLess(prev,1e-5)

    def test_undamped_free_vibration_energy_conserved(self):
        v=replace(Vehicle(),damping_n_s_m=0)
        state=(.04,0,0,0)
        reference=mechanical_energy(state,v)
        for i in range(2000):
            state=rk4_step(i*.00125,state,.00125,v,Road(kind="flat"))
        current=mechanical_energy(state,v)
        self.assertLess(abs(current-reference)/reference,0.00002)

    def test_vehicle_numerical_modes_not_identical(self):
        v=Vehicle()
        u=replace(v,sprung_mass_kg=600)
        self.assertNotAlmostEqual(v.undamped_frequencies_hz[0],u.undamped_frequencies_hz[0],places=3)

    def test_rk4_refinement_on_smooth_profile(self):
        v=Vehicle()
        r=Road(kind="sine",sine_frequency_hz=1.2,start_s=0,height_m=.02)
        y0=(0,0,0,0)
        def steps(h):
            s=y0
            for i in range(round(2/h)):
                s=rk4_step(i*h,s,h,v,r)
            return s
        coarse=steps(.01);fine=steps(.005);reference=steps(.00125)
        e1=sum(abs(x-y) for x,y in zip(coarse,reference))
        e2=sum(abs(x-y) for x,y in zip(fine,reference))
        self.assertLess(e2,e1/10)

    def test_steady_state_of_step_approaches_height(self):
        r=Road(kind="step",height_m=.03,start_s=0)
        o=simulate(road=r,settings=SimulationSettings(duration_s=12,dt_s=.005))
        self.assertAlmostEqual(o['channels']['sprung_m'][-1],.03,delta=1e-4)
        self.assertAlmostEqual(o['channels']['unsprung_m'][-1],.03,delta=1e-4)
        self.assertAlmostEqual(o['channels']['suspension_travel_m'][-1],0,delta=1e-4)

    def test_zero_damping_has_finite_output(self):
        output=simulate(vehicle=replace(Vehicle(),damping_n_s_m=0))
        self.assertTrue(all(math.isfinite(x) for arr in output['channels'].values() for x in arr))

    def test_metrics_consistent_with_series(self):
        o=simulate()
        series=o['channels']['sprung_acceleration_m_s2']
        reference=math.sqrt(sum(x*x for x in series)/len(series))
        self.assertAlmostEqual(o['metrics']['body_acceleration_rms_m_s2'],reference)
        self.assertAlmostEqual(o['metrics']['suspension_travel_peak_mm'],1000*max(map(abs,o['channels']['suspension_travel_m'])))

    def test_rms_less_than_peak(self):
        o=simulate()
        self.assertLessEqual(o['metrics']['body_acceleration_rms_m_s2'],o['metrics']['body_acceleration_peak_m_s2'])

    def test_underresolved_bump_rejected(self):
        with self.assertRaisesRegex(ValueError,"under-resolved"):
            simulate(road=Road(bump_length_m=.5,speed_m_s=40),settings=SimulationSettings(dt_s=.01))

    def test_underresolved_sine_rejected(self):
        with self.assertRaisesRegex(ValueError,"under-resolved"):
            simulate(road=Road(kind="sine",sine_frequency_hz=5),settings=SimulationSettings(dt_s=.02))

    def test_no_nans_in_json(self):
        import json
        json.dumps(simulate(),allow_nan=False)

    def test_initial_state_shape_rejected(self):
        with self.assertRaises(ValueError): simulate(initial_state=(0,0,0))

    def test_initial_state_nan_rejected(self):
        with self.assertRaises(ValueError): simulate(initial_state=(float('nan'),0,0,0))

    def test_unknown_payload_field_rejected(self):
        with self.assertRaises(ValueError): scenario_from_mapping({'settings':{'dt_s':.005},'extra':42})

    def test_unknown_vehicle_field_rejected(self):
        with self.assertRaises(ValueError): scenario_from_mapping({'vehicle':{'evil':10}})

    def test_non_dict_payload_rejected(self):
        with self.assertRaises(ValueError): scenario_from_mapping([])

    def test_missing_payload_uses_defaults(self):
        self.assertEqual(scenario_from_mapping({}),(Vehicle(),Road(),SimulationSettings()))

    def test_invalid_road_height_rejected(self):
        with self.assertRaises(ValueError): scenario_from_mapping({'road':{'height_m':.3}})

    def test_invalid_nested_payload_rejected(self):
        with self.assertRaises(ValueError): scenario_from_mapping({'vehicle':'bad'})

    def test_bump_has_defined_end(self):
        o=simulate()
        self.assertIsNotNone(o['metrics']['post_bump_settling_s'])
        self.assertGreaterEqual(o['metrics']['post_bump_settling_s'],0)

    def test_sine_has_no_bump_settling_metric(self):
        o=simulate(road=Road(kind="sine"))
        self.assertIsNone(o['metrics']['post_bump_settling_s'])


if __name__=='__main__': unittest.main()
