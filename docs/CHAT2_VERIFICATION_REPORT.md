# AutoDyn EV — Chat 2 Verification Report

**Project:** AutoDyn EV v0.2.0, Chat 2 of 10, 29 October 2026. **Source:** exact Chat 1 baseline ZIP SHA-256 `0217d9e6f05b7f04b0d484b9cf9557e1238b5900d8f238f0e6818aa32d90ecae`.

## Acceptance matrix

| Category | Result | Evidence / qualification |
|---|---|---|
| SHA-256 of original Chat 1 baseline | **PASS** | SHA matches final acceptance addendum; unzipped directly, no reconstruction |
| Original 57 unit/API tests | **PASS** | Original two test files preserved; included in 95-test final run |
| Chat 2 additional unit/API tests | **PASS (38)** | 95 tests total, 0 failures; `docs/chat2_automated_test_log.txt` |
| Python compilation / JavaScript syntax | **PASS** | `python -m compileall`, `node --check` |
| Damped pole numerical residual checks | **PASS** | Default/high damping/120 randomized vehicles in automated tests; extra 500-config stress check with zero failures |
| Independent modal eigenvalue reference | **PASS** | 100 randomized vehicle cases vs NumPy 4x4 state-space eigenvalues, largest absolute error **9.47×10⁻⁹ s⁻¹** |
| Independent RK4 trajectory | **PASS** | Separate DOP853 implementation vs RK4 on 4-second sine road, largest channel error **1.75×10⁻⁶ m/s** (not combined across units) |
| Comparison/sweep/refinement API contracts | **PASS** | Direct unit checks plus HTTP 200/400 tests and budget checks |
| Original default metrics/schema | **PASS** | 1,001 samples, legacy 12 columns, unchanged original top-level output structure except additive `provenance`; RMS 0.906082 m/s² |
| Desktop Chromium UI harness | **PASS — isolated** | Injected actual Python computation into unmodified shipped JS. New/old interactions, graphs and downloads passed; no JS errors |
| Mobile Chromium UI harness | **PASS — isolated** | 390×844 viewport; charts and buttons exercised; screenshot reviewed; no JS errors |
| Live browser→localhost in current authoring environment | **BLOCKED** | Chromium reports `ERR_BLOCKED_BY_ADMINISTRATOR`; do not claim live network-driven browser check |
| User's Mac runtime for Chat 2 | **PENDING** | User needs to run `docs/MAC_CHAT2_ACCEPTANCE.md`; Chat 1 Mac acceptance does not transfer automatically |
| Published GitHub/hosted CI for Chat 2 | **PENDING** | No publication attempted or claimed |
| Physical EV model validation / safety/roadworthiness | **NOT CLAIMED** | All outputs are mathematical simulations |

## Numerical reference details

Optional reference script `python3 -m scripts.chat2_reference_check_optional` used installed SciPy 1.17 and NumPy 2.3.5 on Linux (these are **not required** for the application). It checks an independently assembled state-space matrix and a separately specified sinusoidal-input ODE. Verification result is saved in `docs/chat2_reference_results.json`; **PASS** under predeclared modal max error `1×10⁻⁴ s⁻¹` and state-channel max errors `2×10⁻⁵` in each channel's own SI units. This does **not** establish correct real-world physical vehicle parameters or empirically accurate suspension forces.

- Sprung displacement maximum error: 1.7293×10⁻⁹ m.
- Unsprung displacement maximum error: 2.3270×10⁻⁸ m.
- Sprung velocity maximum error: 1.1481×10⁻⁷ m/s.
- Unsprung velocity maximum error: 1.7506×10⁻⁶ m/s.

The selected smooth sine waveform avoids the default bump boundary interaction in the independent RK4/SciPy check; the separate convergence study explicitly reports this limitation. Error against the *finest tested RK4* is not an independent precision validation.

## Browser verification scope

`python -m scripts.browser_smoke_chat2_optional` invokes the real web HTML, CSS and JavaScript in headless Chromium using `page.set_content` and bridges `fetch` calls into the actual Python simulation and analysis handlers. It checks desktop and mobile, three original charts, three new charts, modal display, mass comparison, parameter sweep, step-size checks, CSV and JSON exports, provenance sidecar, flat zero-road response, and animation pause. Evidence: `docs/chat2_browser_harness_results.json`, `docs/chat2-dashboard-desktop.png`, `docs/chat2-dashboard-mobile.png`. This method **does not** exercise network requests from a live Chrome/Safari session to localhost, and thus is not equivalent to acceptance on the user's Mac.

## Release decision

**PASS for packaged Chat 2 development delivery, subject to explicit user-Mac interactive acceptance.** Do not infer calibrated suspension design validity, real-world damping or safety limits, physical vehicle performance, or full vehicle dynamics from this release. Half-car, braking, regenerative braking and 3D vehicle architecture were not started.
