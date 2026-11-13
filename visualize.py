
import os
import pandas as pd
import matplotlib.pyplot as plt

INPUT_FILE = "output/risk_assessment_results.csv"
OUTPUT_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_FILE)

# 1. Risk category distribution
risk_counts = (
    df["risk_category"]
    .value_counts()
    .reindex(["Low", "Medium", "High", "Critical"], fill_value=0)
)

risk_counts.plot(kind="bar")
plt.title("Space Research Risk Category Distribution")
plt.xlabel("Risk Category")
plt.ylabel("Number of Records")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "risk_distribution.png"))
plt.close()

# 2. Records by satellite
satellite_counts = df["satellite_id"].value_counts().sort_index()

satellite_counts.plot(kind="bar")
plt.title("Records Processed by Satellite")
plt.xlabel("Satellite ID")
plt.ylabel("Number of Records")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "satellite_records.png"))
plt.close()

# 3. Risk score distribution
df["risk_score"].plot(kind="hist", bins=10)
plt.title("Distribution of Space Risk Scores")
plt.xlabel("Risk Score")
plt.ylabel("Number of Records")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "risk_score_distribution.png"))
plt.close()

print("Visualizations generated successfully.")

for filename in [
    "risk_distribution.png",
    "satellite_records.png",
    "risk_score_distribution.png",
]:
    print(f"Saved: {os.path.join(OUTPUT_DIR, filename)}")
