
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

app = Flask(__name__)


def load_results():
    path = OUTPUT_DIR / "risk_assessment_results.csv"

    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/summary")
def summary():
    df = load_results()

    if df.empty:
        return jsonify({
            "total": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "satellites": 0,
            "average_score": 0,
            "categories": {},
            "satellite_counts": {}
        })

    categories = (
        df["risk_category"].fillna("Unknown")
        .value_counts().to_dict()
    )

    satellite_counts = (
        df["satellite_id"].fillna("Unknown")
        .value_counts().to_dict()
    )

    return jsonify({
        "total": int(len(df)),
        "critical": int(categories.get("Critical", 0)),
        "high": int(categories.get("High", 0)),
        "medium": int(categories.get("Medium", 0)),
        "low": int(categories.get("Low", 0)),
        "satellites": int(df["satellite_id"].nunique()),
        "average_score": round(
            float(df["risk_score"].mean()), 2
        ),
        "categories": categories,
        "satellite_counts": satellite_counts
    })


@app.route("/api/records")
def records():
    df = load_results()

    if df.empty:
        return jsonify({"records": [], "total": 0})

    category = request.args.get("category", "").strip()
    satellite = request.args.get("satellite", "").strip()
    search = request.args.get("search", "").strip().lower()

    if category:
        df = df[
            df["risk_category"].astype(str).str.lower()
            == category.lower()
        ]

    if satellite:
        df = df[df["satellite_id"].astype(str) == satellite]

    if search:
        mask = df.astype(str).apply(
            lambda col: col.str.lower().str.contains(
                search, regex=False
            )
        ).any(axis=1)
        df = df[mask]

    total = len(df)
    df = df.sort_values("risk_score", ascending=False)

    df = df.head(500).where(pd.notna(df), None)

    return jsonify({
        "records": df.to_dict(orient="records"),
        "total": int(total)
    })


@app.route("/api/high-risk")
def high_risk():
    path = OUTPUT_DIR / "high_risk_records.csv"

    if not path.exists():
        return jsonify({"records": [], "total": 0})

    df = pd.read_csv(path).fillna("")
    return jsonify({
        "records": df.head(500).to_dict(orient="records"),
        "total": int(len(df))
    })


@app.route("/api/export")
def export():
    df = load_results()

    if df.empty:
        return jsonify({"error": "No results available"}), 404

    return send_file(
        OUTPUT_DIR / "risk_assessment_results.csv",
        as_attachment=True,
        download_name="space_risk_results.csv"
    )


@app.route("/api/charts/<filename>")
def charts(filename):
    allowed = {
        "risk_distribution.png",
        "satellite_records.png",
        "risk_score_distribution.png"
    }

    if filename not in allowed:
        return jsonify({"error": "Chart not found"}), 404

    path = OUTPUT_DIR / filename

    if not path.is_file():
        return jsonify({"error": "Chart not generated"}), 404

    return send_file(path, mimetype="image/png")


if __name__ == "__main__":
    app.run(debug=True)
