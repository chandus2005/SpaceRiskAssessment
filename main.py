
import csv
import os
import math
from pyspark import SparkConf, SparkContext

DATA_PATH = "data/satellite_data.csv"
OUTPUT_DIR = "output"


def parse_record(line):
    try:
        values = next(csv.reader([line]))

        if len(values) != 8:
            return None

        record = {
            "record_id": values[0],
            "satellite_id": values[1],
            "altitude_km": float(values[2]),
            "debris_distance_km": float(values[3]),
            "velocity_kms": float(values[4]),
            "temperature_c": float(values[5]),
            "voltage_v": float(values[6]),
            "radiation_level": float(values[7])
        }

        numeric_fields = [
            "altitude_km",
            "debris_distance_km",
            "velocity_kms",
            "temperature_c",
            "voltage_v",
            "radiation_level"
        ]

        if not all(
            math.isfinite(record[field])
            for field in numeric_fields
        ):
            return None

        if (
            record["altitude_km"] <= 0
            or record["debris_distance_km"] < 0
            or record["velocity_kms"] <= 0
        ):
            return None

        if not record["record_id"] or not record["satellite_id"]:
            return None

        return record

    except (ValueError, IndexError, csv.Error):
        return None


def assess_risk(record):
    score = 0
    reasons = []

    distance = record["debris_distance_km"]
    temperature = record["temperature_c"]
    voltage = record["voltage_v"]
    radiation = record["radiation_level"]

    if distance < 1:
        score += 40
        reasons.append("Very close debris distance")
    elif distance < 5:
        score += 25
        reasons.append("Close debris distance")

    if temperature < -20 or temperature > 80:
        score += 20
        reasons.append("Abnormal temperature")

    if voltage < 24 or voltage > 32:
        score += 20
        reasons.append("Abnormal voltage")

    if radiation >= 8:
        score += 20
        reasons.append("High radiation indicator")
    elif radiation >= 5:
        score += 10
        reasons.append("Elevated radiation indicator")

    score = min(score, 100)

    if score >= 70:
        category = "Critical"
    elif score >= 45:
        category = "High"
    elif score >= 20:
        category = "Medium"
    else:
        category = "Low"

    record["risk_score"] = score
    record["risk_category"] = category
    record["risk_reasons"] = (
        "; ".join(reasons) if reasons else "No rule triggered"
    )

    return record


def main():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}. "
            "Run python generate_data.py first."
        )

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    conf = (
        SparkConf()
        .setAppName("SpaceResearchRiskAssessment")
        .setMaster("local[*]")
    )

    sc = SparkContext(conf=conf)
    sc.setLogLevel("WARN")

    try:
        print("Loading dataset using Spark RDD...")

        lines = sc.textFile(DATA_PATH)
        header = lines.first()

        parsed = (
            lines
            .filter(lambda line: line != header)
            .map(parse_record)
            .filter(lambda record: record is not None)
            .cache()
        )

        total_records = parsed.count()

        risk_rdd = parsed.map(assess_risk).cache()

        risk_counts = (
            risk_rdd
            .map(lambda r: (r["risk_category"], 1))
            .reduceByKey(lambda a, b: a + b)
            .collectAsMap()
        )

        satellite_counts = (
            risk_rdd
            .map(lambda r: (r["satellite_id"], 1))
            .reduceByKey(lambda a, b: a + b)
            .collect()
        )

        high_risk_rdd = (
            risk_rdd
            .filter(
                lambda r: r["risk_category"] in ("High", "Critical")
            )
            .sortBy(
                lambda r: r["risk_score"],
                ascending=False
            )
        )

        high_risk_records = high_risk_rdd.take(10)

        fields = [
            "record_id",
            "satellite_id",
            "altitude_km",
            "debris_distance_km",
            "velocity_kms",
            "temperature_c",
            "voltage_v",
            "radiation_level",
            "risk_score",
            "risk_category",
            "risk_reasons"
        ]

        all_records = risk_rdd.collect()

        with open(
            os.path.join(OUTPUT_DIR, "risk_assessment_results.csv"),
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(all_records)

        with open(
            os.path.join(OUTPUT_DIR, "high_risk_records.csv"),
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(high_risk_records)

        print("\n=== SPACE RESEARCH RISK ASSESSMENT ===")
        print(f"Valid records processed: {total_records}")

        print("\nRisk category summary:")
        for category in ["Low", "Medium", "High", "Critical"]:
            print(f"{category}: {risk_counts.get(category, 0)}")

        print("\nRecords by satellite:")
        for satellite, count in sorted(satellite_counts):
            print(f"{satellite}: {count}")

        print("\nTop 10 highest-risk records:")
        for record in high_risk_records:
            print(
                f"{record['record_id']} | "
                f"{record['satellite_id']} | "
                f"Score: {record['risk_score']} | "
                f"{record['risk_category']} | "
                f"{record['risk_reasons']}"
            )

        print("\nResults saved in the output folder.")

    finally:
        parsed.unpersist() if "parsed" in locals() else None
        sc.stop()


if __name__ == "__main__":
    main()

