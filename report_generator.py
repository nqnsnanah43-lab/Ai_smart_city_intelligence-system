"""Create downloadable PDF intelligence reports."""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

def create_pdf(metrics, ai_analysis, recs):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = [Paragraph("AI-Powered Smart City Intelligence Report", styles["Title"]),
             Paragraph("Educational analysis generated from the currently loaded dataset.", styles["Italic"]),
             Spacer(1, 14),
             Paragraph("1. Executive Summary", styles["Heading2"]),
             Paragraph(f"Highest average traffic: {metrics.get('highest_traffic_location')}. "
                       f"Highest average AQI: {metrics.get('highest_aqi_location')}.", styles["BodyText"]),
             Spacer(1, 8),
             Paragraph("2. Traffic Analysis", styles["Heading2"])]
    rows = [["Location", "Average traffic", "Total traffic"]]
    totals = {x["location"]: x["total"] for x in metrics["traffic_by_location"]}
    for item in metrics["traffic_by_location"]:
        rows.append([item["location"], str(item["mean"]), str(totals[item["location"]])])
    table = Table(rows, repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#14532d")),
                               ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                               ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
                               ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f0fdf4")])]))
    story += [table, Spacer(1, 10), Paragraph("3. Air Quality Analysis", styles["Heading2"])]
    for item in metrics["aqi_by_location"]:
        story.append(Paragraph(f"{item['location']}: average AQI {item['mean']}, maximum {item['max']}.", styles["BodyText"]))
    story += [Spacer(1, 8), Paragraph("4. Detected Anomalies", styles["Heading2"])]
    if metrics["anomalies"]:
        for a in metrics["anomalies"][:30]:
            story.append(Paragraph(f"{a['location']} / {a['day']} — {a['metric']}: {a['value']} ({a['reason']})", styles["BodyText"]))
    else:
        story.append(Paragraph("No readings were flagged using the current thresholds.", styles["BodyText"]))
    story += [Spacer(1, 8), Paragraph("5. Experimental Trend Estimates", styles["Heading2"])]
    for p in metrics["predictions"]:
        story.append(Paragraph(f"{p['location']}: traffic {p['traffic']['next_day_estimate']} ({p['traffic']['trend']}), "
                               f"AQI {p['aqi']['next_day_estimate']} ({p['aqi']['trend']}).", styles["BodyText"]))
    story += [Spacer(1, 8), Paragraph("6. AI Analysis", styles["Heading2"]),
              Paragraph((ai_analysis or {}).get("text", "Not generated."), styles["BodyText"]),
              Spacer(1, 8), Paragraph("7. Recommendations", styles["Heading2"])]
    for r in (recs or {}).get("items", []):
        story.append(Paragraph("• " + str(r), styles["BodyText"]))
    story += [Spacer(1, 10), Paragraph("8. Limitations and Data Quality Notes", styles["Heading2"]),
              Paragraph("Built-in values are fictional educational sample data, not live measurements. "
                        "Uploaded CSV data depends on the quality and completeness of its source. "
                        "Anomaly flags are indicators for review, not proof of an emergency. "
                        "Linear estimates based on seven days are experimental and are not reliable production forecasts. "
                        "Missing values are rejected during upload rather than silently replaced with zero.", styles["BodyText"])]
    doc.build(story)
    buffer.seek(0)
    return buffer
