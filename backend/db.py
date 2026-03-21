import os
import secrets
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.getenv("DB_PATH", "air_quality.db")


# ══════════════════════════════════════════════════════════════
# Connection
# ══════════════════════════════════════════════════════════════

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════
# Init
# ══════════════════════════════════════════════════════════════

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

        conn.execute("""
            CREATE TABLE IF NOT EXISTS fetched_ranges (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id   TEXT NOT NULL,
                range_start TEXT NOT NULL,
                range_end   TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_fetched_device
            ON fetched_ranges (device_id, range_start, range_end)
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                role          TEXT    NOT NULL DEFAULT 'viewer',
                created_at    TEXT    NOT NULL,
                is_active     INTEGER NOT NULL DEFAULT 1
            )
        """)

       
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sensors (
                id         TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                lat        REAL NOT NULL,
                lon        REAL NOT NULL,
                location   TEXT,
                is_active  INTEGER NOT NULL DEFAULT 1,
                created_at TEXT    NOT NULL
            )
        """)

  
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                label      TEXT NOT NULL,
                user_id    TEXT NOT NULL,
                user_hash  TEXT NOT NULL,
                api_url    TEXT NOT NULL DEFAULT '',
                is_active  INTEGER NOT NULL DEFAULT 1,
                created_at TEXT    NOT NULL,
                key_type   TEXT    NOT NULL DEFAULT 'external'
            )
        """)
        # migrate existing tables that predate the key_type column
        existing = {row[1] for row in conn.execute("PRAGMA table_info(api_keys)").fetchall()}
        if "key_type" not in existing:
            conn.execute("ALTER TABLE api_keys ADD COLUMN key_type TEXT NOT NULL DEFAULT 'external'")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_configs (
                key         TEXT PRIMARY KEY,
                value       TEXT NOT NULL,
                description TEXT,
                updated_at  TEXT NOT NULL
            )
        """)

    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        if row[0] == 0:
            _create_user_conn(conn, "admin", "admin1234", role="admin")
            print("[db] Default admin created — username: admin / password: admin1234")


# ══════════════════════════════════════════════════════════════
# Original: sensor data helpers
# ══════════════════════════════════════════════════════════════

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
        cursor = conn.execute(sql, [device_id, start_dt.isoformat(), end_dt.isoformat()])
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


# ══════════════════════════════════════════════════════════════
# New: Users
# ══════════════════════════════════════════════════════════════

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _create_user_conn(conn, username: str, password: str, role: str = "viewer"):
    """Internal — reuses an open connection (used by init_db seed)."""
    conn.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        (username, _hash_password(password), role, datetime.utcnow().isoformat()),
    )


def create_user(username: str, password: str, role: str = "viewer") -> dict:
    try:
        plain_secret = secrets.token_hex(32)
        with get_conn() as conn:
            _create_user_conn(conn, username, password, role)
            conn.execute("""
                INSERT INTO api_keys (label, user_id, user_hash, api_url, created_at, key_type)
                VALUES (?, ?, ?, '', ?, 'user')
            """, (f"auto:{username}", username, plain_secret, datetime.utcnow().isoformat()))
        return {"ok": True, "secret": plain_secret}
    except sqlite3.IntegrityError:
        return {"ok": False, "error": "Username already exists"}


def verify_user(username: str, password: str) -> dict | None:
    """Returns user dict on success, None on failure."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username=? AND password_hash=? AND is_active=1",
            (username, _hash_password(password)),
        ).fetchone()
    return dict(row) if row else None


def list_users() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, username, role, created_at, is_active FROM users ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


def delete_user(user_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE users SET is_active=0 WHERE id=?", (user_id,))


def update_user_role(user_id: int, role: str):
    with get_conn() as conn:
        conn.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))


# ══════════════════════════════════════════════════════════════
# New: Sensors metadata
# ══════════════════════════════════════════════════════════════

def upsert_sensor(sensor_id: str, name: str, lat: float, lon: float,
                  location: str = "", is_active: bool = True):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO sensors (id, name, lat, lon, location, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, lat=excluded.lat, lon=excluded.lon,
                location=excluded.location, is_active=excluded.is_active
        """, (sensor_id, name, lat, lon, location, int(is_active), datetime.utcnow().isoformat()))


def list_sensors() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM sensors ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def delete_sensor(sensor_id: str):
    """Soft delete — marks sensor as inactive."""
    with get_conn() as conn:
        conn.execute("UPDATE sensors SET is_active=0 WHERE id=?", (sensor_id,))


# ══════════════════════════════════════════════════════════════
# New: API Keys
# ══════════════════════════════════════════════════════════════

def add_api_key(label: str, user_id: str, user_hash: str, api_url: str, key_type: str = "external"):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO api_keys (label, user_id, user_hash, api_url, created_at, key_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (label, user_id, user_hash, api_url, datetime.utcnow().isoformat(), key_type))


def list_api_keys() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM api_keys ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def toggle_api_key(key_id: int, active: bool):
    with get_conn() as conn:
        conn.execute("UPDATE api_keys SET is_active=? WHERE id=?", (int(active), key_id))


def delete_api_key(key_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM api_keys WHERE id=?", (key_id,))


def validate_api_secret(secret: str) -> dict | None:
    """Returns the api_keys row if the secret is valid and active, else None."""
    if not secret:
        return None
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM api_keys WHERE user_hash=? AND is_active=1 AND key_type='user'",
            (secret,),
        ).fetchone()
    return dict(row) if row else None


# ══════════════════════════════════════════════════════════════
# New: App Configs
# ══════════════════════════════════════════════════════════════

def set_config(key: str, value: str, description: str = ""):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO app_configs (key, value, description, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value=excluded.value,
                updated_at=excluded.updated_at
        """, (key, value, description, datetime.utcnow().isoformat()))


def get_config(key: str, default=None):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM app_configs WHERE key=?", (key,)
        ).fetchone()
    return row["value"] if row else default


def list_configs() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM app_configs ORDER BY key").fetchall()
    return [dict(r) for r in rows]