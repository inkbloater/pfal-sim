
"""
Demonstrate a simple photoperiod with a DLI controller.
Assume a 13-hour light window and a 26-hour simulation day (for safety).
"""
import math
from pfal_sim.env.light import LightFixture
from pfal_sim.env.light import dli_controller_step
from pfal_sim.env.light import integrate_dli

fixture = LightFixture(
    ppf_max=900.0,        # μmol/s at 100%
    ppe=2.4,              # μmol/J
    area_m2=1.2,          # m^2
    spectrum={"B":0.1,"G":0.2,"R":0.6,"FR":0.1},
    driver_loss=0.04,
    thermal_derate=0.0,
    wall_reflectance=0.85,
    beam_spread_deg=120.0
)

dt = 60  # seconds
light_hours = 13
window_seconds = light_hours * 3600

target_dli = 11.2  # mol m^-2 d^-1
ppfd_minmax = (120.0, 260.0)

series = []
lai = 1.0
dli_so_far = 0.0

for t in range(0, window_seconds, dt):
    seconds_left = window_seconds - t
    needed_ppfd = dli_controller_step(target_dli, dli_so_far, seconds_left, ppfd_minmax)
    # back-calc a dim level assuming ppfd scales with dim linearly via ppf -> ppfd
    # we approximate ppfd_max by querying fixture at 100% dim once at current LAI
    _max = fixture.step(1.0, lai)["ppfd"]
    dim = min(1.0, needed_ppfd / max(_max, 1e-6))
    out = fixture.step(dim, lai)
    series.append(out["ppfd"])
    # update running DLI
    dli_so_far = integrate_dli(series, dt)

print(f"DLI achieved: {dli_so_far:.3f} mol m^-2 d^-1 over {light_hours} h")