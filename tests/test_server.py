import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from autodyn_ev.server import Handler


class TestWebServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def fetch(self,path,body=None,ctype='application/json'):
        if body is None:
            req=Request(self.base+path)
        else:
            req=Request(self.base+path,data=body,headers={'Content-Type':ctype},method='POST')
        try:
            with urlopen(req,timeout=8) as r: return r.status,r.headers,r.read()
        except HTTPError as e: return e.code,e.headers,e.read()

    def test_get_health(self):
        code,headers,data=self.fetch('/api/health')
        self.assertEqual(code,200)
        self.assertEqual(json.loads(data)['status'],'ok')
        self.assertEqual(headers['X-Content-Type-Options'],'nosniff')

    def test_defaults(self):
        code,_,data=self.fetch('/api/defaults')
        self.assertEqual(code,200)
        self.assertEqual(json.loads(data)['vehicle']['sprung_mass_kg'],300)

    def test_page_has_schematic(self):
        code,_,data=self.fetch('/')
        self.assertEqual(code,200)
        self.assertIn(b'AutoDyn EV',data)
        self.assertIn(b'Suspension response',data)

    def test_assets_served(self):
        for path in ['/styles.css','/app.js']:
            code,_,data=self.fetch(path)
            self.assertEqual(code,200)
            self.assertGreater(len(data),100)

    def test_simulation_post(self):
        code,headers,data=self.fetch('/api/simulate',b'{}')
        self.assertEqual(code,200)
        payload=json.loads(data)
        self.assertEqual(payload['samples'],1001)
        self.assertEqual(len(payload['channels']['time_s']),1001)

    def test_road_flat_post(self):
        code,_,data=self.fetch('/api/simulate',b'{"road":{"kind":"flat"}}')
        self.assertEqual(code,200)
        self.assertEqual(json.loads(data)['metrics']['body_acceleration_rms_m_s2'],0)

    def test_bad_json_is_400(self):
        code,_,data=self.fetch('/api/simulate',b'{bad')
        self.assertEqual(code,400)
        self.assertIn('error',json.loads(data))

    def test_bad_type_is_415(self):
        code,_,data=self.fetch('/api/simulate',b'{}','text/plain')
        self.assertEqual(code,415)

    def test_invalid_fields_are_400(self):
        code,_,data=self.fetch('/api/simulate',b'{"vehicle":{"sprung_mass_kg":0}}')
        self.assertEqual(code,400)
        self.assertIn('sprung_mass_kg',json.loads(data)['error'])

    def test_invalid_route_is_404(self):
        code,_,data=self.fetch('/.env')
        self.assertEqual(code,404)

    def test_unknown_post_route_is_404(self):
        code,_,data=self.fetch('/api/admin',b'{}')
        self.assertEqual(code,404)

    def test_no_cors_header(self):
        _,headers,_=self.fetch('/api/health')
        self.assertIsNone(headers.get('Access-Control-Allow-Origin'))


if __name__=='__main__':unittest.main()
