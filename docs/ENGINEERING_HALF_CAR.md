# AutoDyn EV v0.3.0 — Independent 4-DOF half-car engineering model

## Purpose and physical scope

This is a *linear, small-angle, vertical half-car model* with four generalized displacements: sprung-body heave `z_b`, body pitch `θ`, front unsprung mass displacement `z_uf`, rear unsprung mass displacement `z_ur`. Each has a velocity; eight first-order state variables. There is no rigid 3D body model, roll, yaw, longitudinal dynamics, braking, regen, tire contact loss, tire damping or physical EV validation. All masses are lumped, stiffnesses linear, damping viscous, and pitch inertia specified independently.

**Coordinate convention:** vehicle x increases toward the FRONT, z increases UP. **Positive `θ` is nose-up**. The body CG is at x=0; front axle at `+a`, rear at `−b`, with `a,b>0`. Small-angle body vertical attachment motions: `z_bf = z_b + aθ`, `z_br = z_b − bθ`. No sine/tangent geometric nonlinearity is retained; the default computed peak pitch is a simulated response, not a guarantee of small angles under all user parameters. **All displacements are *deviations from static equilibrium***: the zero state is the vehicle at its already-loaded ride position. The true static spring and tire preloads counter gravity; these constants cancel when equations are expressed in deviations.

## Suspension and tire forces

Define front and rear relative suspension displacements `δ_f = z_b+aθ−z_uf`, `δ_r = z_b−bθ−z_ur`; relative velocities `δ̇_f = ż_b+aθ̇−ż_uf` and `δ̇_r = ż_b−bθ̇−ż_ur`.

Chassis-side **upward** signed suspension forces (positive up) are:

```text
F_f = −k_sf δ_f − c_sf δ̇_f
F_r = −k_sr δ_r − c_sr δ̇_r
```

Their exact equal-and-opposite forces act on each unsprung mass. Tire variations are `−k_tf(z_uf−r_f)`, `−k_tr(z_ur−r_r)`; **not unilateral contact forces**, so tire detachment is not simulated.

**Equations of motion:**

```text
m_b  z̈_b   = F_f + F_r
I_y  θ̈     = a F_f − b F_r
m_uf z̈_uf = −F_f − k_tf(z_uf−r_f)
m_ur z̈_ur = −F_r − k_tr(z_ur−r_r)
```

Given `θ>0`, front attachment rises and front spring pulls it down: a restoring **negative** torque. With `a=b`, equal stiffness/damping and mirrored symmetric states/forces, the pitch torque cancels.

**State order and units** in `autodyn_ev/halfcar.py`:

```text
(z_b [m], θ [rad], z_uf [m], z_ur [m],
 ż_b [m/s], θ̇ [rad/s], ż_uf [m/s], ż_ur [m/s])
```

The state equations are integrated with classical fixed-step RK4, sampling both front and rear road inputs at RK4 substeps. All output channel names carry units; pitch plots may show degrees for readability while the API stores radians.

## Road excitation and physical delay

`r_f(t) = Road.displacement(t)`; `r_r(t) = Road.displacement(t−τ)`, where `τ=(a+b)/v`, `v>0 m/s`. Rear input remains zero until the feature arrives. Positive finite speed is required **even for flat road**, keeping the interface well-defined; stationary surface excitation needs a *different* physical input model and is not silently substituted. For an ideal step road, the rear onset is delayed by `τ`; for a bump, both axles follow the same smooth finite spatial feature shifted in time; for a sine road the shift also applies to oscillatory excitation. This assumes steady forward motion at constant `v`, aligned front/rear tire tracks and no vehicle acceleration.

The inherited road generator accepts `flat`, `bump`, `sine`, and `step`; road height (0–0.15 m), speed (1–40 m/s), time start (0–5 s) and other inherited limits are strictly validated. For nonzero bumps at least 12 integration samples per traversal are required; for nonzero sine inputs at least 20 per cycle. A further `dt × max(sqrt((ks+kt)/mu)) ≤ 0.8` rule rejects under-resolved wheel-hop frequencies; this is a conservative heuristic, not proof of unconditional numerical stability. Requested duration is between 1 and 15 s and samples are capped.

## Matrix formulation (independent verification)

Let `q=[z_b,θ,z_uf,z_ur]ᵀ` and `S` with rows `(1,a,−1,0)`, `(1,−b,0,−1)`, `(0,0,1,0)`, `(0,0,0,1)`. Let `M=diag(m_b,I_y,m_uf,m_ur)`, `K=Sᵀ diag(k_sf,k_sr,k_tf,k_tr) S`, `C=Sᵀ diag(c_sf,c_sr,0,0) S`. With zero road input,

```text
M q̈ + C q̇ + K q = 0
```

For road excitation only wheel/tire rows receive `k_tf r_f`, `k_tr r_r`, so `M q̈ + C q̇ + K q = [0,0,k_tf r_f,k_tr r_r]ᵀ`.

Unforced/flat-road mechanical energy:

```text
E = ½ q̇ᵀ M q̇ + ½ qᵀ K q
  = ½ m_b ż_b² + ½ I_y θ̇² + ½ m_uf ż_uf² + ½ m_ur ż_ur²
    + ½ k_sf δ_f² + ½ k_sr δ_r² + ½ k_tf z_uf² + ½ k_tr z_ur²
```

For flat road `dE/dt = − c_sf δ̇_f² − c_sr δ̇_r² ≤ 0`. This does **not** hold while the road is forcing motion. The RK4 numerical energy change approximates this dissipative behavior but is not exactly energy-conserving by design.

## Tests and independent checks

- Front/rear chassis force signs and pitch lever arms, symmetric pitch cancellation; front/rear road step onset/delay; strict validation of masses, inertia, wheels, road and integration; finite states; flat-road zero response; nondissipative/viscous energy; `dt` refinement; unaffected quarter-car contracts and endpoints.
- Tests include a **separately assembled** generalised-coordinate M,C,K matrix, and optional NumPy **150 seeded randomized parameter** cases with maximum acceleration discrepancy documented in `docs/chat3_reference_results.json`.
- Optional SciPy DOP853 independently integrates the same ODE with tight tolerances and a finer `max_step`, comparing eight state histories under a smooth sine road. The comparison confirms numerical integration for that specific model/input, not empirical physical accuracy.

## Known limitations

No bump stop/nonlinear suspension, tire compliance nonlinearity/contact separation, wheel hop contact physics, road spatial sampling uncertainty, shock absorber hysteresis, tire damping, 3D CAD, full vehicle lateral dynamics, in-car measured ride comfort or production safety certification. Reproduce external road-test/bench data before drawing conclusions about an actual vehicle. Some 4-DOF nonlinear validation regimes and larger sensitivity experiments belong to future stages; they have **not** been implemented here.

A separately reported `domain_diagnostics.small_angle_caution` becomes true when the computed peak pitch exceeds **0.15 radians**. This is a transparency warning rather than a mathematical proof of accuracy below the threshold. The numerical solver does not replace the small-angle model with nonlinear geometry.
