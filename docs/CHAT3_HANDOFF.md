# AutoDyn EV — Chat 3 of 10 Handoff (Preparation Only)

**Chat 3 has NOT been started in Chat 2.**

## Verified baseline for continuation

Use the exact `AutoDyn_EV_Chat2_v0.2.0.zip` from this Chat 2 deliverable. The root folder is `autodyn-ev-chat2/`. Preserve all **95 passing Python tests** (57 inherited + 38 added), original 2-DOF equation conventions, the old three response charts and schematic animation, legacy CSV/JSON file names, documented endpoint contracts and the new studies. Validate the actual SHA-256 from `docs/CHAT2_SOURCE_SHA256.txt` and the ZIP checksum supplied alongside it.

Version 0.2.0 adds: full state-space damped pole diagnostics, controlled baseline-vs-variant overlays, bounded one-at-a-time vehicle parameter sweeps, aligned numerical refinement study, and additive JSON / sidecar CSV provenance. New API endpoints: `/api/modal`, `/api/compare`, `/api/sweep`, `/api/convergence`.

## Intended Chat 3 scope (do not start until requested)

Title: **AutoDyn EV — Chat 3 of 10: Half-Car Pitch and Heave Model**

1. Define an **independent, correctly derived** half-car 4-DOF vertical model (body heave + body pitch + front and rear unsprung masses), suspension/tire forces, wheelbase and signed lever arms. Clearly document static equilibrium and force/moment signs.
2. Implement front/rear road inputs including physically meaningful axle delay at a stated vehicle speed; preserve all existing quarter-car calculations unchanged.
3. Add a **separate model selector** and front/rear response plots with meaningful legends, model-specific export schema and safe default parameters.
4. Validate isolated spring/damper forces, torque balance, free-response modes, zero-input and static checks, integration refinement and cross-check against an independent numerical integrator where available.
5. Build careful engineering explanations; never claim real-vehicle measurement validation. Add Mac QA instructions and preserve all prior tests.
6. Deliver complete updated source ZIP, test evidence, documentation, Mac walkthrough and Chat 4 handoff. Do not implement braking, regeneration or commercial certification in Chat 3.

### Copy-ready Chat 3 prompt

Start AutoDyn EV — Chat 3 of 10: Half-Car Pitch and Heave Model. Continue only from the exact attached AutoDyn_EV_Chat2_v0.2.0.zip with its verified source manifest. Keep Chat 1 and Chat 2 features, original 2-DOF mathematical contracts, old and new endpoints, UI layouts, exports, all 95 automated tests, and unchanged legacy outputs. Derive and implement a physically consistent 4-DOF half-car heave/pitch/front-wheel/rear-wheel model with front/rear road disturbance delay. Add separate visualization, automated mechanical balance and convergence tests, independent checks when available, documented limitations, responsive UI, complete source ZIP, Mac acceptance guidance and Chat 4 handoff. Do not start Chat 4 or implement braking/regenerative braking yet.
