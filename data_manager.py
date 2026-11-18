"""CSV loading and validation for the Smart City application."""
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_PATH = BASE_DIR / "data" / "sample_city_data.csv"
REQUIRED_COLUMNS = ["location", "day", "traffic", "aqi"]
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

def load_sample_data():
    return pd.read_csv(SAMPLE_PATH)

def validate_dataframe(df):
    if df.empty:
        raise ValueError("The CSV file is empty.")
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    df = df[REQUIRED_COLUMNS].copy()
    if df[REQUIRED_COLUMNS].isnull().any().any():
        raise ValueError("Missing values found. Please fill or remove incomplete rows.")
    df["location"] = df["location"].astype(str).str.strip()
    df["day"] = df["day"].astype(str).str.strip()
    if (df["location"] == "").any() or (df["day"] == "").any():
        raise ValueError("Location and day values cannot be blank.")
    for col in ["traffic", "aqi"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        if df[col].isna().any():
            raise ValueError(f"{col} contains missing or non-numeric values.")
        if (df[col] < 0).any():
            raise ValueError(f"{col} cannot contain negative values.")
    if df.duplicated(["location", "day"]).any():
        raise ValueError("Duplicate location/day rows found. Each location must have one reading per day.")
    if df["aqi"].gt(500).any():
        raise ValueError("AQI values above 500 are outside the supported sample scale.")
    if df["traffic"].gt(10_000_000).any():
        raise ValueError("Traffic values are too large to be valid for this application.")
    return df.sort_values(["location", "day"], kind="stable").reset_index(drop=True)

def read_uploaded_csv(file_storage):
    raw = file_storage.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ValueError("File is too large. Maximum upload size is 5 MB.")
    if not raw:
        raise ValueError("Please select a CSV file.")
    from io import BytesIO
    try:
        df = pd.read_csv(BytesIO(raw))
    except Exception as exc:
        raise ValueError("Could not read this CSV file. Please check its format.") from exc
    return validate_dataframe(df)

def dataframe_to_records(df):
    return df.to_dict(orient="records")
