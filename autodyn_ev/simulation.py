"""Solver, derived engineering channels and reproducible output schema."""

from dataclasses import asdict
from math import sqrt
from typing import Any

from .physics import Road, SimulationSettings, State, Vehicle, derivatives, rk4_step, validate_road_resolution

CHANNELS = (
    "time_s", "road_m", "sprung_m", "unsprung_m", "sprung_velocity_m_s",
    "unsprung_velocity_m_s", "sprung_acceleration_m_s2", "unsprung_acceleration_m_s2",
    "suspension_travel_m", "tire_deflection_m", "suspension_force_n",
    "tire_force_variation_n",
)


def simulate(
    vehicle: Vehicle = Vehicle(),
    road: Road = Road(),
    settings: SimulationSettings = SimulationSettings(),
    initial_state: State = (0.0, 0.0, 0.0, 0.0),
) -> dict[str, Any]:
    vehicle.validate()
    road.validate()
    settings.validate()
    if len(initial_state) != 4 or any(not isinstance(s, (int, float)) or abs(s) > 10 for s in initial_state):
        raise ValueError("initial_state must contain four bounded finite values")
    from math import isfinite
    if not all(isfinite(x) for x in initial_state):
        raise ValueError("initial_state must be finite")

    n_steps = round(settings.duration_s / settings.dt_s)
    actual_dt = settings.duration_s / n_steps
    validate_road_resolution(road, actual_dt)
    output: dict[str, list[float]] = {key: [] for key in CHANNELS}
    state = initial_state
    for i in range(n_steps + 1):
        t = i * actual_dt
        zs, zu, vs, vu = state
        zr = road.displacement(t)
        _, _, ass, aus = derivatives(t, state, vehicle, road)
        travel = zs - zu
        tire = zu - zr
        values = (
            t, zr, zs, zu, vs, vu, ass, aus, travel, tire,
            vehicle.suspension_stiffness_n_m * travel + vehicle.damping_n_s_m * (vs - vu),
            vehicle.tire_stiffness_n_m * tire,
        )
        for key, value in zip(CHANNELS, values):
            output[key].append(value)
        if i < n_steps:
            state = rk4_step(t, state, actual_dt, vehicle, road)

    accel = output["sprung_acceleration_m_s2"]
    travel = output["suspension_travel_m"]
    def peak(values: list[float]) -> float:
        return max(abs(v) for v in values)
    metrics: dict[str, float | None] = {
        "body_acceleration_rms_m_s2": sqrt(sum(x * x for x in accel) / len(accel)),
        "body_acceleration_peak_m_s2": peak(accel),
        "suspension_travel_peak_mm": 1000 * peak(travel),
        "body_displacement_peak_mm": 1000 * peak(output["sprung_m"]),
        "tire_deflection_peak_mm": 1000 * peak(output["tire_deflection_m"]),
        "tire_force_variation_peak_n": peak(output["tire_force_variation_n"]),
        "body_mode_undamped_hz": vehicle.undamped_frequencies_hz[0],
        "wheel_mode_undamped_hz": vehicle.undamped_frequencies_hz[1],
    }
    # Only a finite-duration bump has a meaningful return to zero road profile.
    settling: float | None = None
    if road.kind == "bump" and road.bump_end_s < settings.duration_s:
        # Earliest post-bump point after which every remaining response satisfies
        # stated displacement AND velocity thresholds (no future escape).
        within = [
            abs(output["sprung_m"][i]) <= 0.002
            and abs(output["sprung_velocity_m_s"][i]) <= 0.01
            and abs(output["suspension_travel_m"][i]) <= 0.002
            for i in range(len(output["time_s"]))
        ]
        all_later_within = True
        for i in range(len(within) - 1, -1, -1):
            all_later_within = all_later_within and within[i]
            if all_later_within and output["time_s"][i] >= road.bump_end_s:
                settling = output["time_s"][i] - road.bump_end_s
    metrics["post_bump_settling_s"] = settling
    from .analysis import provenance
    return {
        "provenance": provenance(vehicle, road, settings, "time-domain-simulation"),
        "schema_version": "1.0",
        "model": "linear-two-dof-quarter-car-static-equilibrium-deviations",
        "vehicle": asdict(vehicle),
        "road": asdict(road),
        "settings": {"duration_s": settings.duration_s, "dt_s": actual_dt},
        "samples": n_steps + 1,
        "channels": output,
        "metrics": metrics,
        "assumptions": [
            "Small-displacement linear springs and viscous suspension damping",
            "Two vertical translational DOF; no pitch, roll, lateral dynamics, or braking",
            "Static-equilibrium-relative coordinates, gravity canceled in equations",
            "Tire is linear and always in contact; contact loss is not simulated",
            "RMS values are scenario responses, not ISO 2631 ride-comfort compliance results",
            "No physical vehicle calibration or road-test validation",
        ],
    }


def scenario_from_mapping(data: Any) -> tuple[Vehicle, Road, SimulationSettings]:
    if not isinstance(data, dict):
        raise ValueError("request body must be a JSON object")
    allowed = {"vehicle", "road", "settings"}
    if set(data) - allowed:
        raise ValueError(f"unknown top-level keys: {sorted(set(data) - allowed)}")

    def parse(key: str, cls: type) -> Any:
        fields = cls.__dataclass_fields__
        values = data.get(key, {})
        if not isinstance(values, dict):
            raise ValueError(f"{key} must be a JSON object")
        unknown = set(values) - set(fields)
        if unknown:
            raise ValueError(f"unknown {key} keys: {sorted(unknown)}")
        instance = cls(**values)
        instance.validate()
        return instance

    return (parse("vehicle", Vehicle), parse("road", Road), parse("settings", SimulationSettings))
