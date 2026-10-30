import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from autodyn_ev.server import Handler

class TestBrakingAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=ThreadingHTTPServer(('127.0.0.1',0),Handler);cls.thread=threading.Thread(target=cls.s.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.s.server_port}'
    @classmethod
    def tearDownClass(cls):cls.s.shutdown();cls.s.server_close();cls.thread.join(timeout=2)
    def request(self,path,body=None,content='application/json'):
        r=Request(self.base+path,data=body,headers={'Content-Type':content} if body is not None else {},method='POST' if body is not None else 'GET')
        try:
            with urlopen(r,timeout=10) as f:return f.status,dict(f.headers),f.read()
        except HTTPError as e:return e.code,dict(e.headers),e.read()
    def test_new_post(self):
        status,headers,b=self.request('/api/braking/simulate',b'{}')
        self.assertEqual(status,200);d=json.loads(b);self.assertEqual(d['version'],'0.5.0');self.assertAlmostEqual(d['metrics']['stopping_distance_m'],40,places=10)
    def test_ramp_post(self):
        status,_,b=self.request('/api/braking/simulate',b'{"scenario":{"profile":"ramp"}}')
        self.assertEqual(status,200);self.assertGreater(json.loads(b)['metrics']['stopping_time_s'],4)
    def test_reject_invalid_payload(self):
        for raw in (b'{broken',b'[]',b'{"mass_kg":0}',b'{"profile":"abs"}',b'{"cg_height_m":5}'):
            status,_,b=self.request('/api/braking/simulate',raw)
            self.assertEqual(status,400);self.assertIn('error',json.loads(b))
    def test_reject_wrong_type(self):self.assertEqual(self.request('/api/braking/simulate',b'{}','text/plain')[0],415)
    def test_reject_large_request(self):self.assertEqual(self.request('/api/braking/simulate',b' '*70000)[0],413)
    def test_asset_is_served(self):
        status,_,b=self.request('/braking.js');self.assertEqual(status,200);self.assertIn(b'braking-export-csv',b)
    def test_html_contains_app(self):
        status,_,b=self.request('/');self.assertEqual(status,200);self.assertIn(b'id="braking-lab"',b)
    def test_legacy_health_compatible(self):
        status,_,b=self.request('/api/health');self.assertEqual(status,200);d=json.loads(b)
        self.assertEqual(d['version'],'0.4.0');self.assertEqual(d['application_version'],'0.5.0')
    def test_content_security(self):
        status,h,b=self.request('/');self.assertIn('Content-Security-Policy',h)

if __name__=='__main__':unittest.main()
