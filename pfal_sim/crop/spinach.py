"""
Spinach crop growth physics for PFAL simulation.
Implements daily biomass increment as a function of DLI, temperature, VPD, and CO2.
Parameters are kept here for easy calibration.
"""
import math

# Calibration parameters (can be tuned)
ALPHA = 1.0  # scaling factor for max daily growth (g/day)
DLI_OPT = (10, 18)  # mol/m2/d optimal DLI band
T_OPT = 21.0        # degC, optimal mean temp
T_WIDTH = 5.0       # degC, width of temp bell curve
VPD_OPT = (0.6, 1.2) # kPa, optimal VPD band
CO2_OPT = 1000      # ppm, optimal CO2 (lights on)

def f_DLI(DLI):
	# Smooth response: 0 below min, 1 in band, drop above max
	dli_min, dli_max = DLI_OPT
	if DLI < dli_min:
		return 0.0
	elif DLI > dli_max:
		return max(0.0, 1.0 - 0.05 * (DLI - dli_max))
	else:
		return 1.0

def f_T(T):
	# Bell curve centered at T_OPT
	return math.exp(-0.5 * ((T - T_OPT) / T_WIDTH) ** 2)

def f_VPD(VPD):
	# 1 in comfort band, drop off outside
	vpd_min, vpd_max = VPD_OPT
	if VPD < vpd_min:
		return max(0.0, 1.0 - (vpd_min - VPD))
	elif VPD > vpd_max:
		return max(0.0, 1.0 - (VPD - vpd_max))
	else:
		return 1.0

def f_CO2(CO2):
	# Michaelis-Menten-like, saturates at CO2_OPT
	return min(1.0, CO2 / (CO2_OPT + 1e-6))

def daily_biomass_increment(DLI, T_mean, VPD_mean, CO2_hours):
	"""
	Calculate daily fresh weight increment (g/day) for spinach.
	DLI: daily light integral (mol/m2/d)
	T_mean: mean air temp (degC)
	VPD_mean: mean VPD (kPa)
	CO2_hours: mean CO2 during photoperiod (ppm)
	"""
	return ALPHA * f_DLI(DLI) * f_T(T_mean) * f_VPD(VPD_mean) * f_CO2(CO2_hours)
