import io
import json
import unittest
from autodyn_ev.hosted import application

class HostedTests(unittest.TestCase):
    def call(self, path='/', method='GET', raw=b'{}', **extra):
        env = {'PATH_INFO':path, 'REQUEST_METHOD':method, 'CONTENT_TYPE':'application/json',
               'CONTENT_LENGTH':str(len(raw)), 'wsgi.input':io.BytesIO(raw), **extra}
        result = {}
        def start(status, headers):
            result.update(status=int(status[:3]), headers=dict(headers))
        result['body'] = b''.join(application(env, start))
        return result

    def test_static_whitelist_and_headers(self):
        self.assertEqual(self.call()['status'], 200)
        self.assertEqual(self.call('/../README.md')['status'], 404)
        self.assertEqual(self.call()['headers']['X-Frame-Options'], 'DENY')
        self.assertEqual(self.call(method='HEAD')['body'], b'')

    def test_invalid_requests(self):
        for raw in (b'[]', b'null', b'{', b'{"x":NaN}', b'['*1100):
            self.assertEqual(self.call('/api/simulate','POST',raw)['status'],400)
        self.assertEqual(self.call('/api/simulate','POST',CONTENT_LENGTH='65537')['status'],413)
        self.assertEqual(self.call('/api/simulate','POST',CONTENT_TYPE='text/plain')['status'],415)
        self.assertEqual(self.call('/api/simulate','POST',HTTP_SEC_FETCH_SITE='cross-site')['status'],403)
        self.assertEqual(self.call(method='DELETE')['status'],405)

    def test_mass_regression(self):
        from autodyn_ev.simulation import simulate, scenario_from_mapping
        for mass in (300, 500):
            data={'vehicle':{'sprung_mass_kg':mass}}
            actual=self.call('/api/simulate','POST',json.dumps(data).encode())
            self.assertEqual(actual['status'],200)
            self.assertEqual(json.loads(actual['body']),simulate(*scenario_from_mapping(data)))
