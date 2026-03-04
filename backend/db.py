
import os
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "air_quality.db")

from contextlib import contextmanager

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id   TEXT      NOT NULL,
                location    TEXT      NOT NULL,
                timestamp   TIMESTAMP NOT NULL,
                temperature REAL,
                pressure    REAL,
                humidity    REAL,
                pm1         REAL,
                pm25        REAL,
                pm10        REAL,
                UNIQUE (device_id, timestamp)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_device_ts
            ON sensor_data (device_id, timestamp)
        """)
        # ← NOU
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fetched_ranges (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id   TEXT      NOT NULL,
                range_start TEXT      NOT NULL,
                range_end   TEXT      NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_fetched_device
            ON fetched_ranges (device_id, range_start, range_end)
        """)
        conn.commit()


def mark_range_fetched(device_id: str, start_dt: datetime, end_dt: datetime):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO fetched_ranges (device_id, range_start, range_end)
            VALUES (?, ?, ?)
        """, [
            device_id,
            start_dt.isoformat().replace("T", " "),
            end_dt.isoformat().replace("T", " "),
        ])
        conn.commit()


def is_range_fetched(device_id: str, start_dt: datetime, end_dt: datetime) -> bool:
    sql = """
        SELECT COUNT(*) FROM fetched_ranges
        WHERE device_id   = ?
          AND range_start <= ?
          AND range_end   >= ?
    """
    with get_conn() as conn:
        cursor = conn.execute(sql, [
            device_id,
            start_dt.isoformat().replace("T", " "),
            end_dt.isoformat().replace("T", " "),
        ])
        return cursor.fetchone()[0] > 0
    
def get_cached_range(device_id: str, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
    sql = """
        SELECT device_id, location, timestamp, temperature, pressure, humidity, pm1, pm25, pm10
        FROM   sensor_data
        WHERE  device_id = ?
          AND  timestamp BETWEEN ? AND ?
        ORDER  BY timestamp
    """
    with get_conn() as conn:
        df = pd.read_sql_query(
            sql, conn,
            params=[device_id, start_dt.isoformat(), end_dt.isoformat()],
            parse_dates=["timestamp"],
        )
    return df

def get_cached_boundaries(device_id: str, start_dt: datetime, end_dt: datetime):
    sql = """
        SELECT MIN(timestamp), MAX(timestamp)
        FROM   sensor_data
        WHERE  device_id = ?
          AND  timestamp BETWEEN ? AND ?
    """
    with get_conn() as conn:
        cursor = conn.execute(sql, [device_id, start_dt.isoformat(), end_dt.isoformat()])  # ← list
        row = cursor.fetchone()

    if row and row[0] and row[1]:
        return (datetime.fromisoformat(row[0]), datetime.fromisoformat(row[1]))
    return (None, None)

def save_to_db(df: pd.DataFrame, device_id: str, location: str):
    if df.empty:
        return

    rows = [
        (
            device_id,
            location,
            row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else str(row["timestamp"]),
            row.get("temperature"),
            row.get("pressure"),
            row.get("humidity"),
            row.get("pm1"),
            row.get("pm25"),
            row.get("pm10"),
        )
        for _, row in df.iterrows()
    ]

    sql = """
        INSERT OR IGNORE INTO sensor_data
            (device_id, location, timestamp, temperature, pressure, humidity, pm1, pm25, pm10)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with get_conn() as conn:
        conn.executemany(sql, rows)
        conn.commit()