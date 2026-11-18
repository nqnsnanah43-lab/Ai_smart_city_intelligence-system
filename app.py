import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
from data_manager import load_sample_data, validate_dataframe, read_uploaded_csv, dataframe_to_records
from analytics import analyze
import ai_helper
from report_generator import create_pdf

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
df_current = validate_dataframe(load_sample_data())
dataset_name = "Built-in sample dataset (fictional educational values)"

def current_metrics():
    return analyze(df_current)

def error(message, status=400):
    return jsonify({"success": False, "error": message}), status

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/dashboard")
def dashboard_api():
    m = current_metrics()
    return jsonify({"success": True, "dataset_name": dataset_name,
                    "total_locations": len(m["locations"]),
                    "average_traffic": m["traffic_overall"]["mean"],
                    "average_aqi": m["aqi_overall"]["mean"],
                    "highest_traffic_location": m["highest_traffic_location"],
                    "highest_aqi_location": m["highest_aqi_location"],
                    "high_traffic_readings": m["high_traffic_readings"],
                    "high_aqi_readings": m["high_aqi_readings"],
                    "traffic_by_location": m["traffic_by_location"],
                    "aqi_by_location": m["aqi_by_location"],
                    "daily_traffic_average": m["daily_traffic_average"],
                    "daily_aqi_average": m["daily_aqi_average"],
                    "locations": m["locations"], "days": m["days"],
                    "traffic_matrix": m["traffic_matrix"], "aqi_matrix": m["aqi_matrix"],
                    "ai_status": ai_helper.ai_status()})

@app.get("/api/traffic")
def traffic_api():
    m = current_metrics()
    return jsonify({"success": True, "locations": m["locations"], "days": m["days"],
                    "matrix": m["traffic_matrix"], "by_location": m["traffic_by_location"],
                    "daily_average": m["daily_traffic_average"]})

@app.get("/api/air-quality")
def air_quality_api():
    m = current_metrics()
    return jsonify({"success": True, "locations": m["locations"], "days": m["days"],
                    "matrix": m["aqi_matrix"], "by_location": m["aqi_by_location"],
                    "daily_average": m["daily_aqi_average"]})

@app.get("/api/analytics")
def analytics_api():
    return jsonify({"success": True, **current_metrics()})

@app.get("/api/predictions")
def predictions_api():
    return jsonify({"success": True, "predictions": current_metrics()["predictions"],
                    "note": "Experimental estimates based on a simple linear trend over the available days."})

@app.post("/api/upload-dataset")
def upload_dataset():
    global df_current, dataset_name
    file = request.files.get("file")
    if not file or not file.filename:
        return error("Choose a CSV file first.")
    if not file.filename.lower().endswith(".csv"):
        return error("Only CSV files are supported.")
    try:
        candidate = read_uploaded_csv(file)
    except ValueError as exc:
        return error(str(exc))
    df_current = candidate
    dataset_name = "Uploaded dataset: " + Path(file.filename).name
    return jsonify({"success": True, "message": "Dataset uploaded successfully.", "dataset_name": dataset_name})

@app.post("/api/restore-sample")
def restore_sample():
    global df_current, dataset_name
    df_current = validate_dataframe(load_sample_data())
    dataset_name = "Built-in sample dataset (fictional educational values)"
    return jsonify({"success": True, "message": "Original sample dataset restored.", "dataset_name": dataset_name})

@app.post("/api/ai/analyze")
def ai_analyze():
    return jsonify({"success": True, **ai_helper.analyze_metrics(current_metrics())})

@app.post("/api/ai/recommendations")
def ai_recommendations():
    return jsonify({"success": True, **ai_helper.recommendations(current_metrics())})

@app.post("/api/ai/ask")
def ai_ask():
    body = request.get_json(silent=True) or {}
    question = str(body.get("question", "")).strip()
    if not question:
        return error("Please enter a question.")
    if len(question) > 1000:
        return error("Question is too long. Maximum length is 1000 characters.")
    return jsonify({"success": True, **ai_helper.answer_question(question, current_metrics())})

@app.post("/api/ai/explain")
def ai_explain():
    body = request.get_json(silent=True) or {}
    selection = body.get("selection", "Overall dashboard")
    if not isinstance(selection, (str, dict, list)):
        return error("Invalid analysis selection.")
    return jsonify({"success": True, **ai_helper.explain_analysis(selection, current_metrics())})

@app.post("/api/ai/generate-report")
def ai_report():
    metrics = current_metrics()
    analysis = ai_helper.analyze_metrics(metrics)
    recs = ai_helper.recommendations(metrics)
    pdf = create_pdf(metrics, analysis, recs)
    return send_file(pdf, mimetype="application/pdf", as_attachment=True,
                     download_name="smart_city_intelligence_report.pdf")

@app.get("/api/settings")
def settings_api():
    return jsonify({"success": True, "ai": ai_helper.ai_status(),
                    "dataset_name": dataset_name,
                    "upload_limit_mb": 5,
                    "required_csv_columns": ["location", "day", "traffic", "aqi"]})

@app.errorhandler(413)
def too_large(_):
    return error("Upload too large. Maximum file size is 5 MB.", 413)

@app.errorhandler(500)
def server_error(_):
    return error("An unexpected server error occurred. Please try again.", 500)

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
