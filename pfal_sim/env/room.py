
import csv
from datetime import datetime, timedelta




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


# Main block at the end
if __name__ == "__main__":
	room = RoomBox(T_air=20.0, RH=0.7, T_nutr=20.0)
	T_out = 15.0
	Q_led = 1000.0      # W
	Q_people = 100.0    # W
	Q_equip = 50.0      # W
	Q_HVAC_sens = 800.0 # W
	Q_HVAC_lat = 200.0  # W
	E_canopy = 10.0     # g/s
	E_solution = 2.0    # g/s
	infiltration = 1.0  # g/s
	dt = 60.0           # 1 min
	num_days = 35
	steps = int((24*60*60*num_days) / dt)
	start_time = datetime.now().replace(minute=0, second=0, microsecond=0)
	csv_file = "room_simulation_results.csv"
	with open(csv_file, "w", newline="") as f:
		writer = csv.writer(f)
		writer.writerow(["timestamp", "T_air", "RH", "T_nutr"])
		for step in range(steps):
			room.update(Q_led, Q_people, Q_equip, Q_HVAC_sens, Q_HVAC_lat, T_out, E_canopy, E_solution, infiltration, dt)
			timestamp = start_time + timedelta(seconds=step*dt)
			s = room.state()
			writer.writerow([timestamp.strftime("%Y-%m-%d %H:%M:%S"), s['T_air'], s['RH'], s['T_nutr']])
	print(f"Room simulation results saved to: {csv_file}")

	def state(self):
		return {
			'T_air': self.T_air,
			'RH': self.RH,
			'T_nutr': self.T_nutr
		}

