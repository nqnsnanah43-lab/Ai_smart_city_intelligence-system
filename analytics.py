"""NumPy-based analytics, anomaly detection and simple trend estimates."""
import numpy as np

DEFAULT_TRAFFIC_THRESHOLD = 1500
DEFAULT_AQI_THRESHOLD = 150
DEFAULT_Z_THRESHOLD = 2.0

def _arrays(df):
    locations = np.array(sorted(df["location"].unique()), dtype=str)
    days = np.array(list(dict.fromkeys(df["day"].tolist())), dtype=str)
    traffic = np.full((len(locations), len(days)), np.nan, dtype=float)
    aqi = np.full_like(traffic, np.nan)
    loc_index = {v: i for i, v in enumerate(locations)}
    day_index = {v: i for i, v in enumerate(days)}
    for row in df.itertuples(index=False):
        i, j = loc_index[row.location], day_index[row.day]
        traffic[i, j], aqi[i, j] = float(row.traffic), float(row.aqi)
    return locations, days, traffic, aqi

def _stats(values):
    valid = values[np.isfinite(values)]
    if valid.size == 0:
        return {"mean": None, "median": None, "min": None, "max": None,
                "std": None, "percentile_75": None, "total": None}
    return {
        "mean": round(float(np.mean(valid)), 2),
        "median": round(float(np.median(valid)), 2),
        "min": round(float(np.min(valid)), 2),
        "max": round(float(np.max(valid)), 2),
        "std": round(float(np.std(valid)), 2),
        "percentile_75": round(float(np.percentile(valid, 75)), 2),
        "total": round(float(np.sum(valid)), 2),
    }

def _safe_mean_axis(a, axis):
    counts = np.sum(np.isfinite(a), axis=axis)
    sums = np.nansum(a, axis=axis)
    return np.divide(sums, counts, out=np.full_like(sums, np.nan, dtype=float), where=counts > 0)

def _clean(value):
    return None if not np.isfinite(value) else round(float(value), 2)

def _anomalies(locations, days, values, metric, threshold, z_threshold):
    valid = values[np.isfinite(values)]
    if valid.size == 0:
        return []
    mean, std = float(np.mean(valid)), float(np.std(valid))
    flags = []
    for i, j in zip(*np.where(np.isfinite(values))):
        value = float(values[i, j])
        reasons = []
        if threshold is not None and value > threshold:
            reasons.append(f"Above configured threshold ({threshold:g})")
        if std > 0 and abs((value - mean) / std) >= z_threshold:
            reasons.append(f"Z-score is at least {z_threshold:g} in absolute value")
        if reasons:
            flags.append({
                "location": str(locations[i]), "day": str(days[j]),
                "metric": metric, "value": round(value, 2),
                "reason": "; ".join(reasons)
            })
    return flags

def analyze(df, traffic_threshold=DEFAULT_TRAFFIC_THRESHOLD,
            aqi_threshold=DEFAULT_AQI_THRESHOLD, z_threshold=DEFAULT_Z_THRESHOLD):
    locations, days, traffic, aqi = _arrays(df)
    traffic_mean = _safe_mean_axis(traffic, 1)
    aqi_mean = _safe_mean_axis(aqi, 1)
    daily_traffic = _safe_mean_axis(traffic, 0)
    daily_aqi = _safe_mean_axis(aqi, 0)
    traffic_totals = np.nansum(traffic, axis=1)
    traffic_rank = np.argsort(np.nan_to_num(traffic_mean, nan=-np.inf))[::-1]
    aqi_rank = np.argsort(np.nan_to_num(aqi_mean, nan=-np.inf))[::-1]
    high_traffic = np.isfinite(traffic) & (traffic > traffic_threshold)
    high_aqi = np.isfinite(aqi) & (aqi > aqi_threshold)
    loc_high_aqi = np.isfinite(aqi_mean) & (aqi_mean > 100)
    pct_change = np.full_like(traffic, np.nan)
    if traffic.shape[1] > 1:
        prev = traffic[:, :-1]
        pct_change[:, 1:] = np.divide(
            (traffic[:, 1:] - prev) * 100, prev,
            out=np.full_like(prev, np.nan), where=prev != 0
        )
    growth_scenario = traffic * 1.10  # broadcasting a scalar over the full array
    # Per-location adjustment example: different growth rates broadcast across days.
    location_adjustments = np.linspace(1.05, 1.12, len(locations)).reshape(-1, 1)
    adjusted_by_location = traffic * location_adjustments
    anomalies = (
        _anomalies(locations, days, traffic, "traffic", traffic_threshold, z_threshold)
        + _anomalies(locations, days, aqi, "aqi", aqi_threshold, z_threshold)
    )
    predictions = []
    x = np.arange(len(days), dtype=float)
    for i, loc in enumerate(locations):
        item = {"location": str(loc)}
        for metric, arr in [("traffic", traffic), ("aqi", aqi)]:
            mask = np.isfinite(arr[i])
            if mask.sum() >= 2:
                slope, intercept = np.polyfit(x[mask], arr[i, mask], 1)
                estimate = max(0.0, float(slope * len(days) + intercept))
                direction = "increasing" if slope > 0.5 else ("decreasing" if slope < -0.5 else "stable")
                item[metric] = {"next_day_estimate": round(estimate, 2),
                                "trend": direction, "slope_per_day": round(float(slope), 2)}
            else:
                item[metric] = {"next_day_estimate": None, "trend": "insufficient data", "slope_per_day": None}
        predictions.append(item)
    return {
        "locations": locations.tolist(), "days": days.tolist(),
        "traffic_matrix": [[_clean(v) for v in row] for row in traffic],
        "aqi_matrix": [[_clean(v) for v in row] for row in aqi],
        "array_info": {
            "traffic_ndim": int(traffic.ndim), "traffic_shape": list(traffic.shape),
            "traffic_size": int(traffic.size), "aqi_ndim": int(aqi.ndim),
            "aqi_shape": list(aqi.shape), "aqi_size": int(aqi.size)
        },
        "traffic_overall": _stats(traffic), "aqi_overall": _stats(aqi),
        "traffic_by_location": [
            {"location": str(locations[i]), "mean": _clean(traffic_mean[i]),
             "total": _clean(traffic_totals[i]), "max": _clean(np.nanmax(traffic[i])) if np.isfinite(traffic[i]).any() else None}
            for i in range(len(locations))
        ],
        "aqi_by_location": [
            {"location": str(locations[i]), "mean": _clean(aqi_mean[i]),
             "max": _clean(np.nanmax(aqi[i])) if np.isfinite(aqi[i]).any() else None}
            for i in range(len(locations))
        ],
        "daily_traffic_average": [{"day": str(days[i]), "value": _clean(daily_traffic[i])} for i in range(len(days))],
        "daily_aqi_average": [{"day": str(days[i]), "value": _clean(daily_aqi[i])} for i in range(len(days))],
        "traffic_rank": [str(locations[i]) for i in traffic_rank],
        "aqi_rank": [str(locations[i]) for i in aqi_rank],
        "highest_traffic_location": str(locations[int(np.nanargmax(traffic_mean))]) if np.isfinite(traffic_mean).any() else None,
        "highest_aqi_location": str(locations[int(np.nanargmax(aqi_mean))]) if np.isfinite(aqi_mean).any() else None,
        "high_traffic_readings": int(high_traffic.sum()), "high_aqi_readings": int(high_aqi.sum()),
        "locations_avg_aqi_above_100": [str(locations[i]) for i in np.where(loc_high_aqi)[0]],
        "traffic_percentage_changes": [[_clean(v) for v in row] for row in pct_change],
        "traffic_growth_10_percent": [[_clean(v) for v in row] for row in growth_scenario],
        "location_adjusted_traffic_scenario": [[_clean(v) for v in row] for row in adjusted_by_location],
        "anomalies": anomalies, "predictions": predictions,
        "thresholds": {"traffic": traffic_threshold, "aqi": aqi_threshold, "z_score": z_threshold},
        "note": "Sample or uploaded dataset analysis. Anomaly flags are indicators for review, not proof of an emergency. Predictions are experimental."
    }
