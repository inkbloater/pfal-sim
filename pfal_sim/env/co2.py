
"""
Minimal CO2 physics for PFAL simulation
Models CO2 concentration dynamics in a closed room with injection, uptake, and leaks.
"""

from dataclasses import dataclass
import math

@dataclass
class CO2Box:
	CO2_ppm: float      # Current CO2 concentration (ppm)
	V_room: float = 100.0  # Room volume (m3)

	def update(self,
			   CO2_inj: float,      # CO2 injection rate (mg/s)
			   PPFD: float,         # Canopy PPFD (μmol/m2/s)
			   canopy_area: float,  # m2
			   leaks: float,        # CO2 loss rate (mg/s)
			   dt: float = 60.0):   # timestep (s)
		"""
		Advance CO2 concentration by one timestep.
		- CO2_inj: injection rate (mg/s)
		- PPFD: canopy PPFD (μmol/m2/s)
		- canopy_area: m2
		- leaks: loss rate (mg/s)
		- dt: timestep (s)
		"""
		# Michaelis-Menten-like canopy uptake (μmol/s)
		# Parameters: max uptake rate and half-sat PPFD
		Vmax = 0.8 * canopy_area  # μmol CO2/s at saturating light (tunable)
		Km = 200.0                # μmol/m2/s (half-sat PPFD)
		uptake_umol_s = Vmax * PPFD / (Km + PPFD)
		# Convert uptake to mg/s (1 μmol CO2 = 44e-6 mg)
		uptake_mg_s = uptake_umol_s * 44e-6

		# Net CO2 change (mg/s)
		dCO2_mg = (CO2_inj - uptake_mg_s - leaks) * dt

		# Convert mg to ppm: 1 ppm = 1.96 mg/m3 for CO2 at 25C
		mg_per_ppm = 1.96 * self.V_room
		dCO2_ppm = dCO2_mg / mg_per_ppm
		self.CO2_ppm += dCO2_ppm
		self.CO2_ppm = max(self.CO2_ppm, 0.0)

	def state(self):
		return {
			'CO2_ppm': self.CO2_ppm
		}

