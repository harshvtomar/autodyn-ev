"""Local-only, standard-library HTTP server for the browser UI."""

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from . import CURRENT_RELEASE_VERSION, ACTIVE_APPLICATION_VERSION, FINAL_RELEASE_VERSION
from .physics import Road, SimulationSettings, Vehicle
from .simulation import scenario_from_mapping, simulate
from .analysis import analysis_request

WEB_DIR = (Path(__file__).resolve().parent.parent / "web").resolve()
FILES = {"/": "index.html", "/index.html": "index.html", "/app.js": "app.js", "/styles.css": "styles.css", "/halfcar.js": "halfcar.js", "/ride.js": "ride.js", "/braking.js": "braking.js", "/regen.js": "regen.js", "/viz3d_math.js": "viz3d_math.js", "/viz3d.js": "viz3d.js", "/optimization.js": "optimization.js"}
MAX_BODY = 64 * 1024


class Handler(BaseHTTPRequestHandler):
    server_version = "AutoDynEV/1.0"

    def _send(self, status: int, body: bytes, mime: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, data: object) -> None:
        self._send(status, json.dumps(data, allow_nan=False, separators=(",", ":")).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            return self._json(200, {"status": "ok", "version": "0.4.0", "application_version": "0.5.0", "release_version": "0.6.0", "current_release_version": CURRENT_RELEASE_VERSION, "active_application_version": ACTIVE_APPLICATION_VERSION, "final_release_version": FINAL_RELEASE_VERSION, "model": "two-dof-quarter-car"})
        if path == "/api/defaults":
            from dataclasses import asdict
            return self._json(200, {"vehicle": asdict(Vehicle()), "road": asdict(Road()), "settings": asdict(SimulationSettings())})
        file_name = FILES.get(path)
        if file_name is None:
            return self._json(404, {"error": "not found"})
        payload = (WEB_DIR / file_name).read_bytes()
        mime = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
        return self._send(200, payload, mime + ("; charset=utf-8" if mime.startswith(("text/", "application/javascript")) else ""))

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path not in ("/api/simulate", "/api/modal", "/api/compare", "/api/sweep", "/api/convergence", "/api/halfcar/simulate", "/api/ride/study", "/api/braking/simulate", "/api/regen/simulate", "/api/optimization/study"):
            return self._json(404, {"error": "not found"})
        try:
            if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
                return self._json(415, {"error": "Content-Type must be application/json"})
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > MAX_BODY:
                return self._json(413, {"error": "request body size invalid or too large"})
            body = json.loads(self.rfile.read(size))
            if path == "/api/optimization/study":
                from .optimization import optimization_request
                result = optimization_request(body)
            elif path == "/api/regen/simulate":
                from .regen import scenario_from_mapping as regen_mapping, simulate_regen
                result = simulate_regen(regen_mapping(body))
            elif path == "/api/braking/simulate":
                from .braking import scenario_from_mapping as braking_mapping, simulate_braking
                result = simulate_braking(braking_mapping(body))
            elif path == "/api/simulate":
                vehicle, road, settings = scenario_from_mapping(body)
                result = simulate(vehicle, road, settings)
            elif path == "/api/ride/study":
                from .ride import ride_request
                result = ride_request(body)
            elif path == "/api/halfcar/simulate":
                from .halfcar import scenario_half_from_mapping, simulate_half
                vehicle, road, settings = scenario_half_from_mapping(body)
                result = simulate_half(vehicle, road, settings)
            else:
                result = analysis_request(path.removeprefix("/api/"), body)
            self._json(200, result)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})


def main() -> None:
    parser = argparse.ArgumentParser(description="AutoDyn EV: local quarter-car simulator")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"AutoDyn EV v{FINAL_RELEASE_VERSION} running at http://127.0.0.1:{server.server_port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
