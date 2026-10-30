"""Chat 4 regressions with independent closed-form road/window checks."""
import json
import math
import threading
import unittest
from dataclasses import asdict
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from autodyn_ev.physics import Road, SimulationSettings, Vehicle, finite_road_end_s, validate_road_resolution
from autodyn_ev.halfcar import HalfCarVehicle, axle_roads, simulate_half
from autodyn_ev.simulation import simulate
from autodyn_ev.ride import ride_request, _window
from autodyn_ev.server import Handler

class TestRoadAnalytical(unittest.TestCase):
    def setUp(self): self.r = Road()
    def test_old_flat(self):
        for t in [-1,0,.5,1,5]: self.assertEqual(Road(kind='flat').displacement(t),0)
    def test_old_bump(self):
        for t in [0,.5,.575,.65,.8,.95]:
            tau=t-.5; duration=1.5/5
            expected=0 if tau<0 or tau>=duration else .03*(1-math.cos(2*math.pi*tau/duration))
            self.assertAlmostEqual(self.r.displacement(t),expected,12)
    def test_old_sine(self):
        for t in [0,.5,.53,.62,1]:
            expected=0 if t<.5 else .06*math.sin(2*math.pi*1.5*(t-.5))
            self.assertAlmostEqual(Road(kind='sine').displacement(t),expected,12)
    def test_old_step(self):
        self.assertEqual(Road(kind='step').displacement(.4999),0)
        self.assertAlmostEqual(Road(kind='step').displacement(.5),.06)
    def test_pothole_negative_of_bump(self):
        for t in [0,.5,.55,.65,.75,.8,1]:
            self.assertAlmostEqual(Road(kind='pothole').displacement(t),-self.r.displacement(t),12)
    def test_pothole_zero_at_endpoints(self):
        r=Road(kind='pothole')
        for t in [.5,.8,1.2]:self.assertAlmostEqual(r.displacement(t),0,12)
        self.assertLess(r.displacement(.65),0)
    def test_double_bump_analytical_spacing(self):
        r=Road(kind='double_bump')
        self.assertAlmostEqual(r.displacement(.65),.06)
        self.assertAlmostEqual(r.displacement(.95),0)
        self.assertAlmostEqual(r.displacement(1.25),.06)
        self.assertAlmostEqual(r.displacement(1.4),0)
        self.assertAlmostEqual(finite_road_end_s(r),1.4)
    def test_double_bump_custom_speed_spacing(self):
        r=Road(kind='double_bump',start_s=.75,bump_length_m=1,speed_m_s=10,bump_spacing_m=2,height_m=.08)
        self.assertAlmostEqual(r.displacement(.8),.08)
        self.assertAlmostEqual(r.displacement(1.1),.08)
        self.assertAlmostEqual(finite_road_end_s(r),1.15)
    def test_chirp_start_instantaneous_frequency(self):
        r=Road(kind='chirp',sine_frequency_hz=1,chirp_end_frequency_hz=3,chirp_duration_s=2,height_m=.1)
        self.assertAlmostEqual(r.displacement(.5),0)
        tau=.125;cycles=tau+.5*(3-1)*tau*tau/2
        self.assertAlmostEqual(r.displacement(.5+tau),.1*math.sin(2*math.pi*cycles))
    def test_chirp_phase_continuous_across_ramp(self):
        r=Road(kind='chirp',sine_frequency_hz=1,chirp_end_frequency_hz=3,chirp_duration_s=2)
        self.assertLess(abs(r.displacement(2.5-1e-8)-r.displacement(2.5+1e-8)),1e-5)
    def test_chirp_held_frequency_after_ramp(self):
        r=Road(kind='chirp',sine_frequency_hz=.5,chirp_end_frequency_hz=2,chirp_duration_s=1)
        for x in [1,1.25,1.37,2]:
            phase=(.5+2)/2*1+2*(x-1)
            self.assertAlmostEqual(r.displacement(r.start_s+x),r.height_m*math.sin(2*math.pi*phase))
    def test_chirp_down_ramp_allowed(self):
        r=Road(kind='chirp',sine_frequency_hz=4,chirp_end_frequency_hz=1)
        r.validate();self.assertTrue(math.isfinite(r.displacement(1.5)))
    def test_pothole_delayed_at_axles(self):
        v=HalfCarVehicle();r=Road(kind='pothole')
        for t in [.65,1.15,2]:
            f,rear=axle_roads(t,v,r)
            self.assertAlmostEqual(f,r.displacement(t))
            self.assertAlmostEqual(rear,r.displacement(t-.5))
    def test_double_feature_delayed_at_axles(self):
        v=HalfCarVehicle();r=Road(kind='double_bump')
        self.assertAlmostEqual(axle_roads(1.25,v,r)[0],.06)
        self.assertAlmostEqual(axle_roads(1.75,v,r)[1],.06)
    def test_chirp_delayed_at_axles(self):
        v=HalfCarVehicle();r=Road(kind='chirp')
        for t in [0,1.0,1.75,3.1]:
            self.assertAlmostEqual(axle_roads(t,v,r)[1],r.displacement(t-v.wheelbase_m/r.speed_m_s))
    def test_finite_road_end(self):
        self.assertEqual(finite_road_end_s(Road(kind='flat')),0)
        self.assertIsNone(finite_road_end_s(Road(kind='sine')))
        self.assertIsNone(finite_road_end_s(Road(kind='step')))
        self.assertIsNone(finite_road_end_s(Road(kind='chirp')))
        self.assertAlmostEqual(finite_road_end_s(Road(kind='pothole')),.8)
    def test_bad_kinds_and_fields(self):
        for road in [Road(kind='unknown'),Road(bump_spacing_m=.1),Road(chirp_duration_s=0),Road(chirp_end_frequency_hz=6),Road(bump_spacing_m=float('nan')),Road(chirp_duration_s=True)]:
            with self.subTest(road=road),self.assertRaises(ValueError):road.validate()
    def test_resolution_guard_new_pulse(self):
        for kind in ('bump','pothole','double_bump'):
            with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,'bump'):
                validate_road_resolution(Road(kind=kind,bump_length_m=.5,speed_m_s=40),.005)
    def test_resolution_guard_chirp_high_end(self):
        with self.assertRaisesRegex(ValueError,'chirp'):
            validate_road_resolution(Road(kind='chirp',sine_frequency_hz=1,chirp_end_frequency_hz=5),.011)
        validate_road_resolution(Road(kind='chirp',sine_frequency_hz=1,chirp_end_frequency_hz=5),.005)
    def test_resolution_zero_height_exemption(self):
        validate_road_resolution(Road(kind='double_bump',height_m=0,bump_length_m=.5,speed_m_s=40),.02)
    def test_resolution_both_models(self):
        for kind in ['pothole','double_bump','chirp']:
            with self.subTest(kind=kind):
                r=Road(kind=kind)
                q=simulate(road=r);h=simulate_half(road=r)
                self.assertEqual(q['samples'],h['samples'])
                self.assertTrue(math.isfinite(q['metrics']['body_acceleration_rms_m_s2']))
                self.assertTrue(math.isfinite(h['metrics']['body_heave_acceleration_rms_m_s2']))
    def test_flat_zero_still(self):
        for kind in ['flat','pothole','double_bump','chirp']:
            if kind!='flat':road=Road(kind=kind,height_m=0)
            else:road=Road(kind=kind)
            self.assertEqual(simulate(road=road)['metrics']['body_acceleration_rms_m_s2'],0)
            self.assertEqual(simulate_half(road=road)['metrics']['body_heave_acceleration_rms_m_s2'],0)

class TestRideMetrics(unittest.TestCase):
    def test_known_rms_trapezoid(self):
        m=_window([0,1,2],[0,1,0],0,2)
        self.assertAlmostEqual(m['rms'],math.sqrt(.5))
        self.assertEqual(m['peak_to_peak'],1)
    def test_subwindow_interpolation(self):
        m=_window([0,1,2],[0,1,0],.5,1.5)
        self.assertAlmostEqual(m['rms'],math.sqrt(.625))
        self.assertEqual(m['peak_to_peak'],.5)
    def test_bad_windows(self):
        for start,end in [(-1,1),(1,1),(0,3),(2,1)]:
            with self.subTest((start,end)),self.assertRaises(ValueError):_window([0,1,2],[0,1,0],start,end)
    def test_default_quarter(self):
        s=ride_request({'model':'quarter'})
        self.assertEqual(s['release'],'0.4.0')
        self.assertEqual(s['current']['samples'],1001)
        self.assertIn('post_event',s['current']['windows'])
        self.assertTrue(s['current']['metrics']['body_acceleration_rms_si']>0)
    def test_default_half(self):
        s=ride_request({'model':'half'})
        self.assertEqual(s['current']['samples'],1001)
        self.assertAlmostEqual(s['current']['finite_road_last_excitation_s'],1.3)
        self.assertIn('front_suspension_travel_rms_si',s['current']['metrics'])
    def test_sustained_has_no_settling(self):
        for kind in ['sine','step','chirp']:
            for model in ['quarter','half']:
                with self.subTest((model,kind)):
                    d=ride_request({'model':model,'scenario':{'road':{'kind':kind}}})['current']
                    self.assertIsNone(d['metrics']['settling_after_last_excitation_s'])
                    self.assertNotIn('post_event',d['windows'])
    def test_double_event_end(self):
        q=ride_request({'model':'quarter','scenario':{'road':{'kind':'double_bump'}}})['current']
        h=ride_request({'model':'half','scenario':{'road':{'kind':'double_bump'}}})['current']
        self.assertAlmostEqual(q['finite_road_last_excitation_s'],1.4)
        self.assertAlmostEqual(h['finite_road_last_excitation_s'],1.9)
    def test_flat_zero_metrics(self):
        for model in ['quarter','half']:
            d=ride_request({'model':model,'scenario':{'road':{'kind':'flat'}}})['current']
            self.assertEqual(d['metrics']['body_acceleration_rms_si'],0)
            self.assertEqual(d['metrics']['body_acceleration_peak_to_peak_si'],0)
            self.assertIsNone(d['metrics']['settling_after_last_excitation_s'])
    def test_quarter_independent_rms_trapezoid(self):
        d=ride_request({'model':'quarter'})['current'];c=d['waveforms'];a=c['sprung_acceleration_m_s2'];t=c['time_s'];dt=t[1]-t[0]
        area=dt*(.5*a[0]**2+sum(x*x for x in a[1:-1])+.5*a[-1]**2)
        self.assertAlmostEqual(d['metrics']['body_acceleration_rms_si'],math.sqrt(area/t[-1]),11)
    def test_half_independent_travel_peaks(self):
        d=ride_request({'model':'half'})['current'];f=d['waveforms']['front_suspension_travel_m']
        self.assertAlmostEqual(d['metrics']['front_suspension_travel_peak_to_peak_si'],max(f)-min(f))
    def test_full_vs_post_window(self):
        d=ride_request({'model':'half'})['current'];full=d['windows']['full'];post=d['windows']['post_event']
        self.assertEqual(full['start_s'],0);self.assertEqual(full['end_s'],5)
        self.assertLess(post['start_s'],post['end_s'])
    def test_same_model_baseline(self):
        base={'road':{'kind':'double_bump'}}
        variant={'road':{'kind':'double_bump'},'vehicle':{'sprung_mass_kg':400}}
        r=ride_request({'model':'quarter','baseline':base,'scenario':variant})
        self.assertIsNotNone(r['baseline']);self.assertIsNotNone(r['deltas'])
        self.assertNotEqual(r['deltas']['body_acceleration_rms_si'],0)
        self.assertEqual(r['baseline']['scenario']['road'],r['current']['scenario']['road'])
    def test_reject_mixed_road_comparison(self):
        with self.assertRaisesRegex(ValueError,'identical road'):
            ride_request({'baseline':{'road':{'kind':'pothole'}},'scenario':{'road':{'kind':'double_bump'}}})
    def test_reject_mixed_timestep(self):
        with self.assertRaisesRegex(ValueError,'identical road'):
            ride_request({'baseline':{},'scenario':{'settings':{'dt_s':.0025}}})
    def test_reject_cross_model(self):
        with self.assertRaises(ValueError):ride_request({'model':'both'})
    def test_reject_unknown_top_level(self):
        with self.assertRaises(ValueError):ride_request({'scenario':{},'junk':1})
    def test_reject_road_field(self):
        with self.assertRaises(ValueError):ride_request({'scenario':{'road':{'mystery':1}}})
    def test_pitch_warning_and_provenance(self):
        r=ride_request({'model':'half'})
        self.assertIn('solver',r);self.assertIn('units',r)
        self.assertEqual(r['current']['scenario']['road']['kind'],'bump')
        self.assertTrue(any('ISO' in x for x in r['current']['warnings']))
    def test_timesampling_refinement_quarter(self):
        r1=ride_request({'model':'quarter','scenario':{'settings':{'dt_s':.005}}})['current']['metrics']['body_acceleration_rms_si']
        r2=ride_request({'model':'quarter','scenario':{'settings':{'dt_s':.0025}}})['current']['metrics']['body_acceleration_rms_si']
        self.assertLess(abs(r1-r2),.015)
    def test_timesampling_refinement_half(self):
        r1=ride_request({'model':'half','scenario':{'settings':{'dt_s':.005}}})['current']['metrics']['body_acceleration_rms_si']
        r2=ride_request({'model':'half','scenario':{'settings':{'dt_s':.0025}}})['current']['metrics']['body_acceleration_rms_si']
        self.assertLess(abs(r1-r2),.015)
    def test_zero_height_chirp_is_zero(self):
        for model in ['quarter','half']:
            d=ride_request({'model':model,'scenario':{'road':{'kind':'chirp','height_m':0}}})['current']
            self.assertEqual(d['metrics']['body_acceleration_rms_si'],0)

class TestRideAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.s.serve_forever,daemon=True);cls.thread.start()
        cls.base='http://127.0.0.1:'+str(cls.s.server_port)
    @classmethod
    def tearDownClass(cls):
        cls.s.shutdown();cls.s.server_close();cls.thread.join(timeout=3)
    def post(self,path='/api/ride/study',body=None,ctype='application/json'):
        data=json.dumps({} if body is None else body).encode() if not isinstance(body,bytes) else body
        req=Request(self.base+path,data=data,headers={'Content-Type':ctype},method='POST')
        try:
            with urlopen(req,timeout=20) as r:return r.status,json.loads(r.read())
        except HTTPError as e:return e.code,json.loads(e.read())
    def test_api_default(self):
        code,d=self.post();self.assertEqual(code,200);self.assertEqual(d['release'],'0.4.0')
    def test_api_half(self):
        code,d=self.post(body={'model':'half','scenario':{'road':{'kind':'pothole'}}})
        self.assertEqual(code,200);self.assertEqual(d['current']['model'],'half')
    def test_api_comparison(self):
        code,d=self.post(body={'model':'half','baseline':{},'scenario':{'vehicle':{'pitch_inertia_kg_m2':2000}}})
        self.assertEqual(code,200);self.assertIsNotNone(d['deltas'])
    def test_api_legacy_preserved(self):
        for path in ['/api/simulate','/api/halfcar/simulate']:
            code,d=self.post(path=path);self.assertEqual(code,200);self.assertIn('channels',d)
    def test_api_assets(self):
        for name in ['/ride.js','/app.js','/halfcar.js','/','/styles.css']:
            with self.subTest(name=name),urlopen(self.base+name) as r:
                self.assertEqual(r.status,200)
                self.assertEqual(r.headers['X-Content-Type-Options'],'nosniff')
        with urlopen(self.base+'/') as r:
            page=r.read().decode();self.assertIn('quarter-ride-run',page);self.assertIn('half-ride-run',page)
    def test_api_bad_input(self):
        for b in [{'model':'bogus'},{'model':'half','scenario':{'road':{'speed_m_s':0}}},{'model':'quarter','scenario':{'road':{'kind':'invalid'}}}]:
            with self.subTest(b=b):
                code,d=self.post(body=b);self.assertEqual(code,400);self.assertIn('error',d)
    def test_api_content_type(self):
        code,_=self.post(ctype='text/plain');self.assertEqual(code,415)
    def test_api_malformed_json(self):
        code,_=self.post(body=b'{no');self.assertEqual(code,400)
    def test_api_response_version(self):
        with urlopen(self.base+'/api/health') as r:
            d=json.loads(r.read());self.assertEqual(d['version'],'0.4.0')

if __name__=='__main__':unittest.main()
