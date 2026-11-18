"""Groq integration with a clearly labelled demo fallback."""
import os
import json

DEMO_ANALYSIS = (
    "Demo explanation: Murree Road has the highest average traffic and AQI in the supplied sample. "
    "Review its readings and compare them with additional days of reliable measurements. "
    "These are fictional educational values, not live city measurements."
)
DEMO_RECOMMENDATIONS = [
    "Review traffic flow and signal timing in locations with consistently high traffic readings.",
    "Investigate repeated high AQI readings using verified local monitoring equipment.",
    "Collect more days of data before making long-term traffic or environmental decisions.",
    "Compare peak-day readings with weather, road work and public-event information where available."
]

def ai_status():
    return {"mode": "live" if os.getenv("GROQ_API_KEY") and os.getenv("GROQ_MODEL") else "demo",
            "message": "Live Groq AI is configured." if os.getenv("GROQ_API_KEY") and os.getenv("GROQ_MODEL")
            else "Live AI is not configured. Demo responses are being used."}

def _ask_groq(system_prompt, user_prompt):
    key, model = os.getenv("GROQ_API_KEY", "").strip(), os.getenv("GROQ_MODEL", "").strip()
    if not key or not model:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=key, timeout=30.0, max_retries=1)
        result = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=0.3,
            max_tokens=1200
        )
        return result.choices[0].message.content.strip()
    except Exception:
        # Do not send credentials or raw provider errors to the browser.
        return None

def analyze_metrics(metrics):
    prompt = ("Explain these computed smart-city statistics in beginner-friendly language. "
              "Use only supplied values. Do not invent numbers. Mention that sample values are fictional "
              "if the dataset is the built-in sample. Avoid official health or traffic instructions.")
    response = _ask_groq("You are a careful smart-city data analyst.", prompt + "\nDATA:\n" + json.dumps(metrics))
    if response:
        return {"mode": "live", "text": response}
    return {"mode": "demo", "text": DEMO_ANALYSIS}

def recommendations(metrics):
    prompt = ("Give 3 to 5 practical, informational recommendations based only on the supplied metrics. "
              "Do not claim to issue official traffic-control or public-health instructions. Do not invent numbers.")
    response = _ask_groq("You are a careful urban data assistant.", prompt + "\nDATA:\n" + json.dumps(metrics))
    if response:
        return {"mode": "live", "items": [line.strip("- •") for line in response.splitlines() if line.strip()][:5]}
    return {"mode": "demo", "items": DEMO_RECOMMENDATIONS}

def answer_question(question, metrics):
    prompt = ("Answer the user's question using only the provided computed dataset context. "
              "Never invent numerical values. If the information is absent, say it is unavailable. "
              "Keep the answer simple and concise.")
    response = _ask_groq("You answer questions about city data accurately.", prompt +
                         "\nDATA CONTEXT:\n" + json.dumps(metrics) + "\nQUESTION:\n" + question)
    if response:
        return {"mode": "live", "answer": response}
    # A deterministic demo fallback does not pretend to be live AI.
    q = question.lower()
    if "aqi" in q or "air" in q or "pollut" in q:
        answer = f"Demo answer: {metrics.get('highest_aqi_location')} has the highest average AQI in this dataset."
    elif "traffic" in q or "congest" in q:
        answer = f"Demo answer: {metrics.get('highest_traffic_location')} has the highest average traffic in this dataset."
    else:
        answer = "Demo mode cannot answer this question with a custom AI explanation. Configure Groq for live question answering, or review the dashboard statistics."
    return {"mode": "demo", "answer": answer}

def explain_analysis(selection, metrics):
    response = _ask_groq("Explain a selected smart-city metric in simple beginner-friendly language. Use only supplied data.",
                         "SELECTED ITEM:\n" + str(selection) + "\nCOMPUTED DATA:\n" + json.dumps(metrics))
    return {"mode": "live", "text": response} if response else {
        "mode": "demo", "text": "Demo explanation: This chart displays values calculated from the selected dataset. Compare locations and days to find patterns. Configure Groq for a custom AI explanation."
    }
