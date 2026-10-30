# AutoDyn EV Chat 5 v0.5.0 — Engineering verification report

**Status:** automated software release checks PASS; physical validation and live Mac browser acceptance PENDING.

## Source provenance

- Source base: exact accepted `AutoDyn_EV_Chat4_v0.4.0.zip` SHA-256 `d3875d670e2a19a2f5376a2588dbdb5504e7a15274918028c5a0da0de7805a3e`.
- Before editing: original 188/188 unit/API tests passed.
- New code is additive; legacy original 2-DOF and 4-DOF differential equations, source modules, studies, charts, exports and fixed-speed road-delay behavior preserved.
- One backward-compatibility accommodation: `/api/health` continues returning its legacy `version` field `0.4.0`, and now includes `application_version=0.5.0`. No inherited test was removed or rewritten.

## Test evidence

- `python3 -m unittest discover -s tests -q`: **231/231 passing**, comprised of **188 inherited + 43 new** tests, including braking event calculation, ramp/friction caps, zero demand and zero speed, axle load conservation, force direction, invalid input limits, API routing/content-type/errors, CSV metadata via browser download, and legacy unchanged physics.
- Isolated Chromium with intercepted local Python backend: **32/32** interactions across 1280 px and 390 px. Browser checks cover both old model modes and braking mode, charts, reset, demand/friction cap, command-ramp, exports, and page JavaScript errors. Both screenshots are in `docs/chat5-dashboard-1280.png` and `docs/chat5-dashboard-390.png`.
- Independent SciPy `quad` + Brent numerical reference across **120 seeded cases** (`docs/chat5_reference_results.json`): maximum stopping-time error approximately **4.317×10⁻¹³ s** and stopping-distance error approximately **2.439×10⁻⁷ m**, below specified 1e-7 s / 1e-6 m thresholds.
- The optional SciPy and Playwright checks are developer-only; no mandatory external runtime dependencies for users.

## Acceptance boundaries

The model is an illustrative, non-calibrated friction-cap and quasi-static normal-load study. It is *not* a validated stopping-distance tool, measured ABS/brake model, or a full vehicle multibody system. Mac user acceptance must be separately performed following `docs/MAC_CHAT5_ACCEPTANCE.md`. No GitHub publication or physical road test is claimed. Regenerative braking remains out of scope.
