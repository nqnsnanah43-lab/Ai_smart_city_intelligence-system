# AI-Powered Smart City Intelligence System

A student-friendly Flask application that analyzes traffic and Air Quality Index (AQI) readings with NumPy and optionally explains the results using Groq AI.

## Features
- Responsive dashboard and Chart.js charts.
- NumPy statistics, ranking, vectorized percentage changes and broadcasting examples.
- Threshold and Z-score anomaly flags.
- Experimental next-day linear trend estimates using `numpy.polyfit`.
- CSV upload with validation (5 MB limit; missing/non-numeric values rejected).
- Groq analysis, recommendations and Q&A, with clearly labelled demo fallback.
- PDF report download.
- Restore the built-in fictional sample dataset.

## Dataset format
CSV columns are exactly: `location,day,traffic,aqi`. Each location/day pair must be unique. Traffic and AQI must be numeric and non-negative. Missing values are rejected; they are not silently changed to zero.

The built-in Saddar, Commercial Market, Murree Road and Satellite Town values are fictional educational examples, not live measurements.

## Windows setup (VS Code / PowerShell)
1. Install Python 3.10 or newer and Git.
2. Open this project folder in VS Code.
3. Open Terminal > New Terminal.
4. Create a virtual environment:

   ```powershell
   python -m venv venv
   ```

5. Activate it:

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt instead:

   ```bat
   venv\Scripts\activate
   ```

6. Install packages:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

7. Copy `.env.example` to `.env`. On Windows Command Prompt:

   ```bat
   copy .env.example .env
   ```

   Open `.env` and set your own Groq API key and a currently supported model ID shown in your Groq account/model documentation:

   ```env
   GROQ_API_KEY=your_real_key
   GROQ_MODEL=your_current_supported_model_id
   ```

   Leave both values blank to use Demo Mode. Do not commit `.env`.

8. Run:

   ```powershell
   python app.py
   ```

9. Open http://127.0.0.1:5000 in your browser.

## Test both AI modes
- Demo: remove/blank `GROQ_API_KEY` and `GROQ_MODEL`, restart Flask, and use AI City Analyst. The interface labels fallback responses as DEMO.
- Live: set a valid key and currently supported model ID, restart Flask, then generate analysis or ask a question. If the key/model/provider is unavailable, the app safely falls back to demo mode.
- Test CSV upload with `data/sample_city_data.csv`. Required columns are `location,day,traffic,aqi`.
- Try a CSV missing a required column, containing blank cells, non-numeric traffic/AQI, duplicate location/day pairs, or a file larger than 5 MB to see validation errors.
- Use Restore sample dataset to return to the built-in sample.

## API endpoints
- `GET /api/dashboard`
- `GET /api/traffic`
- `GET /api/air-quality`
- `GET /api/analytics`
- `GET /api/predictions`
- `GET /api/settings`
- `POST /api/upload-dataset`
- `POST /api/restore-sample`
- `POST /api/ai/analyze`
- `POST /api/ai/ask` with JSON `{"question":"Which location has the highest traffic?"}`
- `POST /api/ai/recommendations`
- `POST /api/ai/explain`
- `POST /api/ai/generate-report` (returns PDF)

## Important limitations
- The built-in readings are fictional, not live sensor data.
- Z-score and threshold anomaly flags are prompts for review, not proof of an emergency.
- Seven days of data are not enough for reliable forecasting. Linear estimates are educational only.
- The in-memory active dataset resets when the Flask process restarts. This is intentional for this student demo.
- Do not send confidential data to an external LLM. AI prompts include computed dataset context.
- For production, add authentication, CSRF protection, stricter rate limits, logging, database-backed datasets and privacy review.

## GitHub
Run these commands from the project folder:

```bash
git init
git add .
git commit -m "Initial Smart City Intelligence project"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/AI_Smart_City_Intelligence.git
git push -u origin main
```

Before pushing, check that `.env` is not staged:

```bash
git status
```

If `.env` was ever committed, rotate the key and remove it from repository history; adding it to `.gitignore` afterward does not erase past commits.

## Deployment notes
Render is a straightforward option for a Flask web service. Configure the start command as `gunicorn app:app` and set `GROQ_API_KEY` and `GROQ_MODEL` in the service's environment settings. Do not upload `.env`.

This demo stores the active uploaded dataset in process memory, so it resets on restart/redeploy and may not be shared reliably across multiple workers. For durable uploads, use managed object storage or a database (for example, PostgreSQL for metadata and an object store for CSV files). Do not rely on a serverless/local filesystem for permanent user uploads. Review the current hosting provider's Python runtime, build and storage documentation before deployment.

## Screenshots
Add screenshots of your running dashboard here after launching the app, for example:
- `screenshots/dashboard.png`
- `screenshots/ai-analyst.png`
- `screenshots/report-preview.png`
