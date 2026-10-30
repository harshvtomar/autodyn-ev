# AutoDyn EV · Chat 8 engineering optimization scope and mathematics

## Purpose and safety boundary

Chat 8 is a **bounded design-exploration study**, not a globally optimal or experimentally verified suspension design. It runs the accepted 2-DOF quarter-car or independent 4-DOF half-car physics with alternate spring and/or damper settings. All cases are simulated with the exact same road, speed, event times, duration, fixed-step RK4 settings, masses, tire parameters and zero initial state. The study has **no coupling** to the standalone friction braking or regenerative energy model and makes no ABS, tire-grip, SOC/thermal, BMS, battery range or real-road stopping claims.

## Input scope

- Quarter-car: `suspension_stiffness_n_m` and `damping_n_s_m`.
- Half-car: `front_spring_n_m`, `rear_spring_n_m`, `front_damping_n_s_m`, `rear_damping_n_s_m`.
- One or two **distinct** parameter names per study; a Cartesian 7-point grid per parameter, maximum 49 candidate simulations.
- Candidate values span 80%–120% of selected baseline, clipped to the unchanged model validation limits. Zero-valued baseline damping cannot generate seven distinct values and is rejected explicitly.
- A hard guard rejects duration/time-step combinations exceeding 3,000 integration steps per candidate. Model and road resolution guards from the accepted solver still apply.
- Unknown fields, invalid types, non-finite values, over-large study grids and unsupported models/parameters are rejected with clear 400 responses.

## Objective calculations and units

The first objective is body acceleration **unweighted time-domain RMS** in m/s², using trapezoidal integration of squared acceleration over the full simulated duration, then square root of the integral divided by duration. It is *not* ISO 2631 frequency-weighted ride-comfort assessment. The second objective is sampled suspension travel peak-to-peak (mm). Quarter-car uses the single body-minus-wheel travel channel. Half-car uses the **larger** of front and rear individual peak-to-peak travels, each computed over its complete waveform (do not combine asynchronous front/rear points). Tire-deflection maximum absolute magnitude (mm) is a **proxy for linear tire force variation**, not proof of real tire contact loss, dynamic friction, or grip. Half-car uses the larger of the separate front/rear absolute tire proxies. Front/rear individual metrics and peak pitch (degrees) are retained in each half-car result.

## Feasibility, Pareto and selection

Optional upper bounds may independently restrict body acceleration RMS, maximum axle travel peak-to-peak, and worst tire-deflection proxy. A case is feasible only if all supplied constraints pass, inclusive of the threshold. Candidate IDs and ordering are deterministic in lexicographic grid order. A feasible case is Pareto/non-dominated when no other feasible case is no worse on **both** RMS and suspension-travel objectives and strictly better on at least one. No synthetic weighted score is computed.

For reproducible **illustrative** default selection, among the feasible set choose the smallest RMS, then the smallest peak-to-peak travel, then the smallest tire proxy, then the smallest candidate ID. If zero feasible candidates survive, `selected_id` is `null` and `pareto_ids` is empty. Neither selection nor Pareto membership constitutes an engineering recommendation or proven optimum.

## API and exports

Additive `POST /api/optimization/study` JSON body with `model` (`quarter` or `half`), `vehicle`, `road`, `settings`, `parameters` (one or two), `points_per_axis` (exactly 7) and optional `constraints`. The original endpoints, input/output payloads and physics source files are unchanged. The response includes complete baseline vehicle metrics, selected parameter values and validated bounds/units, scenario road/settings, constraints, candidate IDs/metrics/feasibility/rejection reasons, Pareto IDs, selection rule and explicit limitations. `schema_version=optimization-study-1.0`, `application_version=0.8.0`.

Downloads from the local UI: CSV with full numeric metrics plus repeated version, model, road, timing, baseline-vehicle and constraint provenance columns; JSON with the complete returned response; and a readable plain-text engineering report. All exports are local client-side files; no cloud services or credentials.

## Limitations

Linear small-displacement springs, viscous damping, always-contact tire model, static-equilibrium-relative displacements, fixed prescribed suspension road speed, no real suspension geometry, motion ratio, bump stop, nonlinear stiffness, temperature variation, sensor calibration, vehicle test rig, road-test validation, ABS, braking-suspension coupling or production BMS. Experimental validation would require independently measured rig/vehicle response and sensitivity analysis.

## Version compatibility

The inherited tests assert the v0.7 package compatibility marker and archived Chat 7 HTML text. Chat 8 preserves those as historical test fixtures (non-visible HTML comment and `__version__` compatibility constant); the active header/footer, HTTP server startup and `current_release_version` health field report **v0.8.0**. This preserves the inherited test contract without pretending that the earlier test fixture represents current release metadata.
