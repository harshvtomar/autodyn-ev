import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request,urlopen

from autodyn_ev.server import Handler
from tests.test_analysis import base

class TestAnalysisAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.t=threading.Thread(target=cls.s.serve_forever,daemon=True)
        cls.t.start();cls.base=f'http://127.0.0.1:{cls.s.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.s.shutdown();cls.s.server_close();cls.t.join(timeout=2)
    def request(self,endpoint,payload):
        data=json.dumps(payload).encode()
        req=Request(self.base+'/api/'+endpoint,data=data,headers={'Content-Type':'application/json'},method='POST')
        try:
            with urlopen(req,timeout=15) as r:return r.status,json.load(r)
        except HTTPError as e:return e.code,json.load(e)
    def test_modal(self):
        status,resp=self.request('modal',{'vehicle':base()['vehicle']})
        self.assertEqual(status,200)
        self.assertEqual(len(resp['oscillatory_modes']),2)
    def test_compare(self):
        sc=base();status,resp=self.request('compare',{'baseline':sc,'variant':sc})
        self.assertEqual(status,200);self.assertEqual(resp['kind'],'comparison')
    def test_sweep(self):
        status,resp=self.request('sweep',{'scenario':base(),'parameter':'damping_n_s_m','start':1000,'stop':2000,'count':3})
        self.assertEqual(status,200);self.assertEqual(len(resp['points']),3)
    def test_convergence(self):
        status,resp=self.request('convergence',{'scenario':base(),'steps_s':[.01,.005,.0025]})
        self.assertEqual(status,200);self.assertEqual(len(resp['results']),3)
    def test_invalid_request_is_400(self):
        status,resp=self.request('sweep',{'garbage':123})
        self.assertEqual(status,400);self.assertIn('error',resp)
    def test_massive_sweep_rejected(self):
        sc=base();sc['settings']={'duration_s':15,'dt_s':.001}
        status,resp=self.request('sweep',{'scenario':sc,'parameter':'damping_n_s_m','start':500,'stop':2000,'count':11})
        self.assertEqual(status,400);self.assertIn('budget',resp['error'])

if __name__=='__main__':unittest.main()
