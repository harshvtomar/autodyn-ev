# AutoDyn EV — Chat 6 of 10 preparation only (NOT implemented)

## Required baseline

Use the accepted source archive `AutoDyn_EV_Chat5_v0.5.0.zip` with its final published release SHA-256 from the accompanying checksum file. Before edits, check checksum, inspect this source and rerun all 231 inherited tests. Confirm ten Mac interactive acceptance checks for Chat 5 first.

## Chat 6 scope: EV regenerative braking and energy recovery

Implement a physically bounded **separate** regenerative energy-recovery extension to the longitudinal braking model:

- Distinguish demanded friction braking, commanded motor regeneration, realizable regen torque/power limits, traction caps and residual friction braking, with clearly documented energy pathways.
- If brake blend is added, enforce actual deceleration and energy conservation consistently, including battery charge acceptance (power, SOC, temperature models must be explicitly assumptions, not real-car calibration).
- Provide traction/braking force and power versus time charts; recoverable versus motor/battery losses and friction-dissipated energy with unit-consistent integrals. Keep capacity assumptions transparent.
- Handle battery/regeneration unavailable cases and zero-speed behavior without claiming recovered energy that exceeds the vehicle kinetic-energy change.
- Preserve all legacy quarter-/half-car models, braking controls, APIs, regression tests, exports and constant-speed axle-delay logic. Never silently conflate suspension speed with dynamic braking speed.
- Add independent numerical/energy reference tests; deliver full source ZIP, Mac acceptance, exact verification evidence, checksum, source change manifest and Chat 7 handoff.

**Do not start Chat 6 as part of Chat 5.** No ABS, tire slip, physical hardware or production battery safety claims without further dedicated models and verification.
