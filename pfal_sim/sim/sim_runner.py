"""
Central simulation runner for PFAL vertical farm simulation.
Integrates RoomBox, LightFixture, crop growth, and controllers.
Simulates a 30-day crop cycle with 10-min time steps.
"""
import numpy as np
from datetime import datetime, timedelta
from pfal_sim.env.room import RoomBox, vpd_kpa
from pfal_sim.env.light import LightFixture
from pfal_sim.env.co2 import CO2Box
from pfal_sim.crop.spinach import daily_biomass_increment
from pfal_sim.env.light import dli_controller_step
from pfal_sim.data.logger import SimulationLogger

# --- Simulation parameters ---
SIM_DAYS = 30
DT_MIN = 1  # timestep in minutes (smaller for stability)
N_STEPS = SIM_DAYS * 24 * (60 // DT_MIN)

# Room and environment (RH handled internally, so omit RH)
room = RoomBox(T_air=20.0, T_nutr=20.0)

# Light fixture
fixture = LightFixture(
    ppf_max=900.0,
    ppe=2.4,
    area_m2=1.2,
    spectrum={"B":0.1,"G":0.2,"R":0.6,"FR":0.1},
    driver_loss=0.04,
    thermal_derate=0.0,
    wall_reflectance=0.85,
    beam_spread_deg=120.0
)

# Crop
LAI = 1.0
biomass_fw = 0.0

# Control setpoints
T_set = 20.0
DLI_target = 12.0
ppfd_minmax = (120.0, 260.0)
light_hours = 13
window_seconds = light_hours * 3600

# Logging
logger = SimulationLogger()

# --- Simulation loop ---
start_time = datetime(2025, 9, 8, 6, 0, 0)
time = start_time
ppfd_series = []
DLI_so_far = 0.0

for step in range(N_STEPS):
    # Time in day
    day = step // (24 * (60 // DT_MIN))
    t_in_day = (step % (24 * (60 // DT_MIN))) * DT_MIN * 60
    lights_on = t_in_day < window_seconds

    # DLI controller for lights
    if lights_on:
        seconds_left = window_seconds - t_in_day
        needed_ppfd = dli_controller_step(DLI_target, DLI_so_far, seconds_left, ppfd_minmax)
        _max = fixture.step(1.0, LAI)["ppfd"]
        dim_frac = min(1.0, needed_ppfd / max(_max, 1e-6))
    else:
        dim_frac = 0.0

    # Light fixture step
    light_out = fixture.step(dim_frac, LAI)
    ppfd = light_out["ppfd"]
    heat_watts = light_out["heat_watts"]
    watts_in = light_out["watts_in"]
    ppfd_series.append(ppfd)

    # Simple HVAC: bang-bang control to maintain T_air
    Q_HVAC_sens = 0.0
    # Reduce HVAC power to avoid runaway
    if room.T_air > T_set + 0.5:
        Q_HVAC_sens =  -10.0  # cooling (W, reduced for stability)
    elif room.T_air < T_set - 0.5:
        Q_HVAC_sens =  10.0   # heating (W, reduced for stability)


    # Room update: all physics handled inside RoomBox
    # Print debug info for temperature dynamics
    prev_T = room.T_air
    room.update(
        Q_led=heat_watts,
        Q_people=0,
        Q_equip=0,
        Q_HVAC_sens=Q_HVAC_sens,
        Q_HVAC_lat=0,
        T_out=18.0,
        E_canopy=None,  # Let RoomBox compute from VPD, LAI
        E_solution=0,
        infiltration=0,
        LAI=LAI,
        dt=DT_MIN*60,
        CO2_inj=0,
        PPFD=ppfd,
        canopy_area=fixture.area_m2,
        CO2_leaks=0
    )
    dT = room.T_air - prev_T
    print(f"Step {step}: T_air={room.T_air:.2f}C, T_nutr={room.T_nutr:.2f}C, Q_HVAC_sens={Q_HVAC_sens:.1f}W, dT={dT:.2f}, Q_led={heat_watts:.1f}W, PPFD={ppfd:.1f}")

    # Get updated state
    state = room.state()

    # DLI update
    DLI_so_far = sum(ppfd_series) * DT_MIN * 60 / 1e6

    # Log step
    logger.log_step({
        'time': time,
        'PPFD': ppfd,
        'DLI_so_far': DLI_so_far,
        'T': state['T_air'],
        'RH': state['RH'],
        'VPD': vpd_kpa(state['T_air'], state['RH']),
        'CO2': state['CO2_ppm'],
        'EC': 1.5,
        'pH': 6.0,
        'actuators': {'LED': 'ON' if dim_frac > 0 else 'OFF', 'HVAC': 'COOL' if Q_HVAC_sens < 0 else ('HEAT' if Q_HVAC_sens > 0 else 'IDLE')},
        'LED_W': watts_in,
        'HVAC_W': abs(Q_HVAC_sens)
    })

    # End of day: update biomass, reset DLI
    if (step+1) % (24 * (60 // DT_MIN)) == 0:
        mean_T = np.mean([logger.records[i]['T'] for i in range(len(logger.records)-24*(60//DT_MIN), len(logger.records))])
        mean_VPD = np.mean([logger.records[i]['VPD'] for i in range(len(logger.records)-24*(60//DT_MIN), len(logger.records))])
        mean_CO2 = np.mean([logger.records[i]['CO2'] for i in range(len(logger.records)-24*(60//DT_MIN), len(logger.records))])
        biomass_fw += daily_biomass_increment(DLI_so_far, mean_T, mean_VPD, mean_CO2)
        DLI_so_far = 0.0
        ppfd_series = []
    time += timedelta(minutes=DT_MIN)

# Save log
logger.save()
print(f"Sim complete. Final biomass FW: {biomass_fw:.2f} g/m2")
