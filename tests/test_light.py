
import math
from pfal_sim.light import integrate_dli, dli_controller_step, dim_for_target_ppfd, electrical_watts

def test_dli_200_12h():
    # 200 μmol for 12 hours => 8.64 mol
    ppfd = 200.0
    hours = 12
    dt = 60  # 1 minute
    series = [ppfd] * int(hours * 3600 / dt)
    dli = integrate_dli(series, dt)
    assert abs(dli - 8.64) < 0.01

def test_dli_240_13h():
    # 240 μmol for 13 hours => 11.232 mol
    ppfd = 240.0
    hours = 13
    dt = 60
    series = [ppfd] * int(hours * 3600 / dt)
    dli = integrate_dli(series, dt)
    assert abs(dli - 11.232) < 0.02

def test_electrical_watts_simple():
    # ppe=2.0 μmol/J, ppf=200 μmol/s -> 100 W at the lamp
    # with 4% driver loss, input power ~104.17 W
    watts_in, heat = electrical_watts(ppf=200.0, ppe=2.0, driver_loss=0.04, thermal_derate=0.0)
    assert abs(watts_in - 104.1667) < 0.2
    assert abs(heat - watts_in) < 1e-6

def test_dim_for_target_ppfd():
    assert dim_for_target_ppfd(150.0, 300.0) == 0.5
