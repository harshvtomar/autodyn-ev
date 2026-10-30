"""Independent level-road, single-track longitudinal braking demonstrator.

Positive forward velocity; positive brake force and deceleration magnitudes.
Assumptions: rigid, no drag, no rolling resistance, aggregate friction mu*m*g,
quasi-static axle loads, no wheel-slip, ABS, actual tire contact or brake bias.

For L=a+b: Nf=m*g*b/L+m*d*h/L; Nr=m*g*a/L-m*d*h/L.
Within each integration subsegment d(t) is linear or constant; the integrator
uses its exact speed and distance antiderivatives and solves the stop event.
"""
from dataclasses import asdict, dataclass, fields
from math import isfinite, sqrt

GRAVITY = 9.80665


@dataclass(frozen=True)
class BrakingScenario:
    mass_kg: float = 1200.0
    cg_height_m: float = 0.55
    cg_to_front_m: float = 1.2
    cg_to_rear_m: float = 1.3
    initial_speed_m_s: float = 20.0
    friction_coefficient: float = 0.8
    demanded_decel_m_s2: float = 5.0
    profile: str = "constant"  # or 'ramp'
    ramp_s: float = 1.0
    duration_s: float = 12.0
    dt_s: float = 0.02

    def validate(self):
        bounds = {
            "mass_kg": (200, 5000), "cg_height_m": (0, 2),
            "cg_to_front_m": (0.4, 4), "cg_to_rear_m": (0.4, 4),
            "initial_speed_m_s": (0, 55), "friction_coefficient": (0.05, 1.5),
            "demanded_decel_m_s2": (0, 15), "ramp_s": (0.05, 10),
            "duration_s": (1, 40), "dt_s": (0.002, 0.1),
        }
        for name, (lo, hi) in bounds.items():
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value):
                raise ValueError(f"{name} must be a finite number")
            if not lo <= value <= hi:
                raise ValueError(f"{name} must be between {lo} and {hi}")
        if self.profile not in ("constant", "ramp"):
            raise ValueError("profile must be constant or ramp")
        if (self.cg_to_front_m + self.cg_to_rear_m) > 7:
            raise ValueError("wheelbase must be at most 7 m")
        # Evaluate for MAXIMUM possible braking over the run, not hypothetical
        # cap-only braking that is never commanded.
        max_decel = min(self.demanded_decel_m_s2, self.friction_coefficient * GRAVITY)
        if self.cg_to_front_m * GRAVITY < max_decel * self.cg_height_m - 1e-12:
            raise ValueError("rear axle normal load would become negative; quasi-static model invalid")
        if self.duration_s / self.dt_s > 10000:
            raise ValueError("simulation must contain at most 10,000 nominal steps")


def scenario_from_mapping(raw):
    if not isinstance(raw, dict):
        raise ValueError("braking scenario must be a JSON object")
    source = raw.get("scenario", raw)
    if not isinstance(source, dict):
        raise ValueError("scenario must be an object")
    valid = {f.name for f in fields(BrakingScenario)}
    extra = set(source) - valid
    if extra:
        raise ValueError("unknown braking field(s): " + ", ".join(sorted(extra)))
    result = BrakingScenario(**source)
    result.validate()
    return result


def demand_at(t, sc):
    if sc.profile == "ramp":
        return sc.demanded_decel_m_s2 * min(1.0, max(0.0, t / sc.ramp_s))
    return sc.demanded_decel_m_s2


def actual_at(t, sc):
    return min(demand_at(t, sc), sc.friction_coefficient * GRAVITY)


def axle_loads(decel, sc):
    length = sc.cg_to_front_m + sc.cg_to_rear_m
    front = sc.mass_kg * (GRAVITY * sc.cg_to_rear_m + decel * sc.cg_height_m) / length
    rear = sc.mass_kg * (GRAVITY * sc.cg_to_front_m - decel * sc.cg_height_m) / length
    return front, rear


def simulate_braking(sc=None):
    sc = sc or BrakingScenario()
    sc.validate()
    m, cap = sc.mass_kg, sc.friction_coefficient * GRAVITY
    stop = sc.initial_speed_m_s == 0
    t, v, x = 0.0, sc.initial_speed_m_s, 0.0
    keys = ("time_s", "speed_m_s", "distance_m", "demanded_decel_m_s2",
            "actual_decel_m_s2", "requested_force_n", "traction_limit_n",
            "actual_brake_force_n", "front_normal_n", "rear_normal_n")
    channels = {key: [] for key in keys}
    max_during_motion = 0.0
    traction_limited = False

    def record(time, speed, distance, active):
        request = demand_at(time, sc) if active else 0.0
        actual = min(request, cap)
        nf, nr = axle_loads(actual, sc)
        values = (time, speed, distance, request, actual, m*request,
                  m*cap, m*actual, nf, nr)
        for key, value in zip(keys, values):
            channels[key].append(float(value))

    record(t, v, x, not stop)
    while t < sc.duration_s - 1e-11 and not stop:
        end = min(sc.duration_s, t + sc.dt_s)
        # Break step at both slope changes: friction cap onset and end of ramp.
        boundaries = [end]
        if sc.profile == "ramp" and sc.demanded_decel_m_s2 > 0:
            saturation_t = cap * sc.ramp_s / sc.demanded_decel_m_s2
            for boundary in (saturation_t, sc.ramp_s):
                if t + 1e-11 < boundary < end - 1e-11:
                    boundaries.append(boundary)
        for boundary in sorted(boundaries):
            length = boundary - t
            d0, d1 = actual_at(t, sc), actual_at(boundary, sc)
            slope = (d1-d0)/length
            reduction = d0*length + 0.5*slope*length*length
            tau = length
            if reduction >= v and reduction > 0:
                # Stable solution to 0.5*k*tau² + d0*tau - v=0.
                tau = 2*v/(d0 + sqrt(d0*d0 + 2*slope*v)) if slope > 1e-14 else v/d0
                tau = min(length, max(0.0, tau))
                stop = True
            # Exact distance integral of v(t)=v0-d0*t-k*t²/2.
            x += v*tau - 0.5*d0*tau*tau - slope*tau*tau*tau/6
            v = 0.0 if stop else max(0.0, v - d0*tau - .5*slope*tau*tau)
            max_during_motion = max(max_during_motion, d0, d0+slope*tau)
            if demand_at(t + tau, sc) > cap + 1e-10:
                traction_limited = True
            t += tau
            if stop:
                break
        record(t, v, x, not stop)
    peak = max_during_motion
    static_front, static_rear = axle_loads(0, sc)
    peak_front, peak_rear = axle_loads(peak, sc)
    stop_time = t if stop else None
    stop_distance = x if stop else None
    warnings = ["Illustrative aggregate-friction model only: no wheel-specific grip, lockup, ABS, aero drag, rolling resistance, perception or reaction distance.",
                "Axle normal loads use quasi-static straight-line load transfer; no pitch transients or measured tire forces."]
    if traction_limited:
        warnings.append("Driver brake demand exceeded aggregate friction capacity and was capped.")
    if not stop:
        warnings.append("Vehicle did not reach zero speed during the configured simulation duration; distance shown is travel during the window, not stopping distance.")
    if sc.profile == "ramp":
        warnings.append("Brake demand begins at t=0 and ramps linearly; ramp is a simplified commanded-deceleration profile, not measured brake build-up.")
    return {
        "model": "independent-longitudinal-braking", "version": "0.5.0",
        "scenario": asdict(sc), "provenance": {
            "model_revision": "chat5-longitudinal-v1", "integration": "exact piecewise-linear-deceleration antiderivative with analytic stop event",
            "gravity_m_s2": GRAVITY, "coordinate_convention": "forward velocity positive; brake force and deceleration are positive magnitudes",
            "road": "level dry/low-friction illustrative surface; friction coefficient supplied by user",
            "friction_constraint": "aggregate longitudinal tire force <= mu*m*g; no axle-specific allocation",
            "suspension_coupling": "none; quarter-/half-car constant-speed equations unchanged",
            "units": {"time_s":"s", "speed_m_s":"m/s", "distance_m":"m",
                      "demanded_decel_m_s2":"m/s²", "actual_decel_m_s2":"m/s²",
                      "requested_force_n":"N", "traction_limit_n":"N", "actual_brake_force_n":"N",
                      "front_normal_n":"N", "rear_normal_n":"N"},
        },
        "assumptions": warnings[:2], "warnings": warnings,
        "samples": len(channels["time_s"]), "channels": channels,
        "metrics": {
            "stopped": stop, "stopping_time_s": stop_time, "stopping_distance_m": stop_distance,
            "elapsed_s": t, "distance_travelled_m": x,
            "final_speed_m_s": v, "peak_deceleration_m_s2": peak,
            "average_deceleration_m_s2": ((sc.initial_speed_m_s-v)/t) if t>0 else 0.0,
            "traction_limited": traction_limited,
            "available_traction_n": m*cap,
            "static_front_normal_n": static_front, "static_rear_normal_n": static_rear,
            "peak_front_normal_n": peak_front, "min_rear_normal_n": peak_rear,
            "max_front_load_transfer_n": peak_front-static_front,
        },
    }
