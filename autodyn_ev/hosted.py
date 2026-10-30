"""WSGI transport for the public educational demo; physics and local server unchanged."""
from http import HTTPStatus
from io import BytesIO
import json
from .server import Handler, MAX_BODY


class Response(Handler):
    """Reuse the accepted routes without starting the local HTTP server."""
    def __init__(self, environ, body=b''):
        self.path = environ.get('PATH_INFO', '/')
        self.headers = {'Content-Type': environ.get('CONTENT_TYPE', ''),
                        'Content-Length': str(len(body))}
        self.rfile = BytesIO(body)

    def _send(self, status, body, mime):
        self.status, self.body, self.mime = status, body, mime


def application(environ, start_response):
    response = Response(environ)
    method = environ.get('REQUEST_METHOD', 'GET')
    try:
        if method in ('GET', 'HEAD'):
            response.do_GET()
        elif method == 'POST':
            # Only finite, bounded JSON objects reach the accepted route validators.
            size = int(environ.get('CONTENT_LENGTH') or '0')
            if size <= 0 or size > MAX_BODY:
                response._json(413, {'error': 'Request body must be 1–65536 bytes.'})
            elif environ.get('CONTENT_TYPE', '').split(';')[0].strip().lower() != 'application/json':
                response._json(415, {'error': 'Content-Type must be application/json'})
            elif environ.get('HTTP_SEC_FETCH_SITE') == 'cross-site':
                response._json(403, {'error': 'Use the simulator on this website.'})
            else:
                raw = environ['wsgi.input'].read(size)
                if len(raw) != size:
                    raise ValueError('Incomplete request body')
                data = json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Non-finite JSON number')))
                if not isinstance(data, dict):
                    raise ValueError('Request must be a JSON object')
                response = Response(environ, raw)
                response.do_POST()
        else:
            response._json(405, {'error': 'Method not allowed'})
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError, OverflowError):
        response._json(400, {'error': 'Invalid request. Check the input values and structure.'})
    except Exception:
        response._json(500, {'error': 'Simulation could not complete. Try a smaller study.'})
    headers = [('Content-Type', response.mime), ('Content-Length', str(len(response.body))),
               ('Cache-Control', 'no-store'), ('X-Content-Type-Options', 'nosniff'),
               ('X-Frame-Options', 'DENY'), ('Referrer-Policy', 'no-referrer'),
               ('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; form-action 'none'")]
    start_response(f'{response.status} {HTTPStatus(response.status).phrase}', headers)
    return [b'' if method == 'HEAD' else response.body]
