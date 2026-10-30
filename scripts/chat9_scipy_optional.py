"""Optional independent numerical cross-check using SciPy, not needed at runtime.

The reference derivatives are independently written Newton/D'Alembert equations;
the only reused part is the accepted externally imposed road displacement function.
The comparison is numerical consistency, not empirical real-vehicle validation.
"""
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scipy.integrate import solve_ivp
from autodyn_ev.physics import Road,Vehicle,SimulationSettings
from autodyn_ev.halfcar import HalfCarVehicle,simulate_half
from autodyn_ev.simulation import simulate
from autodyn_ev.verification import quarter_force_reference,half_force_reference,max_abs_delta


def run():
    records=[]
    for model in ('quarter','half'):
        for kind in ('sine','bump','pothole'):
            road=Road(kind=kind,start_s=0 if kind=='sine' else .5,height_m=.01)
            settings=SimulationSettings(duration_s=3,dt_s=.005)
            if model=='quarter':
                v=Vehicle();out=simulate(v,road,settings)
                mass=(v.sprung_mass_kg,v.unsprung_mass_kg)
                stiffness=(v.suspension_stiffness_n_m,v.damping_n_s_m,v.tire_stiffness_n_m)
                def rhs(t,y):
                    a,b=quarter_force_reference(mass,stiffness,y,road.displacement(t))
                    return [y[2],y[3],a,b]
                fields=['sprung_m','unsprung_m','sprung_velocity_m_s','unsprung_velocity_m_s']
                dim=4
            else:
                v=HalfCarVehicle();out=simulate_half(v,road,settings)
                p=(v.body_mass_kg,v.pitch_inertia_kg_m2,v.cg_to_front_m,v.cg_to_rear_m,
                   v.front_unsprung_mass_kg,v.rear_unsprung_mass_kg,
                   v.front_spring_n_m,v.rear_spring_n_m,v.front_damping_n_s_m,v.rear_damping_n_s_m,
                   v.front_tire_n_m,v.rear_tire_n_m)
                delay=(v.cg_to_front_m+v.cg_to_rear_m)/road.speed_m_s
                def rhs(t,y):
                    a,b,c,d=half_force_reference(p,y,road.displacement(t),road.displacement(t-delay))
                    return [y[4],y[5],y[6],y[7],a,b,c,d]
                fields=['body_heave_m','body_pitch_rad','front_wheel_m','rear_wheel_m',
                        'body_heave_velocity_m_s','body_pitch_rate_rad_s','front_wheel_velocity_m_s','rear_wheel_velocity_m_s']
                dim=8
            tt=out['channels']['time_s'];ref=solve_ivp(rhs,(0,settings.duration_s),[0.0]*dim,
                method='DOP853',rtol=1e-11,atol=1e-13,dense_output=True,max_step=.01)
            assert ref.success,ref.message
            yy=ref.sol(tt)
            errors={field:max_abs_delta(out['channels'][field],yy[i]) for i,field in enumerate(fields)}
            # Coordinate units differ. Check each channel by absolute threshold and document units.
            threshold=2e-4
            passed=all(val<threshold for val in errors.values())
            records.append({'model':model,'kind':kind,'method':'independent Newton force balance + SciPy DOP853',
                'rk4_dt_s':settings.dt_s,'rtol':1e-11,'atol':1e-13,
                'max_abs_state_channel_difference':errors,'tolerance_per_channel':threshold,
                'units':'m for positions, rad for angle, m/s or rad/s for rates',
                'passed':passed})
            if not passed:raise AssertionError(f'Independent DOP853 mismatch: {model}/{kind}: {errors}')
    out=Path('docs/CHAT9_SCIPY_REFERENCES.json');out.write_text(json.dumps(records,indent=2)+'\n')
    print(f'SciPy independent reference: {len(records)}/{len(records)} passed')

if __name__=='__main__':run()
