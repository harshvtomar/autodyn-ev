# AutoDyn EV — Chat 3 Engineering Verification Report

**Release:** 0.3.0 · 29 October 2026 · **Decision:** source release ready for Mac acceptance, NOT final Mac-accepted.

## Exact inherited baseline

Source input: `AutoDyn_EV_Chat2_v0.2.0.zip`, SHA-256 `ef432705ef43f31262d0c5703d822b17ba2d04c0b92ab352478127eff67792bb`, archive root `autodyn-ev-chat2/`. SHA-256 independently matched the handoff. Extracted source was used and renamed `autodyn-ev-chat3/`, not reconstructed. Before modifications, **95 of 95 tests passed**. The original `physics.py`, `simulation.py`, `analysis.py`, `web/app.js`, and all four inherited test modules are byte-for-byte identical to the accepted ZIP. Old routes, 12-channel quarter-car response and study schema were not replaced.

## Scope implemented

1. Standalone half-car physics `autodyn_ev/halfcar.py`: 4 generalized coordinates/8 states, independent front/rear suspension, tire, wheel masses; body mass and pitch inertia, front/rear CG-to-axle arms, nonlinearity explicitly excluded.
2. Physically signed front/rear suspension forces, chassis heave and restoring pitch torque; front/rear road profiles separated by `wheelbase/speed` constant forward-motion delay.
3. Flat/bump/sine/step road profiles, step-size/under-resolution checks, strict finite bounds, RK4 output channels, model-specific metrics and model/solver/units provenance. Small-angle diagnostic at peak pitch >0.15 rad (warning only).
4. New additive `POST /api/halfcar/simulate` endpoint. `GET /api/health` reports release 0.3.0; legacy endpoint contracts remain intact.
5. Switchable model selector and separate 4-DOF UI: independent numeric inputs, front/rear road/axle plot, pitch/heave plot, travel/acceleration plot, time-indexed schematic animation, CSV/JSON downloads and responsive desktop/mobile layout. Legacy 2-DOF panels retained.

## Verification performed

| Check | Evidence | Result |
|---|---|---|
| Original 95 Python tests before modification | Original unpacked accepted source | PASS (95/95) |
| Full Python suite after additions | `docs/chat3_automated_test_log.txt` | **PASS (136/136)** (95 inherited + 41 new) |
| Python compile all package/tests/scripts | `python3 -m compileall -q autodyn_ev tests scripts` | PASS |
| JavaScript syntax | `node --check web/app.js` and `node --check web/halfcar.js` | PASS |
| Exact inherited source preservation | `docs/CHAT3_CHANGE_MANIFEST.json` | PASS for key mechanics, analysis, original UI JS and tests |
| Independent M,C,K state equations | `scripts/chat3_reference_check_optional.py` | PASS, 150 seeded vehicle configurations |
| Independent energy-rate identity | `scripts/chat3_reference_check_optional.py` | PASS |
| Independent DOP853 integration | SciPy comparison with smooth sine road | PASS within 2×10⁻⁵ per state channel |
| New HTTP route and invalid-request handling | 9 additional real local-server integration tests | PASS |
| Browser harness, desktop (1440×960) | `docs/chat3_browser_harness_results.json` + screenshot | PASS, isolated Chromium, no JS errors |
| Browser harness, mobile (390×844) | `docs/chat3_browser_harness_results.json` + screenshot | PASS, isolated Chromium, no JS errors |
| Native browser in user's Mac and actual localhost navigation | User acceptance checklist | **PENDING** |
| Physical vehicle or hardware calibration | Not attempted | **NOT PERFORMED** |
| GitHub publication | Not requested/executed | **PENDING** |

## Numerical reference details

Independent NumPy M,C,K generalized-force assembly over 150 randomized model/initial-state configurations: maximum acceleration-channel discrepancy **1.14×10⁻¹³** (SI channel units); energy-rate identity residual **4.55×10⁻¹³**. One smooth 0.012 m/0.8 Hz sine road at 2 s with dt=0.0025 s was compared with `scipy.integrate.solve_ivp(method='DOP853', rtol=2e-11, atol=1e-12, max_step=0.0004)`; maximum error among eight state histories was **6.98×10⁻⁷** (front wheel velocity; SI units), below the **2×10⁻⁵** per-channel criterion. Numerical verification supports a model/integrator implementation, **not accuracy for a real car**.

## Reproducible default half-car response

600 kg sprung body; 1000 kg·m² pitch inertia; 40 kg unsprung each; 18 kN/m spring each; 1500 N·s/m damper each; 190 kN/m tire each; a=1.2 m, b=1.3 m, speed=5 m/s; 60 mm/1.5 m raised-cosine bump; 5 s, dt 0.005 s. 1001 samples; rear delay **0.500 s**; heave acceleration RMS **0.62345 m/s²**; peak pitch **1.64212 degrees**; front/rear peak suspension travel **47.17 / 49.00 mm**. These are **simulated** values. Source: `examples/chat3_default_halfcar_metrics.json`.

## Pending and limitations

- Live Mac Chrome/Safari acceptance, exports opened on Mac, responsive hardware resize, local port, and user signoff remain pending. Isolated Chromium DOM tests do not establish a real Mac session.
- No real road/EV measurement, calibration, tire contact loss or 3D physical validation.
- Pitches beyond 0.15 rad trigger a transparent caution, not an automatic physically valid nonlinear model.
- A fixed rear delay assumes constant positive forward speed and aligned wheel tracks.
- Plots intentionally place separate physical-unit curves on common display ranges for trend comparison. Do not treat overlaid graph amplitudes with mixed units as directly comparable.

## Mac acceptance

Use the specific checklist at `docs/MAC_CHAT3_ACCEPTANCE.md`. Retain this v0.3.0 ZIP as baseline; do not begin Chat 4 until user confirms required Mac checks or any failure is resolved.
