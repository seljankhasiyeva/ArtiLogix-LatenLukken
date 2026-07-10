import joblib
import pandas as pd
import numpy as np
from fastapi import APIRouter
from pathlib import Path

router = APIRouter()

MODEL_DIR = Path("models")

def _get_model(name: str):
    path = MODEL_DIR / name
    if not path.exists():
        return None
    return joblib.load(path)


def _build_row(region: str, target_date: pd.Timestamp, orders_df: pd.DataFrame,
               weather_df: pd.DataFrame = None) -> pd.DataFrame:
    ALL_REGIONS = [
        'Absheron','Ganja','Kalbajar','Khachmaz','Khankendi',
        'Lankaran','Nakhchivan','Qazakh','Sheki','Yevlakh'
    ]

    reg = orders_df[orders_df['region'] == region].sort_values('date')

    def lag(n):
        d = target_date - pd.Timedelta(days=n)
        r = reg[reg['date'] == d]
        return float(r['order_count'].values[0]) if len(r) > 0 else 0.0

    def roll_mean(n):
        end = target_date - pd.Timedelta(days=1)
        sub = reg[(reg['date'] >= end - pd.Timedelta(days=n-1)) & (reg['date'] <= end)]
        return float(sub['order_count'].mean()) if len(sub) > 0 else 0.0

    def roll_std(n):
        end = target_date - pd.Timedelta(days=1)
        sub = reg[(reg['date'] >= end - pd.Timedelta(days=n-1)) & (reg['date'] <= end)]
        return float(sub['order_count'].std()) if len(sub) > 1 else 0.0

    # Holiday check
    import bisect
    try:
        hol = pd.read_parquet("data/holidays.parquet")
        hol['date'] = pd.to_datetime(hol['date'])
        hol_sorted = sorted(hol['date'].tolist())
        hol_set    = set(hol_sorted)
    except Exception:
        hol_sorted = []
        hol_set    = set()

    def days_to_hol(d):
        if not hol_sorted: return 99
        d_p = pd.to_datetime(d)
        idx  = bisect.bisect_left(hol_sorted, d_p)
        best = 9999
        if idx < len(hol_sorted): best = min(best, (hol_sorted[idx]-d_p).days)
        if idx > 0:                best = min(best, abs((d_p-hol_sorted[idx-1]).days))
        return best

    # Weather 
    temp, rain, wind = 15.0, 0.0, 10.0
    avg_item, express = 3.5, 0.3
    if weather_df is not None and len(weather_df) > 0:
        yesterday = target_date - pd.Timedelta(days=1)
        wx = weather_df[(weather_df['region']==region) & (weather_df['date']==yesterday)]
        if len(wx) > 0:
            temp  = float(wx['temperature'].values[0])
            rain  = float(wx['rainfall'].values[0])
            wind  = float(wx['wind_speed'].values[0])

    d   = target_date
    dow = d.dayofweek

    return pd.DataFrame([{
        'dayofweek'        : dow,
        'month'            : d.month,
        'quarter'          : d.quarter,
        'year'             : d.year,
        'dayofyear'        : d.dayofyear,
        'week'             : int(d.isocalendar()[1]),
        'is_weekend'       : int(dow >= 5),
        'is_month_end'     : int(d.is_month_end),
        'is_holiday'       : int(d in hol_set),
        'trend'            : (d - pd.Timestamp('2020-01-01')).days,
        'sin_dow'          : np.sin(2*np.pi*dow/7),
        'cos_dow'          : np.cos(2*np.pi*dow/7),
        'sin_month'        : np.sin(2*np.pi*d.month/12),
        'cos_month'        : np.cos(2*np.pi*d.month/12),
        'lag_1'            : lag(1),
        'lag_2'            : lag(2),
        'lag_3'            : lag(3),
        'lag_7'            : lag(7),
        'lag_14'           : lag(14),
        'lag_21'           : lag(21),
        'lag_28'           : lag(28),
        'lag_364'          : lag(364),
        'lag_365'          : lag(365),
        'lag_366'          : lag(366),
        'rolling_mean_3'   : roll_mean(3),
        'rolling_mean_7'   : roll_mean(7),
        'rolling_mean_14'  : roll_mean(14),
        'rolling_mean_28'  : roll_mean(28),
        'rolling_std_3'    : roll_std(3),
        'rolling_std_7'    : roll_std(7),
        'rolling_std_14'   : roll_std(14),
        'rolling_std_28'   : roll_std(28),
        'rolling_mean_365' : roll_mean(365),
        'same_dow_last_week': lag(7),
        'days_to_holiday'  : days_to_hol(d),
        'is_holiday_eve'   : int((d + pd.Timedelta(days=1)) in hol_set),
        'is_holiday_after' : int((d - pd.Timedelta(days=1)) in hol_set),
        'temperature'      : temp,
        'rainfall'         : rain,
        'wind_speed'       : wind,
        'avg_item_count'   : avg_item,
        'express_ratio'    : express,
        'region_enc'       : ALL_REGIONS.index(region) if region in ALL_REGIONS else 0,
    }])


def _load_orders():
    try:
        orders = pd.read_parquet("data/orders.parquet")
        orders['created_at'] = pd.to_datetime(orders['created_at'])
        orders['date'] = orders['created_at'].dt.normalize()
        return orders.groupby(['date','region']).size().reset_index(name='order_count')
    except Exception:
        return pd.DataFrame(columns=['date','region','order_count'])

def _load_weather():
    try:
        # Əgər hava durumu faylın varsa bura oxunacaq
        wx = pd.read_parquet("data/weather.parquet")
        wx['date'] = pd.to_datetime(wx['date']).dt.normalize()
        return wx
    except Exception:
        return None


@router.get("/forecast")
def get_forecast(region: str, date_from: str = None, weeks: int = 1):
    model = _get_model("target1_XGBoost_Tuned_best.joblib")
    orders_agg = _load_orders()
    weather_df = _load_weather()
    target_date = pd.Timestamp(date_from) if date_from else pd.Timestamp.today().normalize()

    results = []
    for i in range(weeks):
        d = target_date + pd.Timedelta(weeks=i)
        if model:
            X    = _build_row(region, d, orders_agg, weather_df)
            pred = max(0, float(model.predict(X)[0]))
        else:
            pred = 42.0
        results.append({"week": d.strftime("%Y-%m-%d"), "forecast_orders": round(pred), "estimated_desi": round(pred*8)})

    if not results:
        return {"error": "No results generated"}

    return {
        "region"         : region,
        "date_from"      : target_date.strftime("%Y-%m-%d"),
        "weeks"          : weeks,
        "forecast_orders": results[0]["forecast_orders"],
        "estimated_desi" : results[0]["estimated_desi"],
        "weekly_breakdown": results,
        "model"          : "target1_XGBoost_Tuned_best" if model else "mock",
    }


@router.get("/load")
def get_load(region: str, date_from: str = None, weeks: int = 1):
    model = _get_model("target2_XGBoost_Tuned_best.joblib")
    orders_agg = _load_orders()
    weather_df = _load_weather()
    target_date = pd.Timestamp(date_from) if date_from else pd.Timestamp.today().normalize()

    results = []
    for i in range(weeks):
        d = target_date + pd.Timedelta(weeks=i)
        if model:
            X    = _build_row(region, d, orders_agg, weather_df)
            pred = max(0, float(model.predict(X)[0]))
        else:
            pred = 336.0
        results.append({"week": d.strftime("%Y-%m-%d"), "item_count_sum": round(pred)})

    if not results:
        return {"error": "No results generated"}

    return {
        "region"        : region,
        "date_from"     : target_date.strftime("%Y-%m-%d"),
        "item_count_sum": results[0]["item_count_sum"],
        "estimated_desi": round(results[0]["item_count_sum"] * 0.8),
        "weekly_breakdown": results,
        "model"         : "target2_XGBoost_Tuned_best" if model else "mock",
    }