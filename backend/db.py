import os
import secrets
import sqlite3
import hashlib
import pandas as pd
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.getenv("DB_PATH", "air_quality.db")


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
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                label          TEXT NOT NULL,
                owner_username TEXT,
                user_id        TEXT NOT NULL,
                user_hash      TEXT NOT NULL,
                api_url        TEXT NOT NULL,
                is_active      INTEGER NOT NULL DEFAULT 1,
                created_at     TEXT    NOT NULL
            )
        """)

        existing_cols = {row[1] for row in conn.execute("PRAGMA table_info(api_keys)").fetchall()}
        if "owner_username" not in existing_cols:
            conn.execute("ALTER TABLE api_keys ADD COLUMN owner_username TEXT")

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


def mark_range_fetched(device_id: str, start_dt: datetime, end_dt: datetime):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO fetched_ranges (device_id, range_start, range_end)
            VALUES (?, ?, ?)
        """,
            [
                device_id,
                start_dt.isoformat().replace("T", " "),
                end_dt.isoformat().replace("T", " "),
            ],
        )


def is_range_fetched(device_id: str, start_dt: datetime, end_dt: datetime) -> bool:
    sql = """
        SELECT COUNT(*) FROM fetched_ranges
        WHERE device_id   = ?
          AND range_start <= ?
          AND range_end   >= ?
    """
    with get_conn() as conn:
        cursor = conn.execute(
            sql,
            [
                device_id,
                start_dt.isoformat().replace("T", " "),
                end_dt.isoformat().replace("T", " "),
            ],
        )
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
            sql,
            conn,
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


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _generate_api_credentials() -> tuple[str, str]:
    """
    Returns (user_id, user_hash) — unique, URL-safe random strings.

    user_id   : 12-char uppercase hex  e.g. "A3F9C2D10B4E"
    user_hash : 48-char lowercase hex  e.g. "9f3a...c2b1"
    """
    user_id = secrets.token_hex(6).upper()
    user_hash = secrets.token_hex(24)
    return user_id, user_hash


def _create_user_conn(conn, username: str, password: str, role: str = "viewer"):
    """
    Internal helper — reuses an open connection (used by init_db seed).
    Also auto-generates and stores API credentials for the new user.
    """
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        (username, _hash_password(password), role, now),
    )
    _create_api_key_for_user_conn(conn, username, now)


def _create_api_key_for_user_conn(conn, username: str, now: str | None = None):
    """
    Internal helper — generates and inserts one api_key row for `username`.
    Skips if the user already has a key (idempotent).
    """
    now = now or datetime.utcnow().isoformat()
    existing = conn.execute("SELECT id FROM api_keys WHERE owner_username=?", (username,)).fetchone()
    if existing:
        return

    api_url = os.getenv("API_URL", "https://api.example.com/data")
    user_id, user_hash = _generate_api_credentials()

    conn.execute(
        """
        INSERT INTO api_keys (label, owner_username, user_id, user_hash, api_url, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, 1, ?)
        """,
        (username, username, user_id, user_hash, api_url, now),
    )


def create_user(username: str, password: str, role: str = "viewer") -> dict:
    """
    Creates the user and automatically generates their API credentials.
    Returns {"ok": True} or {"ok": False, "error": "..."}.
    """
    try:
        with get_conn() as conn:
            _create_user_conn(conn, username, password, role)
        return {"ok": True}
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


def verify_password(username: str, password: str) -> bool:
    """
    Returns True if `password` matches the stored hash for `username`.
    Used by the user_settings change-password form.
    """
    return verify_user(username, password) is not None


def update_user_password(user_id: int, new_password: str):
    """
    Replaces the password hash for the given user_id.
    Called after verify_password() confirms the old password is correct.
    """
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET password_hash=? WHERE id=?",
            (_hash_password(new_password), user_id),
        )


def list_users() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT id, username, role, created_at, is_active FROM users ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def delete_user(user_id: int):
    with get_conn() as conn:
        conn.execute("UPDATE users SET is_active=0 WHERE id=?", (user_id,))


def update_user_role(user_id: int, role: str):
    with get_conn() as conn:
        conn.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))


def upsert_sensor(sensor_id: str, name: str, lat: float, lon: float, location: str = "", is_active: bool = True):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO sensors (id, name, lat, lon, location, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, lat=excluded.lat, lon=excluded.lon,
                location=excluded.location, is_active=excluded.is_active
        """,
            (sensor_id, name, lat, lon, location, int(is_active), datetime.utcnow().isoformat()),
        )


def list_sensors() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM sensors ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def delete_sensor(sensor_id: str):
    with get_conn() as conn:
        conn.execute("UPDATE sensors SET is_active=0 WHERE id=?", (sensor_id,))


def activate_sensor(sensor_id: str):
    with get_conn() as conn:
        conn.execute("UPDATE sensors SET is_active=1 WHERE id=?", (sensor_id,))


def add_api_key(label: str, user_id: str, user_hash: str, api_url: str, owner_username: str | None = None):
    """
    Manually add an API key (admin use).
    `owner_username` links the key to a specific app user so it appears
    on their /settings page.  Leave None for a shared / unowned key.
    """
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO api_keys (label, owner_username, user_id, user_hash, api_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (label, owner_username, user_id, user_hash, api_url, datetime.utcnow().isoformat()),
        )


def get_user_api_keys(username: str) -> list[dict]:
    """
    Returns all active API keys that belong to `username`.
    This is what the /settings page calls — it gets exactly
    the credentials generated for that user (or manually assigned to them).
    """
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM api_keys WHERE owner_username=? AND is_active=1 ORDER BY id",
            (username,),
        ).fetchall()
    return [dict(r) for r in rows]


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


def set_config(key: str, value: str, description: str = ""):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO app_configs (key, value, description, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value=excluded.value,
                updated_at=excluded.updated_at
        """,
            (key, value, description, datetime.utcnow().isoformat()),
        )


def get_config(key: str, default=None):
    with get_conn() as conn:
        row = conn.execute("SELECT value FROM app_configs WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def list_configs() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM app_configs ORDER BY key").fetchall()
    return [dict(r) for r in rows]
