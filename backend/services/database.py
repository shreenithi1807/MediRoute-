import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "mediroute.db"


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = connect()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS ambulances (
        id TEXT PRIMARY KEY,
        location TEXT NOT NULL,
        status TEXT DEFAULT 'available',
        latitude REAL,
        longitude REAL
    );

    CREATE TABLE IF NOT EXISTS hospitals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        location TEXT NOT NULL,
        beds INTEGER DEFAULT 0,
        icu INTEGER DEFAULT 0,
        trauma INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS roads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_node TEXT NOT NULL,
        to_node TEXT NOT NULL,
        distance REAL DEFAULT 1,
        traffic REAL DEFAULT 1,
        status TEXT DEFAULT 'open'
    );

    CREATE TABLE IF NOT EXISTS emergencies (
        id TEXT PRIMARY KEY,
        location TEXT NOT NULL,
        emergency_type TEXT NOT NULL,
        severity INTEGER NOT NULL,
        required_facility TEXT DEFAULT '',
        status TEXT DEFAULT 'waiting',
        latitude REAL,
        longitude REAL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emergency_id TEXT,
        ambulance_id TEXT,
        hospital_name TEXT,
        route TEXT,
        eta_minutes INTEGER,
        status TEXT DEFAULT 'assigned',
        created_at TEXT
    );
    """)

    conn.commit()
    conn.close()


def rows(query, params=()):
    conn = connect()
    result = [
        dict(row)
        for row in conn.execute(query, params).fetchall()
    ]
    conn.close()
    return result


def execute(query, params=()):
    conn = connect()
    cur = conn.execute(query, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


def now():
    return datetime.now().isoformat(timespec="seconds")