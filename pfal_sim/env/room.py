
"""
Minimal thermal and moisture physics for PFAL room (box model)
Implements sensible and latent heat/moisture balances for air and solution.
"""


from dataclasses import dataclass
from typing import Optional
import math


def vpd_kpa(T: float, RH: float) -> float:
	"""
	Calculate vapor pressure deficit (VPD, kPa) from T (C) and RH (0-1).
	"""
	es = 0.6108 * math.exp((17.27 * T) / (T + 237.3))  # kPa
	ea = RH * es
	return max(0.0, es - ea)




@dataclass
class RoomBox:
	def _n_sat(self, T):
		try:
			es = 610.8 * math.exp((17.27 * T) / (T + 237.3))  # Pa
			R = 8.314  # J/(mol K)
			V = self.V_air
			n_sat = es * V / (R * (T + 273.15))
			return float(n_sat)
		except Exception:
			return 0.0
	# State variables
	T_air: float  # Air temperature (C)
	T_nutr: float # Solution temperature (C)
	CO2_ppm: float = 900.0  # CO2 concentration (ppm)
	n_vapor: float = 0.0    # moles of water vapor in air

	# Room parameters
	V_air: float = 100.0      # m3, room air volume
	UA: float = 200.0         # W/K, envelope conductance
	C_air: float = 120000.0    # J/K, effective air heat capacity (increased for stability)
	M_air: float = 120.0      # mol, air moles (approx for 100 m3)
	M_v: float = 18.0         # g/mol, molar mass of water vapor

	# Nutrient solution parameters
	V_nutr: float = 0.2       # m3, solution volume (200 L default)
	C_nutr: float = 836.0     # J/K, heat capacity (200 L * 4.18 kJ/K)

	# Transpiration conductance (tunable, g/s/kPa per LAI=1)
	g_c: float = 2.0

	def __post_init__(self):
		# Initialize n_vapor from T_air and assumed RH=0.7 if not set
		if self.n_vapor == 0.0:
			RH0 = 0.7
			n_sat = self._n_sat(self.T_air)
			self.n_vapor = RH0 * n_sat


	def _RH(self):
		n_sat = self._n_sat(self.T_air)
		return min(max(self.n_vapor / n_sat, 0.0), 1.0)

	def update(self,
			   Q_led: float,
			   Q_people: float,
			   Q_equip: float,
			   Q_HVAC_sens: float,
			   Q_HVAC_lat: float,
			   T_out: float,
			   E_canopy: Optional[float] = None,
			   E_solution: float = 0.0,
			   infiltration: float = 0.0,
			   LAI: float = 1.0,
			   dt: float = 60.0,
			   CO2_inj: float = 0.0,
			   PPFD: float = 0.0,
			   canopy_area: float = 1.0,
			   CO2_leaks: float = 0.0):
		"""
		Advance the room state by one timestep (dt seconds).
		All Q in W (J/s), E in g/s, dt in seconds.
		If E_canopy is None, compute as g_c * VPD * LAI.
		CO2 state is updated using injection, plant uptake, and leaks.
		Humidity is tracked as absolute moles of vapor, RH is derived.
		"""
		# Sensible heat balance (air temperature)
		dT = (Q_led + Q_people + Q_equip - Q_HVAC_sens - self.UA * (self.T_air - T_out)) * dt / self.C_air

		self.T_air += dT
		# Clamp T_air to physical range and warn if runaway
		if not math.isfinite(self.T_air) or self.T_air < -10 or self.T_air > 50:
			print(f"[WARNING] T_air runaway: {self.T_air:.2f} C, clamping to [0,40]")
			self.T_air = min(max(self.T_air, 0.0), 40.0)

		# Solution temperature (thermal mass)
		UA_nutr = 20.0  # W/K, tunable conductance between air and solution
		dT_nutr = (UA_nutr * (self.T_air - self.T_nutr) + E_solution) * dt / self.C_nutr

		self.T_nutr += dT_nutr
		# Clamp T_nutr to physical range and warn if runaway
		if not math.isfinite(self.T_nutr) or self.T_nutr < -10 or self.T_nutr > 50:
			print(f"[WARNING] T_nutr runaway: {self.T_nutr:.2f} C, clamping to [0,40]")
			self.T_nutr = min(max(self.T_nutr, 0.0), 40.0)

		# Improved transpiration model
		if E_canopy is None:
			vpd = vpd_kpa(self.T_air, self._RH())
			E_canopy = self.g_c * vpd * LAI  # g/s

		# Latent balance (absolute humidity)
		# Convert E_canopy, E_solution, infiltration (g/s) to mol/s
		dn = (E_canopy + E_solution - Q_HVAC_lat/self.M_v - infiltration) * dt / self.M_v
		self.n_vapor = max(self.n_vapor + dn, 0.0)

		# CO2 state update (Michaelis-Menten uptake, light and CO2 dependent)
		Vmax = 0.8 * canopy_area  # μmol CO2/s at saturating light (tunable)
		Km = 200.0                # μmol/m2/s (half-sat PPFD)
		Kc = 800.0                # ppm (half-sat CO2)
		uptake_umol_s = Vmax * PPFD / (Km + PPFD) * (self.CO2_ppm / (Kc + self.CO2_ppm))
		uptake_mg_s = uptake_umol_s * 44e-6
		dCO2_mg = (CO2_inj - uptake_mg_s - CO2_leaks) * dt
		mg_per_ppm = 1.96 * self.V_air
		dCO2_ppm = dCO2_mg / mg_per_ppm
		self.CO2_ppm += dCO2_ppm
		self.CO2_ppm = max(self.CO2_ppm, 0.0)

	def state(self):
		return {
			'T_air': self.T_air,
			'RH': self._RH(),
			'T_nutr': self.T_nutr,
			'CO2_ppm': self.CO2_ppm
		}

