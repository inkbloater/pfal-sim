"""
Simulate sensor data for a hydroponic NFT system growing baby spinach.
Stores data in a CSV file and defines optimal ranges for each sensor.
"""
import csv
import random
from datetime import datetime, timedelta

# Define sensors and optimal ranges for baby spinach (hydroponics, NFT)
SENSORS = [
    {
        "name": "air_temp",
        "unit": "C",
        "optimal_range": (18, 22),  # °C
    },
    {
        "name": "humidity",
        "unit": "%",
        "optimal_range": (60, 80),  # %
    },
    {
        "name": "co2",
        "unit": "ppm",
        "optimal_range": (800, 1200),  # ppm
    },
    {
        "name": "ppfd",
        "unit": "μmol/m²/s",
        "optimal_range": (200, 400),  # μmol/m²/s
    },
    {
        "name": "solution_temp",
        "unit": "C",
        "optimal_range": (18, 22),  # °C
    },
    {
        "name": "ec",
        "unit": "mS/cm",
        "optimal_range": (1.2, 1.8),  # mS/cm
    },
    {
        "name": "ph",
        "unit": "",
        "optimal_range": (5.8, 6.2),  # pH
    },
]

CSV_FILE = "simulated_sensor_data.csv"


# Simulate data for 35 days at 10-minute intervals
num_days = 35
samples_per_day = 24 * 6  # 6 samples per hour
start_time = datetime.now().replace(minute=0, second=0, microsecond=0)
rows = []
for i in range(0, num_days * samples_per_day):
    timestamp = start_time + timedelta(minutes=10 * i)
    for sensor in SENSORS:
        low, high = sensor["optimal_range"]
        # Simulate value within optimal range ±10% noise
        value = random.uniform(low * 0.9, high * 1.1)
        rows.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "sensor_type": sensor["name"],
            "value": round(value, 2),
            "unit": sensor["unit"]
        })

# Write to CSV
with open(CSV_FILE, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["timestamp", "sensor_type", "value", "unit"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Simulated sensor data written to {CSV_FILE}")
