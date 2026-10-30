"""Linear, 2-DOF quarter-car dynamics about static equilibrium.

Coordinates: positive upward. Both displacements and velocities are *deviations*
from the static-equilibrium values, not actual absolute ride heights.

ms*z_s'' = -ks*(z_s-z_u) - cs*(z_s'-z_u')
mu*z_u'' = +ks*(z_s-z_u) + cs*(z_s'-z_u') - kt*(z_u-z_r)

No gravity term appears because equilibrium offsets have been subtracted.
A linear tire is always connected to road; contact loss is not represented.
"""

from dataclasses import dataclass
from math import cos, isfinite, pi, sin, sqrt
from typing import Literal

RoadKind = Literal["bump", "step", "sine", "flat", "pothole", "double_bump", "chirp"]


@dataclass(frozen=True)
class Vehicle:
    sprung_mass_kg: float = 300.0
    unsprung_mass_kg: float = 40.0
    suspension_stiffness_n_m: float = 18000.0
    damping_n_s_m: float = 1500.0
    tire_stiffness_n_m: float = 190000.0

    def validate(self) -> None:
        limits = {
            "sprung_mass_kg": (100, 1200),
            "unsprung_mass_kg": (15, 150),
            "suspension_stiffness_n_m": (5000, 120000),
            "damping_n_s_m": (0, 12000),
            "tire_stiffness_n_m": (40000, 500000),
        }
        for field, (minimum, maximum) in limits.items():
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                raise ValueError(f"{field} must be a finite number")
            if not minimum <= value <= maximum:
                raise ValueError(f"{field} must be between {minimum} and {maximum}")

    @property
    def undamped_frequencies_hz(self) -> tuple[float, float]:
        """Natural modes of M^-1 K (ignores damping)."""
        ms, mu = self.sprung_mass_kg, self.unsprung_mass_kg
        ks, kt = self.suspension_stiffness_n_m, self.tire_stiffness_n_m
        trace = ks / ms + (ks + kt) / mu
        determinant = ks * kt / (ms * mu)
        discriminant = max(0.0, trace * trace - 4 * determinant)
        roots = ((trace - sqrt(discriminant)) / 2, (trace + sqrt(discriminant)) / 2)
        return tuple(sqrt(root) / (2 * pi) for root in roots)


@dataclass(frozen=True)
class Road:
    kind: RoadKind = "bump"
    height_m: float = 0.06
    start_s: float = 0.5
    bump_length_m: float = 1.5
    speed_m_s: float = 5.0
    sine_frequency_hz: float = 1.5
    bump_spacing_m: float = 1.5  # spatial gap between first bump end and second bump start
    chirp_end_frequency_hz: float = 4.0
    chirp_duration_s: float = 3.0

    def validate(self) -> None:
        if self.kind not in ("bump", "step", "sine", "flat", "pothole", "double_bump", "chirp"):
            raise ValueError("road.kind must be bump, step, sine, flat, pothole, double_bump, or chirp")
        for key, minimum, maximum in (
            ("height_m", 0, 0.15),
            ("start_s", 0, 5),
            ("bump_length_m", 0.5, 8),
            ("speed_m_s", 1, 40),
            ("sine_frequency_hz", 0.2, 5),
            ("bump_spacing_m", 0.5, 10),
            ("chirp_end_frequency_hz", 0.2, 5),
            ("chirp_duration_s", 0.5, 12),
        ):
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                raise ValueError(f"road.{key} must be a finite number")
            if not minimum <= value <= maximum:
                raise ValueError(f"road.{key} must be between {minimum} and {maximum}")

    @property
    def bump_end_s(self) -> float:
        return self.start_s + self.bump_length_m / self.speed_m_s

    def displacement(self, t: float) -> float:
        if t < self.start_s or self.kind == "flat":
            return 0.0
        tau = t - self.start_s
        if self.kind == "step":
            return self.height_m
        if self.kind == "sine":
            return self.height_m * sin(2 * pi * self.sine_frequency_hz * tau)
        if self.kind == "chirp":
            # Continuous phase and displacement. Linear instantaneous-frequency
            # ramp; after chirp_duration_s, the final frequency is held.
            q = min(tau, self.chirp_duration_s)
            phase = (self.sine_frequency_hz*q +
                     0.5*(self.chirp_end_frequency_hz-self.sine_frequency_hz)*q*q/self.chirp_duration_s +
                     self.chirp_end_frequency_hz*(tau-q))
            return self.height_m * sin(2*pi*phase)
        duration = self.bump_length_m / self.speed_m_s
        def pulse(local_time: float) -> float:
            if local_time < 0 or local_time >= duration:
                return 0.0
            return 0.5*self.height_m*(1-cos(2*pi*local_time/duration))
        if self.kind == "pothole":
            return -pulse(tau)
        if self.kind == "double_bump":
            return pulse(tau) + pulse(tau - duration - self.bump_spacing_m/self.speed_m_s)
        return pulse(tau)


@dataclass(frozen=True)
class SimulationSettings:
    duration_s: float = 5.0
    dt_s: float = 0.005

    def validate(self) -> None:
        for key, minimum, maximum in (("duration_s", 1, 15), ("dt_s", 0.001, 0.02)):
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                raise ValueError(f"{key} must be a finite number")
            if not minimum <= value <= maximum:
                raise ValueError(f"{key} must be between {minimum} and {maximum}")
        if round(self.duration_s / self.dt_s) > 15000:
            raise ValueError("maximum 15,000 integration steps")


State = tuple[float, float, float, float]  # zs, zu, vs, vu


def derivatives(t: float, state: State, vehicle: Vehicle, road: Road) -> State:
    zs, zu, vs, vu = state
    suspension_force = (
        vehicle.suspension_stiffness_n_m * (zs - zu)
        + vehicle.damping_n_s_m * (vs - vu)
    )
    tire_force = vehicle.tire_stiffness_n_m * (zu - road.displacement(t))
    return (
        vs,
        vu,
        -suspension_force / vehicle.sprung_mass_kg,
        (suspension_force - tire_force) / vehicle.unsprung_mass_kg,
    )


def mechanical_energy(state: State, vehicle: Vehicle) -> float:
    """Energy of free, flat-road response (road is assumed 0)."""
    zs, zu, vs, vu = state
    return (
        0.5 * vehicle.sprung_mass_kg * vs**2
        + 0.5 * vehicle.unsprung_mass_kg * vu**2
        + 0.5 * vehicle.suspension_stiffness_n_m * (zs - zu) ** 2
        + 0.5 * vehicle.tire_stiffness_n_m * zu**2
    )


def rk4_step(t: float, state: State, dt: float, vehicle: Vehicle, road: Road) -> State:
    def offset(y: State, k: State, coefficient: float) -> State:
        return tuple(y_i + coefficient * k_i for y_i, k_i in zip(y, k))  # type: ignore[return-value]

    k1 = derivatives(t, state, vehicle, road)
    k2 = derivatives(t + dt / 2, offset(state, k1, dt / 2), vehicle, road)
    k3 = derivatives(t + dt / 2, offset(state, k2, dt / 2), vehicle, road)
    k4 = derivatives(t + dt, offset(state, k3, dt), vehicle, road)
    return tuple(
        y + dt * (a + 2 * b + 2 * c + d) / 6
        for y, a, b, c, d in zip(state, k1, k2, k3, k4)
    )  # type: ignore[return-value]


def finite_road_end_s(road: Road) -> float | None:
    """Last forcing time for a finite-height feature, not a predicted settling time."""
    if road.kind == "flat":
        return 0.0
    if road.kind in ("bump", "pothole"):
        return road.bump_end_s
    if road.kind == "double_bump":
        return road.start_s + (2*road.bump_length_m + road.bump_spacing_m)/road.speed_m_s
    return None

def validate_road_resolution(road: Road, dt: float) -> None:
    """Require adequate forcing samples; vehicle's wheel-hop check is separate."""
    if road.height_m == 0 or road.kind == "flat":
        return
    if road.kind in ("bump", "pothole", "double_bump"):
        if road.bump_length_m / road.speed_m_s / dt < 12 - 1e-10:
            raise ValueError("road bump feature under-resolved: require at least 12 steps per raised-cosine feature")
    if road.kind in ("sine", "chirp"):
        frequency = max(road.sine_frequency_hz, road.chirp_end_frequency_hz) if road.kind == "chirp" else road.sine_frequency_hz
        if 1 / (frequency*dt) < 20 - 1e-10:
            raise ValueError("road sine/chirp frequency under-resolved: require at least 20 steps per highest-frequency cycle")
