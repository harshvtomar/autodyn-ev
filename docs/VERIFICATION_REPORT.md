# AutoDyn EV — Chat 1 Engineering & Software Verification Report

**Date:** 29 October 2026  
**Deliverable:** `AutoDyn_EV_Chat1_v0.1.0.zip`  
**Application:** AutoDyn EV v0.1.0  
**Implementation:** Python standard library + HTML/CSS/JavaScript; zero mandatory pip/npm dependencies.

## 1. Executive acceptance summary

| Acceptance requirement | Status | Evidence / qualification |
|---|---|---|
| Source code delivered, standalone | PASS | Package `autodyn_ev/`, `web/`, `tests/`, `scripts/`, docs and examples |
| 2-DOF quarter-car ODE correctly implemented | PASS for specified mathematical model | Exact equations in `physics.py` and `ENGINEERING_MODEL.md`, tests of sign and equilibrium |
| Fixed-step RK4 integrator | PASS | `rk4_step`, convergence tests, independent DOP853 comparison |
| 4 road profile types | PASS in tests / isolated browser | bump, step, sine, flat; invalid inputs rejected |
| Visual interactive dashboard | PASS in isolated Chromium harness | desktop 1440px and mobile 390px, injected fetch -> Python solver |
| Plot channels | PASS in isolated Chromium harness | 3 canvases, charts populated, parameter changes reflected |
| Exports | PASS in isolated Chromium harness | CSV and JSON downloads tested; example files committed |
| Python/API test suite | PASS | **57 passed**: physics, integration and HTTP layer |
| Static syntax checks | PASS | `python -m compileall`, `node --check web/app.js` |
| Independent numerical reference | PASS within chosen reference tolerance | SciPy DOP853 cross-check for smooth sine input |
| MacBook Air M2 local startup | **PENDING** | No user Mac connected for direct terminal/runtime test |
| True browser -> live localhost API end-to-end | **PENDING** | Chromium navigation blocked by authoring-environment administrator policy; API network checked separately |
| Real vehicle / suspension measurement validation | **NOT CLAIMED** | No empirical measurements, calibration or hardware |
| GitHub publication and hosted CI run | **PENDING** | Repository configuration delivered; user must publish and observe CI |

## 2. Environment used

- **Authoring environment:** Linux container, Python **3.13.5**.
- **Testing tools available:** `unittest` (stdlib), Node.js `--check`, optional SciPy `1.17.0`, Chromium via Playwright.
- **Target environment:** macOS on Apple Silicon (MacBook Air M2), Python 3.10+ and Chrome/Safari. This compatibility is based on use of cross-platform language/stdlib APIs, not verified installation on that particular Mac.

## 3. Executed test results

Command run from project root:

```bash
python3 -m unittest discover -s tests -v
```

**Observed: 57 tests, 0 failures, 0 errors (PASS).** Full log: `docs/automated_test_log.txt`.

Coverage includes: equilibrium RHS, equal-and-opposite spring reaction, damper sign, tire force action, natural-mode eigenvalue invariants, flat-road zero response, energy dissipation, energy conservation with numerical tolerance, time-step refinement, static step asymptote, finite serialization, bounded parameter validation, under-resolved bump/sine rejection, 200/400/404/415 API behavior, static page/asset serving, no permissive CORS header.

An earlier exploratory energy-conservation test at an unnecessarily coarse free-vibration step exceeded its initially stringent tolerance. Rather than weakening the energy criterion, the test was improved to `dt=0.00125s` and rerun; the relative numerical energy drift was **1.32×10⁻⁶** after 2.5 seconds with undamped, flat-road motion. It passes the specified `2×10⁻⁵` check. Only the final 57-test green run is the delivery acceptance point.

## 4. Independent numerical reference check

Separate optional command:

```bash
python3 -m scripts.scipy_reference_check
```

Comparison inputs: default vehicle settings, 0.02 m sinusoidal road at 1.2 Hz, starting at `t=0s`, 5 seconds duration, custom RK4 step `0.005s` vs SciPy `solve_ivp(method='DOP853', rtol=1e-11, atol=1e-12)`.

| State channel | Max absolute RK4 vs DOP853 difference |
|---|---:|
| Sprung displacement | 2.8622×10⁻⁸ m |
| Unsprung displacement | 3.8586×10⁻⁷ m |
| Sprung velocity | 1.9374×10⁻⁶ m/s |
| Unsprung velocity | 2.8858×10⁻⁵ m/s |

**PASS** under preselected maximum absolute state-channel error tolerance `5×10⁻⁵` in each channel's own SI units. These errors are different physical units and must not be combined into one dimensional quality metric. Cross-check intentionally uses a smooth road profile to avoid solver event-discontinuity complications. Result file: `docs/scipy_reference_results.json`.

## 5. Reproducible default scenario

Parameters: sprung mass 300 kg, unsprung mass 40 kg, suspension stiffness 18,000 N/m, damper 1,500 N·s/m, tire stiffness 190,000 N/m, 60 mm cosine bump, 1.5 m length, 5 m/s speed, onset 0.5 s, 5 s run, 0.005 s step.

| Computed metric | Result |
|---|---:|
| Response samples | 1,001 |
| Body acceleration RMS | 0.906082 m/s² |
| Peak absolute body acceleration | 5.220637 m/s² |
| Peak suspension travel | 48.064271 mm |
| Peak body displacement | 52.225277 mm |
| Peak tire deflection | 8.113585 mm |
| Peak tire-force variation | 1,541.581 N |
| Lower / body-like undamped eigenfrequency | 1.177665 Hz |
| Higher / wheel-like undamped eigenfrequency | 11.482616 Hz |
| Post-bump settling heuristic | 1.575 s |

**Important:** These are *hypothetical model outputs*, not observed EV measurements and not evidence of ride comfort compliance. Source files: `examples/default_bump_metrics.json` and `examples/default_bump_response.csv`.

## 6. Browser QA details

An isolated test harness used `Playwright` + Chromium, loaded the **exact shipped HTML, stylesheet and JS** into a browser document, and injected `fetch('/api/simulate')` to call the **actual Python simulation function**. This was necessary because browser navigation to `localhost`, `127.0.0.1` and even `file://` returned `net::ERR_BLOCKED_BY_ADMINISTRATOR` in the authoring environment.

**Desktop (1440×1050): PASS in isolated harness.**  
**Mobile (390×844): PASS in isolated harness.**

For each size, checks passed for initial status/RMS, rendering three canvas plots, flat-road zero output, mass-input modification, rerun of bump scenario, sample-count consistency, CSV download, summary JSON download, animation pause, and no uncaught JavaScript page errors.

Evidence: `docs/browser_harness_results.json`, `docs/dashboard-desktop.png`, `docs/dashboard-mobile.png`, `scripts/browser_smoke_optional.py`.

These results **do not establish** end-to-end server-to-browser communication on a Mac; that check remains pending in `docs/MAC_SETUP.md`.

## 7. Safety, provenance and limitations

- No user personal data, API keys or remote network calls required by the app.
- HTTP server binds **only** `127.0.0.1`, has allowlisted static routes, bounded JSON POST payloads and no permissive cross-origin headers.
- Sliders are numerical sandbox controls, not physical design constraints or calibrated component specification ranges.
- Quarter-car tire is always attached to road in the chosen linear ODE; tire-force variation must **not** be advertised as a physical normal contact load.
- Road input is idealized; vehicle speed only affects bump duration, not longitudinal inertia/traction.
- No physical hardware tests, real-time control, ISO 2631 assessment, braking model, FEA or multi-body validation are included in Chat 1.

## 8. Release decision

**ACCEPTED FOR CHAT 1 SOFTWARE HANDOFF** as an educational two-DOF suspension simulation foundation, subject to the explicit *pending user Mac live-browser acceptance* and *no physical validation claims*. Use the supplied ZIP as the sole starting point for Chat 2. No Chat 2 implementation has begun.
