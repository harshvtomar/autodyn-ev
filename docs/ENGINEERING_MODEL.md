# AutoDyn EV — Session 1 Engineering Model Contract

**Status:** Implemented linear, two-degree-of-freedom vertical quarter-car model. Reference frame and limitations are deliberate, not implied.

## 1. Physical assumptions

- **Sprung mass** `m_s` represents one quarter of a vehicle's effective sprung body mass, not necessarily the mass of a full EV.
- **Unsprung mass** `m_u` represents wheel/axle-associated mass at that corner.
- Masses translate only vertically (up positive); suspension is linear stiffness `k_s` with linear viscous damping `c_s`; tire is linear stiffness `k_t`, with **no tire damping**.
- The static tire/suspension deflections from gravity are subtracted. `z_s = z_u = z_r = 0` is rest equilibrium; response plots show deviations relative to this point.
- Tire-to-road connection persists at all times. Therefore neither tire lift-off nor impact/contact force transients are modeled. The `tire_force_variation_n` channel is the **linear dynamic force variation** `k_t*(z_u-z_r)`, not total wheel normal force nor a contact guarantee.
- No pitch, roll, nonlinear damping, hydraulic parameters, bump stops, travel hard limits, braking, traction, motor, battery or road-test calibration is included.
- All sliders apply bounded, plausible-for-demonstration ranges, not validated design envelopes.

## 2. Governing equations

From spring and viscous damper forces opposing body-minus-wheel displacement and velocity:

```text
F_s = k_s (z_s − z_u) + c_s (v_s − v_u)
F_t = k_t (z_u − z_r)

m_s * a_s = −F_s
m_u * a_u = +F_s − F_t
```

The first-order ODE state is `y=[z_s,z_u,v_s,v_u]`; derivative `y'=[v_s,v_u,a_s,a_u]`. Zero road input and zero initial state produce zero response.

The undamped natural frequencies are the square roots of eigenvalues of `M^-1 K`, divided by `2π`, where:

```text
M = [[m_s, 0], [0, m_u]]
K = [[k_s, -k_s], [-k_s, k_s+k_t]]
```

The two modal frequencies intentionally **ignore damping** and are not measured resonance frequencies from a full vehicle.

## 3. Input definitions

- `flat`: `z_r(t) = 0`.
- `step`: `z_r(t) = h` for `t>=t0`, otherwise zero; instantaneous jump is mathematical and not a realistic finite-slope road feature.
- `sine`: `z_r(t) = h sin(2πf(t−t0))` for `t>=t0`, otherwise zero. `h` is a **signed peak amplitude**; the sine wave rises and falls about static zero, unlike the positive-only bump.
- `bump`: `z_r(t) = h[1−cos(2π(t−t0)/T)]/2`, for `t0 <= t < t0+T` and zero elsewhere, with `T=L/v`. Bump peak is `h`, initial and final height are zero, and endpoints have zero slope. Vehicle speed influences only the encounter duration, not longitudinal vehicle dynamics.

All displayed inputs are SI internally. UI road amplitude is mm and speed is km/h for readability; conversion is explicit. `start_s=0.5` is fixed in the Session 1 UI; Python accepts changing it programmatically. Bounds are in `physics.py`.

## 4. Numerical solution and controls

Classical fixed-step RK4:

```text
k1 = f(t, y)
k2 = f(t + h/2, y + h*k1/2)
k3 = f(t + h/2, y + h*k2/2)
k4 = f(t + h, y + h*k3)
y_next = y + h*(k1 + 2*k2 + 2*k3 + k4)/6
```

Max 15,000 steps; time range 1–15 seconds, step 0.001–0.020 s. A nonzero bump requires >=12 numerical steps across the road encounter; a nonzero sine requires >=20 steps per cycle. Violation is rejected with an explanation rather than returning visually convincing but underresolved traces. Step events are discontinuous and should be checked by time-step refinement; high-order global accuracy is not guaranteed at events.

## 5. Result channels and metrics

Every saved time row includes `time_s`, `road_m`, `sprung_m`, `unsprung_m`, both velocities, both accelerations, `suspension_travel_m` (body minus wheel), `tire_deflection_m` (wheel minus road), `suspension_force_n` and `tire_force_variation_n`.

Metrics:

- **Body acceleration RMS:** square root of the mean squared sampled body acceleration over the selected scenario duration; includes pre- and post-disturbance time.
- **Peak body acceleration:** maximum absolute value of sampled `a_s`.
- **Peak suspension travel:** maximum absolute value of `z_s − z_u` in mm.
- **Peak body displacement:** maximum absolute `z_s` in mm.
- **Peak tire deflection:** maximum absolute `z_u − z_r` in mm.
- **Peak tire-force variation:** maximum absolute `k_t(z_u−z_r)` in N.
- **Undamped modes:** eigenfrequencies of `M^-1K`, body-like lower mode and wheel-hop higher mode.
- **Post-bump settling time:** earliest time after bump ends when all later *sampled* points simultaneously satisfy `|z_s| <= 2 mm`, `|v_s| <= 0.01 m/s`, `|z_s−z_u| <= 2 mm`. If no such sampled time exists, the metric is `null`. This is a scenario-specific heuristic, not a regulated criterion.

## 6. Validation approach

Internal tests assert equilibrium, force signs, correct tire force to unsprung mass, dissipative energy derivative `dE/dt = −c_s(v_s−v_u)^2` for flat ground, undamped energy behavior, eigenfrequency invariants, RK4 time-step refinement and damped long-time step response. A separate SciPy DOP853 cross-check uses smooth sinusoidal input to avoid discontinuities. **Numerical agreement confirms only computational implementation against the chosen model—not physical fidelity.**

## 7. Non-goals

This model is **not** a 3D multibody vehicle dynamics solver, FEA package, crash/safety model, tire contact model, ISO 2631 comfort certification, or physical EV control system. Do not interpret the animation as geometrically scaled physical travel; its displacement scale is deliberately exaggerated for visibility. The model's physical scope is the two vertical suspension coordinates.
