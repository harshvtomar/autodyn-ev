# AutoDyn EV — Chat 8 of 10 Handoff (PLAN ONLY)

**Chat 8 has not been started or implemented.**

## Starting point

- Accepted candidate release: `AutoDyn_EV_Chat7_v0.7.0.zip`, pending user Mac acceptance.
- Verify ZIP hash and integrity before any edits. Run all inherited tests (expected at least 298 Python tests, including optional Node-backed checks if Node available).
- Preserve the unmodified Python physical solver modules and their historical v0.6.0-calibrated response schemas. Continue to preserve the health API compatibility contract.
- 3D scene remains an optional projected geometry renderer of cached model channels; do not modify physics to improve animation aesthetics.

## Suggested Chat 8 scope

**Engineering dashboard enhancements and bounded parameter optimization** (subject to separate authorization): objective selection (ride RMS, travel, wheel/road deflection proxies, braking/regen metrics where valid), normalized Pareto-style tradeoff visualization, reproducible deterministic parameter grids, safe runtime bounds, diagnostic warnings, downloadable engineering reports and source-cited decision tables. Never combine incompatible uncoupled models into an invented whole-vehicle score. Avoid using energy recovery as a proxy for real range improvement without calibrated loss models.

## Chat 8 acceptance gates

Run full inherited suite and add tests for parameter bounds, reproducibility, comparison fairness, stop cases, conserved numerical outputs, report precision, browser accessibility, CSV/JSON provenance, and Mac acceptance. Deliver complete updated ZIP, manifest, checksum, verification, Mac checklist and Chat 9 planning handoff. Keep real-vehicle hardware, ABS, SOC/thermal BMS, CAD/CFD and certified safety outside scope.
