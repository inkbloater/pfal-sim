"""
Baby spinach crop growth physics for PFAL simulation.
Implements daily biomass increment as a function of DLI, temperature, VPD, and CO2.
All response curve parameters are defined here for easy calibration.
"""
import math

# --- Parameters for baby spinach (can be calibrated) ---
ALPHA = 1.0  # scaling factor for max daily fresh weight gain (g/m2/day)
DLI_OPT = (10, 15)  # mol/m2/d (optimum band)
T_OPT = 20.0        # degC (optimum)
T_WIDTH = 5.0       # degC (bell curve width)
VPD_OPT = (0.6, 1.2)  # kPa (comfort band)
CO2_OPT = 1000      # ppm (positive effect up to this value)

# --- Response curves (all return 0..1) ---
def f_DLI(DLI):
    # Flat optimum band, smooth dropoff outside
    lo, hi = DLI_OPT
    if DLI < lo:
        return max(0.0, (DLI / lo))
    elif DLI > hi:
        return max(0.0, 1.0 - 0.1 * (DLI - hi))
    else:
        return 1.0

def f_T(T):
    # Bell curve centered at T_OPT, robust to overflow/NaN
    if not math.isfinite(T):
        return 0.0
    exponent = -((T - T_OPT) ** 2) / (2 * T_WIDTH ** 2)
    exponent = max(exponent, -700)  # Prevent math.exp underflow
    return math.exp(exponent)

def f_VPD(VPD):
    # Flat comfort band, smooth dropoff outside
    lo, hi = VPD_OPT
    if VPD < lo:
        return max(0.0, (VPD / lo))
    elif VPD > hi:
        return max(0.0, 1.0 - 0.5 * (VPD - hi))
    else:
        return 1.0

def f_CO2(CO2):
    # Michaelis-Menten-like, saturates at CO2_OPT
    return min(1.0, CO2 / CO2_OPT)

# --- Main growth function ---
def daily_biomass_increment(DLI, T_mean, VPD_mean, CO2_mean):
    """
    Compute daily fresh weight increment (g/m2/day)
    """
    return ALPHA * f_DLI(DLI) * f_T(T_mean) * f_VPD(VPD_mean) * f_CO2(CO2_mean)
