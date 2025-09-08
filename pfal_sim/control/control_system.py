"""
Control system for maintaining optimal conditions for baby spinach in a hydroponic NFT system.
Reads sensor data and sends control signals to actuators to adjust environmental systems.
"""
import csv
from collections import defaultdict

# Define optimal ranges for each sensor
OPTIMAL_RANGES = {
    "air_temp": (18, 22),
    "humidity": (60, 80),
    "co2": (800, 1200),
    "ppfd": (200, 400),
    "solution_temp": (18, 22),
    "ec": (1.2, 1.8),
    "ph": (5.8, 6.2),
}

# Example actuator control functions (stubs)
def control_hvac(current, target_range):
    if current < target_range[0]:
        return "HEAT_ON"
    elif current > target_range[1]:
        return "COOL_ON"
    else:
        return "HVAC_IDLE"

def control_humidifier(current, target_range):
    if current < target_range[0]:
        return "HUMIDIFY_ON"
    elif current > target_range[1]:
        return "DEHUMIDIFY_ON"
    else:
        return "HUMIDITY_IDLE"

def control_co2(current, target_range):
    if current < target_range[0]:
        return "CO2_INJECT_ON"
    elif current > target_range[1]:
        return "VENTILATE_ON"
    else:
        return "CO2_IDLE"

def control_light(current, target_range):
    if current < target_range[0]:
        return "LIGHTS_UP"
    elif current > target_range[1]:
        return "LIGHTS_DOWN"
    else:
        return "LIGHTS_IDLE"

def control_solution_temp(current, target_range):
    if current < target_range[0]:
        return "HEAT_SOLUTION_ON"
    elif current > target_range[1]:
        return "COOL_SOLUTION_ON"
    else:
        return "SOLUTION_IDLE"

def control_ec(current, target_range):
    if current < target_range[0]:
        return "ADD_NUTRIENTS"
    elif current > target_range[1]:
        return "DILUTE_SOLUTION"
    else:
        return "EC_IDLE"

def control_ph(current, target_range):
    if current < target_range[0]:
        return "ADD_PH_UP"
    elif current > target_range[1]:
        return "ADD_PH_DOWN"
    else:
        return "PH_IDLE"

# Map sensor to actuator control function
CONTROL_MAP = {
    "air_temp": control_hvac,
    "humidity": control_humidifier,
    "co2": control_co2,
    "ppfd": control_light,
    "solution_temp": control_solution_temp,
    "ec": control_ec,
    "ph": control_ph,
}

# Read latest sensor values from CSV (for each sensor, get the most recent value)

# Get sensor values for every time step (grouped by timestamp)
def get_all_sensor_timesteps(csv_file):
    timesteps = defaultdict(dict)
    with open(csv_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamp = row["timestamp"]
            sensor = row["sensor_type"]
            value = float(row["value"])
            timesteps[timestamp][sensor] = value
    return timesteps

# Main control loop (single step)
def control_step(sensor_values):
    actions = {}
    for sensor, value in sensor_values.items():
        if sensor in OPTIMAL_RANGES:
            control_fn = CONTROL_MAP[sensor]
            actions[sensor] = control_fn(value, OPTIMAL_RANGES[sensor])
    return actions

import os
from datetime import datetime

LOG_FILE = "control_actions_log.csv"

def log_actions(actions, log_file=LOG_FILE):
    log_exists = os.path.isfile(log_file)
    with open(log_file, "a", newline="") as f:
        writer = csv.writer(f)
        if not log_exists:
            writer.writerow(["timestamp", "sensor", "action"])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for sensor, action in actions.items():
            writer.writerow([timestamp, sensor, action])

if __name__ == "__main__":
    timesteps = get_all_sensor_timesteps("simulated_sensor_data.csv")
    all_actions = []
    for timestamp, sensor_values in timesteps.items():
        actions = control_step(sensor_values)
        # Print only the first and last time step for preview
        if len(all_actions) == 0 or len(all_actions) == len(timesteps) - 1:
            print(f"Timestamp: {timestamp}")
            for sensor, action in actions.items():
                print(f"  {sensor}: {action}")
        # Log actions for this time step
        # Overwrite log_actions to accept timestamp
        log_exists = os.path.isfile(LOG_FILE)
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            if not log_exists and len(all_actions) == 0:
                writer.writerow(["timestamp", "sensor", "action"])
            for sensor, action in actions.items():
                writer.writerow([timestamp, sensor, action])
        all_actions.append((timestamp, actions))
