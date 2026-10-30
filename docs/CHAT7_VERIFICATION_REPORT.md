# AutoDyn EV — Chat 7 Verification Report

**Release:** v0.7.0 · Interactive 3D Engineering Visualization  
**Build date:** 29 October 2026  
**Scope:** Presentation layer, model-aware camera/timeline, SVG fallback, accessibility and footer fix. Chat 8 not started.

## Immutable baseline acceptance

- Baseline ZIP: `AutoDyn_EV_Chat6_v0.6.0.zip`
- Baseline SHA-256: `1d70af9c90c8a2822f449134f672747f5f116c1bffe3ba654135a53de3af4227`
- `unzip -t` passed before extracting to a new working directory.
- **291/291 inherited Python tests passed before modifications** (`/mnt/data/_autodyn7_inherited_tests.log`).
- No accepted numerical model source files (`physics.py`, `simulation.py`, `halfcar.py`, `analysis.py`, `ride.py`, `braking.py`, `regen.py`) were edited.

## Executed verification

| Check | Result | Evidence |
|---|---|---|
| Full inherited + added Python tests | **298/298 passed** | `python3 -m unittest discover -s tests -v` |
| New integration tests | **7/7 passed** | Version, self-hosted assets, no external renderer, footer, hooks, optional Node math and JS syntax |
| Pure JavaScript presentation math | Passed | `node tests/test_viz_math.cjs` through the Python test runner |
| Isolated Chromium interactive checks | **35/35 passed** | `docs/chat7_browser_results.json` |
| 1280px and 390px viewer screenshots | Produced and inspected | `docs/chat7-visualization-1280.png` and `docs/chat7-visualization-390.png` |
| Canvas unavailable -> SVG fallback | Passed | Isolated Chromium with viewer Canvas2D disabled |
| Reduced-motion preference | Passed | Viewer remained paused until deliberate Play |
| Normal four-model selection, playback, scrub, orbit, exports retained | Passed in isolated harness for visual controls; previous exports unaffected | Browser results + original 291 regression tests |
| Physics output hash comparison, separate baseline/current processes | **10/10 exactly identical** | `docs/chat7_no_physics_drift.json` |
| Python compilation, JavaScript syntax, clean ZIP extraction | See release record | `docs/CHAT7_RELEASE_CHECK.md` |

**No numerical drift:** Outputs from quarter-car default/sine, half-car default/step, braking default/ramped/low grip, regenerative default/zero battery charge/incomplete stopping scenarios were serialized as complete, sorted-key JSON including settings, metrics, channel arrays and physics provenance. For each scenario, the SHA-256 digest matched exactly between the pristine v0.6.0 source and the new v0.7.0 source. This confirms these ten scenarios; it is not a mathematical proof for every possible input.

## Geometric mapping and sign conventions

- World +X = forward (toward front axle); +Y = upward; +Z = lateral.
- Half-car positive body pitch is nose-up; front attachment rises with positive pitch. Geometry is rotated around lateral +Z, visually magnified 4× and clamped to 0.38 rad for display only.
- Quarter and half body/wheel heave is rendered at roughly 18 visual metres per simulated metre, clamped to 0.38 m to keep geometry visible. Schematic height/width/wheel radius are generic artistic constants, not actual vehicle dimensions.
- Braking and regen do **not** visualize body pitch/heave motion, because those simulations do not compute it. Their vehicle shell stays level; load-transfer arrows, speed/travel readouts and blended-force bars read the accepted response channels.
- Display time interpolation: bounded, piecewise-linear interpolation of adjacent authoritative samples. No solving, integrating or recomputing speed, acceleration, distance, motor power or battery energy in the 3D view.
- The visualizer does not write to response channels. Existing CSV and JSON exporters are unchanged.

## Version compatibility / issue disposition

- `AD-EV-UI-006`: old active footer `Chat 5 of 10` -> `Chat 7 of 10` in both active footers. Banner -> `v0.7 · Session 07`. Automated footer checks plus isolated browser check passed. **Resolved in v0.7.0**.
- Legacy `/api/health` `release_version: "0.6.0"` intentionally retained for inherited tests/API clients. New `current_release_version: "0.7.0"` added; this is an explicitly documented compatibility field, not an actual claim that the running app is v0.6.0.
- v0.5/v0.6 model response payloads continue to identify their validated algorithm versions.

## Evidence limits

- **Not** run in Chrome/Safari on the user's own Mac; Mac acceptance must be user-confirmed separately.
- The local browser harness could not navigate to localhost (`ERR_BLOCKED_BY_ADMINISTRATOR`); isolated Chromium used the actual served UI source and genuine backend outputs supplied as precomputed mock API responses. It is not evidence that local HTTP networking works on the user's Mac.
- No experimental real-EV or physical safety certification, no ABS, tire slip, battery thermal/SOC dynamics, or full-vehicle coupling.
- The 3D geometry is a custom **software-projected 3D schematic on Canvas2D**, not CAD, not WebGL, not measured geometry and not a second physics engine.
