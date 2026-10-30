# Chat 2 Change Manifest

## Baseline preservation

Extracted the exact Chat 1 ZIP with matching SHA-256 and applied only additive/backwards-compatible changes. The previous `tests/test_physics.py`, `tests/test_server.py`, `autodyn_ev/physics.py`, `docs/ENGINEERING_MODEL.md`, original examples, and original plot definitions remain intact. The original version string, server handlers and app HTML/JS/CSS were amended rather than replaced. Additional endpoints are registered in the local Python HTTP server; original `/api/simulate`, `/api/defaults`, `/api/health` are retained.

## Changed existing files

- `autodyn_ev/__init__.py`: v0.2.0 version.
- `autodyn_ev/simulation.py`: additive deterministic provenance block (all existing keys/values remain).
- `autodyn_ev/server.py`: registered four new analysis POST endpoints, with same content-type, bounded payload, no CORS and local binding.
- `web/index.html`, `web/styles.css`, `web/app.js`: appended study dashboard, visual plots, interactive controls and export sidecar while retaining original interface.
- `pyproject.toml`, `README.md`: version and release documentation.
- `scripts/browser_smoke_optional.py`: delegates to Chat 2 harness, so the optional legacy test launcher does not fail on new endpoints.

## Newly added files

- `autodyn_ev/analysis.py`: damped poles, comparison, sweep, convergence, provenance.
- `tests/test_analysis.py`, `tests/test_analysis_server.py`: 38 new executed tests.
- `scripts/chat2_reference_check_optional.py`: independent NumPy/SciPy verification.
- `scripts/browser_smoke_chat2_optional.py`: optional isolated browser-interaction QA.
- `docs/ENGINEERING_STUDIES_CHAT2.md`, `docs/CHAT2_VERIFICATION_REPORT.md`, `docs/MAC_CHAT2_ACCEPTANCE.md`, `docs/CHAT3_HANDOFF.md`, `docs/CHAT2_CHANGE_MANIFEST.md`.
- `docs/chat2_*` machine-readable/log/screenshot evidence.
- `examples/chat2_*` sample numerical studies.

## Not implemented (intentionally)

No half-car physics, force-controlled 3D mechanical assembly, braking, regenerative braking, tire-contact loss or physical EV certification. No network or paid dependencies introduced.
