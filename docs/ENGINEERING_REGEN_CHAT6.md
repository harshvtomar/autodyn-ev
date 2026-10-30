# AutoDyn EV v0.6.0 — Regenerative Braking Engineering Model

## Model boundary

This is a **separate** level-road, single-coordinate longitudinal regenerative braking mode extending the **unmodified** accepted Chat 5 `braking.py` trajectory. Its speed, distance, ramped/constant command, friction cap, stopping event and quasi-static axle loads are inherited unchanged. The quarter-car 2-DOF and half-car 4-DOF simulations remain independent and use their original prescribed constant-speed road excitation. No regenerative signal is coupled into either suspension ODE.

## Force and battery limits

For vehicle mass `m` [kg], speed `v >= 0` [m/s], total demanded deceleration `a_req` [m/s²], coefficient `mu` [–], `g=9.80665` [m/s²]:

- `F_requested = m*a_req`; `F_grip = mu*m*g` [N]; `F_total = min(F_requested, F_grip)` while vehicle moves.
- `F_regen_torque_cap = T_motor_max * ideal_gear_ratio / wheel_radius` [N]; shaft-side torque is translated to equivalent wheel force with an *ideal*, lossless ratio and radius.
- `F_regen_power_cap = P_mechanical_max / v` [N] while `v>0`.
- `F_regen_battery_cap = P_charge_max / (eta*v)` [N] for positive `eta` and `v`.
- `F_regen = min(F_total, these three caps)` when `v` is above the optional illustrative low-speed cutoff and `eta > 0`; else `F_regen=0`.
- `F_friction = F_total - F_regen`; both forces are nonnegative. Friction braking fills demand rejected by regen capability; total demanded force can still exceed the **aggregate** road grip cap.
- `P_motor_mechanical = F_regen*v` [W]; `P_battery_charge = eta*P_motor_mechanical` [W]; `P_conversion_loss=(1-eta)*P_motor_mechanical` [W]. No energy is generated at zero speed.

**Efficiency:** `0 <= eta <= 1` is an assumed wheel-to-battery conversion efficiency, combining mechanical and electrical losses in a single lumped parameter. The motor shaft torque/generator-limit relation assumes ideal gear conversion; actual gearbox losses are folded into eta, avoiding double counting. Battery charging power acceptance is an *input cap*, not a SOC/temperature/chemistry model. No production motor maps are used.

## Numerical integration and conservation

Chat 5's exact piecewise-linear deceleration antiderivative provides the velocity and stopping distance/time. Chat 6 uses each exact segment's continuous velocity polynomial for adaptive Simpson quadrature of `integral(F_regen*v dt)` [J]. The motor mechanical energy is integrated independently of the display sampling. Friction work is **also integrated separately** using `integral(F_friction*v dt)`; its uncorrected quadrature residual is exported. The reported friction-dissipated energy is closed against the exact change in kinetic energy to eliminate tiny numerical quadrature discrepancies, and the size of that correction remains visible as `uncorrected_work_quadrature_residual_j`.

`K_initial - K_final = E_battery_stored + E_conversion_loss + E_friction_dissipation`, with `E_battery=eta*E_motor`, `E_loss=(1-eta)*E_motor`. For incomplete stops use the actual final velocity rather than assuming all initial kinetic energy disappeared. The final sample at the exact stop event has zero speed and battery power. Time-sampled channels and cumulative energies include strictly nonnegative force, power and energy magnitudes.

### Default illustrative example

The independent scenario is `1200 kg, v0=20 m/s, requested constant deceleration=5 m/s², mu=0.8, motor max torque=140 N·m, ideal ratio=8, driven radius=0.32 m, motor wheel-side mechanical max=40 kW, battery charge cap=24 kW, efficiency=85%, low-speed cutoff=0`. This results in a 4.00 s stop at 40.00 m (the accepted Chat 5 longitudinal trajectory). Initial kinetic energy is 240.00 kJ. Stored battery energy is approximately 76.64 kJ, conversion loss 13.52 kJ, and friction dissipation 149.84 kJ. These numbers are model outputs, **not empirical EV performance or road safety advice**.

## Constraints, confidence and out of scope

- Single longitudinal coordinate on a flat surface; constant mu and no aero or rolling resistance, measured wheel/tire grip, axle-specific adhesion, ABS, slip, dynamic load sharing, pitch transient, wheel torque response or mechanical brake temperature.
- The battery is represented by constant charge-power acceptance only; no state of charge, real vehicle thermal limits, cell physics, inverter map or drivetrain calibration.
- Regenerative prioritization is a simplified energy allocation, *not* a hardware-certified safety brake-blending controller.
- The idealized braking distance excludes driver perception/reaction travel, weather, grade and variability in tire friction. Never use results to plan actual stopping or emergency braking.
- Numerical comparisons validate equations and code against an independent ODE reference. They cannot establish physically correct real-world recovery.

## JSON/CSV engineering evidence

New `POST /api/regen/simulate` accepts `{ "scenario": { ... } }` (all input fields listed in the front-end). Response includes `version:0.6.0`, full scenario, units dictionary, provenance, warnings, array channels, stopping metrics, energies, energy balance and independent quadrature residual. Browser CSV includes model/version/input columns on every sample row. Original `POST /api/braking/simulate` and other routes are unchanged. For compatibility `/api/health` retains the inherited `version:0.4.0` and `application_version:0.5.0` values and adds `release_version:0.6.0`.
