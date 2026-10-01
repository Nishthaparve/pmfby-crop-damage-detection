# -*- coding: utf-8 -*-
"""
PMFBY Weather Verification Branch
=================================
Source: Google Earth Engine ECMWF/ERA5_LAND/HOURLY
Bands:
  - temperature_2m: 2m air temperature in Kelvin (converted to °C: K - 273.15)
  - total_precipitation: Hourly accumulated precipitation in meters (converted to mm: m * 1000.0)

Calculates:
  1. Event-window rainfall in mm
  2. Event-window mean temperature in °C
  3. Historical comparable-period rainfall baseline (preceding calendar years)
  4. Historical comparable-period temperature baseline
  5. Rainfall anomaly %: ((R_event - R_hist) / max(R_hist, 1.0)) * 100.0
  6. Temperature anomaly °C: T_event - T_hist
  7. Weather consistency score (0 to 100) based on reported disaster event type
  8. Human-readable meteorological summary
  9. event_supported boolean (score >= 60.0)
  10. daily_records time-series for chart rendering
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import ee

_EE_INITIALIZED = False


def ensure_ee_initialized():
    global _EE_INITIALIZED
    if not _EE_INITIALIZED:
        try:
            ee.Initialize(project='pmfby-crop-damage-detection')
            _EE_INITIALIZED = True
        except Exception:
            try:
                ee.Initialize()
                _EE_INITIALIZED = True
            except Exception as err:
                print(f"[weather_analysis] Earth Engine init notice: {err}")


def analyze_weather(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    event_start_date: Optional[str] = None,
    event_end_date: Optional[str] = None,
    event_type: str = "",
    crop: str = "",
    district: str = "",
    state: str = "",
) -> Dict[str, Any]:
    """
    Query GEE ECMWF/ERA5_LAND/HOURLY for location and event window.
    Compares against historical comparable period in previous years.
    Returns structured JSON with daily time-series.
    """
    empty_result = {
        "weather_available": False,
        "rainfall_mm": None,
        "historical_rainfall_mm": None,
        "rainfall_anomaly_pct": None,
        "temperature_c": None,
        "historical_temperature_c": None,
        "temperature_anomaly_c": None,
        "weather_consistency_score": None,
        "weather_summary": "Weather data unavailable",
        "event_supported": None,
        "daily_records": [],
        "dataset": "ECMWF/ERA5_LAND/HOURLY",
        "bands": ["temperature_2m", "total_precipitation"],
    }

    if latitude is None or longitude is None:
        empty_result["weather_summary"] = "Weather data unavailable: coordinates not provided."
        return empty_result

    # Date parsing
    if not event_start_date:
        empty_result["weather_summary"] = "Weather data unavailable: event date not specified."
        return empty_result

    try:
        s_dt = datetime.strptime(str(event_start_date).strip()[:10], "%Y-%m-%d")
        if event_end_date:
            e_dt = datetime.strptime(str(event_end_date).strip()[:10], "%Y-%m-%d")
            if e_dt <= s_dt:
                e_dt = s_dt + timedelta(days=1)
        else:
            # Default 5-day event window centered around event date
            e_dt = s_dt + timedelta(days=3)
            s_dt = s_dt - timedelta(days=2)
    except Exception:
        empty_result["weather_summary"] = "Weather data unavailable: invalid event date format."
        return empty_result

    ensure_ee_initialized()

    try:
        pt = ee.Geometry.Point([float(longitude), float(latitude)])
        s_str = s_dt.strftime("%Y-%m-%d")
        # GEE filterDate end is exclusive, add 1 day to encompass e_dt
        e_exclusive = (e_dt + timedelta(days=1)).strftime("%Y-%m-%d")

        col = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')\
            .filterBounds(pt)\
            .filterDate(s_str, e_exclusive)\
            .select(['temperature_2m', 'total_precipitation'])

        collection_size = col.size().getInfo()
        if collection_size == 0:
            empty_result["weather_summary"] = (
                "Weather data unavailable for the selected location or date range."
            )
            return empty_result

        region_data = col.getRegion(pt, 11132).getInfo()
        if not region_data or len(region_data) <= 1:
            empty_result["weather_summary"] = "Weather data unavailable for this location or date range in ERA5-Land."
            return empty_result

        header = region_data[0]
        rows = region_data[1:]
        time_idx = header.index('time')
        t2m_idx = header.index('temperature_2m')
        tp_idx = header.index('total_precipitation')

        by_day_tp = defaultdict(list)
        by_day_t2m = defaultdict(list)

        for r in rows:
            t_ms = r[time_idx]
            if t_ms is None:
                continue
            dt = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(milliseconds=t_ms)
            day_key = dt.strftime('%Y-%m-%d')
            t2m_k = r[t2m_idx]
            tp_m = r[tp_idx]
            if t2m_k is not None:
                by_day_t2m[day_key].append(t2m_k - 273.15)
            if tp_m is not None:
                by_day_tp[day_key].append(tp_m * 1000.0)

        daily_records: List[Dict[str, Any]] = []
        for day_k in sorted(by_day_tp.keys()):
            d_rain = max(by_day_tp[day_k]) if by_day_tp[day_k] else 0.0
            d_temp = sum(by_day_t2m[day_k]) / len(by_day_t2m[day_k]) if by_day_t2m[day_k] else 0.0
            daily_records.append({
                "date": day_k,
                "rainfall_mm": round(d_rain, 2),
                "temperature_c": round(d_temp, 2)
            })

        if not daily_records:
            empty_result["weather_summary"] = "Weather data unavailable: no daily records retrieved."
            return empty_result

        rainfall_mm = round(sum(d["rainfall_mm"] for d in daily_records), 2)
        temperature_c = round(sum(d["temperature_c"] for d in daily_records) / len(daily_records), 2)

        # -------------------------------------------------------------
        # HISTORICAL BASELINE: Same calendar period in preceding 2 years
        # -------------------------------------------------------------
        hist_years = [1, 2]
        hist_rain_samples = []
        hist_temp_samples = []

        for y_offset in hist_years:
            try:
                h_s = s_dt.replace(year=s_dt.year - y_offset).strftime("%Y-%m-%d")
                h_e = (e_dt.replace(year=e_dt.year - y_offset) + timedelta(days=1)).strftime("%Y-%m-%d")
                h_col = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')\
                    .filterBounds(pt)\
                    .filterDate(h_s, h_e)\
                    .select(['temperature_2m', 'total_precipitation'])
                historical_size = h_col.size().getInfo()
                if historical_size == 0:
                    continue
                h_data = h_col.getRegion(pt, 11132).getInfo()
                if h_data and len(h_data) > 1:
                    h_rows = h_data[1:]
                    h_by_day_tp = defaultdict(list)
                    h_by_day_t2m = defaultdict(list)
                    for hr in h_rows:
                        t_ms = hr[time_idx]
                        if t_ms is None:
                            continue
                        dt = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(milliseconds=t_ms)
                        d_k = dt.strftime('%Y-%m-%d')
                        if hr[t2m_idx] is not None:
                            h_by_day_t2m[d_k].append(hr[t2m_idx] - 273.15)
                        if hr[tp_idx] is not None:
                            h_by_day_tp[d_k].append(hr[tp_idx] * 1000.0)
                    yr_rain = sum(max(h_by_day_tp[k]) for k in h_by_day_tp if h_by_day_tp[k])
                    yr_temps = [sum(h_by_day_t2m[k])/len(h_by_day_t2m[k]) for k in h_by_day_t2m if h_by_day_t2m[k]]
                    yr_temp = sum(yr_temps)/len(yr_temps) if yr_temps else 25.0
                    hist_rain_samples.append(yr_rain)
                    hist_temp_samples.append(yr_temp)
            except Exception as e_hist:
                print(f"[weather_analysis] Baseline sample year offset -{y_offset} notice: {e_hist}")

        if hist_rain_samples:
            historical_rainfall_mm = round(
                sum(hist_rain_samples) / len(hist_rain_samples), 2
            )
            historical_temperature_c = round(
                sum(hist_temp_samples) / len(hist_temp_samples), 2
            )
        else:
            empty_result["weather_summary"] = (
                "Weather observations are available, but the historical baseline is unavailable for the selected period."
            )
            return empty_result

        # -------------------------------------------------------------
        # ANOMALIES
        # -------------------------------------------------------------
        baseline_rain_denom = max(historical_rainfall_mm, 1.0)
        rainfall_anomaly_pct = round(((rainfall_mm - historical_rainfall_mm) / baseline_rain_denom) * 100.0, 1)
        temperature_anomaly_c = round(temperature_c - historical_temperature_c, 2)

        # -------------------------------------------------------------
        # WEATHER CONSISTENCY SCORE (0 to 100) & EVENT SUPPORT
        # -------------------------------------------------------------
        ev_type = str(event_type or "").lower()
        score = 70.0

        if any(w in ev_type for w in ["excess", "flood", "heavy", "rain", "inundation"]):
            if rainfall_anomaly_pct >= 50.0:
                score = min(98.0, 75.0 + (rainfall_anomaly_pct - 50.0) * 0.3)
            elif rainfall_anomaly_pct >= 0.0:
                score = 65.0 + (rainfall_anomaly_pct / 50.0) * 10.0
            elif rainfall_anomaly_pct >= -30.0:
                score = 45.0 + (rainfall_anomaly_pct + 30.0) * 0.6
            else:
                score = max(15.0, 45.0 + rainfall_anomaly_pct * 0.4)

        elif any(w in ev_type for w in ["drought", "dry", "deficit"]):
            if rainfall_anomaly_pct <= -50.0:
                score = min(98.0, 80.0 + abs(rainfall_anomaly_pct + 50.0) * 0.3)
            elif rainfall_anomaly_pct <= -15.0:
                score = 65.0 + (abs(rainfall_anomaly_pct) - 15.0) * 0.4
            elif rainfall_anomaly_pct <= 10.0:
                score = 50.0
            else:
                score = max(15.0, 40.0 - rainfall_anomaly_pct * 0.5)

        elif any(w in ev_type for w in ["heat", "temperature", "scorch"]):
            if temperature_anomaly_c >= 2.5:
                score = min(98.0, 80.0 + (temperature_anomaly_c - 2.5) * 6.0)
            elif temperature_anomaly_c >= 0.5:
                score = 65.0 + (temperature_anomaly_c - 0.5) * 7.5
            elif temperature_anomaly_c >= -1.0:
                score = 50.0
            else:
                score = max(20.0, 40.0 + temperature_anomaly_c * 10.0)

        elif any(w in ev_type for w in ["hail", "storm", "cyclone", "unseasonal"]):
            max_daily_rain = max((d["rainfall_mm"] for d in daily_records), default=0.0)
            if max_daily_rain >= 25.0:
                score = min(95.0, 75.0 + max_daily_rain * 0.4)
            else:
                score = 55.0

        elif any(w in ev_type for w in ["pest", "disease", "insect"]):
            if temperature_c >= 22.0 and rainfall_mm >= 15.0:
                score = 78.0
            else:
                score = 65.0
        else:
            score = 72.0

        weather_consistency_score = round(max(0.0, min(100.0, score)), 1)
        event_supported = bool(weather_consistency_score >= 60.0)

        # -------------------------------------------------------------
        # HUMAN-READABLE SUMMARY
        # -------------------------------------------------------------
        ev_name = event_type if event_type else "reported agricultural event"
        support_str = "corroborate" if event_supported else "show low correlation with"
        summary = (
            f"During the {len(daily_records)}-day event window ({daily_records[0]['date']} to {daily_records[-1]['date']}), "
            f"ERA5-Land recorded {rainfall_mm} mm total rainfall (anomaly: {rainfall_anomaly_pct:+.1f}%) and "
            f"{temperature_c}°C mean temperature (anomaly: {temperature_anomaly_c:+.2f}°C) relative to the "
            f"historical baseline ({historical_rainfall_mm} mm, {historical_temperature_c}°C). "
            f"Meteorological observations {support_str} the {ev_name}."
        )

        return {
            "weather_available": True,
            "rainfall_mm": rainfall_mm,
            "historical_rainfall_mm": historical_rainfall_mm,
            "rainfall_anomaly_pct": rainfall_anomaly_pct,
            "temperature_c": temperature_c,
            "historical_temperature_c": historical_temperature_c,
            "temperature_anomaly_c": temperature_anomaly_c,
            "weather_consistency_score": weather_consistency_score,
            "weather_summary": summary,
            "event_supported": event_supported,
            "daily_records": daily_records,
            "dataset": "ECMWF/ERA5_LAND/HOURLY",
            "bands": ["temperature_2m", "total_precipitation"],
        }

    except Exception as e:
        return {
            "weather_available": False,
            "rainfall_mm": None,
            "historical_rainfall_mm": None,
            "rainfall_anomaly_pct": None,
            "temperature_c": None,
            "historical_temperature_c": None,
            "temperature_anomaly_c": None,
            "weather_consistency_score": None,
            "weather_summary": f"Weather data unavailable: {str(e)}",
            "event_supported": None,
            "daily_records": [],
            "dataset": "ECMWF/ERA5_LAND/HOURLY",
            "bands": ["temperature_2m", "total_precipitation"],
        }
