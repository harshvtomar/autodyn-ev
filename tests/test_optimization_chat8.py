"""Chat 8 independent deterministic design-study and error-contract checks."""
import copy
import json
import math
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from dataclasses import asdict

from autodyn_ev.optimization import _grid, _metrics, _pareto, optimization_request
from autodyn_ev.physics import Road, SimulationSettings, Vehicle
from autodyn_ev.halfcar import HalfCarVehicle, simulate_half
from autodyn_ev.simulation import simulate
from autodyn_ev.server import Handler


def independent_rms(time,signal):
    # A separate trapezoidal discretization of the squared signal.
    energy = math.fsum((time[i+1]-time[i]) * (signal[i]**2 + signal[i+1]**2)/2 for i in range(len(time)-1))
    return math.sqrt(energy/(time[-1]-time[0]))


class TestOptimizationMath(unittest.TestCase):
    def test_study_default(self):
        d=optimization_request({})
        self.assertEqual(d['application_version'],'0.8.0')
        self.assertEqual(d['schema_version'],'optimization-study-1.0')
        self.assertEqual(d['grid']['run_count'],7)
        self.assertEqual(d['feasible_count'],7)
        self.assertEqual([x['id'] for x in d['candidates']],list(range(1,8)))

    def test_two_dimensional_grid(self):
        d=optimization_request({'parameters':['damping_n_s_m','suspension_stiffness_n_m']})
        self.assertEqual(d['grid']['run_count'],49)
        self.assertEqual(len({(x['parameters']['damping_n_s_m'],x['parameters']['suspension_stiffness_n_m']) for x in d['candidates']}),49)
        self.assertEqual(d['grid']['hard_cap'],49)

    def test_half_case_counts(self):
        d=optimization_request({'model':'half','parameters':['front_spring_n_m','rear_damping_n_s_m']})
        self.assertEqual(d['grid']['run_count'],49)
        self.assertIn('body_pitch_peak_deg',d['candidates'][0]['metrics'])
        self.assertIn('rear_suspension_travel_peak_to_peak_mm',d['candidates'][0]['metrics'])

    def test_invariant_baseline(self):
        d=optimization_request({})
        self.assertEqual(d['baseline']['vehicle'],asdict(Vehicle()))
        self.assertEqual(d['scenario']['road'],asdict(Road()))
        self.assertEqual(d['baseline']['metrics'],_metrics(simulate(), 'quarter'))

    def test_metric_recomputation_quarter(self):
        raw=simulate()
        m=_metrics(raw,'quarter');t=raw['channels']['time_s'];ch=raw['channels']
        self.assertAlmostEqual(m['body_acceleration_rms_m_s2'],independent_rms(t,ch['sprung_acceleration_m_s2']),places=13)
        self.assertAlmostEqual(m['suspension_travel_peak_to_peak_mm'],1000*(max(ch['suspension_travel_m'])-min(ch['suspension_travel_m'])),places=13)
        self.assertAlmostEqual(m['tire_deflection_peak_abs_mm'],1000*max(abs(x) for x in ch['tire_deflection_m']),places=13)

    def test_metric_recomputation_half(self):
        raw=simulate_half()
        m=_metrics(raw,'half');t=raw['channels']['time_s'];ch=raw['channels']
        self.assertAlmostEqual(m['body_acceleration_rms_m_s2'],independent_rms(t,ch['body_heave_acceleration_m_s2']),places=13)
        for axle in ('front','rear'):
            travel=ch[axle+'_suspension_travel_m'];tire=ch[axle+'_tire_deflection_m']
            self.assertAlmostEqual(m[axle+'_suspension_travel_peak_to_peak_mm'],1000*(max(travel)-min(travel)),places=12)
            self.assertAlmostEqual(m[axle+'_tire_deflection_peak_abs_mm'],1000*max(abs(x) for x in tire),places=12)
        self.assertEqual(m['suspension_travel_peak_to_peak_mm'],max(m[k+'_suspension_travel_peak_to_peak_mm'] for k in ('front','rear')))

    def test_determinism(self):
        b={'model':'half','parameters':['rear_spring_n_m']}
        self.assertEqual(json.dumps(optimization_request(b),sort_keys=True),json.dumps(optimization_request(b),sort_keys=True))

    def test_prescribed_grid(self):
        d=optimization_request({'parameters':['suspension_stiffness_n_m']})
        vals=d['grid']['values']['suspension_stiffness_n_m']
        self.assertAlmostEqual(vals[0],18000*.8)
        self.assertAlmostEqual(vals[-1],18000*1.2)
        self.assertEqual(vals[3],18000.)

    def test_grid_clamped(self):
        vals=_grid(115000,5000,120000)
        self.assertEqual(vals[-1],120000)
        self.assertGreater(vals[0],5000)

    def test_no_feasible(self):
        d=optimization_request({'constraints':{'max_body_acceleration_rms_m_s2':0.000001}})
        self.assertEqual(d['feasible_count'],0)
        self.assertEqual(d['pareto_ids'],[])
        self.assertIsNone(d['selected_id'])
        self.assertTrue(all(not c['feasible'] for c in d['candidates']))

    def test_limits_within_feasible(self):
        d=optimization_request({'constraints':{'max_suspension_travel_peak_to_peak_mm':90.0}})
        for c in d['candidates']:
            self.assertEqual(c['feasible'],c['metrics']['suspension_travel_peak_to_peak_mm']<=90.0)

    def test_independent_pareto(self):
        d=optimization_request({'model':'half','parameters':['front_spring_n_m','rear_spring_n_m']})
        cases=d['candidates'];valid=[]
        for p in cases:
            if not p['feasible']:continue
            x,y=(p['metrics'][k] for k in ('body_acceleration_rms_m_s2','suspension_travel_peak_to_peak_mm'))
            dominated=False
            for q in cases:
                if p is q or not q['feasible']:continue
                a,b=(q['metrics'][k] for k in ('body_acceleration_rms_m_s2','suspension_travel_peak_to_peak_mm'))
                if a<=x and b<=y and (a<x or b<y):dominated=True;break
            if not dominated:valid.append(p['id'])
        self.assertEqual(valid,d['pareto_ids'])

    def test_independent_tie_breaking(self):
        d=optimization_request({'model':'quarter','parameters':['damping_n_s_m','suspension_stiffness_n_m']})
        eligible=[c for c in d['candidates'] if c['feasible']]
        m=min(eligible,key=lambda c:(c['metrics']['body_acceleration_rms_m_s2'],c['metrics']['suspension_travel_peak_to_peak_mm'],c['metrics']['tire_deflection_peak_abs_mm'],c['id']))
        self.assertEqual(m['id'],d['selected_id'])

    def test_explicit_units(self):
        d=optimization_request({})
        self.assertEqual(d['units']['body_acceleration_rms_m_s2'],'m/s²')
        self.assertEqual(d['grid']['bounds']['damping_n_s_m']['unit'],'N·s/m')
        self.assertEqual(d['objectives'][0]['direction'],'min')

    def test_no_mutation(self):
        body={'model':'quarter','vehicle':{'damping_n_s_m':2000},'parameters':['damping_n_s_m']}
        before=copy.deepcopy(body);optimization_request(body);self.assertEqual(body,before)

    def test_invalid_top_level(self):
        for data in ([],42,{'bad':1},{'model':'truck'},{'model':[]},{'model':'braking'}):
            with self.subTest(data=data),self.assertRaises((ValueError,TypeError)):optimization_request(data)

    def test_reject_invalid_parameter_selection(self):
        for params in ([],['damping_n_s_m']*2,['damping_n_s_m']*3,['no'],['body_mass_kg'],False):
            with self.subTest(params=params),self.assertRaises((ValueError,TypeError)):
                optimization_request({'parameters':params})

    def test_reject_wrong_model_parameter(self):
        with self.assertRaises(ValueError):optimization_request({'model':'half','parameters':['damping_n_s_m']})

    def test_reject_oversized_grid(self):
        for n in (6,8,10,0,49,'7',7.0,True):
            with self.subTest(n=n),self.assertRaises(ValueError):optimization_request({'points_per_axis':n})

    def test_reject_nonfinite_limits(self):
        for value in (float('nan'),float('inf'),-1,'10',True,1e6):
            with self.subTest(value=value),self.assertRaises(ValueError):
                optimization_request({'constraints':{'max_tire_deflection_peak_abs_mm':value}})

    def test_reject_unknown_constraint(self):
        for limits in ({'no':100},['x'],0):
            with self.subTest(limits=limits),self.assertRaises(ValueError):optimization_request({'constraints':limits})

    def test_reject_excessive_duration(self):
        with self.assertRaisesRegex(ValueError,'3000'):
            optimization_request({'settings':{'duration_s':15,'dt_s':.001}})

    def test_reject_bad_vehicle_or_road(self):
        for bad in ({'vehicle':{'damping_n_s_m':-100}},
                    {'road':{'speed_m_s':0}},
                    {'settings':{'dt_s':0}},
                    {'settings':{'duration_s':100}}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):optimization_request(bad)

    def test_zero_damping_grid_rejected(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):
            optimization_request({'vehicle':{'damping_n_s_m':0},'parameters':['damping_n_s_m']})

    def test_constraints_not_combined_score(self):
        d=optimization_request({})
        self.assertNotIn('score',d)
        self.assertTrue(all('score' not in c and 'combined_score' not in c['metrics'] for c in d['candidates']))
        self.assertIn('Pareto' if False else 'pareto_ids',d)
        self.assertEqual(len(d['objectives']),2)


class TestOptimizationAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2)
    def req(self,path,body=None,content='application/json'):
        payload=None if body is None else (body if isinstance(body,bytes) else json.dumps(body).encode())
        r=Request(self.base+path,data=payload,headers={'Content-Type':content} if body is not None else {},method='POST' if body is not None else 'GET')
        try:
            with urlopen(r,timeout=15) as f:return f.status,json.loads(f.read()) if path.startswith('/api/') else f.read()
        except HTTPError as e:return e.code,json.loads(e.read())
    def test_api_default(self):
        status,data=self.req('/api/optimization/study',{})
        self.assertEqual(status,200);self.assertEqual(data['grid']['run_count'],7)
    def test_api_two_parameters(self):
        status,data=self.req('/api/optimization/study',{'parameters':['suspension_stiffness_n_m','damping_n_s_m']})
        self.assertEqual(status,200);self.assertEqual(len(data['candidates']),49)
    def test_api_half(self):
        status,data=self.req('/api/optimization/study',{'model':'half','parameters':['front_spring_n_m']})
        self.assertEqual(status,200);self.assertEqual(data['model'],'half')
    def test_api_rejects_excess(self):
        status,data=self.req('/api/optimization/study',{'points_per_axis':999})
        self.assertEqual(status,400);self.assertIn('error',data)
    def test_api_rejects_bad_body(self):
        status,data=self.req('/api/optimization/study',b'{bad')
        self.assertEqual(status,400);self.assertIn('error',data)
    def test_api_wrong_content(self):
        self.assertEqual(self.req('/api/optimization/study',{},'text/plain')[0],415)
    def test_api_no_override(self):
        self.assertEqual(self.req('/api/health')[1]['version'],'0.4.0')
        self.assertEqual(self.req('/api/health')[1]['current_release_version'],'0.8.0')
        self.assertEqual(self.req('/api/regen/simulate',{})[0],200)
    def test_assets(self):
        r=Request(self.base+'/optimization.js')
        with urlopen(r,timeout=10) as f:self.assertIn(b'autodyn-chat8-optimization.csv',f.read())
    def test_legacy_api_default(self):
        self.assertEqual(self.req('/api/simulate',{})[0],200)
        self.assertEqual(self.req('/api/halfcar/simulate',{})[0],200)

if __name__=='__main__':unittest.main()
