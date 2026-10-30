# AutoDyn EV — v1.0.0 — Publication Prepared (Chat 10 of 10)

**Local, reproducible engineering demonstrator — not an experimentally validated vehicle or road-safety tool.** This release preserves the accepted Chat 9 physics and study calculations and adds release-quality QA evidence, a clearer user guide, a GitHub-ready repository layout, and a mechanical/automotive portfolio case study.

**Verification:** 393 automated tests (391 inherited + 2 Git-layout regression tests). See [export versions and matching examples](docs/EXPORT_GUIDE.md) and [current verification](docs/CHAT10_VERIFICATION_REPORT.md). Historical reports below retain their original dates and counts.

## Quick start (MacBook Air M2; Python 3.10+)

```bash
cd ~/Downloads/autodyn-ev-chat10
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8774
```

Manually open `http://127.0.0.1:8774/` in Chrome or Safari. No pip/npm or Internet access is required. In a second Terminal, generate the reproducible verification evidence:

```bash
python3 scripts/chat9_evidence.py --out docs/chat10_evidence
python3 scripts/chat10_release_audit.py --out docs/chat10_release_audit.json
```

The four **independent, not dynamically coupled** simulation modes are a 2-DOF linear quarter-car, 4-DOF linear half-car with prescribed-speed axle road delay, friction-limited longitudinal braking, and friction/regenerative blending with illustrative motor/battery limits. Other tools: linear suspension road studies, 7-/49-case bounded discrete trade-off experiments and non-dominated comparisons, 3D projected schematic/2D fallback, and versioned downloads.

The plotted road/suspension state is not driven by braking deceleration. Tire deflection is a proxy (not contact verification); no ABS, wheel slip, nonlinear tire model, real motor efficiency map, real battery SOC/temperature, uncertainty calibration, physical road tests, functional-safety certification, ISO 2631 compliance, or globally optimal design claims are supplied. **Numerical and regression verification do not establish real-vehicle accuracy.**

**Release guide:** [`docs/FINAL_ENGINEERING_GUIDE.md`](docs/FINAL_ENGINEERING_GUIDE.md) · [verification](docs/CHAT10_VERIFICATION_REPORT.md) · [Mac acceptance](docs/CHAT10_MAC_ACCEPTANCE.md) · [portfolio case study](docs/PORTFOLIO_CASE_STUDY.md) · [known issues](docs/KNOWN_ISSUES_CHAT10.md) · [hosting and publication](docs/PUBLICATION_PLAN.md). Public GitHub publication and hosting have not been carried out.

**Parameter-update verification:** After moving the sprung-mass slider, previous metrics are cleared and visibly marked stale. Releasing the slider automatically recalculates the simulation; **Run simulation** also works explicitly. The refreshed status names the applied sprung mass. Under the default bump conditions, 300 kg yields 0.906 RMS acceleration and 500 kg yields 0.556 m/s². Run `python3 scripts/check_mass_update.py --port 8774` while the server is running to check the API. The corrected Chat 9 hotfix was user-verified in Chrome (300 → 500 kg, 0.906 → 0.556 RMS) and passed 376 Mac tests. This v1.0.0 merge preserves that code; the supplied owner acceptance handoff records all four final Mac checks as confirmed.

**Versioning:** Final *local release* is `v1.0.0` (`/api/health.final_release_version`, header/footer, packaging). The established `version`, `application_version`, `release_version`, `current_release_version`, `active_application_version` health fields intentionally retain older compatibility values. Historical sections below document their respective former releases, not current-version promises.

---

## Historical release notes (retained unchanged below)

# AutoDyn EV — Current release v0.9.0 (Chat 9 of 10)

**Engineering verification, sensitivity and credibility hardening**. This version is derived *only* from the accepted v0.8.0 source ZIP (SHA-256 `c9919d5ebc406cf30ec652e9f187fa78607b618d20ed48aef217186c9b8a7e7a`). All authoritative dynamics/optimization algorithms and previous UI features remain unchanged.

New: optional reproducible independent-reference and deterministic optimization evidence, strict numerical/API regression tests, standalone SciPy DOP853 cross-checks (development-time only), 14-case exact numerical no-drift comparison, and optional Chromium browser checks forwarded to the real local API. Verification does **not** constitute calibration against a real EV, tire-contact certification, ABS validation, ISO ride-comfort compliance, or a globally optimal design.

The legacy `__version__`, old `CURRENT_RELEASE_VERSION` and historical health compatibility keys remain unchanged to preserve existing clients/tests. The active application release is `ACTIVE_APPLICATION_VERSION = "0.9.0"`, reported by `active_application_version` in `/api/health`, the visible header/footer and server startup output. Optimization outputs retain their historical v0.8.0 schema/version because numerical behavior is preserved.

## Run on a MacBook Air M2

```bash
cd ~/Downloads/autodyn-ev-chat9
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8773
```

Open `http://127.0.0.1:8773/` manually in Chrome. There are **zero third-party mandatory runtime dependencies**. To regenerate the reference evidence using only the Python standard library:

```bash
python3 scripts/chat9_evidence.py --out docs/chat9_evidence
```

To independently recheck the accepted baseline, extract **the unchanged v0.8.0 ZIP** to another folder and run `python3 scripts/chat9_no_drift.py /path/to/pristine/autodyn-ev-chat8`. Optional developer tools: `python3 scripts/chat9_scipy_optional.py` (SciPy), `python3 scripts/chat9_browser_optional.py` (Playwright plus Chromium).

See `docs/CHAT9_VERIFICATION_REPORT.md`, `docs/CHAT9_MAC_ACCEPTANCE.md`, `docs/CHAT9_NO_DRIFT.json` and `docs/CHAT10_PREPARATION_ONLY_HANDOFF.md`. Chat 9's live Mac acceptance and physical road-test validation are **not completed**. Chat 10 is **not implemented**.

---

# AutoDyn EV — Current release v0.8.0 (Chat 8 of 10)

**Baseline:** accepted v0.7.0 archive, SHA-256 `ab402d8b2bb5e213f9e6535b370cc078425e5c9a143454dc564fb7dcc664401c`. This section describes the **current application release**; earlier release sections below are preserved for historical reference, not presented as current release instructions.

**New in Chat 8:** offline Engineering Optimization / Trade-off Laboratory for validated quarter-car and half-car simulations. A deterministic, bounded 7-case or 49-case grid varies one/two suspension stiffness and damping parameters over ±20% of the current vehicle configuration, clipped to accepted physical input bounds. It calculates explicit time-weighted acceleration RMS, suspension travel peak-to-peak, and tire-deflection **proxies**. Optional thresholds filter feasible cases; a two-objective non-dominance set illustrates trade-offs without a synthetic combined score. Exports include a versioned JSON report with complete provenance, precision-preserving CSV with repeated input provenance, and a plain-text engineering report. **No real-vehicle optimum, ISO ride-comfort certification, tire-contact prediction, combined brake/ride score or battery range claim.**

**All four original physics modes, original API response shapes, 3D viewer, 2D fallback, and legacy analysis tools remain available.** The optimizer is additive at `POST /api/optimization/study` and does not change original physics modules. `__version__` is retained as a legacy compatibility marker for accepted tests; the active application release and `current_release_version` API field identify v0.8.0.

Run on MacBook Air M2 using only Python standard library:

```bash
cd ~/Downloads/autodyn-ev-chat8
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8772
```

Open `http://127.0.0.1:8772/` manually. Use the optimization laboratory above the half-car workstation and select a quarter-car or half-car study. No `pip` or `npm` installation is required for the application; optional browser/independent numerical tools are verification aids only.

**Engineering validation:** see `docs/CHAT8_VERIFICATION_REPORT.md`, `docs/ENGINEERING_OPTIMIZATION_CHAT8.md`, and `docs/CHAT8_MAC_SETUP_AND_ACCEPTANCE.md`. Chat 8 Mac live-browser acceptance and physical vehicle calibration remain pending until actually performed.

---

# AutoDyn EV — Current release v0.6.0 (Chat 6 of 10)

**Accepted origin:** Chat 5 source `AutoDyn_EV_Chat5_v0.5.0.zip`, SHA-256 `fd7f4f37cf615203b90eb94b7250330b5e78e25d4c6c1658022f1ebdb9a4cffa`. The following is the **current** release overview; historical Chat 1 descriptions and its original verification claims below are preserved as project history, not current project state.

**Four independent modes:** quarter-car 2-DOF, half-car 4-DOF, longitudinal friction braking and independent regenerative braking / energy-recovery extension. **No** braking-to-suspension speed coupling. The regen mode allocates feasible braking demand to motor regeneration first, then friction braking; it bounds motor shaft torque (converted to an ideal wheel-side force using gear ratio and wheel radius), mechanical power and electrical battery charging power. A constant illustrative conversion efficiency accounts for losses. No ABS, tire-slip model, production BMS, battery SOC/temperature physics, motor map or real-vehicle validation.

Run using Python 3.10+ standard library only (MacBook Air M2 compatible):

```bash
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8770
```

Open `http://127.0.0.1:8770/` and select **Regenerative braking · EV**. You may also use `bash run_mac.sh 8770`.

**Verified in this release:** 291 tests (231 inherited + 60 Chat 6), independent SciPy DOP853 reference comparison across 100 braking scenarios, 33 browser-harness checks in isolated Chromium with a proxied local API, a complete source ZIP and reproducible CSV/JSON examples. **Not verified:** actual macOS Chrome/Safari acceptance, physical vehicle/battery performance, public GitHub deployment. SciPy/Playwright are for optional independent verification only, and are not required to run the application or standard tests.

**Engineering details:** [Regenerative Braking Model](docs/ENGINEERING_REGEN_CHAT6.md) · [Verification Report](docs/CHAT6_VERIFICATION_REPORT.md) · [Mac Acceptance](docs/MAC_CHAT6_ACCEPTANCE.md) · [Chat 7 Handoff](docs/CHAT7_HANDOFF.md).

---

# AutoDyn EV · v0.5.0 — Chat 5 of 10 · Longitudinal Braking & Load Transfer

**Independent engineering simulation, not road-safety guidance or vehicle-certified software.** Derived from the accepted Chat 4 v0.4.0 ZIP (verified SHA-256 `d3875d670e2a19a2f5376a2588dbdb5504e7a15274918028c5a0da0de7805a3e`). Chat 4 is preserved as a separate immutable ZIP; all 188 inherited tests remain passing. There are no mandatory third-party Python or JavaScript packages.

## Start on MacBook Air M2

Download `AutoDyn_EV_Chat5_v0.5.0.zip`, extract in Downloads, then run:

```bash
cd ~/Downloads/autodyn-ev-chat5
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8769
```

**Manually enter `http://127.0.0.1:8769/` in Chrome** (without URL suffixes or markdown characters). Keep Terminal open. If port 8769 is occupied, choose another free port. The application requires no network access except the browser connecting to your own `127.0.0.1` server.

Select **Braking & load transfer** from the model selector. Enter vehicle mass, CG geometry, initial speed, assumed aggregate friction μ, requested deceleration, constant/ramp command, time step and duration. The new display shows exact stop-event results, traction limitation, front/rear quasi-static normal loads and five graphs. Export versioned CSV and JSON. The **Quarter-car · 2 DOF** and **Half-car · 4 DOF** model views remain available and do not receive a time-varying braking speed input.

- New endpoint: `POST /api/braking/simulate` with `{ "scenario": { "initial_speed_m_s": 20, "profile": "constant" } }`, also accepts an empty `{}` to use documented defaults.
- Zero mandatory third-party dependencies. Optional isolated Chromium/Playwright and SciPy reference scripts are developer-only.
- Verification: **231 Python unit/API tests passed** (188 inherited + 43 new), **46 isolated Chromium desktop/mobile checks**, and **120 independent SciPy quadrature/reference cases**. Mac live-browser acceptance and physical validation are pending.
- Read [braking engineering method](docs/ENGINEERING_BRAKING_CHAT5.md), [Chat 5 verification report](docs/CHAT5_VERIFICATION_REPORT.md), [Mac acceptance](docs/MAC_CHAT5_ACCEPTANCE.md), and [Chat 6 handoff](docs/CHAT6_HANDOFF.md).

---

## Previous release notes, preserved below

# AutoDyn EV · v0.4.0 — Chat 4 of 10 · Road & Ride Laboratory

**Complete offline/local browser source — no mandatory paid or third-party runtime dependencies.** Based exclusively on the verified accepted Chat 3 v0.3.0 archive. All 136 inherited tests retained; 52 new tests added. This is a **software engineering simulation**, NOT a validated real vehicle or ISO 2631 comfort tool.

## Mac launch (including MacBook Air M2)

Extract `AutoDyn_EV_Chat4_v0.4.0.zip` into Downloads and run:

```bash
cd ~/Downloads/autodyn-ev-chat4
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8768
```

Type **http://127.0.0.1:8768/** manually in Chrome. Use a different unused port if 8768 is already occupied. Do **not** append paths or query parameters. No `pip` or `npm` required.

## Chat 4 features

- **Added shared deterministic road profiles** for both 2-DOF quarter-car and 4-DOF half-car: smooth negative **pothole**, two **separated raised-cosine bumps**, and a **linear frequency chirp**, alongside preserved flat, bump, step and sine behavior.
- **Explicit spatial and temporal controls:** signed vertical road input (road amplitude remains a nonnegative magnitude), bump feature length/gap, constant speed, chirp start/end frequency and ramp duration, and numerical sample-resolution safeguards.
- **New Ride Response Laboratory** in both model views: time-weighted **unweighted** body-acceleration RMS, acceleration peaks, peak-to-peak suspension travel, tire-deflection proxies, and correctly scoped post-event window/settling metrics. Separate charts retain consistent units. Optional **within-model** baseline comparisons permit suspension sensitivity studies with exactly matched road/time settings.
- Versioned `POST /api/ride/study` and CSV/JSON engineering exports with model/road/vehicle/time-unit provenance and explicit warnings. Inherited routes, models, animation and original exports remain available.
- Verified **188 Python tests**, optional independent SciPy reference checks and **24 isolated Chromium desktop/mobile interaction checks**. **User Mac acceptance pending.**

See [Chat 4 road/ride engineering methods](docs/ENGINEERING_ROAD_RIDE_CHAT4.md), [verification report](docs/CHAT4_VERIFICATION_REPORT.md), [Mac browser acceptance guide](docs/MAC_CHAT4_ACCEPTANCE.md), [change manifest](docs/CHAT4_CHANGE_MANIFEST.json), and [Chat 5 preparation-only handoff](docs/CHAT5_HANDOFF.md).

---

## Preserved Chat 3 documentation

# AutoDyn EV · Chat 3 of 10 — Half-Car Pitch and Heave

**v0.3.0 · October 29, 2026 · mechanical-engineering educational simulator · zero mandatory third-party dependencies**

> **Chat 3 adds a distinct 4-DOF half-car mode without replacing the accepted 2-DOF quarter-car.** The inherited quarter-car equations, simulation channels, studies, exports, UI charts/animation and 95 regression tests are preserved. The original Chat 2 README follows below as historical documentation.

![Half-car v0.3.0 desktop](docs/chat3-dashboard-desktop.png)

## Run v0.3.0 on macOS (Apple Silicon MacBook Air M2)

```bash
cd ~/Downloads/autodyn-ev-chat3
python3 -m unittest discover -s tests -v
python3 -m autodyn_ev.server --port 8767
```

Then open **http://127.0.0.1:8767/** in Chrome or Safari. Keep Terminal open and press `Control+C` to stop. Port 8767 avoids previously used 8765/8766 if Chat 1/2 are still running. `./run_mac.sh 8767` is an alternative. No pip installation, npm or internet connection required.

## Chat 3 model and controls

Select **Half-car · 4 DOF** in the top-right **MODEL SELECTOR**. The original **Quarter-car · 2 DOF** remains selectable and unchanged. Adjust body mass, pitch inertia, CG-to-axle distances and independent front/rear spring, damper, wheel mass and tire stiffness inputs, then select road profile, positive speed, duration and integration step. Press **Run half-car model**. Inspect body acceleration RMS, peak pitch, front/rear travel and wheelbase-derived road delay. Inspect the animated side view and four chart panels; export model-specific time-history CSV and full JSON technical report.

The half-car API is an **additive endpoint**, `POST /api/halfcar/simulate`, with scenario body `{"vehicle":{},"road":{},"settings":{}}`. Empty maps produce the documented defaults. Response `schema_version=half-car-1.0` includes eight-state time histories, independent wheel/road profiles, suspension forces, metrics, SI units and provenance. Original `/api/simulate`, `/api/modal`, `/api/compare`, `/api/sweep` and `/api/convergence` retain their existing contracts.

**Software verification:** 136/136 Python unit/API tests passed (95 inherited + 41 new); NumPy independent M,C,K assembly agreed on 150 randomized models and SciPy DOP853 agreed for a smooth sine input, within documented tolerances. Isolated Chromium desktop/mobile UX harness passed. **Live browser acceptance on your Mac, real vehicle validation and GitHub deployment are PENDING.** See [`docs/CHAT3_VERIFICATION_REPORT.md`](docs/CHAT3_VERIFICATION_REPORT.md), [`docs/ENGINEERING_HALF_CAR.md`](docs/ENGINEERING_HALF_CAR.md), [`docs/MAC_CHAT3_ACCEPTANCE.md`](docs/MAC_CHAT3_ACCEPTANCE.md) and [`docs/CHAT4_HANDOFF.md`](docs/CHAT4_HANDOFF.md).

This is a linear small-angle educational half-car, not a 3D vehicle digital twin or physical safety tool. Tires are always engaged; no contact loss, roll, yaw, tire damping or actual vehicle calibration. The rear axle sees the same road feature delayed by wheelbase/forward speed; speed must be positive. For mixed-unit display plots, consult CSV for accurate numerical interpretation.

---

## Preserved Chat 2 documentation (historical)

# AutoDyn EV · Interactive Vehicle Dynamics Laboratory

**Chat 2 of 10 · v0.2.0 · 29 October 2026 · Software-only educational quarter-car analysis laboratory**

A transparent, testable **two-degree-of-freedom quarter-car suspension simulator** with a browser-based engineering interface. Intended as a mechanical-engineering portfolio project, not certified vehicle simulation software.

![AutoDyn EV Chat 2 desktop dashboard](docs/chat2-dashboard-desktop.png)

## Launch on macOS (including Apple Silicon MacBook Air M2)

Requires **Python 3.10+** and an up-to-date browser. **No npm, pip installation, cloud account, external services, or paid license required.**

1. Extract the ZIP and open **Terminal**.
2. Enter the extracted folder (adjust path if you moved it):

   ```bash
   cd ~/Downloads/autodyn-ev-chat2
   python3 --version
   python3 -m unittest discover -s tests -v
   python3 -m autodyn_ev.server --port 8765
   ```
3. In Chrome or Safari, open **http://127.0.0.1:8765/**. Keep Terminal open; use **Ctrl+C** to stop.

If port 8765 is occupied, use `python3 -m autodyn_ev.server --port 8766` and open the corresponding URL.

If `python3` is unavailable, install a current Python 3.x version from the official Python downloads site. This code supports Python 3.10–3.13 by design; local verification was with Python 3.13.5 on Linux, **not** on your Mac.

For Chat 2-specific acceptance see [`docs/MAC_CHAT2_ACCEPTANCE.md`](docs/MAC_CHAT2_ACCEPTANCE.md). The original Chat 1 setup remains in `docs/MAC_SETUP.md` for historical reference.

## How to use

1. Set sprung/unsprung mass, suspension stiffness, damping coefficient and tire stiffness.
2. Choose a bump, step, sine-wave road or zero-input flat road.
3. Set road amplitude, bump length, vehicle speed (for bump traversal), duration and integration time step.
4. Select **Run simulation**.
5. Inspect RMS body acceleration, peak body acceleration, suspension travel, first undamped mode and three interactive plots.
6. Pause or scrub the schematic; move the pointer over charts to inspect time-aligned values.
7. **Export CSV** for all 12 channels and **Export summary** for parameters, assumptions and metrics.

**Illustrative default scenario:** 300 kg sprung mass, 40 kg unsprung mass, 18,000 N/m spring, 1,500 N·s/m damper, 190,000 N/m tire, 60 mm raised-cosine bump, 1.5 m traversal at 5 m/s, 5 seconds of response, 0.005 s integration step. Results are in [`examples/default_bump_metrics.json`](examples/default_bump_metrics.json) and [`examples/default_bump_response.csv`](examples/default_bump_response.csv).


## New in Chat 2 (v0.2.0)

Preserves Chat 1's original physics, three charts, animation, flat/bump/step/sine roads, old CSV/JSON exports and all 57 legacy tests. Added an **Engineering Studies** section below the original graphs:

1. **Damped modal analysis** using poles of the exact coupled 2-DOF state-space system, with real-pole handling and distinct undamped metrics.
2. **Baseline vs variant comparison** with two time-aligned responses and transparent metric deltas. Save a baseline, change suspension sliders, then compare.
3. **Bounded one-at-a-time parameter sweep** over suspension mass/stiffness/damping/tire parameters (7 points by default in browser; server supports 3–11).
4. **RK4 time-step sensitivity study** at aligned 10/5/2.5 ms time steps; finest tested trajectory is the numerical reference, not exact truth.
5. **Provenance-enhanced exports:** additive JSON model/solver/unit metadata; separately downloaded provenance sidecar for **unchanged 12-column legacy CSV**; new study CSV/JSON formats.

**New API endpoints:** `POST /api/modal`, `/api/compare`, `/api/sweep`, `/api/convergence`. For exact schemas, equations, validation limits and caveats see [`docs/ENGINEERING_STUDIES_CHAT2.md`](docs/ENGINEERING_STUDIES_CHAT2.md).

**Verification:** 95 Python tests passed (57 inherited + 38 new), optional SciPy/NumPy independent checks passed, and isolated Chromium desktop/mobile interaction checks passed. Live browser-to-localhost acceptance on *your Mac* is pending: follow [`docs/MAC_CHAT2_ACCEPTANCE.md`](docs/MAC_CHAT2_ACCEPTANCE.md). Full evidence: [`docs/CHAT2_VERIFICATION_REPORT.md`](docs/CHAT2_VERIFICATION_REPORT.md). **Chat 3 has not started.**

## Mathematical model

The state is `y = [z_s, z_u, v_s, v_u]`; `z_s` is sprung body deviation, `z_u` wheel/unsprung deviation, `z_r` road disturbance. Positive is upward. Displacements are **relative to static equilibrium**.

```text
m_s z̈_s = −k_s(z_s − z_u) − c_s(ż_s − ż_u)
m_u z̈_u = +k_s(z_s − z_u) + c_s(ż_s − ż_u) − k_t(z_u − z_r)
```

The default 60 mm bump is smooth: `z_r(t) = h/2 · [1 − cos(2π(t − t0)/T)]` for `t0 <= t < t0 + T`, otherwise zero, with `T = bump length / speed`.

The solver is a **fixed-step classical fourth-order Runge–Kutta integrator (RK4)**. Step-size safety checks require >=12 steps through a nonzero bump or >=20 steps per sine-wave period. See [`docs/ENGINEERING_MODEL.md`](docs/ENGINEERING_MODEL.md) for a complete sign convention, derivation, metrics and limitations.

## Repo layout

```text
autodyn-ev-chat2/
├── autodyn_ev/
│   ├── __init__.py        # Semantic version
│   ├── analysis.py        # Chat 2 modal, comparison, sweep, refinement and provenance
│   ├── physics.py         # Data contracts, road profiles, ODE, RK4, energy
│   ├── simulation.py      # Channel history, scenario metrics, data schema
│   └── server.py          # Local-only Python HTTP + JSON API
├── web/
│   ├── index.html         # Accessible controls and panels
│   ├── styles.css         # Responsive visual design
│   └── app.js             # Charts, animation, scenario interaction, exports
├── tests/
│   ├── test_physics.py    # Mechanics, conservation/dissipation, convergence
│   └── test_server.py     # Real local API integration checks
├── scripts/
│   ├── export_example.py
│   ├── scipy_reference_check.py  # Optional independent numerical cross-check
│   └── browser_smoke_optional.py # Optional isolated browser harness
├── examples/
│   ├── default_bump_metrics.json
│   └── default_bump_response.csv
├── docs/
│   ├── ENGINEERING_MODEL.md
│   ├── VERIFICATION_REPORT.md
│   ├── MAC_SETUP.md
│   ├── CHAT2_HANDOFF.md
│   ├── SESSION1_SCOPE.md
│   └── dashboard-*.png
├── .gitignore
├── pyproject.toml
└── README.md
```

## Engineering verification

Run:

```bash
python3 -m unittest discover -s tests -v
python3 -m scripts.export_example
```

**57 automated unit + HTTP integration checks passed on the authoring runtime**. Optional independent solver verification against SciPy DOP853 passed (external package used for **verification only**; it is not needed to run the app). An isolated Chromium UI harness also passed desktop and mobile checks with an injected simulation bridge, but **end-to-end browser navigation to the actual local server was blocked in this environment**. You must confirm the live desktop/Mac workflow yourself.

See [`docs/VERIFICATION_REPORT.md`](docs/VERIFICATION_REPORT.md) for verified/pending status and reproducibility steps.

## Scope boundaries

**Implemented in Chat 1:** linear 2-DOF vertical suspension, smooth bump/step/sine/flat road, fixed-step RK4, numerical constraints, output CSV/JSON, interactive graphing and schematic animation, engineering checks.

**Not implemented in Chat 1:** half-car pitch, roll, nonlinear dampers, tire separation, tire force/contact clipping, braking, longitudinal weight transfer, EV regenerative braking, 3D car, optimization, measured vehicle calibration, validation against road-test data, public hosting. These belong to later chats, subject to separate validation. Refer to [`docs/CHAT2_HANDOFF.md`](docs/CHAT2_HANDOFF.md). **Chat 2 has NOT been started.**

## Attribution and integrity

Independent educational prototype prepared with ChatGPT assistance. All sample vehicle settings are illustrative; no claim of calibration, manufacturing feasibility, ISO comfort compliance, real-world braking performance, or commercial accuracy. Numerical validation is not the same as physical validation.

## Chat 7 — Interactive engineering visualization (v0.7.0)

This milestone adds an **optional software-projected 3D viewer** before the individual model workspaces. It uses local Canvas2D polygon projection, interactive camera orbit (pointer drag / arrow keys), zoom, deterministic read-only channel interpolation, playback/pause/restart, 0.5×/1×/2× playback, time scrubbing, live SI measurements, a 2D SVG fallback and a reduced-motion-aware initially paused timeline. It runs offline with no CDN, WebGL or third-party runtime modules. Selecting the viewer's 2D fallback never disables the original plots/exports.

The projected shapes are generic schematic solids, not measured vehicle geometry. Quarter-car uses computed sprung/unsprung vertical displacement; half-car uses computed body heave, **positive nose-up pitch** and front/rear wheels; braking and EV regeneration use computed **speed, travel, axle loads**, and, for regen, battery energy and brake-blend channels. The longitudinal view deliberately **does not animate body pitch**, because the braking model does not solve pitch dynamics. The suspension vehicle road speed remains constant in its own independent model. Display interpolation is strictly **linear between returned time samples** and does not change the underlying solver or exports. Heave and pitch are visually exaggerated (and clipped for display) and never feed into calculations.

Run the full Python suite from the project root with `python3 -m unittest discover -s tests -v`; run the application with `python3 -m autodyn_ev.server --port 8771` and open `http://127.0.0.1:8771/`. No `pip install` is necessary. Optional Node checks for visual math are included in the Python test runner when Node is present.

**Compatibility:** The legacy health response's `version`, `application_version`, and historical `release_version` remain unchanged for compatibility; new `current_release_version` reports `0.7.0`. Historical braking and regen API payload versions are intentionally not rewritten. The current UI header/footer display Chat 7.

Evidence: `docs/CHAT7_VERIFICATION_REPORT.md`, `docs/chat7_no_physics_drift.json`, `docs/chat7_browser_results.json`, `docs/CHAT7_MAC_SETUP_AND_ACCEPTANCE.md`. Live Mac browser acceptance and real-vehicle calibration remain pending.
