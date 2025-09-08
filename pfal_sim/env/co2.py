"""
Minimal CO2 physics for PFAL room (box model)
Simulates CO2 concentration over 35 days and saves results to a CSV file in the project root.
"""
import csv
from datetime import datetime, timedelta

class CO2Box:
	def __init__(self, CO2_ppm=800.0, V_air=100.0):
		self.CO2_ppm = CO2_ppm  # initial CO2 concentration (ppm)
		self.V_air = V_air      # room air volume (m3)
		self.CO2_mol = self.CO2_ppm * 1e-6 * 44.6 * self.V_air  # mol (approx)

	def update(self, CO2_inj=0.0, canopy_uptake=0.0, leaks=0.0, dt=60.0):
		"""
		CO2_inj: mol/s injected
		canopy_uptake: mol/s consumed by plants
		leaks: mol/s lost to leaks
		dt: timestep in seconds
		"""
		dCO2 = (CO2_inj - canopy_uptake - leaks) * dt
		self.CO2_mol += dCO2
		# Convert back to ppm for output
		self.CO2_ppm = (self.CO2_mol / (44.6 * self.V_air)) * 1e6
		return self.CO2_ppm

if __name__ == "__main__":
	# Simulation parameters
	V_air = 100.0  # m3
	co2 = CO2Box(CO2_ppm=800.0, V_air=V_air)
	dt = 60.0  # 1 min
	num_days = 35
	steps = int((24*60*60*num_days) / dt)
	start_time = datetime.now().replace(minute=0, second=0, microsecond=0)
	csv_file = "co2_simulation_results.csv"

	# Example: constant injection, uptake, and leak (can be replaced with more realistic logic)
	CO2_inj = 0.01  # mol/s injected
	leaks = 0.002   # mol/s lost
	# Michaelis-Menten-like uptake: Vmax * PPFD/(K+PPFD), here we use a simple constant for demo
	Vmax = 0.008    # mol/s
	K = 300         # umol/m2/s (not used in this simple demo)
	PPFD = 250      # umol/m2/s (not used in this simple demo)
	canopy_uptake = Vmax  # constant for now

	with open(csv_file, "w", newline="") as f:
		writer = csv.writer(f)
		writer.writerow(["timestamp", "CO2_ppm"])
		for step in range(steps):
			ppm = co2.update(CO2_inj=CO2_inj, canopy_uptake=canopy_uptake, leaks=leaks, dt=dt)
			timestamp = start_time + timedelta(seconds=step*dt)
			writer.writerow([timestamp.strftime("%Y-%m-%d %H:%M:%S"), ppm])
	print(f"CO2 simulation results saved to: {csv_file}")

