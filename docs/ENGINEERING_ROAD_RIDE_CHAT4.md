# AutoDyn EV v0.4.0 — Road excitation and ride-response engineering contract

## Models retained

The accepted **2-DOF quarter-car** and **4-DOF half-car** equations, static-equilibrium-relative upward-positive coordinate convention, RK4 solver and rear axle delay are inherited unchanged. Only their *road source* and shared under-resolution validation were extended. The half-car has small-angle **nose-up-positive pitch**; wheels are always attached to linear tires. This is not a nonlinear tire-road/contact model and is **not experimentally calibrated**.

## Road definitions and exact units

All heights `height_m` are bounded **magnitudes** in meters, from 0 to 0.15; start time `start_s` is seconds. Length `bump_length_m` and the inter-feature gap `bump_spacing_m` are **spatial distances in meters**. Speed `speed_m_s` is fixed throughout the simulation, between 1 and 40 m/s. Define elapsed time after onset `τ = t − start_s`, pulse duration `D = bump_length_m / speed_m_s`, and half-cosine pulse:

`P(τ) = (height_m/2) * (1 − cos(2π τ / D))` for `0 ≤ τ < D`; `P=0` otherwise.

| Road kind | Road elevation signal `r(t)` | Excitation class |
|---|---|---|
| `flat` | `0` | Identically zero |
| `bump` | `+P(τ)` | Finite smooth positive bump (legacy) |
| `pothole` | `−P(τ)` | Finite smooth negative depression (new) |
| `double_bump` | `P(τ) + P(τ − D − bump_spacing_m/speed_m_s)` | Two identical, spatially separated smooth bumps (new) |
| `step` | `height_m` for `τ ≥ 0`, else `0` | Permanent vertical step (legacy, discontinuous) |
| `sine` | `height_m sin(2π sine_frequency_hz τ)` for `τ ≥ 0`, else `0` | Sustained sinusoid (legacy) |
| `chirp` | `height_m sin(2π φ(τ))`, described below | Sustained frequency sweep (new) |

For `chirp`, let `q = min(τ, chirp_duration_s)` after the start time, then `φ(τ) = f0*q + (f1−f0)*q²/(2*chirp_duration_s) + f1*(τ−q)` cycles, where `f0 = sine_frequency_hz`, `f1 = chirp_end_frequency_hz`. This yields a continuous phase with frequency linearly increasing/decreasing from f0 to f1 over `chirp_duration_s`, then holding f1. Both frequencies are between 0.2 and 5 Hz; ramp duration is 0.5–12 s. **All profiles are synthetic engineering stimuli, not measured road roughness.**

Sine and chirp are specified in **time-frequency** units at a constant reference speed. For a spatially repeating interpretation, a local equivalent wavelength is `speed_m_s/frequency_hz`. This is only valid at the stated constant speed. Quarter-car front road is `r(t)`; half-car uses front `r(t)` and rear `r(t−(cg_to_front_m+cg_to_rear_m)/speed_m_s)`. Delay is based on **distance/constant speed**, not a separately generated random phase.

Validation: legacy static bounds remain in place. A nonzero finite raised-cosine feature (including pothole and each double bump) must have at least 12 numerical integration steps across D. Sine/chirp must have at least 20 steps per cycle at their highest considered frequency. Simulations are bounded to at most 15,000 steps, and the accepted half-car wheel-hop resolution check remains active. A zero-amplitude input bypasses forcing-resolution guards because it is exactly flat.

## Ride analysis and units

The additive endpoint `POST /api/ride/study` accepts:

```json
{"model":"half","scenario":{"vehicle":{},"road":{"kind":"double_bump"},"settings":{}},"baseline":{"vehicle":{},"road":{"kind":"double_bump"},"settings":{}}}
```

`model` is exactly `quarter` or `half` and applies to *both* scenarios. `baseline` is optional. The `baseline` and `scenario` must have exactly the same road definition, duration and integration settings; only **vehicle parameters** may change. The endpoint returns `schema_version=ride-study-1.0`, `release=0.4.0`, selected and baseline study outputs, like-for-like numerical deltas, units, simulation warnings, full parameter provenance and plotting waveforms.

The time-weighted, **unweighted** RMS for a sampled signal x is the trapezoid approximation of `sqrt((1/(b−a)) * ∫[a,b] x(t)² dt)`. For subwindows not exactly on the sample grid, the two boundaries are **linearly interpolated**. This is not the same as an unweighted sample mean when a window has uneven boundaries; it is not a physically measured RMS. Peak absolute magnitude is `max |x|` over the window samples and boundaries. Peak-to-peak is `max(x)−min(x)` (signed extrema). Reported acceleration, suspension travel, tire-deflection proxy and half-car pitch preserve native SI units: `m/s²`, `m`, `m`, and `rad` respectively. The new browser renders displacement/travel in **millimeters** but labels those axes; it never plots acceleration and pitch together on one new study graph.

Windows:

* `full`: [0, duration] seconds, always available.
* `post_event`: from the **last completed finite road feature** to the simulation end, if nonzero and completed before the end. For half-car, the endpoint includes the rear-axle delay. Sine, step and chirp are sustained, so no post-event window or settling claim is supplied.

Settling time is the **first sample after the last disturbance** such that the required displacements, velocities, and suspension travels (and half-car pitch / pitch-rate) remain inside stated absolute thresholds for every **subsequent sampled time**. Thresholds: 2 mm displacement/travel, 0.01 m/s velocity, half-car pitch 0.002 rad, pitch rate 0.01 rad/s. This is a finite-horizon, sample-based numerical diagnostic; it is **not proof of asymptotic stability**, certification, or real vehicle performance. If thresholds are not met by the simulation end, settling is `null`. A zero-height road contains no nonzero disturbance, so settling is not defined.

Tire deflection is relative motion of the always-engaged *linear tire* and is only a **tire-force variation proxy**. It must not be used to infer tire lift-off, wheel load reversal, or braking traction. The inherited half-car 0.15-radian peak pitch warning is surfaced when the linear small-angle range is exceeded; this threshold is only a diagnostic, not a proof of validity. No ISO 2631 frequency weighting or comfort classification is applied and no industry comfort threshold is claimed.

## Reproducibility and limits

All numeric simulation inputs and deterministic results can be downloaded as `Ride JSON`; the `Ride CSV` includes the release, model, case, road parameters, vehicle parameters, actual time step and the plotted signal columns with SI units. No time-varying speed, braking, regeneration, tire separation, lateral/yaw/roll dynamics, user-uploaded roads or probabilistic roads have been introduced. Optional SciPy verification code is *development only*.
