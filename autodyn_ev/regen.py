"""Chat 6: separate EV energy recovery extension for the accepted braking solution.

The longitudinal trajectory is *exactly* the Chat 5 aggregate-friction trajectory;
regen only allocates physically feasible total brake force between motor and
friction braking. Energy is integrated along the moving trajectory, not by
blindly summing samples. No wheel-slip/ABS, SOC/thermal cell physics or hardware.
"""
from dataclasses import asdict, dataclass, fields
from math import isfinite
from .braking import BrakingScenario, GRAVITY, actual_at, simulate_braking


@dataclass(frozen=True)
class RegenScenario(BrakingScenario):
    motor_max_torque_nm: float = 140.0
    gear_ratio: float = 8.0
    driven_wheel_radius_m: float = 0.32
    motor_max_mech_power_w: float = 40000.0
    battery_charge_limit_w: float = 24000.0
    conversion_efficiency: float = 0.85
    low_speed_cutoff_m_s: float = 0.0

    def validate(self):
        braking_fields = {f.name for f in fields(BrakingScenario)}
        BrakingScenario(**{name: getattr(self, name) for name in braking_fields}).validate()
        bounds = {
            'motor_max_torque_nm': (0.0, 1500.0),
            'gear_ratio': (0.2, 30.0),
            'driven_wheel_radius_m': (0.1, 1.0),
            'motor_max_mech_power_w': (0.0, 400000.0),
            'battery_charge_limit_w': (0.0, 400000.0),
            'conversion_efficiency': (0.0, 1.0),
            'low_speed_cutoff_m_s': (0.0, 10.0),
        }
        for key, (lo, hi) in bounds.items():
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
                raise ValueError(f'{key} must be a finite number')
            if not lo <= value <= hi:
                raise ValueError(f'{key} must be between {lo} and {hi}')


def scenario_from_mapping(raw):
    if not isinstance(raw, dict):
        raise ValueError('regenerative braking scenario must be a JSON object')
    source = raw.get('scenario', raw)
    if not isinstance(source, dict):
        raise ValueError('scenario must be a JSON object')
    names = {f.name for f in fields(RegenScenario)}
    unknown = set(source) - names
    if unknown:
        raise ValueError('unknown regeneration field(s): ' + ', '.join(sorted(unknown)))
    try:
        result = RegenScenario(**source)
    except TypeError as exc:
        raise ValueError('invalid regenerative braking inputs: ' + str(exc)) from exc
    result.validate()
    return result


def braking_only(sc):
    return BrakingScenario(**{f.name: getattr(sc, f.name) for f in fields(BrakingScenario)})


def allocate(total_force_n, speed_m_s, sc):
    """Feasible instantaneous regen and friction forces (N), wheel-side conventions."""
    if total_force_n <= 0 or speed_m_s <= 0 or speed_m_s < sc.low_speed_cutoff_m_s or sc.conversion_efficiency == 0 or sc.battery_charge_limit_w == 0:
        return 0.0, max(0.0, total_force_n)
    torque_cap_n = sc.motor_max_torque_nm * sc.gear_ratio / sc.driven_wheel_radius_m
    power_cap_n = sc.motor_max_mech_power_w / speed_m_s
    battery_cap_n = sc.battery_charge_limit_w / (sc.conversion_efficiency * speed_m_s)
    regen = max(0.0, min(total_force_n, torque_cap_n, power_cap_n, battery_cap_n))
    return regen, max(0.0, total_force_n - regen)


def _simpson(f, a, b):
    middle = (a + b) / 2
    return (b - a) / 6 * (f(a) + 4*f(middle) + f(b))


def _adaptive(f, a, b, whole, tolerance, depth):
    mid = (a+b)*0.5
    left, right = _simpson(f,a,mid), _simpson(f,mid,b)
    err = left + right - whole
    if depth == 0 or abs(err) <= 15*tolerance:
        return left + right + err/15
    return (_adaptive(f,a,mid,left,tolerance/2,depth-1)
          + _adaptive(f,mid,b,right,tolerance/2,depth-1))


def simulate_regen(sc=None):
    sc = sc if sc is not None else RegenScenario()
    sc.validate()
    base = simulate_braking(braking_only(sc))
    m = sc.mass_kg
    ch0 = base['channels']; t = ch0['time_s']; v = ch0['speed_m_s']
    out = {k:list(values) for k,values in ch0.items()}
    keys = ('regen_force_n','friction_force_n','motor_mechanical_power_w','battery_charge_power_w',
            'friction_dissipation_power_w','conversion_loss_power_w','cumulative_motor_energy_j',
            'cumulative_battery_energy_j','cumulative_friction_energy_j','cumulative_conversion_loss_j',
            'kinetic_energy_j','kinetic_energy_reduction_j','energy_balance_residual_j')
    for name in keys: out[name] = []
    total_regen = total_friction = raw_friction_work = 0.0
    initial_kinetic = 0.5*m*sc.initial_speed_m_s**2
    max_residual = 0.0
    max_regen_power = max_battery_power = 0.0
    regen_constrained = False
    any_friction = False

    for i, (now, speed) in enumerate(zip(t, v)):
        active = speed > 0
        force = out['actual_brake_force_n'][i] if active else 0.0
        regen, friction = allocate(force, speed, sc)
        mech_power = regen*speed
        batt_power = mech_power*sc.conversion_efficiency
        if active and force > regen + 1e-8: any_friction = True
        if active and force > regen + 1e-8 and sc.motor_max_torque_nm > 0: regen_constrained = True
        max_regen_power = max(max_regen_power, mech_power)
        max_battery_power = max(max_battery_power, batt_power)
        if i:
            t0, t1 = t[i-1], now
            v0 = v[i-1]
            dt = t1-t0
            if dt > 0 and v0 > 0:
                # The accepted Chat 5 solver divides every ramp slope transition.
                # Evaluate velocity at continuous intermediate time with exact local
                # linear-deceleration antiderivative, respecting the final stop.
                a0 = actual_at(t0, sc)
                a1 = actual_at(t1, sc)
                slope = (a1-a0)/dt
                def _powers(u):
                    local = u-t0
                    vel = max(0.0, v0 - a0*local - 0.5*slope*local*local)
                    if vel <= 0: return 0.0,0.0
                    decel = max(0.0, a0+slope*local)
                    regen, friction = allocate(m*decel,vel,sc)
                    return regen*vel,friction*vel
                def energy_rate(u): return _powers(u)[0]
                def friction_rate(u): return _powers(u)[1]
                # The cutoff introduces a known discontinuity. Explicitly break
                # the integral there so no arbitrary endpoint convention matters.
                intervals=[t0,t1]
                if sc.low_speed_cutoff_m_s > 0 and v0 > sc.low_speed_cutoff_m_s > speed:
                    lo,hi=t0,t1
                    for _ in range(52):
                        mid=(lo+hi)/2; u=mid-t0
                        vv=v0-a0*u-0.5*slope*u*u
                        if vv > sc.low_speed_cutoff_m_s: lo=mid
                        else: hi=mid
                    intervals=[t0,(lo+hi)/2,t1]
                for left,right in zip(intervals, intervals[1:]):
                    if right > left:
                        # Integrate only meaningful motor mechanical work (J).
                        whole=_simpson(energy_rate,left,right)
                        total_regen += _adaptive(energy_rate,left,right,whole,max(1e-8,(right-left)*1e-4),16)
                        raw_friction_work += _adaptive(friction_rate,left,right,_simpson(friction_rate,left,right),max(1e-8,(right-left)*1e-4),16)
            current_drop = max(0.0, initial_kinetic-0.5*m*speed*speed)
            total_regen = min(max(0.0,total_regen),current_drop)
            total_friction = max(0.0,current_drop-total_regen)
        kinetic = 0.5*m*speed*speed
        kinetic_drop = max(0.0,initial_kinetic-kinetic)
        battery = sc.conversion_efficiency*total_regen
        conversion_loss = total_regen-battery
        residual = kinetic_drop-(battery+conversion_loss+total_friction)
        max_residual = max(max_residual,abs(residual))
        values=(regen, friction, mech_power,batt_power,friction*speed,(1-sc.conversion_efficiency)*mech_power,
                total_regen,battery,total_friction,conversion_loss,kinetic,kinetic_drop,residual)
        for key,val in zip(keys,values): out[key].append(float(val))

    # The friction total uses exact kinetic-energy closure after independently
    # integrating regen and friction power. The *uncorrected* quadrature residual
    # is exported separately to expose integration error rather than hiding it.
    final = base['metrics']
    kinetic_decrease = initial_kinetic - 0.5*m*final['final_speed_m_s']**2
    battery = sc.conversion_efficiency*total_regen
    conversion_loss = total_regen-battery
    raw_quadrature_residual = kinetic_decrease-total_regen-raw_friction_work
    flags=list(base['warnings'])
    flags += [
        'Illustrative fixed motor/charge-power limits; no SOC, temperature, thermal protection, motor maps or axle-specific traction model.',
        'Wheel-side mechanical torque = motor shaft torque × ideal gear ratio; a single assumed efficiency accounts for wheel-to-battery electrical conversion.',
        'No ABS, wheel slip, dynamic brake bias, aerodynamic drag, rolling loss, brake temperature or physical EV validation.',
    ]
    if regen_constrained: flags.append('Some braking demand is supplied by friction brakes because regeneration is constrained.')
    if not any_friction and total_regen > 0: flags.append('Illustrative scenario permits all braking work to be absorbed mechanically by regeneration.')
    if sc.low_speed_cutoff_m_s > 0: flags.append(f'Regeneration disabled below assumed {sc.low_speed_cutoff_m_s:g} m/s cutoff.')
    if battery == 0: flags.append('No energy is stored in the battery for this scenario.')
    units=dict(base['provenance']['units']); units.update({
        'regen_force_n':'N','friction_force_n':'N','motor_mechanical_power_w':'W','battery_charge_power_w':'W',
        'friction_dissipation_power_w':'W','conversion_loss_power_w':'W','cumulative_motor_energy_j':'J',
        'cumulative_battery_energy_j':'J','cumulative_friction_energy_j':'J','cumulative_conversion_loss_j':'J',
        'kinetic_energy_j':'J','kinetic_energy_reduction_j':'J','energy_balance_residual_j':'J'
    })
    return {
        'model':'independent-longitudinal-regenerative-braking', 'version':'0.6.0',
        'scenario':asdict(sc),'provenance':{
            'model_revision':'chat6-regen-v1','base_solver':'exact Chat 5 constant/ramp stopping trajectory',
            'integration':'adaptive Simpson mechanical regen power integration with exact segment speed; energy balance allocation',
            'gravity_m_s2':GRAVITY,'source':'accepted v0.5.0 braking branch, isolated extension',
            'constraints':'aggregate mu*m*g; regen limited by motor shaft torque × ideal ratio / radius, wheel mechanical power, battery power / efficiency',
            'battery':'assumed constant charge-power acceptance; not a calibrated battery, cell, SOC or temperature model',
            'coordinate_convention':'positive speed, positive braking forces/deceleration and positive battery charge energy',
            'suspension_coupling':'none; no changes to fixed-speed quarter-/half-car dynamics', 'units':units,
        },
        'channels':out,'samples':len(t),'warnings':flags,
        'metrics':{
            **final,'initial_kinetic_energy_j':initial_kinetic,'final_kinetic_energy_j':0.5*m*final['final_speed_m_s']**2,
            'kinetic_energy_reduction_j':kinetic_decrease,'motor_mechanical_recovered_j':total_regen,
            'battery_energy_stored_j':battery,'conversion_loss_j':conversion_loss,
            'friction_dissipation_j':total_friction,'energy_balance_residual_j':kinetic_decrease-(battery+conversion_loss+total_friction),
            'max_sample_energy_balance_residual_j':max_residual,
            'independently_integrated_friction_work_j':raw_friction_work,
            'uncorrected_work_quadrature_residual_j':raw_quadrature_residual,
            'recovery_fraction_of_kinetic_reduction':(battery/kinetic_decrease if kinetic_decrease>0 else 0.0),
            'peak_motor_mechanical_power_w':max_regen_power,'peak_battery_charge_power_w':max_battery_power,
        },
    }
