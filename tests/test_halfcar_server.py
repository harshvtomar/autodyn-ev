import json,threading,unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from autodyn_ev.server import Handler

class TestHalfCarAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2)
    def get(self,path):
        with urlopen(self.base+path,timeout=10) as r:return r.status,r.headers,r.read()
    def post(self,data):
        body=json.dumps(data).encode() if not isinstance(data,bytes) else data
        req=Request(self.base+'/api/halfcar/simulate',data=body,headers={'Content-Type':'application/json'},method='POST')
        try:
            with urlopen(req,timeout=10) as r:return r.status,json.loads(r.read())
        except HTTPError as e:return e.code,json.loads(e.read())
    def test_half_default(self):
        code,data=self.post({});self.assertEqual(code,200)
        self.assertEqual(data['samples'],1001)
        self.assertEqual(data['model'],'linear-four-dof-half-car-heave-pitch-equilibrium-relative')
        self.assertEqual(data['rear_road_delay_s'],.5)
        self.assertEqual(data['provenance']['release'],'0.3.0')
    def test_half_road_flat(self):
        code,data=self.post({'road':{'kind':'flat'}})
        self.assertEqual(code,200)
        self.assertEqual(data['metrics']['body_heave_acceleration_rms_m_s2'],0)
    def test_legacy_unchanged(self):
        with urlopen(Request(self.base+'/api/simulate',data=b'{}',headers={'Content-Type':'application/json'}),timeout=10) as r:
            d=json.loads(r.read())
        self.assertEqual(d['schema_version'],'1.0')
        self.assertEqual(d['samples'],1001)
        self.assertEqual(len(d['channels']),12)
    def test_half_static_assets(self):
        for p in ('/halfcar.js','/app.js','/styles.css','/'):
            with self.subTest(p=p):
                code,headers,body=self.get(p)
                self.assertEqual(code,200);self.assertGreater(len(body),200)
                self.assertEqual(headers['X-Content-Type-Options'],'nosniff')
        self.assertIn(b'model-select',self.get('/')[2]);self.assertIn(b'half-car',self.get('/')[2].lower())
    def test_bad_vehicle(self):
        for body in ({'vehicle':{'body_mass_kg':-3}}, {'vehicle':{'front_spring_n_m':900000}}, {'vehicle':{'junk':6}}):
            with self.subTest(body=body):
                code,data=self.post(body);self.assertEqual(code,400);self.assertIn('error',data)
    def test_invalid_zero_speed(self):
        code,data=self.post({'road':{'speed_m_s':0}})
        self.assertEqual(code,400);self.assertIn('speed_m_s',data['error'])
    def test_invalid_dt(self):
        code,data=self.post({'settings':{'dt_s':.02},'vehicle':{'front_unsprung_mass_kg':15,'front_tire_n_m':500000}})
        self.assertEqual(code,400);self.assertIn('step',data['error'])
    def test_unknown_field(self):
        code,data=self.post({'full_vehicle':{}})
        self.assertEqual(code,400);self.assertIn('unknown',data['error'])
    def test_invalid_body(self):
        code,data=self.post(b'{bad json')
        self.assertEqual(code,400);self.assertIn('error',data)

if __name__=='__main__':unittest.main()
