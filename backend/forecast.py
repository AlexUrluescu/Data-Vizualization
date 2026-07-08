"""
forecast.py — XGBoost time-series forecasting module for Urban Bike.

Provides functions to:
  1. Build temporal features from a sensor DataFrame.
  2. Train an XGBRegressor and produce multi-step forecasts.
"""

import pandas as pd
import numpy as np
from xgboost import XGBRegressor


def build_features(df: pd.DataFrame, param: str) -> pd.DataFrame:
    """
    Accepts a DataFrame with a DatetimeIndex and a target column `param`.
    Returns a copy with lag, rolling-mean and calendar features attached.
    """
    out = df[[param]].copy()

    out["hour"] = out.index.hour
    out["day_of_week"] = out.index.dayofweek
    out["day_of_year"] = out.index.dayofyear
    out["month"] = out.index.month

    out["hour_sin"] = np.sin(2 * np.pi * out["hour"] / 24)
    out["hour_cos"] = np.cos(2 * np.pi * out["hour"] / 24)
    out["dow_sin"] = np.sin(2 * np.pi * out["day_of_week"] / 7)
    out["dow_cos"] = np.cos(2 * np.pi * out["day_of_week"] / 7)

    for lag in [1, 3, 6, 12, 24]:
        out[f"lag_{lag}h"] = out[param].shift(lag)
    out["rolling_6h"] = out[param].shift(1).rolling(6, min_periods=1).mean()
    out["rolling_24h"] = out[param].shift(1).rolling(24, min_periods=1).mean()

    return out


FEATURE_COLS = [
    "hour",
    "day_of_week",
    "day_of_year",
    "month",
    "hour_sin",
    "hour_cos",
    "dow_sin",
    "dow_cos",
    "lag_1h",
    "lag_3h",
    "lag_6h",
    "lag_12h",
    "lag_24h",
    "rolling_6h",
    "rolling_24h",
]


def train_and_forecast(
    df: pd.DataFrame,
    param: str = "pm25",
    horizon_hours: int = 24,
) -> pd.DataFrame:
    """
    End-to-end pipeline: resample → features → train → multi-step forecast.

    Parameters
    ----------
    df : pd.DataFrame
        Raw sensor data with at least 'timestamp' and `param` columns.
    param : str
        Column to forecast (e.g. 'temperature', 'humidity', 'pm25').
    horizon_hours : int
        Number of hours to forecast into the future.

    Returns
    -------
    pd.DataFrame with columns ['timestamp', 'forecast'].
    """
    if df is None or df.empty or param not in df.columns:
        return pd.DataFrame(columns=["timestamp", "forecast"])

    tmp = df[["timestamp", param]].copy()
    tmp["timestamp"] = pd.to_datetime(tmp["timestamp"])
    tmp = tmp.set_index("timestamp").sort_index()

    hourly = tmp.resample("1h").mean()
    hourly[param] = hourly[param].interpolate(method="linear", limit=3).ffill().bfill()

    if len(hourly) < 24:
        return pd.DataFrame(columns=["timestamp", "forecast"])

    featured = build_features(hourly, param)
    featured = featured.dropna()

    if len(featured) < 10:
        return pd.DataFrame(columns=["timestamp", "forecast"])

    X = featured[FEATURE_COLS]
    y = featured[param]

    model = XGBRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.1,
        objective="reg:squarederror",
        verbosity=0,
        random_state=42,
    )
    model.fit(X, y)

    history = hourly[[param]].copy()
    last_ts = history.index[-1]
    forecasts = []

    for step in range(1, horizon_hours + 1):
        next_ts = last_ts + pd.Timedelta(hours=step)

        new_row = pd.DataFrame({param: [np.nan]}, index=[next_ts])
        history = pd.concat([history, new_row])

        feat = build_features(history, param)

        row_features = feat.loc[[next_ts], FEATURE_COLS].ffill()

        if row_features.isna().any(axis=1).iloc[0]:
            row_features = row_features.fillna(0)

        pred = model.predict(row_features)[0]
        forecasts.append({"timestamp": next_ts, "forecast": float(pred)})

        history.loc[next_ts, param] = pred

    return pd.DataFrame(forecasts)
