# AutoDyn EV · Chat 8 v0.8.0 verification report

**Scope:** bounded engineering design-study and trade-off dashboard, NOT real-world vehicle design validation. **Date:** 2026-10-29. **Baseline:** accepted `AutoDyn_EV_Chat7_v0.7.0.zip` SHA-256 `ab402d8b2bb5e213f9e6535b370cc078425e5c9a143454dc564fb7dcc664401c`.

## Pre-edit gates

- Required original archive available; SHA-256 exact match; ZIP CRC/integrity successful.
- Source extracted into separate Chat 8 working directory; original archive never modified.
- **298/298 inherited tests passed before any edits.**
- Source modules inspected: quarter/half/braking/regen/road/analysis/visualization, health and API contracts.

## New deliverables

- Separate `autodyn_ev/optimization.py`, strict `POST /api/optimization/study` endpoint; quarter/half parameter and road/config validators reused unchanged.
- 7-point per-axis ±20% capped and clipped to validated parameter bounds; one or two dimensions, at most 49 physical simulations per study; max 3,000 steps per simulation.
- Time-weighted unweighted body acceleration RMS (m/s²); sampled peak-to-peak suspension travel (mm), separate/worst front/rear half-car metrics; peak absolute tire-deflection proxy (mm). Optional constraint rejection with all reason codes, Pareto/nondominated set, deterministic tie-break of illustrative selected case; no combined score.
- Standalone HTML/CSS/JS panel with model and parameter controls, feasible/infeasible candidate table, trade-off scatter chart, checked versions, CSV/JSON/text engineering report downloads, accessible status and mobile support.
- `AD-EV-DOC-011` corrected: current README section now starts with **v0.8.0** while historical release notes are retained.
- Footer/header show Chat 8 in active application. The immutable v0.7 package metadata test contract is retained as a legacy compatibility field; current-release health/startup/display identify v0.8.0.

## Executed testing

| Verification | Result | Evidence |
|---|---|---|
| Original inherited Python tests, pre-edit | **298/298 passed** | original clean extraction and log |
| Full Python automated suite after changes | **332/332 passed** | `docs/CHAT8_TEST_LOG.txt` |
| Independent metric recomputation and Pareto checks | **Passed** | `tests/test_optimization_chat8.py` |
| Determinism, invalid grids, bounds, zero-feasible, constraint and 49-case cases | **Passed** | `tests/test_optimization_chat8.py` |
| Additive API, invalid content and legacy API checks | **Passed** | `tests/test_optimization_chat8.py` |
| Unmodified physics outputs Chat 7 vs Chat 8 | **10/10 byte-identical** | `docs/CHAT8_NO_DRIFT.json` |
| Isolated Chromium 1280 px and 390 px UI/export checks | **36/36 passed, zero JS page errors** | `docs/CHAT8_BROWSER_RESULTS.json` and screenshots |
| Python module compilation, JavaScript syntax | **Passed** | `python3 -m compileall` and `node --check` |
| Local HTTP assets/API startup | **Passed** | API integration unit tests |
| Release ZIP integrity and tests after fresh extraction | **PASS: ZIP integrity and 332/332 on fresh extraction** | `docs/CHAT8_CLEAN_EXTRACTION_REPORT.md` |

### Independent metric checks

The Python test suite independently trapezoid-integrates the original quarter-car sprung acceleration and half-car body-heave acceleration, and independently recomputes sampled peak-to-peak and maximum absolute tire deflection per axle; these agree with the study outputs. A separately coded brute-force nondominance check agrees with reported Pareto IDs for the half-car 49-case grid. Repeated identical studies return identical JSON candidate order and objective values.

### Baseline no-drift comparison

Ten scenarios cover three quarter-car, two half-car, two friction braking and three regenerative cases. Baseline and new results are serialized with the same sorted JSON settings and compared byte-for-byte. **All ten are identical.** The new model does not change their numerical outputs or original endpoint schemas.

### Browser evidence limitations

Isolated headless Chromium loaded the actual HTML/CSS/JS using precomputed real study responses and simulated API handling. The UI passed desktop and 390 px layout checks, table/candidate selection, 7/49 grids, no feasible results, duplicate input validation, CSV/JSON/plain-text downloads, and 2D/3D switching. This **does not** count as a live browser-to-localhost test on the user's Mac. Live Mac Chrome/Safari acceptance and external experimental validation are **pending**.

## Accepted preservation and constraints

All 146 baseline files are accounted for, with zero deletions. The original source files under `autodyn_ev/` for quarter/half/braking/regen/ride/analysis/simulation remain byte-for-byte unchanged. Five integration files were modified (README, `autodyn_ev/__init__.py`, `autodyn_ev/server.py`, `web/index.html`, `web/styles.css`); new optimization module, browser JS, tests and reports were added. All 298 inherited tests remain unchanged. Compare `docs/CHAT8_SOURCE_CHANGE_MANIFEST.json`.

**Engineering limitations:** zero physical vehicle validation; linear always-connected tire model; no nonlinear suspension geometry, ABS, slip/friction coupling, battery range inference or ISO 2631 comfort rating. A minimum-RMS result is not a globally optimal, safe or certified suspension design.
