import pandas as pd
import numpy as np

def generate_period_insights(df: pd.DataFrame, param: str = 'pm25') -> dict:
    if df is None or df.empty or param not in df.columns:
        return {"error": "Nu există date suficiente pentru această perioadă sau parametru."}

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour
    df['is_weekend'] = df['timestamp'].dt.dayofweek >= 5 

    insights = {}

    if param == 'temperature':
        txt_more = "mai cald"
    elif param == 'humidity':
        txt_more = "mai umed"
    else:
        txt_more = "mai poluat"

    if 'Location' in df.columns:
        if df['Location'].nunique() > 1:
            loc_means = df.groupby('Location')[param].mean()
            insights['cleanest_loc'] = loc_means.idxmin()
            insights['worst_loc'] = loc_means.idxmax()
        else:
            single_loc = df['Location'].iloc[0]
            insights['cleanest_loc'] = f"{single_loc} (Unică)"
            insights['worst_loc'] = f"{single_loc} (Unică)"
    else:
        insights['cleanest_loc'] = "N/A"
        insights['worst_loc'] = "N/A"

    max_idx = df[param].idxmax()
    worst_row = df.loc[max_idx]
    
    if isinstance(worst_row, pd.DataFrame):
        worst_row = worst_row.iloc[0]
    
    insights['worst_day_date'] = worst_row['timestamp'].strftime("%d %b %Y")
    insights['worst_day_val'] = round(worst_row[param], 1)

    hourly_mean = df.groupby('hour')[param].mean()
    worst_hour = hourly_mean.idxmax()
    insights['worst_hour_interval'] = f"{worst_hour:02d}:00 - {(worst_hour+1)%24:02d}:00"

    weekend_mean = df[df['is_weekend']][param].mean()
    weekday_mean = df[~df['is_weekend']][param].mean()
    
    if pd.isna(weekend_mean) or pd.isna(weekday_mean) or weekend_mean == 0:
         insights['weekend_comparison'] = "Date insuficiente pentru comparație weekend."
    else:
        if weekday_mean > weekend_mean:
            diff_percent = ((weekday_mean - weekend_mean) / weekend_mean) * 100
            insights['weekend_comparison'] = f"A fost cu **{diff_percent:.0f}% {txt_more}** în timpul săptămânii comparativ cu weekendul."
        else:
            diff_percent = ((weekend_mean - weekday_mean) / weekday_mean) * 100
            insights['weekend_comparison'] = f"A fost cu **{diff_percent:.0f}% {txt_more}** în weekend!"

    return insights