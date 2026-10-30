# AutoDyn EV — Chat 5 of 10 engineering handoff (PREPARATION ONLY)

**Current accepted baseline:** Chat 3 v0.3.0, 136 original automated tests and ten Mac checks. **Current Chat 4 deliverable:** v0.4.0 candidate, 188 automated tests and 24 isolated browser checks. **Mac acceptance of Chat 4 is pending** until the user runs `docs/MAC_CHAT4_ACCEPTANCE.md`.

## Required inputs for next development chat

- `AutoDyn_EV_Chat4_v0.4.0.zip` and its SHA-256 checksum text.
- `docs/CHAT4_VERIFICATION_REPORT.md`, `docs/ENGINEERING_ROAD_RIDE_CHAT4.md`, `docs/MAC_CHAT4_ACCEPTANCE.md`, and `docs/CHAT4_CHANGE_MANIFEST.json`.
- User-confirmed Chat 4 Mac browser acceptance, or an explicit correction list if any check fails.

## Do not start until accepted

Chat 5 is **braking dynamics and longitudinal weight transfer**, not regression into suspension. First verify candidate ZIP hash, inspect the actual files, rerun all **188** automated tests and preserve the unchanged Chat 1–4 behaviors, APIs, plots and exports. Keep both inherited constant-speed vertical models independent; do **not** silently couple a longitudinal speed trajectory into existing half-car road delay. Design explicit independent longitudinal equations and road/contact limitations, then test them against analytic limiting cases. No regeneration belongs in Chat 5; that is a later milestone. If the source is unavailable, request exact ZIP rather than rebuilding.

Suggested Chat 5 tasks once approved: longitudinal point-mass stopping dynamics, normal-load transfer *under clearly stated flat-road quasi-static assumptions*, braking force bounds with tire-road friction as a separate explicit assumption, driver-command profiles, speed and stopping-distance plots, tests and independently checked analytical cases, versioned exports and conservative safety disclaimers. Resist claims of vehicle-level ABS/ESC validation or safe stopping distances without real road/vehicle parameters.

## Ready-to-copy Chat 5 starter prompt (do not execute now)

> Start AutoDyn EV — Chat 5 of 10: Braking Dynamics and Longitudinal Weight Transfer. Continue only from the attached accepted AutoDyn_EV_Chat4_v0.4.0.zip and verified checksum after Chat 4 Mac acceptance. Preserve all 188 inherited tests and all quarter-car/half-car models, road and ride response studies, APIs, UI and exports. Inspect actual source, verify checksum and run tests before edits. Design a separate, bounded point-mass longitudinal braking model with clearly defined tire/normal-load assumptions, stopping-distance and weight-transfer diagnostics, analytical limiting-case comparisons, interactive plots, provenance exports and regression tests. No regeneration or undocumented coupling to existing constant-speed rear-axle delay. Deliver complete source ZIP and Mac verification; do not implement Chat 6.
