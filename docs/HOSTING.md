# Optional hosted demo

The v1.0.0 tag preserves the accepted local release. The main branch adds an optional WSGI transport; the physics, browser assets and local server are unchanged.

Install `requirements-hosting.txt`, then run:

```sh
gunicorn --config gunicorn.conf.py autodyn_ev.hosted:application
```

Render configuration: Python 3, build `pip install -r requirements-hosting.txt`, start command above, health check `/api/health`, Free compute. No database, disk, payment method or paid features are required. Render's HTTPS proxy fronts Gunicorn. Do not expose the local standard-library development server.

Safety boundaries: two synchronous workers, backlog 16, 120-second worker timeout, periodic worker recycling, bounded request headers, 64 KiB JSON bodies, object/finite-number checks, static-file allowlist, same-origin browser policy and the existing numerical step/case caps. A saturated demo can be temporarily unavailable; these limits are not a claim of production-grade denial-of-service protection. No user data is stored. The Gunicorn control socket is disabled.

The free service sleeps after inactivity and can be suspended at usage limits. Do not add a payment method or upgrade compute to keep the demo within the zero-cost scope. Hosted availability is not guaranteed.

Verification before initial deployment: 396 local tests passed (393 inherited plus three WSGI transport checks); release audit 8/8. A real Gunicorn HTTP smoke check returned RMS 0.9060817384 for 300 kg and 0.5556923126 for 500 kg. Public deployment and browser verification are separate acceptance steps.
