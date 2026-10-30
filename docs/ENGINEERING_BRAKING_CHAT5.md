# Chat 5 — Braking engineering model and validation limits

## Coordinate system, scope and units

- Independent **1-D straight, level, symmetric vehicle**; no yaw, lateral load or coupling into the pre-existing quarter-/half-car equations.
- `v` = forward velocity in m/s; positive braking *deceleration magnitude* `d` in m/s²; positive brake force in N. Distance `x` increases in the forward direction.
- `m` vehicle mass (kg), `h` center-of-gravity height above ground (m), `a` center-of-gravity distance to front axle (m), `b` center-of-gravity distance to rear axle (m), `L=a+b` wheelbase (m).
- `g=9.80665 m/s²`; road friction parameter `μ` is a **user-specified illustrative aggregate coefficient**, not measured or inferred from real tires.
- Rigid-body, quasi-static load transfer; no braking pitch transients, wheel inertias, tire slip, axle-specific friction allocation, brake bias, tire load sensitivity, ABS, EBD, ESC, hydraulic system, aerodynamics, rolling resistance or reaction time.

## Force model

Requested command `d_req(t)` is either `demanded_decel_m_s2` immediately from t=0 or a linear ramp from zero to its final value over `ramp_s`. The aggregate traction model is deliberately independent of axle-specific force allocation:

```
F_requested(t) = m * d_req(t)
F_available = μ * m * g
d_actual(t) = min(d_req(t), μ*g)
F_actual(t) = m * d_actual(t)
```

This only enforces **whole-vehicle aggregate** grip: it does not assert that each axle can deliver the requested force and does not model wheel lock/ABS. It must not be used to set safe real-world brake distances.

Axle normal forces during braking use:

```
N_front = m*g*b/L + m*d_actual*h/L
N_rear  = m*g*a/L - m*d_actual*h/L
N_front + N_rear = m*g
```

The initial static loads follow `m*g*b/L` at the front and `m*g*a/L` at the rear. Positive deceleration increases front normal load and reduces rear normal load. Inputs that would produce negative rear normal load under the maximum requested/realizable deceleration are rejected rather than claiming physical contact loss. These values are normal-load approximations, not predicted front/rear braking forces.

## Continuous braking integration and stop event

For each step, split at the ramp endpoint and aggregate friction-saturation time so deceleration over each subinterval is exactly linear: `d(τ)=d0+kτ`, where `k≥0`. Use the analytical antiderivatives:

```
v(τ) = v0 - d0*τ - 0.5*k*τ²
Δx(τ) = v0*τ - 0.5*d0*τ² - k*τ³/6
```

If the subinterval would reach zero speed, solve `v(τ)=0` for its earliest nonnegative root, truncate the interval exactly there, record zero speed, and halt. This avoids numerical overshoot of the stopping event and makes stopping time/distance independent of output time step (up to floating-point precision) for these piecewise-linear command profiles. At the final stopping sample, demand and acceleration are reported as zero (brakes released at rest); **peak** loads and peak acceleration are calculated from the moving trajectory immediately before stopping.

If the simulation duration ends before stopping (or requested braking is zero), return `stopped=false`, null stopping time/distance, the window's *travelled* distance, and the remaining speed. Never relabel window distance as stopping distance.

For constant deceleration `d>0`: `t_stop=v0/d`, `x_stop=v0²/(2d)`. For linear ramp that completes before stop: `v(r)=v0-d*r/2`, `x(r)=v0*r-d*r²/6`, followed by constant-deceleration motion. The external SciPy reference check numerically integrates requested/capped deceleration and finds the stopping event independently using quadrature and Brent root finding.

## Default illustrative scenario

`m=1200 kg, h=0.55 m, a=1.2 m, b=1.3 m, v0=20 m/s, μ=0.8, d_req=5 m/s², constant command`:

- stopping time `4.0 s`, distance `40.0 m`, deceleration `5 m/s²`.
- total normal load `11767.98 N`, static front `6119.3496 N`, static rear `5648.6304 N`.
- braking front `7439.3496 N`, braking rear `4328.6304 N`.

No measured tire friction, mass distribution, brake hardware, aerodynamic force, gradient, temperature or driver reaction time is incorporated. **Not suitable for estimating safe road stopping distance.**

## Output schema

`model=independent-longitudinal-braking`, `version=0.5.0`, `scenario`, `metrics`, `channels`, `provenance`, `assumptions`, and `warnings`. Each time channel is a unit-explicit snake-case field; `provenance.units` lists the physical units. CSV repeats scenario parameters and version on each row, while JSON carries full solver/units/warning metadata. Legacy simulation `/api/health` keeps its `version: 0.4.0` field for backward compatibility and adds `application_version: 0.5.0`. No existing v0.4 route or physics was replaced.
