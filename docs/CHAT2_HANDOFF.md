# AutoDyn EV — Exact Chat 2 of 10 Handoff

**Do not treat Chat 2 as started.** This is a handoff contract for a separate future conversation.

## Verified checkpoint

- Source artifact: `AutoDyn_EV_Chat1_v0.1.0.zip`
- App version: `0.1.0`, content root: `autodyn-ev-chat1/`.
- Backend: `autodyn_ev.physics`, `.simulation`, `.server`; frontend `web/index.html`, `styles.css`, `app.js`.
- Runtime: local-only Python stdlib server, no required external dependencies.
- Verified: 57 Python automated tests; SciPy DOP853 reference comparison; Chromium desktop/mobile **isolated** browser UI tests via injected simulation bridge.
- **Pending:** User Mac live browser acceptance; external physical-model validation; actual public GitHub publication.
- Review `docs/VERIFICATION_REPORT.md`, `docs/ENGINEERING_MODEL.md`, and `docs/MAC_SETUP.md` before making edits.

## Goal of Chat 2

Implement a **validated quarter-car suspension laboratory expansion** (not yet the half-car model, which is Chat 3), focusing on meaningful engineering tools without breaking the Session 1 interface:

1. Add parametric road case comparison with controlled baseline-vs-variant metrics; clearly define repeatable road scenarios.
2. Add correct damped modal/damping-ratio analysis where applicable; do not confuse the current *undamped* eigenfrequencies with system damping.
3. Add suspension design-variable studies (mass, k, c, tire stiffness) and sweep visualizations, with computational budget limits.
4. Add numerical stability/time-step sensitivity diagnostics and step discontinuity caveats; make any derived conclusions explicit.
5. Expand CSV/JSON report provenance with model revision, parameter snapshot, scenario units, and solver method.
6. Add mechanical regression tests and (optionally) SciPy cross-verification. Preserve local/no-paid-dependency operation.

## Strict preservation rules

- Preserve the two-DOF equations, positive-up sign, static-equilibrium reference, shape of existing results and API response (or use backwards-compatible versioning).
- Maintain all 57 Session 1 tests; do not weaken validation to achieve green tests.
- Preserve 3 charts, schematic, responsive controls and CSV/JSON downloads.
- Keep current `tire_force_variation_n` clearly labeled dynamic **variation**, not actual contact force.
- Avoid claiming measured ride comfort, safety certification, or real-vehicle accuracy.
- No Step 3 half-car dynamics or Step 5 braking in Chat 2.
- If the ZIP isn't available, ask the user to upload **that exact source archive** rather than recreating it.

## Copy-paste prompt for Chat 2

> Start **AutoDyn EV — Chat 2 of 10: Quarter-Car Engineering Analysis & Parameter Studies**. Continue **only** from the exact `AutoDyn_EV_Chat1_v0.1.0.zip` baseline attached here. Do not restart the project or modify completed functionality unnecessarily. First inspect the source and read `README.md`, `docs/ENGINEERING_MODEL.md`, `docs/VERIFICATION_REPORT.md`, and `docs/CHAT2_HANDOFF.md`. Preserve all 57 passed tests and frontend/API compatibility. Implement validated sensitivity studies, baseline-versus-variant comparison, damping diagnostics, step-size/time-step accuracy investigation, provenance-enhanced exports, and engineering visualizations as specified in the handoff. Keep zero mandatory third-party dependencies and compatibility with MacBook Air M2. Perform genuine available tests and distinguish automated browser checks from user Mac acceptance. Deliver complete updated source ZIP, test evidence, exact Mac instructions, and Chat 3 handoff. Do not start Chat 3.
