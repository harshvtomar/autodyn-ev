# AutoDyn EV v1.0.0 — Architecture & Engineering Reference

## Purpose and topology

A **local educational dynamics laboratory**, not physical vehicle hardware, a certified digital twin or safe-distance calculator. Python standard library computes independent scenario traces and serves JSON from loopback; plain HTML/CSS/JavaScript renders charts, projected 3D/2D schematics, parameter studies and downloads. All eight original numerical/analysis modules from accepted Chat 9 are unchanged. Release-only source changes are version metadata, keyboard skip navigation and evidence/QA material.

| Subsystem | Authoritative modules | Meaning / boundaries |
| --- | --- | --- |
| 2-DOF quarter-car | `physics.py`, `simulation.py` | Upward static-equilibrium-relative sprung/unsprung motion with linear suspension and tire stiffness |
| 4-DOF half-car | `halfcar.py` | Sprung-body heave, nose-up pitch, front/rear wheel displacement; road rear-delay = wheelbase / **prescribed**, non-braking speed |
| Friction braking | `braking.py` | Separate longitudinal stopping model; bounded brake demand, aggregate friction, quasi-static front/rear axle normal-load transfer |
| Regenerative braking | `regen.py` | Separate regeneration-first/friction blending subject to torque, power, battery acceptance, efficiency and speed limits |
| Engineering comparison | `analysis.py`, `ride.py`, `optimization.py` | Diagnostic modal/study tools, ride metrics, deterministic discrete 7-/49-case constraints and non-dominance |
| User interface | `web/` | Presentation and downloads, not a physics solver; offline when served from the local Python server |

## Quarter-car equations and conventions

Static-equilibrium-relative vertical coordinates, up positive: sprung `z_s`, unsprung `z_u`, road `r`, stiffness `k_s`, damping `c_s`, tire stiffness `k_t`.

`F_s = k_s(z_s-z_u) + c_s(v_s-v_u)`; `F_t = k_t(z_u-r)`;
`m_s a_s = -F_s`; `m_u a_u = F_s - F_t`.

Flat road and zero initial conditions yield zero motion. The tire force variation is **not** a guaranteed nonnegative normal contact force. No nonlinear suspension travel or tire separation is modeled. See `docs/ENGINEERING_MODEL.md` for the original complete contract.

## Half-car equations and conventions

Body heave `z_b` is up-positive; pitch `theta` is **nose-up positive**. The body attachment displacements under the small-angle assumption are approximately `z_b+a theta` at the front, `z_b-b theta` at rear for positive axle distances `a,b`. Each attachment has an independent linear spring/damper to its own unsprung coordinate, and each unsprung mass has tire stiffness to its local road displacement. Rear road signal is delayed by `(a+b)/v_road` with **fixed prescribed road speed**. No coupling to the separately simulated longitudinal braking speed. See `docs/ENGINEERING_HALF_CAR.md` and `docs/CHAT3_VERIFICATION_REPORT.md`.

## Braking and energy

Simplified longitudinal acceleration is bounded by requested braking and the assumed aggregate friction cap `mu*g`, within model limits; ideal constant deceleration for a 20 m/s initial speed and 5 m/s² gives 4 s, 40 m using `t_stop=v0/a`, `d_stop=v0²/(2a)`. Front/rear quasi-static normal load transfer balances weight and depends on CG height/wheelbase; it is not a suspension pitch dynamics solution. Regenerative force is capped by wheel-side torque, mechanical power, battery charge acceptance, conversion efficiency and cutoff, then friction braking supplies the remaining feasible demand. Energy bookkeeping distinguishes battery stored, conversion loss, friction heat and residual kinetic energy. These are **model calculations**, not an actual motor or BMS map.

## Numerical approach and validation

- Deterministic fixed-step RK4 integrates suspension ODE states, with scenario bounds and minimum road-resolution checks. Event-sensitive limits and alignment effects must be considered. No adaptive solver is required at runtime.
- Independent SciPy DOP853 verification is **optional QA**; comparing to DOP853 tests implemented equations, not physical calibration.
- Model outputs are immutable from accepted v0.9.0: the Chat 10 14-case exact output hash comparison is the regression anchor. `scripts/chat10_no_drift.py` uses clean subprocesses for each tree.
- Optimization enumerates only a **bounded, discrete** sampled design grid; feasibility conditions are explicit, tire-deflection is a proxy, and Pareto candidates are nondominated for the stated simulated objectives. No combined score/global optimum assertion.

## Reproducible experiment matrix

| Investigation | Workflow | Recorded evidence |
| --- | --- | --- |
| Road excitation | Run quarter-car bump, sine and pothole; vary road amplitude and step | Vertical displacement/acceleration/travel curves, time-step differences |
| Pitch/heave | Select half-car; compare front and rear response and delayed road input | Body heave and pitch, front/rear wheel traces, 0.500-s default delay |
| Friction cap | Select braking; compare constant and ramp demand and lower mu | Stop/no-stop flag, distance, axle load channels |
| Recovery | Select regenerative; vary torque, battery acceptance and efficiency | Stored battery energy, mechanical work, friction heat and losses |
| Design grid | Quarter/half 7 cases, then distinct 49-case parameters, apply constraints | Candidate table, separate objectives, nondominance and no-feasible outcome |

Regenerate: `python3 scripts/chat9_evidence.py --out docs/chat10_evidence`. This runner retains historical **Chat 9 schema identifiers** because physics is unchanged; the Chat 10 report records it as regenerated evidence, not new model calibration.

## Explicit exclusions

No tire slip or ABS/ESC, full 3D multibody kinematics, true tire contact, nonlinear stops, real-vehicle test data, physical model correlation, ISO ride-comfort compliance, road-safety guidance, measured motor efficiencies, production BMS, battery SOC/temperature or uncertainty quantification. Graphics are exaggerated schematic projections, **not measured or validated CAD geometry**. No claim of a globally optimal suspension, energy consumption/range prediction or deployment is supported.
