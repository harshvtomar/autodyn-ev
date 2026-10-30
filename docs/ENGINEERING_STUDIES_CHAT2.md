# AutoDyn EV — Chat 2 Engineering Studies and Numerical Interpretation

**v0.2.0; two-degree-of-freedom, linear vertical quarter-car; software-only educational simulation.** This document supplements the preserved `ENGINEERING_MODEL.md`. It does not modify the governing equations or redefine the legacy metrics.

## 1. Unchanged physical model

Positive vertical displacement is **up** and `z_s, z_u` are measured relative to **static equilibrium**, so gravity is not explicitly integrated. `z_r(t)` is road displacement, positive upwards.

```text
m_s z̈_s = −k_s(z_s − z_u) − c_s(ż_s − ż_u)
m_u z̈_u = +k_s(z_s − z_u) + c_s(ż_s − ż_u) − k_t(z_u − z_r)
M = diag(m_s,m_u)
C = [[c_s,-c_s],[-c_s,c_s]]
K = [[k_s,-k_s],[-k_s,k_s+k_t]]
```

These equations assume a linear tire continuously connected to the road; **normal tire load, road contact loss, physical damper saturation and roadworthiness cannot be inferred**. The vehicle speed input alters the *bump duration only*. No longitudinal vehicle motion, braking, regenerative energy, steering, pitch or roll is solved.

## 2. Damped modal analysis: exact linear characteristic equation

Unlike an SDOF approximation such as `c/(2√(k m))`, modal damping here is obtained from the **full coupled state-space poles** of `det(λ²M + λC + K)=0`:

```text
m_s m_u λ⁴ + c_s(m_s+m_u) λ³
+ [m_s(k_s+k_t)+m_u k_s] λ² + c_s k_t λ + k_s k_t = 0.
```

All four roots are found by an independent standard-library scaled quartic iterative solver and checked against polynomial residuals. For each root pair `λ = α ± iβ` with `β > 0`, the output contains:

- oscillation frequency `f_d = β/(2π)` **Hz**;
- complex-pole magnitude `f_n,modal = |λ|/(2π)` **Hz** (not an undamped coupled eigenfrequency);
- decay rate `−α` in **s⁻¹**;
- damping ratio `ζ = −α/|λ|` **dimensionless**.

The old `body_mode_undamped_hz` and `wheel_mode_undamped_hz` are **left unchanged**. With non-proportional damping, damped pole modes should not be automatically given physical body/wheel labels or assumed to match undamped eigenvectors. If there are real poles, they are reported only as real decay rates — **not fabricated oscillatory frequencies**. At nearly repeated poles, a numerical conditioning warning/error may be needed instead of overclaiming accuracy. All calculations are for this idealized linear system.

Default 300/40 kg, 18,000 N/m, 1,500 N·s/m and 190,000 N/m modal example:

| Oscillatory pair (ascending f) | Damped frequency | ζ (modal) |
|---|---:|---:|
| Lower-frequency pole pair | 1.14727 Hz | 0.28482 |
| Higher-frequency pole pair | 10.88161 Hz | 0.26916 |

The undamped frequencies, which remain the original UI metric definition, are **1.177665 Hz** and **11.482616 Hz**.

## 3. Baseline versus variant comparison

`POST /api/compare` accepts two complete Chat 1 scenario objects: `baseline` and `variant`. It enforces **the same duration and step settings**, and computes both via the original `simulate()` function. It returns complete native results for both, additive deltas for six named metrics, and unmodified state-channel arrays suitable for overlay.

- Positive percentage changes mean the variant metric is higher; this is **not intrinsically better**.
- When the baseline metric is zero, percentage is returned as `null` (not infinity).
- When road inputs differ, a clear note warns that response differences cannot be attributed solely to vehicle parameters.
- Equal road inputs and matched time grids are needed before attributing *within-model* response changes to suspension settings.

Example: increasing the baseline damper from 1,500 to 2,300 N·s/m for the default bump raises *this scenario's* RMS body acceleration from **0.906082** to **1.083868 m/s²**. This **does not** establish that the baseline is universally superior; tire/suspension travel, comfort standards, road spectrum and constraints also matter.

## 4. One-at-a-time parameter sweep

`POST /api/sweep` accepts one vehicle field plus two bounded endpoints and an integer count from **3 to 11**, and preserves all other vehicle/road/solver fields. Accepted design variables: both masses, suspension stiffness, damping, and tire stiffness. Controls and server both enforce the same Chat 1 physical parameter sandbox ranges; the server applies a maximum **75,000 total RK4 integration steps** to limit compute. The UI uses seven sample points around the chosen value (nominal ±20%, clipped to the validated domain).

Results include six response metrics, sampled points, the original reference metrics, units, reproducible inputs and a warning that the *minimum sampled RMS* is **not a global optimum**, and that ride comfort cannot be reduced to a single scalar.

## 5. Step-size sensitivity (not a proof of stability)

`POST /api/convergence` performs 3–5 fixed-step RK4 simulations with distinct, descending requested `dt_s` in the existing 0.001–0.020 s bounds. The endpoint enforces a **35,000-total-step budget** and outputs maximum absolute differences, per state channel and in the correct SI unit, comparing each coarse trajectory against the finest **tested** run. Values at nonmatching times are obtained by **linear interpolation on the finest time grid**, which can dominate the reported error even if the RK4 integrator has smaller truncation error.

The UI uses **aligned 0.010 / 0.005 / 0.0025 s grids** to avoid the worst interpolation artifact. The calculated step may be slightly adjusted internally because the existing integrator uses `round(duration/dt)` equally spaced intervals; therefore `requested_dt_s` and `actual_dt_s` are reported separately.

- For the default bump, max displacement difference between `dt = 0.010 s` and finest tested `0.0025 s` is **~8.42×10⁻⁷ m**. For `dt=0.005 s` it is **~4.85×10⁻⁸ m**.
- The finest tested run is treated as a numerical **comparison reference**, **not** as an exact analytical ground truth.
- A road **step** contains a displacement discontinuity; a bump is piecewise smooth but has profile boundaries, and all finite-onset waveforms may affect observed order. A refinement study is useful evidence but cannot prove numerical stability, safety or empirical accuracy.

## 6. Reproducibility and backward compatibility

The original `POST /api/simulate`, `GET /api/health`, `GET /api/defaults`, existing `schema_version = "1.0"`, 12 channel columns, metric names, legacy browser CSV header and simulation export names remain in place. Chat 2 adds a **top-level `provenance` dictionary** containing model revision, solver, units, road, vehicle, exact requested settings, reference frame and simulated-data status.

The **legacy 12-column CSV is unchanged** to protect existing imports; use the separate **Simulation provenance** JSON export as its required **sidecar** when preparing engineering evidence. New study CSVs add relevant model/solver columns; the corresponding study JSON records full scenario and units metadata. **CSV + sidecar** is a two-file report; keep the files together. These data are simulated, not measured.

## 7. Endpoints summary

| Endpoint | Input | Output | Limits |
|---|---|---|---|
| `/api/simulate` | Chat 1 vehicle/road/settings | Unchanged core + additive provenance | Original 15k steps |
| `/api/modal` | `{"vehicle":{...}}` | Full complex poles and modal ratios | Input ranges |
| `/api/compare` | `{"baseline":scenario,"variant":scenario}` | Two full responses and metric deltas | Same time grid; 7.5k steps/run |
| `/api/sweep` | `{"scenario":scenario,"parameter":"damping_n_s_m","start":900,"stop":2400,"count":7}` | Metrics at each design point | 3–11 points; 75k steps total |
| `/api/convergence` | `{"scenario":scenario,"steps_s":[0.01,0.005,0.0025]}` | Channel differences vs finest | 3–5 steps; 35k steps total |

All endpoints reject unknown top-level keys and invalid physical quantities, do not require external APIs, and bind the server only to `127.0.0.1`. The browser and API are not a tool for safety-critical vehicle design or professional certification.
