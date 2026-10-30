# AutoDyn EV — Chat 7 of 10: Ready-to-start handoff (planning only)

**Chat 6 release:** v0.6.0. **Chat 7 has NOT been implemented.**

## Immutable accepted baseline and gate

Use the complete `AutoDyn_EV_Chat6_v0.6.0.zip` from Chat 6 and its SHA-256 checksum file. First inspect the actual archive, verify its checksum, unzip into a fresh working directory and run **all inherited automated tests** before edits. Do not rebuild from a summary or use an older release. Treat the current Mac browser acceptance as pending until separately user-confirmed.

## Recommended Chat 7 focus

**3D and interactive visual engineering presentation:** retain precise numerical physics and keep renderers as *views of already-calculated results*, not a second physics source. Add optional lightweight Three.js/browser 3D representations or a standard-library-only fallback 2D view, frame-synchronized timelines, model switches and 390-pixel responsive behavior. Document any network-first third-party renderer download as optional, not required for core operation. Render suspension heave/pitch and EV deceleration as separate modes, never create unintended coupling. Ensure exported numerical results remain identical to accepted physics and provenance; add rendering/interaction tests.

## Preserve exactly

- Accepted 2-DOF quarter-car, RK4, road studies, modal analysis, baseline comparison, convergence tools and exports.
- Accepted 4-DOF half-car with front/rear axle delay and small-angle limitations.
- Accepted Chat 5 longitudinal braking with identical stopping event, friction caps, axle load and legacy API schema.
- Chat 6 bounded regenerative motor/friction force blending, power/torque/battery acceptance constraints, exact stop trajectory, work accounting and v0.6.0 exports. All new tests must remain passing.
- Legacy health compatibility fields, no mandatory paid/third-party runtime installation, local MacBook Air M2 support.

## Do not implement without a separately approved scope

No actual hardware, ABS, physical BMS integration, tire slip, manufacturer motor map, real-world braking safety claims, unverified battery life/range estimates or Chat 8 features.

## Required Chat 7 deliverables when separately started

Complete updated source ZIP, verification report with inherited and new tests, independent numerical checks (showing no physics drift), clean Mac setup, user-verifiable browser checklist, checksum, source change manifest and Chat 8 planning-only handoff. Do not claim Mac verification without user confirmation.

## Copyable Chat 7 start prompt

> Start AutoDyn EV — Chat 7 of 10: Interactive 3D Engineering Visualization. Continue only from the attached accepted AutoDyn_EV_Chat6_v0.6.0.zip and exact release SHA-256. Inspect source, verify checksum, and rerun inherited tests first. Preserve the unchanged 2-DOF and 4-DOF suspension models, road studies, longitudinal braking and regenerative braking, numerical outputs, APIs and exports. Implement a lightweight, optional interactive 3D visualization synchronized to the existing physics data, with robust mobile and standard-library-compatible fallback, and validate that no dynamics or energy numbers change. Deliver full ZIP, verification report, Mac acceptance steps, manifest, checksum and Chat 8 handoff. Do not implement ABS, real hardware or Chat 8.
