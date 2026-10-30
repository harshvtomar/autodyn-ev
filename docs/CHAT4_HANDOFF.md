# AutoDyn EV — Chat 4 of 10 handoff (preparation only; NOT implemented)

## Starting point

**Required source:** `AutoDyn_EV_Chat3_v0.3.0.zip` from Chat 3. Extract with root `autodyn-ev-chat3/`. Verify the release SHA-256 in the accompanying checksum file and the immutable Chat 2 baseline checksum `ef432705ef43f31262d0c5703d822b17ba2d04c0b92ab352478127eff67792bb`. Preserve Chat 1/2 mechanics and all new half-car behaviors.

## Current implementation

- Quarter-car 2-DOF RK4, UI, baseline-vs-variant, seven-point sweep, damped modal poles, time-step sensitivity, original exports: **all preserved** with 95 inherited tests.
- New *separate* 4-DOF linear half-car physics `autodyn_ev/halfcar.py` with heave, nose-up pitch, front/rear wheel masses, independent suspension and tire forces, front/rear road delay, controlled step size and `POST /api/halfcar/simulate` JSON output.
- UI model selector, half-car response panels, responsive input forms, animation and half-car CSV/JSON download; 41 new tests; independent M,C,K and SciPy comparisons; isolated desktop/mobile browser checks.
- **Live Mac browser acceptance not performed by assistant**. Review checklist in `docs/MAC_CHAT3_ACCEPTANCE.md` and ask user for their results first. Do not claim physical calibration or GitHub publication.

## Planned Chat 4 (scope to confirm before starting)

Focus on road-profile variations, meaningful suspension ride-response diagnostics, and engineering sensitivity under the two existing mathematical models. Do **not** silently implement braking or regeneration until their assigned milestone. Preserve backward-compatible APIs, existing model conventions and all 136 tests; verify new calculation methods independently. Any handling of longitudinal speed changes or longitudinal force requires an explicit, separately validated model rather than changing current fixed-speed axle delay implicitly.

## Copy-ready continuation prompt

Start AutoDyn EV — Chat 4 of 10: Road Excitation and Ride Dynamics Studies. Continue exclusively from the attached accepted `AutoDyn_EV_Chat3_v0.3.0.zip`, never recreate the repository. Verify its SHA-256, inspect source and all v0.3 handoff documentation, and run 136 inherited tests before changes. Preserve 2-DOF and 4-DOF equations, API schemas, dashboards, charts, exports and numerical verification. First reconcile any pending Mac acceptance issues. Add validated road-profile variation and meaningful ride/vehicle response studies without introducing undocumented braking, tire separation or unverified physics. Add transparent assumptions, independent mathematical checks, robust desktop/mobile controls, regression tests, complete updated source ZIP, verification report, Mac acceptance and Chat 5 handoff. Do not start Chat 5.
