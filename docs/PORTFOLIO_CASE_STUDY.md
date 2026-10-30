# AutoDyn EV — Mechanical / Automotive Engineering Portfolio Case Study

**Title:** AutoDyn EV — Offline Vehicle Dynamics & Engineering Trade-off Laboratory  
**Role:** Independent software-based engineering project  
**Technology:** Python 3.10+ (standard library), classical RK4, HTML/CSS/JavaScript, Canvas2D, GitHub-ready CI workflow. Optional QA: SciPy, Chromium/Playwright.  
**Release:** v1.0.0 published; public Python simulator verified on Render Free on 30 October 2026.

## Engineering question

How do changes in suspension stiffness/damping, road input and available braking/regen constraints alter **simulated** ride response, stopping dynamics and energy partition? How can the results be made inspectable without implying a real-vehicle optimum?

## Method

1. Implemented a linear 2-DOF quarter-car with sprung/unsprung displacements, spring-damper and tire stiffness; used a deterministic RK4 time integrator.
2. Added independent linear 4-DOF half-car with body heave/pitch, front/rear wheel response and prescribed-speed axle delay.
3. Built separate friction-limited braking and regenerative/friction-blending models; track exact idealized stopping events and energy paths.
4. Developed a local web interface showing interactive time-domain traces, schematic projected 3D/2D fallback, study comparisons and CSV/JSON results.
5. Enumerated bounded 7-/49-case suspension grids with explicit feasible constraints and Pareto-nondominated candidates, **without a single fabricated global score**.
6. Hardened numerical claims with force/energy identities, time-step sensitivity, independent SciPy references, 14 exact baseline no-drift comparisons, and release tests.

## Representative calculated results, not experimental measurements

| Demonstration | Output (assumptions apply) |
| --- | --- |
| Default quarter-car bump | ~0.906 m/s² RMS sprung acceleration; 48.06 mm peak suspension travel |
| Default half-car road delay | 2.5-m wheelbase at 5 m/s → 0.500 s rear-axle delay |
| Constant idealized braking | 20 m/s, 5 m/s² → 4 s stop, 40 m travel |
| Default regenerative example | 240 kJ initial kinetic energy, ~76.64 kJ battery storage, ~31.9% recovery fraction of kinetic reduction |
| Engineering grid | 7 one-parameter or 49 two-parameter cases; explicit feasible/Pareto trade-offs |
| Release QA | 393 automated Python tests (391 inherited + 2 publication regression tests), 14 byte-identical no-drift cases, 46 historical isolated Chromium real-API checks and 6 optional independent SciPy cases |

**Interpretation:** In the bounded damping grid, the selected case was **case 1** for bump/pothole and **case 7** for sine input (with unchanged case-enumeration rule). This is a road-input-dependent *simulation choice*, not an optimal real suspension setting.

## Resume bullets (two or three; adjust to available space)

- Developed **AutoDyn EV**, a Python-based vehicle-dynamics laboratory modelling 2-DOF quarter-car and 4-DOF half-car heave/pitch response, deterministic RK4 integration and parameter-sensitive road excitation.
- Implemented independent friction-limited braking and regenerative energy accounting with motor/battery constraints; created interactive projected-3D/2D visualizations and downloadable engineering reports.
- Validated the educational simulator with **393 automated tests**, **14 exact historical-output comparisons**, six SciPy reference cases and bounded 7-/49-case Pareto trade-off studies; documented model limitations and reproducibility.

## Two-minute interview demo outline

**0:00–0:20** State problem, model scope and limitations. **0:20–0:45** Run quarter-car bump; explain sprung acceleration and unsprung travel. **0:45–1:05** Switch half-car; show heave, nose-up pitch and front/rear delay. **1:05–1:25** Explain isolated longitudinal braking and regeneration with an energy ledger. **1:25–1:45** Run 7-case damper study, show Pareto outcomes and why road profile changes selected case. **1:45–2:00** Show source/tests, evidence and missing real-world calibration; do not imply certification.

## Interview questions with grounded short answers

1. **Why RK4?** A deterministic fourth-order integration scheme for smooth ODE segments; convergence checks matter near event boundaries.
2. **Why both quarter- and half-car?** Quarter-car isolates vertical body/wheel response; half-car adds sprung-body pitch and separate front/rear axles.
3. **What is assumed about road speed?** Prescribed and fixed for suspension road-input timing; it does not follow braking speed.
4. **Can tire-deflection proxy predict lift-off?** No. The model retains a linear tire connection and does not simulate contact separation.
5. **What does the 49-case Pareto plot mean?** It shows discrete non-dominated candidates for reported simulated objectives under explicit constraints, not a global optimum.
6. **What does 14/14 no-drift mean?** The accepted model outputs match the earlier source byte-for-byte for selected test scenarios; this is not physical accuracy.
7. **Is the regeneration figure a real EV measurement?** No. It follows an idealized torque/power/battery-acceptance model with constant efficiency.
8. **What next for industrial credibility?** Calibrate parameters with instrumented tests; compare against real acceleration, pitch, travel, tire forces and battery/motor maps; quantify uncertainty and add tire contact/slip.

**Portfolio disclosure:** This is a software simulation project. No vehicle hardware prototype, measured test track results, homologation, safety certification, or commercial deployment is claimed. **Public repository and live demo verified:** https://github.com/harshvtomar/autodyn-ev and https://autodyn-ev.onrender.com/. See LIVE_VERIFICATION.md for scope.
