# AutoDyn EV v0.4.0 — Chat 4 engineering verification

**Status:** candidate software engineering release; awaiting user Mac browser acceptance. **No experimental calibration, no tire lift-off, no ISO 2631 rating, no GitHub publication claimed.**

## Starting source

- Exact source: `AutoDyn_EV_Chat3_v0.3.0.zip`.
- SHA-256: `5b325513740fd30b3a0e968a616a4b17497b59b057f5f3316cc2ac633b121b41` (matched before extraction).
- Ran inherited unmodified suite **136/136 PASS before implementing Chat 4**.

## Implementation scope

Three additive profiles: `pothole` (negative smooth half-cosine), `double_bump` (two separated raised-cosine pulses), `chirp` (continuous-phase frequency ramp then final frequency). Added a single shared road-resolution guard to both existing integrators. Added a separate, deterministic `ride.py` analysis module, bounded `POST /api/ride/study`, read-only scenario comparisons, time-integrated unweighted acceleration RMS, peak-to-peak travel, tire-deflection proxy, transparent time windows and conditionally defined settling. Added mode-specific browser controls/plots/CSV/JSON. **The existing differential equations, force sign conventions and RK4 stepping formulas were not altered.**

## Test evidence

| Test | Actual result |
|---|---|
| 136 inherited Python tests before changes | PASS |
| 136 inherited Python tests after changes | PASS |
| 52 new road/metric/API tests | PASS |
| Total automated Python tests | **188/188 PASS** |
| Static JS `node --check` (all 3 scripts) | PASS |
| Python compilation | PASS |
| Optional SciPy DOP853 reference (4 model/road cases) | PASS |
| Isolated Chromium behavior in 1280 and 390 px, 24 checks | PASS, no page exceptions |
| Actual Chrome/Safari browser on user's Mac | **PENDING** |
| Physical vehicle/ISO comfort calibration | **NOT PERFORMED** |

The SciPy oracle independently implements road elevation, quarter-car force balance and half-car M/C/K dynamics. It uses DOP853 with tight tolerances and 0.001-second maximum internal steps; the accepted RK4 uses 0.005-second steps. Four reference cases include quarter-car pothole, half-car double-bump, and quarter/half chirp. See `docs/chat4_reference_results.json` for **per-channel** max differences and native units; every maximum is below 2e-4. The 2e-4 numeric bound applies per channel, not to a single dimensionless combined error.

The browser harness runs a locally hosted real Python backend, with an intercepted HTTP relay into isolated Chromium because normal browser navigation to local domains is blocked in this environment. It verifies form/road changes, model switching, new study status, plotted canvas dimensions, baseline comparisons, actual CSV/JSON download contents, desktop and 390px mobile; it is **not** equivalent to the user's real Mac browser. See `docs/chat4_browser_harness_results.json` and screenshots.

## Important limitations and known boundaries

- The original quarter-car API returns the inherited sample-mean RMS; **new ride study** returns time-weighted, trapezoidal RMS. These are intentionally different definitions. The old API schema and metrics are preserved.
- Original half-car `provenance.release=0.3.0` is retained for backward compatibility of its existing schema. The additive ride endpoint has `release=0.4.0`. Do not mix revision provenance.
- Existing Chat 3 mixed-unit overview chart is preserved for compatibility; the **new** road/ride charts do not mix incompatible units.
- New profiles are analytical **synthetic**, not measured road classification. Constant forward speed is an assumption; no longitudinal solver added.
- Settling is conditional on *all subsequent samples within a finite horizon* and fixed thresholds, never a physical guarantee; it is absent for sustained/zero-amplitude excitation or insufficient horizon.
- Tire deflection proxies don't indicate tire-road contact loss, traction or braking.
- The quarter-/half-car models are independently parameterized; no cross-model percent improvements are advertised.
