import requests
import pandas as pd
from datetime import datetime, timedelta
import os
from db import get_cached_range, get_cached_boundaries, save_to_db, is_range_fetched, mark_range_fetched

API_URL   = os.getenv("API_URL")
USER_ID   = os.getenv("USER_ID")
USER_HASH = os.getenv("USER_HASH")

TOLERANCE_SECONDS = 120

def fetch_location_data(
    device_id: str,
    location: str,
    start_dt: datetime,
    end_dt: datetime,
) -> pd.DataFrame:
    print(f"\n{'='*60}")
    print(f"📡 fetch_location_data | {location} ({device_id})")
    print(f"   Requested range : {start_dt} → {end_dt}")

    cached_min, cached_max = get_cached_boundaries(device_id, start_dt, end_dt)
    initial_fetch_ranges = []

    if cached_min is None:
        print(f"   💾 DB cache      : EMPTY — will fetch full range from API")
        initial_fetch_ranges.append((start_dt, end_dt))
    else:
        print(f"   💾 DB cache      : {cached_min} → {cached_max}")

        gap_start = (cached_min - start_dt).total_seconds()
        gap_end   = (end_dt - cached_max).total_seconds()

        if gap_start > TOLERANCE_SECONDS:
            print(f"   ⚠️  Gap at START : {gap_start:.0f}s missing → fetching {start_dt} → {cached_min}")
            initial_fetch_ranges.append((start_dt, cached_min - timedelta(seconds=1)))
        else:
            print(f"   ✅ No gap at START (within {gap_start:.0f}s tolerance)")

        if gap_end > TOLERANCE_SECONDS:
            print(f"   ⚠️  Gap at END   : {gap_end:.0f}s missing → fetching {cached_max} → {end_dt}")
            initial_fetch_ranges.append((cached_max + timedelta(seconds=1), end_dt))
        else:
            print(f"   ✅ No gap at END (within {gap_end:.0f}s tolerance)")


    chunked_ranges = []
    for (f_dt, t_dt) in initial_fetch_ranges:
        curr_start = f_dt
        while curr_start < t_dt:
            curr_end = min(curr_start + timedelta(days=1), t_dt)
            chunked_ranges.append((curr_start, curr_end))
            curr_start = curr_end

    frames = []
    if not chunked_ranges:
        print(f"   🚀 Source        : DB ONLY (no API call needed)")
    
    for (from_dt, to_dt) in chunked_ranges:
        if is_range_fetched(device_id, from_dt, to_dt):
                print(f"   ⏭️  Skip API (deja interogat): {from_dt} → {to_dt}")
                continue

        print(f"   🌐 API fetch chunk: {from_dt.date()} to {to_dt.date()}")
        api_df = _fetch_from_api(device_id, location, from_dt, to_dt)

        mark_range_fetched(device_id, from_dt, to_dt)

        if not api_df.empty:
            print(f"   ✅ API returned  : {len(api_df)} rows → saving to DB")
            save_to_db(api_df, device_id, location)
            frames.append(api_df)
        else:
            print(f"   ⚠️  API returned  : 0 rows (empty or error)")

    db_df = get_cached_range(device_id, start_dt, end_dt)
    if not db_df.empty:
        print(f"   📦 DB returned   : {len(db_df)} rows")
        frames.append(db_df)
    else:
        print(f"   📦 DB returned   : 0 rows")

    if not frames:
        print(f"   ❌ Final result  : no data available")
        print(f"{'='*60}\n")
        return pd.DataFrame()

    result = (
        pd.concat(frames)
        .drop_duplicates(subset=["device_id", "timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    result["Location"] = location
    print(f"   🏁 Final result  : {len(result)} rows (after dedup)")
    print(f"{'='*60}\n")
    return result

def _fetch_from_api(
    device_id: str,
    location: str,
    from_dt: datetime,
    to_dt: datetime,
) -> pd.DataFrame:
    try:
        now = datetime.utcnow()
        start_sec = int((now - from_dt).total_seconds()) 
        stop_sec  = int((now - to_dt).total_seconds())   

        start_sec = max(0, start_sec)
        stop_sec  = max(0, stop_sec)

        headers  = {"X-User-id": USER_ID, "X-User-hash": USER_HASH}
        api_url  = f"{API_URL}/{device_id}/all/{start_sec}/{stop_sec}"

        print(f"      → GET {api_url}")
        response = requests.get(api_url, headers=headers, timeout=10) 
        print(f"      ← HTTP {response.status_code}")

        if response.status_code != 200:
            print(f"      ❌ API Error {response.status_code} for {location}")
            return pd.DataFrame()

        api_data = response.json()
        if not isinstance(api_data, list) or len(api_data) == 0:
            print(f"      ⚠️  API response is empty or not a list")
            return pd.DataFrame()

        df = pd.DataFrame(api_data)
        if "time" in df.columns:
            df["timestamp"] = pd.to_datetime(df["time"], unit="s", utc=True).dt.tz_convert("Europe/Bucharest").dt.tz_localize(None)
        df["device_id"] = device_id
        df["Location"]  = location

        print(f"      ✅ Parsed {len(df)} rows | {df['timestamp'].min()} → {df['timestamp'].max()}")
        return df

    except Exception as e:
        print(f"      ❌ Exception fetching API for {location}: {e}")
        return pd.DataFrame()