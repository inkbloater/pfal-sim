
"""
Simulation logger and daily feature engineering for PFAL simulation.
Logs every step to Parquet and computes daily features for ML/analytics.
"""
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import os

class SimulationLogger:
	def __init__(self, log_path="sim_log.parquet"):
		self.log_path = log_path
		self.records = []

	def log_step(self, record):
		"""
		record: dict with keys: time, PPFD, DLI_so_far, T, RH, VPD, CO2, EC, pH, actuators, LED_W, HVAC_W
		actuators: dict of actuator states
		"""
		flat = record.copy()
		# Flatten actuator states
		if 'actuators' in flat:
			for k, v in flat['actuators'].items():
				flat[f'act_{k}'] = v
			del flat['actuators']
		self.records.append(flat)

	def save(self):
		df = pd.DataFrame(self.records)
		table = pa.Table.from_pandas(df)
		pq.write_table(table, self.log_path)

class DailyFeatureJob:
	def __init__(self, log_path="sim_log.parquet"):
		self.log_path = log_path
		self.df = pq.read_table(log_path).to_pandas()

	def compute_features(self):
		# Group by day
		self.df['date'] = pd.to_datetime(self.df['time']).dt.date
		features = []
		for date, group in self.df.groupby('date'):
			feat = {'date': date}
			feat['DLI'] = group['DLI_so_far'].max()
			for var in ['T', 'RH', 'VPD', 'CO2']:
				feat[f'{var}_mean'] = group[var].mean()
				feat[f'{var}_max'] = group[var].max()
			feat['hours_in_spec'] = ((group['act_HVAC'] == 'HVAC_IDLE') & (group['act_LED'] == 'LIGHTS_IDLE')).sum() * (group['time'].diff().dt.total_seconds().fillna(0)/3600).mean()
			feat['kWh_day'] = (group['LED_W'] + group['HVAC_W']).sum() / 1000 / 6  # assuming 10-min steps
			# Stage tags can be added here
			features.append(feat)
		return pd.DataFrame(features)

