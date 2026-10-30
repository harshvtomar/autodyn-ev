"""Chat 4 deterministic road/ride studies (not ISO 2631 or physical calibration).

Read-only postprocessing of the accepted quarter/half model outputs. All temporal
moments use a trapezoidal integral, including the partial final window step.
"""
from dataclasses import asdict
from math import sqrt, isfinite
from typing import Any

from .physics import Road, finite_road_end_s
from .simulation import scenario_from_mapping, simulate
from .halfcar import scenario_half_from_mapping, simulate_half

RELEASE = '0.4.0'


def _window(time: list[float], signal: list[float], start: float, end: float) -> dict[str, float | int]:
    """Trapezoid-RMS with linearly interpolated endpoints on a uniform grid."""
    if not (0 <= start < end <= time[-1] + 1e-10):
        raise ValueError('window must be within sampled timeline and have positive duration')
    if len(time) != len(signal) or len(time) < 2:
        raise ValueError('invalid samples for window')
    def interp(x):
        lo = max(0, min(len(time)-2, int(x/(time[1]-time[0]))))
        while lo > 0 and time[lo] > x: lo -= 1
        while lo < len(time)-2 and time[lo+1] < x: lo += 1
        a = (x-time[lo])/(time[lo+1]-time[lo])
        return signal[lo]*(1-a)+signal[lo+1]*a
    pts = [(start,interp(start))] + [(t,x) for t,x in zip(time[1:-1],signal[1:-1]) if start < t < end] + [(end,interp(end))]
    integral = sum((b[0]-a[0])*(a[1]*a[1]+b[1]*b[1])/2 for a,b in zip(pts,pts[1:]))
    vals = [x for _,x in pts]
    return {'start_s':start,'end_s':end,'rms':sqrt(max(integral,0)/(end-start)),
            'peak_abs':max(abs(x) for x in vals),'peak_to_peak':max(vals)-min(vals),
            'samples_including_interpolated_boundaries':len(pts)}


def _settling(ch: dict, end: float | None, mapping: dict[str,tuple[str,float]], total: float) -> float | None:
    """First post-feature sample after which all sampled states remain in bounds."""
    if end is None or end >= total: return None
    t = ch['time_s']; ok = [all(abs(ch[key][i]) <= lim for key,lim in mapping.values()) for i in range(len(t))]
    future_good = True; first = None
    for i in range(len(t)-1,-1,-1):
        future_good = future_good and ok[i]
        if future_good and t[i] >= end-1e-12: first = t[i]
    return None if first is None else max(0.,first-end)


def _one(model: str, mapping: Any) -> dict[str, Any]:
    if model=='quarter':
        vehicle,road,settings = scenario_from_mapping(mapping); raw=simulate(vehicle,road,settings)
        names = {'body_acceleration':'sprung_acceleration_m_s2',
                 'suspension_travel':'suspension_travel_m',
                 'tire_deflection':'tire_deflection_m'}
        settling_map = {'body':('sprung_m',.002),'body_velocity':('sprung_velocity_m_s',.01),
                        'travel':('suspension_travel_m',.002)}
        channel_names = ['time_s','road_m','sprung_acceleration_m_s2','suspension_travel_m','tire_deflection_m']
    elif model=='half':
        vehicle,road,settings = scenario_half_from_mapping(mapping);raw=simulate_half(vehicle,road,settings)
        names = {'body_acceleration':'body_heave_acceleration_m_s2',
                 'front_suspension_travel':'front_suspension_travel_m',
                 'rear_suspension_travel':'rear_suspension_travel_m',
                 'front_tire_deflection':'front_tire_deflection_m',
                 'rear_tire_deflection':'rear_tire_deflection_m',
                 'body_pitch':'body_pitch_rad'}
        settling_map = {'body':('body_heave_m',.002),'velocity':('body_heave_velocity_m_s',.01),
                        'front_travel':('front_suspension_travel_m',.002),
                        'rear_travel':('rear_suspension_travel_m',.002),
                        'pitch':('body_pitch_rad',.002),'pitch_rate':('body_pitch_rate_rad_s',.01)}
        channel_names = ['time_s','front_road_m','rear_road_m','body_heave_acceleration_m_s2',
                         'front_suspension_travel_m','rear_suspension_travel_m',
                         'front_tire_deflection_m','rear_tire_deflection_m','body_pitch_rad']
    else: raise ValueError('model must be quarter or half')
    ch=raw['channels'];t=ch['time_s'];last=t[-1]
    end=finite_road_end_s(road) if road.height_m > 0 else None
    # An event has only fully ended after the back axle has encountered it.
    if model=='half' and end is not None and road.kind!='flat':
        end += raw['rear_road_delay_s']
    windows={'full':{'start_s':0.,'end_s':last,'channels':{}}}
    if end is not None and road.kind!='flat' and end < last-1e-10:
        windows['post_event']={'start_s':end,'end_s':last,'channels':{}}
    for window in windows.values():
        for name,key in names.items():
            window['channels'][name]=_window(t,ch[key],window['start_s'],window['end_s'])
    warnings=['All response data are simulated, static-equilibrium-relative; unweighted acceleration RMS is NOT ISO 2631-compliant ride comfort.',
              'Linear tire deflection is a force-variation proxy, NOT proof of tire contact or separation.']
    if end is None: warnings.append('No finite nonzero road event has completed; post-event settling is not defined (sustained forcing or zero amplitude).')
    elif end>=last: warnings.append('Finite road feature has not ended within the simulation; no post-event window or settling time.')
    if model=='half' and raw['domain_diagnostics']['small_angle_caution']:
        warnings.append('Peak body pitch exceeds 0.15 rad: small-angle approximation warrants caution.')
    settling = _settling(ch,end if road.kind!='flat' else None,settling_map,last)
    summary={}
    for name,key in names.items():
        stats=windows['full']['channels'][name]
        summary[name+'_rms_si']=stats['rms']
        summary[name+'_peak_abs_si']=stats['peak_abs']
        summary[name+'_peak_to_peak_si']=stats['peak_to_peak']
    summary['settling_after_last_excitation_s']=settling
    return {'model':model,'scenario':{'vehicle':asdict(vehicle),'road':asdict(road),'settings':raw['settings']},
            'samples':raw['samples'],'windows':windows,'metrics':summary,
            'finite_road_last_excitation_s':end if road.kind!='flat' else None,
            'waveforms':{k:ch[k] for k in channel_names},'warnings':warnings,
            'tolerance_definition':{'displacement_m':.002,'velocity_m_s':.01,
                        'halfcar_pitch_rad':.002,'halfcar_pitch_rate_rad_s':.01,
                        'rule':'First post-event sample after which all future sampled response states remain within thresholds; no guaranteed physical settling.'}}


def ride_request(body: Any) -> dict[str,Any]:
    if not isinstance(body,dict):raise ValueError('ride study must be a JSON object')
    unknown=set(body)-{'model','scenario','baseline'}
    if unknown:raise ValueError(f'unknown ride study keys: {sorted(unknown)}')
    model=body.get('model','quarter')
    if model not in ('quarter','half'):raise ValueError('model must be quarter or half')
    selected=_one(model,body.get('scenario',{}))
    baseline=None;deltas=None
    if 'baseline' in body:
        baseline=_one(model,body['baseline'])
        # Identical road and simulation horizon are required, not comparable otherwise.
        a,b=baseline['scenario'],selected['scenario']
        if a['road']!=b['road'] or a['settings']!=b['settings']:
            raise ValueError('baseline and variant must share identical road and time-step/duration settings')
        deltas={k: selected['metrics'][k]-v for k,v in baseline['metrics'].items()
                if isinstance(v,(int,float)) and isfinite(v) and isinstance(selected['metrics'][k],(int,float))}
    return {'schema_version':'ride-study-1.0','release':RELEASE,'model':model,
            'solver':'inherited fixed-step RK4, evaluated at intermediate road times',
            'integration':'trapezoidal time-weighted RMS, sample peaks, interpolated window boundaries',
            'units':{'time':'s','acceleration':'m/s^2','suspension_travel':'m','tire_deflection':'m','body_pitch':'rad'},
            'data':'deterministic synthetic engineering simulation; not physical validation',
            'current':selected,'baseline':baseline,'deltas':deltas,
            'comparison_rule':'Same model, road and time grid; differences are changes in simulated scenario response, not overall engineering optimization.'}
