"""Four-DOF small-angle, linear half-car heave/pitch model.

Right-handed longitudinal x points FRONT; upward z is positive; theta > 0
raises the nose. All coordinates are deviations about static equilibrium. Tire
contact is bilateral/always engaged and gravity cancels in these coordinates.

z_front_body = z + a*theta; z_rear_body = z - b*theta.
Ff = -ksf*(z+a*theta-zuf) - cf*(vz+a*omega-vuf)
Fr = -ksr*(z-b*theta-zur) - cr*(vz-b*omega-vur)
mb*z_ddot = Ff+Fr; Iy*theta_ddot = a*Ff-b*Fr
muf*zuf_ddot = -Ff - ktf*(zuf-road_front)
mur*zur_ddot = -Fr - ktr*(zur-road_rear).
The fixed rear delay is (a+b)/speed, with speed strictly positive.
"""
from dataclasses import dataclass, asdict
from math import isfinite, sqrt
from typing import Any
from .physics import Road, SimulationSettings, validate_road_resolution


@dataclass(frozen=True)
class HalfCarVehicle:
    body_mass_kg: float = 600.0
    pitch_inertia_kg_m2: float = 1000.0
    cg_to_front_m: float = 1.2
    cg_to_rear_m: float = 1.3
    front_unsprung_mass_kg: float = 40.0
    rear_unsprung_mass_kg: float = 40.0
    front_spring_n_m: float = 18000.0
    rear_spring_n_m: float = 18000.0
    front_damping_n_s_m: float = 1500.0
    rear_damping_n_s_m: float = 1500.0
    front_tire_n_m: float = 190000.0
    rear_tire_n_m: float = 190000.0

    def validate(self) -> None:
        limits = {
            'body_mass_kg': (200, 2400), 'pitch_inertia_kg_m2': (100, 15000),
            'cg_to_front_m': (.5, 3), 'cg_to_rear_m': (.5, 3),
            'front_unsprung_mass_kg': (15, 150), 'rear_unsprung_mass_kg': (15, 150),
            'front_spring_n_m': (5000, 120000), 'rear_spring_n_m': (5000, 120000),
            'front_damping_n_s_m': (0, 12000), 'rear_damping_n_s_m': (0, 12000),
            'front_tire_n_m': (40000, 500000), 'rear_tire_n_m': (40000, 500000),
        }
        for key, (minimum, maximum) in limits.items():
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                raise ValueError(f'{key} must be a finite number')
            if not minimum <= value <= maximum:
                raise ValueError(f'{key} must be between {minimum} and {maximum}')

    @property
    def wheelbase_m(self) -> float:
        return self.cg_to_front_m + self.cg_to_rear_m


HalfState = tuple[float, float, float, float, float, float, float, float]
ZERO_STATE: HalfState = (0.,) * 8


def axle_roads(t: float, vehicle: HalfCarVehicle, road: Road) -> tuple[float, float]:
    """Rear sees same spatial feature tau = wheelbase/speed later than front."""
    delay = vehicle.wheelbase_m / road.speed_m_s
    return road.displacement(t), road.displacement(t - delay)


def suspension_forces(y: HalfState, v: HalfCarVehicle) -> tuple[float, float]:
    z, theta, uf, ur, vz, omega, vuf, vur = y
    f = -v.front_spring_n_m*(z+v.cg_to_front_m*theta-uf) - v.front_damping_n_s_m*(vz+v.cg_to_front_m*omega-vuf)
    r = -v.rear_spring_n_m*(z-v.cg_to_rear_m*theta-ur) - v.rear_damping_n_s_m*(vz-v.cg_to_rear_m*omega-vur)
    return f, r


def derivatives_half(t: float, y: HalfState, v: HalfCarVehicle, road: Road) -> HalfState:
    _, _, uf, ur, vz, omega, vuf, vur = y
    ff, fr = suspension_forces(y, v)
    rf, rr = axle_roads(t, v, road)
    return (
        vz, omega, vuf, vur,
        (ff+fr)/v.body_mass_kg,
        (v.cg_to_front_m*ff-v.cg_to_rear_m*fr)/v.pitch_inertia_kg_m2,
        (-ff-v.front_tire_n_m*(uf-rf))/v.front_unsprung_mass_kg,
        (-fr-v.rear_tire_n_m*(ur-rr))/v.rear_unsprung_mass_kg,
    )


def half_energy(y: HalfState, v: HalfCarVehicle) -> float:
    """Unforced mechanical energy for zero road displacement (not forced-road energy)."""
    z,theta,uf,ur,vz,omega,vuf,vur=y
    df = z + v.cg_to_front_m*theta - uf
    dr = z - v.cg_to_rear_m*theta - ur
    return .5*(v.body_mass_kg*vz*vz + v.pitch_inertia_kg_m2*omega*omega +
        v.front_unsprung_mass_kg*vuf*vuf + v.rear_unsprung_mass_kg*vur*vur +
        v.front_spring_n_m*df*df + v.rear_spring_n_m*dr*dr +
        v.front_tire_n_m*uf*uf + v.rear_tire_n_m*ur*ur)


def half_energy_rate_flat(y: HalfState, v: HalfCarVehicle) -> float:
    _,_,_,_,vz,omega,vuf,vur=y
    return -(v.front_damping_n_s_m*(vz+v.cg_to_front_m*omega-vuf)**2 +
             v.rear_damping_n_s_m*(vz-v.cg_to_rear_m*omega-vur)**2)


def rk4_half(t: float, y: HalfState, dt: float, v: HalfCarVehicle, road: Road) -> HalfState:
    def add(state, rate, h):
        return tuple(x+h*k for x,k in zip(state,rate))
    k1=derivatives_half(t,y,v,road)
    k2=derivatives_half(t+dt/2,add(y,k1,dt/2),v,road)
    k3=derivatives_half(t+dt/2,add(y,k2,dt/2),v,road)
    k4=derivatives_half(t+dt,add(y,k3,dt),v,road)
    return tuple(x+dt*(a+2*b+2*c+d)/6 for x,a,b,c,d in zip(y,k1,k2,k3,k4))


HALF_CHANNELS = (
    'time_s','front_road_m','rear_road_m','body_heave_m','body_pitch_rad',
    'front_wheel_m','rear_wheel_m','body_heave_velocity_m_s','body_pitch_rate_rad_s',
    'front_wheel_velocity_m_s','rear_wheel_velocity_m_s',
    'body_heave_acceleration_m_s2','body_pitch_acceleration_rad_s2',
    'front_wheel_acceleration_m_s2','rear_wheel_acceleration_m_s2',
    'front_body_attachment_m','rear_body_attachment_m',
    'front_suspension_travel_m','rear_suspension_travel_m',
    'front_tire_deflection_m','rear_tire_deflection_m',
    'front_suspension_force_n','rear_suspension_force_n',
)


def _peak(xs: list[float]) -> float:
    return max(abs(x) for x in xs)


def simulate_half(v: HalfCarVehicle = HalfCarVehicle(), road: Road = Road(),
                  settings: SimulationSettings = SimulationSettings(),
                  initial_state: HalfState = ZERO_STATE) -> dict[str, Any]:
    v.validate(); road.validate(); settings.validate()
    if not isinstance(initial_state,(tuple,list)) or len(initial_state)!=8:
        raise ValueError('initial_state must contain eight finite state values')
    bounds = (.5,.20,.5,.5,10.,5.,10.,10.)
    if any(isinstance(x,bool) or not isinstance(x,(float,int)) or not isfinite(x) or abs(x)>limit
           for x,limit in zip(initial_state,bounds)):
        raise ValueError('initial_state out of bounded finite physical range')
    n=round(settings.duration_s/settings.dt_s)
    dt=settings.duration_s/n
    # Restrict time steps relative to highest wheel-hop natural frequency.
    fastest = max(sqrt((v.front_spring_n_m+v.front_tire_n_m)/v.front_unsprung_mass_kg),
                  sqrt((v.rear_spring_n_m+v.rear_tire_n_m)/v.rear_unsprung_mass_kg))
    if dt*fastest > .8:
        raise ValueError('half-car step under-resolves wheel-hop: reduce dt_s')
    validate_road_resolution(road, dt)
    out={k:[] for k in HALF_CHANNELS}
    y=tuple(initial_state)
    for i in range(n+1):
        t=i*dt
        z,theta,uf,ur,vz,omega,vuf,vur=y
        rf,rr=axle_roads(t,v,road)
        dy=derivatives_half(t,y,v,road)
        ff,fr=suspension_forces(y,v)
        front_att=z+v.cg_to_front_m*theta
        rear_att=z-v.cg_to_rear_m*theta
        row=(t,rf,rr,z,theta,uf,ur,vz,omega,vuf,vur,*dy[4:],
             front_att,rear_att,front_att-uf,rear_att-ur,uf-rf,ur-rr,ff,fr)
        for key,value in zip(HALF_CHANNELS,row):
            if not isfinite(value):
                raise ValueError('nonfinite numerical state; reduce dt_s')
            out[key].append(value)
        if i<n:
            y=rk4_half(t,y,dt,v,road)
    delay=v.wheelbase_m/road.speed_m_s
    acceleration=out['body_heave_acceleration_m_s2']
    metrics={
        'body_heave_acceleration_rms_m_s2':sqrt(sum(x*x for x in acceleration)/len(acceleration)),
        'body_heave_acceleration_peak_m_s2':_peak(acceleration),
        'body_heave_peak_mm':1000*_peak(out['body_heave_m']),
        'body_pitch_peak_deg':_peak(out['body_pitch_rad'])*180/3.141592653589793,
        'front_suspension_travel_peak_mm':1000*_peak(out['front_suspension_travel_m']),
        'rear_suspension_travel_peak_mm':1000*_peak(out['rear_suspension_travel_m']),
        'front_tire_deflection_peak_mm':1000*_peak(out['front_tire_deflection_m']),
        'rear_tire_deflection_peak_mm':1000*_peak(out['rear_tire_deflection_m']),
    }
    return {
        'schema_version':'half-car-1.0','model':'linear-four-dof-half-car-heave-pitch-equilibrium-relative',
        'provenance':{'release':'0.3.0','solver':'explicit fixed-step RK4','integration':'intermediate RK4 road samples',
                      'model':'linear 4-DOF, small pitch; always-engaged tires','time_s_origin':'simulation time zero',
                      'road_delay_s':delay,'units':'SI','data':'synthetic deterministic simulation'},
        'vehicle':asdict(v),'road':asdict(road),'settings':{'duration_s':settings.duration_s,'dt_s':dt},
        'wheelbase_m':v.wheelbase_m,'rear_road_delay_s':delay,'samples':n+1,'channels':out,'metrics':metrics,
        'initial_state':list(initial_state),
        'domain_diagnostics':{'peak_abs_pitch_rad':_peak(out['body_pitch_rad']),
                              'small_angle_caution':_peak(out['body_pitch_rad']) > .15,
                              'small_angle_threshold_rad':.15,
                              'note':'If peak pitch exceeds 0.15 rad, small-angle results require particular caution; this is a diagnostic threshold, not a formal validity proof.'},
        'assumptions':['Upward-positive heave/wheels, front-positive x, nose-up-positive pitch',
             'Small-angle linear pitch; all deviations relative to static equilibrium',
             'Gravity cancels at equilibrium; no absolute ride heights',
             'Front and rear axles follow same road feature at constant forward speed; rear delayed wheelbase/speed',
             'Linear always-engaged tires, no contact loss and no tire damping',
             'No body roll, steering, braking, regeneration, lateral forces or road-test calibration',
             'Artificial road-forcing input may inject energy; energy decay applies to unforced flat road only'],
    }


def scenario_half_from_mapping(data: Any) -> tuple[HalfCarVehicle,Road,SimulationSettings]:
    if not isinstance(data,dict):
        raise ValueError('half-car request body must be a JSON object')
    if set(data)-{'vehicle','road','settings'}:
        raise ValueError(f'unknown half-car top-level keys: {sorted(set(data)-{"vehicle","road","settings"})}')
    def extract(key,cls):
        mapping=data.get(key,{})
        if not isinstance(mapping,dict):raise ValueError(f'{key} must be an object')
        extra=set(mapping)-set(cls.__dataclass_fields__)
        if extra:raise ValueError(f'unknown {key} keys: {sorted(extra)}')
        instance=cls(**mapping)
        instance.validate()
        return instance
    return extract('vehicle',HalfCarVehicle),extract('road',Road),extract('settings',SimulationSettings)
