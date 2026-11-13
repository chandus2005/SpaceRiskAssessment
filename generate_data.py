import csv
import random
import os

# Removed random.seed(42) so data changes on every run

os.makedirs("data", exist_ok=True)

fields = [
    "record_id",
    "satellite_id",
    "altitude_km",
    "debris_distance_km",
    "velocity_kms",
    "temperature_c",
    "voltage_v",
    "radiation_level"
]

satellites = ["SAT_A", "SAT_B", "SAT_C", "SAT_D"]

with open("data/satellite_data.csv", "w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()

    for i in range(1, 1001):
        abnormal = random.random() < 0.25

        row = {
            "record_id": f"R{i:04d}",
            "satellite_id": random.choice(satellites),
            "altitude_km": round(random.uniform(400, 1200), 2),
            "debris_distance_km": round(
                random.uniform(0.1, 3) if abnormal
                else random.uniform(5, 100), 2
            ),
            "velocity_kms": round(random.uniform(6.5, 8.0), 2),
            "temperature_c": round(
                random.choice([-35, 95]) if abnormal
                else random.uniform(-10, 65), 2
            ),
            "voltage_v": round(
                random.choice([18, 36]) if abnormal
                else random.uniform(26, 30), 2
            ),
            "radiation_level": round(
                random.uniform(8, 12) if abnormal
                else random.uniform(1, 5), 2
            )
        }

        writer.writerow(row)

print("Dataset generated successfully.")
print("File: data/satellite_data.csv")
print("Total records: 1000")