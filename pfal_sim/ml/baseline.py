
"""
ML baselines for PFAL simulation analytics.
Goal 1: Predict next-day harvestable fresh weight (FW) per m² from last N days’ features (ridge/XGB).
Goal 2: Classify tipburn risk from “hours above VPD/T limits” + DLI overshoot.
Goal 3: Predict kWh/kg for scenario comparison.
"""
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score

# --- Goal 1: Predict next-day FW per m² ---
def train_fw_regression(features_df, target_col='FW_next_day', N=7, model_type='ridge'):
	# Use last N days' features to predict next-day FW
	X = []
	y = []
	for i in range(N, len(features_df)):
		X.append(features_df.iloc[i-N:i].values.flatten())
		y.append(features_df.iloc[i][target_col])
	X = pd.DataFrame(X)
	y = pd.Series(y)
	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
	if model_type == 'ridge':
		model = Ridge()
	else:
		model = GradientBoostingRegressor()
	model.fit(X_train, y_train)
	y_pred = model.predict(X_test)
	mse = mean_squared_error(y_test, y_pred)
	return model, mse

# --- Goal 2: Classify tipburn risk ---
def train_tipburn_classifier(features_df, target_col='tipburn_risk', N=7):
	# Use last N days' features to classify tipburn risk
	X = []
	y = []
	for i in range(N, len(features_df)):
		X.append(features_df.iloc[i-N:i][['hours_above_VPD_limit','hours_above_T_limit','DLI_overshoot']].values.flatten())
		y.append(features_df.iloc[i][target_col])
	X = pd.DataFrame(X)
	y = pd.Series(y)
	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
	model = GradientBoostingClassifier()
	model.fit(X_train, y_train)
	y_pred = model.predict(X_test)
	acc = accuracy_score(y_test, y_pred)
	return model, acc

# --- Goal 3: Predict kWh/kg ---
def train_kwh_per_kg_regression(features_df, target_col='kWh_per_kg', N=7, model_type='ridge'):
	# Use last N days' features to predict kWh/kg
	X = []
	y = []
	for i in range(N, len(features_df)):
		X.append(features_df.iloc[i-N:i].values.flatten())
		y.append(features_df.iloc[i][target_col])
	X = pd.DataFrame(X)
	y = pd.Series(y)
	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
	if model_type == 'ridge':
		model = Ridge()
	else:
		model = GradientBoostingRegressor()
	model.fit(X_train, y_train)
	y_pred = model.predict(X_test)
	mse = mean_squared_error(y_test, y_pred)
	return model, mse

