# AutoDyn EV — Chat 9 of 10 preparation-only handoff

**Status:** PREPARED, NOT IMPLEMENTED. Chat 8 v0.8.0 Mac acceptance is pending.

**Proposed milestone:** Independent verification, sensitivity and engineering credibility hardening. Do not launch Chat 9 until the user has accepted Chat 8's Mac checklist and provided the exact accepted v0.8.0 archive.

## Baseline requirements

- Use exact accepted `AutoDyn_EV_Chat8_v0.8.0.zip` with its recorded SHA-256; inspect actual source and rerun all inherited tests before changing anything.
- Preserve accepted quarter/half/braking/regenerative models and API contracts, road study mathematics, 3D/2D visualization, optimization grids, outputs and exports.
- Keep zero mandatory third-party runtime dependencies and MacBook Air M2 compatibility.

## Planning focus

1. Engineering verification matrix with independently derived reference cases, explicit units and domain assumptions. Validate analytical limiting cases, numerical time-step convergence, and road-profile continuity.
2. Optimization reliability: numerical grid reproducibility, input validation, no-feasible handling, alternate trade-off objectives shown transparently, sensitivity to road/event and solver settings; distinguish study results from real-world design recommendations.
3. Separate test reports for physics, APIs, UI and independent numerical reference calculations. Seek 3rd-party experimental data only with clear provenance and user authorization; never present fabricated vehicle tests.
4. Improve accessibility, browser responsiveness, error messages, performance, and zero-third-party deployability as revealed by Mac acceptance, without changing model results.
5. Prepare interview-ready technical case studies and engineering validation tables, while deferring GitHub publication/final project closure to Chat 10 unless explicitly authorized earlier.

## Proposed delivery contract

Complete updated source ZIP, automated/independent testing evidence, preserved-model no-drift report, source manifest, release checksum, Mac checklist, and Chat 10 preparation-only handoff. Do not implement Chat 10 within Chat 9. Do not claim physical-vehicle certification.
