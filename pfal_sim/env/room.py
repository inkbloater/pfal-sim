
"""
Minimal thermal and moisture physics for PFAL room (box model)
Implements sensible and latent heat/moisture balances for air and solution.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class RoomBox:
	# State variables
	T_air: float  # Air temperature (C)
	RH: float     # Relative humidity (0-1)
	T_nutr: float # Solution temperature (C)

	# Room parameters
	V_air: float = 100.0      # m3, room air volume
	UA: float = 200.0         # W/K, envelope conductance
	C_air: float = 1200.0     # J/K, effective air heat capacity
	M_air: float = 120.0      # mol, air moles (approx for 100 m3)
	M_v: float = 18.0         # g/mol, molar mass of water vapor

	def update(self,
			   Q_led: float,
			   Q_people: float,
			   Q_equip: float,
			   Q_HVAC_sens: float,
			   Q_HVAC_lat: float,
			   T_out: float,
			   E_canopy: float,
			   E_solution: float,
			   infiltration: float,
			   dt: float = 60.0):
		"""
		Advance the room state by one timestep (dt seconds).
		All Q in W (J/s), E in g/s, dt in seconds.
		"""
		# Sensible heat balance (air temperature)
		dT = (Q_led + Q_people + Q_equip - Q_HVAC_sens - self.UA * (self.T_air - T_out)) * dt / self.C_air
		self.T_air += dT

		# Latent balance (humidity ratio, simplified)
		# Convert E_canopy, E_solution, infiltration (g/s) to mol/s
		dw = (E_canopy + E_solution - Q_HVAC_lat/self.M_v - infiltration) * dt / (self.M_air * self.M_v)
		# Convert RH to humidity ratio (approx, not exact psychrometrics)
		self.RH = min(max(self.RH + dw, 0.0), 1.0)

		# Solution temperature (simple balance, can be expanded)
		# For now, assume tracks air temp with some lag
		self.T_nutr += 0.1 * (self.T_air - self.T_nutr)

	def state(self):
		return {
			'T_air': self.T_air,
			'RH': self.RH,
			'T_nutr': self.T_nutr
		}

