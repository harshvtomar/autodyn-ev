"""Independent mechanical and numerical checks for the additive half-car."""
from dataclasses import replace
from math import isclose, pi, sqrt
import unittest
from autodyn_ev.physics import Road,SimulationSettings
from autodyn_ev.halfcar import (HalfCarVehicle,ZERO_STATE,axle_roads,derivatives_half,
    half_energy, half_energy_rate_flat, rk4_half,simulate_half,scenario_half_from_mapping,
    suspension_forces, HALF_CHANNELS)

V=HalfCarVehicle()
F=Road(kind='flat')
DT=SimulationSettings(duration_s=2.,dt_s=.005)
class TestHalfCar(unittest.TestCase):
    def test_default_model_properties(self):
        V.validate();self.assertEqual(V.wheelbase_m,2.5)
    def test_zero_derivative_flat(self):
        self.assertEqual(derivatives_half(0,ZERO_STATE,V,F),ZERO_STATE)
    def test_flat_static_equilibrium_zero(self):
        result=simulate_half(settings=DT,road=F)
        for key,series in result['channels'].items():
            if key!='time_s': self.assertTrue(all(x==0 for x in series),key)
        self.assertEqual(result['metrics']['body_pitch_peak_deg'],0)
    def test_time_axis(self):
        data=simulate_half(settings=DT,road=F)
        self.assertEqual(data['samples'],401)
        self.assertAlmostEqual(data['channels']['time_s'][-1],2)
        self.assertEqual(tuple(data['channels']),HALF_CHANNELS)
    def test_spring_front_opposes_body_extension(self):
        state=(.01,0.,0.,0.,0.,0.,0.,0.)
        ff,fr=suspension_forces(state,V)
        self.assertEqual(ff,-180.);self.assertEqual(fr,-180.)
    def test_torque_pitch_sign_nose_up_restored(self):
        y=(0.,.01,0.,0.,0.,0.,0.,0.)
        ff,fr=suspension_forces(y,V)
        expected=(V.cg_to_front_m*ff-V.cg_to_rear_m*fr)/V.pitch_inertia_kg_m2
        self.assertAlmostEqual(derivatives_half(0,y,V,F)[5],expected)
        self.assertLess(expected,0)
    def test_road_front_force_acceleration_up(self):
        r=Road(kind='step',start_s=0,height_m=.04)
        dy=derivatives_half(0,ZERO_STATE,V,r)
        self.assertGreater(dy[6],0);self.assertEqual(dy[7],0)
    def test_no_spurious_pitch_symmetric_vehicle_and_states(self):
        v=replace(V,cg_to_front_m=1.25,cg_to_rear_m=1.25)
        y=(.02,0,0,0,.10,0,0,0)
        self.assertAlmostEqual(derivatives_half(0,y,v,F)[5],0,places=12)
        self.assertEqual(suspension_forces(y,v)[0],suspension_forces(y,v)[1])
    def test_symmetric_road_with_zero_delay_limit_by_large_speed_not_required(self):
        # The physical delay does NOT vanish by default: symmetric inputs are deliberately distinct.
        r=Road(kind='step',start_s=0,height_m=.02,speed_m_s=5)
        self.assertEqual(axle_roads(0,V,r),(.02,0.))
    def test_rear_delay_spatial(self):
        r=Road(kind='bump',start_s=.4,bump_length_m=1.0,speed_m_s=5,height_m=.04)
        tau=V.wheelbase_m/r.speed_m_s
        self.assertAlmostEqual(tau,.5)
        for t in [0,.4,.5,.61,.71,.9,1.2]:
            rf,rr=axle_roads(t,V,r)
            self.assertAlmostEqual(rr,r.displacement(t-tau),places=14)
        self.assertAlmostEqual(axle_roads(.5,V,r)[1],0)
    def test_step_front_rear_time_offsets(self):
        r=Road(kind='step',start_s=.2,height_m=.05)
        self.assertEqual(axle_roads(.3,V,r),(.05,0))
        self.assertEqual(axle_roads(.71,V,r),(.05,.05))
    def test_energy_nonnegative(self):
        y=(.02,.03,.005,-.01,.2,.04,-.1,.05)
        self.assertGreater(half_energy(y,V),0)
        self.assertEqual(half_energy(ZERO_STATE,V),0)
    def test_energy_rate_damped(self):
        y=(.02,.01,0,0,.1,.06,0,0)
        self.assertLess(half_energy_rate_flat(y,V),0)
    def test_energy_decays_flat_road(self):
        y=(.02,.02,.005,-.01,0,0,0,0)
        previous=half_energy(y,V)
        for i in range(2500):
            y=rk4_half(i*.002,y,.002,V,F)
            current=half_energy(y,V)
            self.assertLessEqual(current,previous+1e-10)
            previous=current
    def test_energy_unforced_no_damping_conserved(self):
        v=replace(V,front_damping_n_s_m=0,rear_damping_n_s_m=0)
        y=(.012,.006,.01,-.012,0,0,0,0)
        start=half_energy(y,v)
        for i in range(1200):y=rk4_half(i*.001,y,.001,v,F)
        self.assertLess(abs(half_energy(y,v)-start)/start,1e-5)
    def test_dissipation_rate_finite_difference(self):
        y=(.01,.004,0,0,.3,.08,0,.01)
        delta=.0000001
        estimate=(half_energy(rk4_half(0,y,delta,V,F),V)-half_energy(y,V))/delta
        self.assertAlmostEqual(estimate,half_energy_rate_flat(y,V),delta=.01)
    def test_deterministic(self):
        r=Road(kind='bump',height_m=.04)
        a=simulate_half(V,r,DT);b=simulate_half(V,r,DT)
        self.assertEqual(a['channels'],b['channels']);self.assertEqual(a['metrics'],b['metrics'])
    def test_refinement_order_smooth_flat_free(self):
        initial=(.01,.005,.004,-.003,0.,0.,0.,0.)
        # Compare fixed-time full-state response to finely resolved RK4.
        def integrate(dt):
            y=initial
            for i in range(round(.5/dt)):y=rk4_half(i*dt,y,dt,V,F)
            return y
        ref=integrate(.0002)
        errors=[max(abs(a-b) for a,b in zip(integrate(h),ref)) for h in (.01,.005,.0025)]
        self.assertTrue(errors[0]>errors[1]>errors[2],errors)
        self.assertLess(errors[2],errors[0]/10)
    def test_metrics_and_schema_units(self):
        data=simulate_half(settings=DT)
        self.assertEqual(data['schema_version'],'half-car-1.0')
        self.assertEqual(data['rear_road_delay_s'],.5)
        self.assertEqual(data['settings']['dt_s'],.005)
        self.assertGreater(data['metrics']['body_heave_acceleration_rms_m_s2'],0)
        self.assertEqual(len(data['channels']['front_suspension_force_n']),data['samples'])
        self.assertIn('small_angle_caution',data['domain_diagnostics'])
    def test_variant_changes_heave(self):
        a=simulate_half(settings=DT)
        b=simulate_half(replace(V,body_mass_kg=750),settings=DT)
        self.assertNotEqual(a['metrics']['body_heave_peak_mm'],b['metrics']['body_heave_peak_mm'])
    def test_initial_state_validation(self):
        for state in [[0]*7, [float('nan')]+[0]*7,[float('inf')]+[0]*7,[True]+[0]*7,[0,.25]+[0]*6]:
            with self.subTest(state=state),self.assertRaises(ValueError):simulate_half(settings=DT,initial_state=state)
    def test_road_validation(self):
        with self.assertRaisesRegex(ValueError,'speed_m_s'):simulate_half(road=Road(speed_m_s=0),settings=DT)
    def test_unstable_step_guard(self):
        extreme=replace(V,front_unsprung_mass_kg=15,front_tire_n_m=500000)
        with self.assertRaisesRegex(ValueError,'wheel-hop'):simulate_half(extreme,F,SimulationSettings(2,.02))
    def test_bump_resolution_guard(self):
        with self.assertRaisesRegex(ValueError,'bump'):simulate_half(road=Road(bump_length_m=.5,speed_m_s=40),settings=DT)
    def test_sine_resolution_guard(self):
        with self.assertRaisesRegex(ValueError,'sine'):simulate_half(road=Road(kind='sine',sine_frequency_hz=5),settings=SimulationSettings(2.2,.011))
    def test_road_scenarios(self):
        for kind in ('flat','step','sine','bump'):
            with self.subTest(kind=kind):
                result=simulate_half(road=Road(kind=kind),settings=DT)
                self.assertEqual(result['samples'],401)
    def test_bounds(self):
        for key,val in [('body_mass_kg',0),('pitch_inertia_kg_m2',0),('cg_to_front_m',0),('rear_unsprung_mass_kg',0),('front_tire_n_m',10000000),('rear_damping_n_s_m',-1),('body_mass_kg',True),('body_mass_kg',float('nan'))]:
            with self.subTest(key=key),self.assertRaises(ValueError):replace(V,**{key:val}).validate()
    def test_mapping_and_unknown_fields(self):
        v,r,s=scenario_half_from_mapping({'vehicle':{'body_mass_kg':700},'road':{'kind':'flat'},'settings':{'dt_s':.005}})
        self.assertEqual(v.body_mass_kg,700);self.assertEqual(r.kind,'flat')
        for body in [[],{'missing':0},{'vehicle':{'extra':0}}, {'road':{'kind':'wrong'}},{'settings':{'dt_s':0}}]:
            with self.subTest(body=body),self.assertRaises(ValueError):scenario_half_from_mapping(body)
    def test_tire_force_direction_rear(self):
        y=(0,0,0,.01,0,0,0,0)
        d=derivatives_half(0,y,V,F)
        self.assertLess(d[7],0)
    def test_pitch_acceleration_uses_inertia(self):
        y=(0,.03,0,0,0,0,0,0)
        d1=derivatives_half(0,y,V,F)[5]
        d2=derivatives_half(0,y,replace(V,pitch_inertia_kg_m2=2000),F)[5]
        self.assertAlmostEqual(d1,2*d2)
    def test_road_profile_no_mutation(self):
        road=Road(kind='bump');v=V
        simulate_half(v,road,DT)
        self.assertEqual(road,Road(kind='bump'));self.assertEqual(v,V)
    def test_state_space_matrices_spring_consistency(self):
        # Independent generalized-coordinate M,K,C assembly (not derivative copying):
        # S rows map generalized q=[z,theta,zuf,zur] to spring extensions.
        S=((1,V.cg_to_front_m,-1,0),(1,-V.cg_to_rear_m,0,-1),(0,0,1,0),(0,0,0,1))
        ks=(V.front_spring_n_m,V.rear_spring_n_m,V.front_tire_n_m,V.rear_tire_n_m)
        c=(V.front_damping_n_s_m,V.rear_damping_n_s_m,0,0)
        masses=(V.body_mass_kg,V.pitch_inertia_kg_m2,V.front_unsprung_mass_kg,V.rear_unsprung_mass_kg)
        q=(.023,.012,-.007,.003);qd=(.12,.03,-.04,.015)
        force=[-sum(S[i][j]*(ks[i]*sum(S[i][k]*q[k] for k in range(4))+
                                  c[i]*sum(S[i][k]*qd[k] for k in range(4))) for i in range(4)) for j in range(4)]
        actual=derivatives_half(.0,(*q,*qd),V,F)[4:]
        for j in range(4):self.assertAlmostEqual(actual[j],force[j]/masses[j],places=11)

if __name__=='__main__':unittest.main()
