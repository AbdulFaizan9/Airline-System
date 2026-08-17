"""
database.py
-----------
SQLite database layer for the Airline Management & Tracking System.
Handles schema creation and all CRUD operations used by the GUI.
"""

import sqlite3
import os
import math
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "airline.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def create_schema(reset=False):
    """Create all tables. If reset=True, drop existing tables first."""
    conn = get_connection()
    cur = conn.cursor()

    if reset:
        cur.executescript("""
            DROP TABLE IF EXISTS tickets;
            DROP TABLE IF EXISTS passengers;
            DROP TABLE IF EXISTS flights;
            DROP TABLE IF EXISTS routes;
            DROP TABLE IF EXISTS planes;
            DROP TABLE IF EXISTS staff;
            DROP TABLE IF EXISTS airports;
        """)

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS airports (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        country TEXT NOT NULL,
        lat REAL NOT NULL,
        lon REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS planes (
        plane_id INTEGER PRIMARY KEY AUTOINCREMENT,
        tail_number TEXT UNIQUE NOT NULL,
        model TEXT NOT NULL,
        capacity INTEGER NOT NULL,
        rows INTEGER NOT NULL,
        seats_per_row INTEGER NOT NULL,
        status TEXT DEFAULT 'Active'
    );

    CREATE TABLE IF NOT EXISTS staff (
        staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL,          -- Pilot / Co-Pilot / Cabin Crew / Booking Agent / Ground Staff
        email TEXT,
        phone TEXT
    );

    CREATE TABLE IF NOT EXISTS routes (
        route_id INTEGER PRIMARY KEY AUTOINCREMENT,
        origin_code TEXT NOT NULL,
        destination_code TEXT NOT NULL,
        distance_km REAL NOT NULL,
        FOREIGN KEY (origin_code) REFERENCES airports(code),
        FOREIGN KEY (destination_code) REFERENCES airports(code)
    );

    CREATE TABLE IF NOT EXISTS flights (
        flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_number TEXT UNIQUE NOT NULL,
        plane_id INTEGER NOT NULL,
        route_id INTEGER NOT NULL,
        captain_id INTEGER,
        departure_time TEXT NOT NULL,
        arrival_time TEXT NOT NULL,
        base_price REAL NOT NULL DEFAULT 15000,
        status TEXT DEFAULT 'Scheduled',   -- Scheduled/Boarding/Departed/In Air/Landed/Cancelled
        FOREIGN KEY (plane_id) REFERENCES planes(plane_id),
        FOREIGN KEY (route_id) REFERENCES routes(route_id),
        FOREIGN KEY (captain_id) REFERENCES staff(staff_id)
    );

    CREATE TABLE IF NOT EXISTS passengers (
        passenger_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        cnic_passport TEXT,
        phone TEXT,
        email TEXT
    );

    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_id INTEGER NOT NULL,
        passenger_id INTEGER NOT NULL,
        seat_no TEXT NOT NULL,
        booking_channel TEXT NOT NULL,      -- 'Online' or 'Staff Counter'
        booked_by_staff_id INTEGER,         -- NULL if Online
        booking_time TEXT NOT NULL,
        price REAL NOT NULL,
        status TEXT DEFAULT 'Confirmed',    -- Confirmed / Cancelled
        FOREIGN KEY (flight_id) REFERENCES flights(flight_id),
        FOREIGN KEY (passenger_id) REFERENCES passengers(passenger_id),
        FOREIGN KEY (booked_by_staff_id) REFERENCES staff(staff_id),
        UNIQUE (flight_id, seat_no)
    );
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Utility: seat map generation
# ---------------------------------------------------------------------------
def seats_per_row_for_capacity(capacity):
    if capacity >= 800:
        return 10   # 3-4-3
    elif capacity >= 650:
        return 9    # 3-3-3
    elif capacity >= 400:
        return 8    # 2-4-2
    else:
        return 6    # 3-3


def generate_seat_layout(capacity):
    spr = seats_per_row_for_capacity(capacity)
    rows = math.ceil(capacity / spr)
    return rows, spr


def all_seat_codes(rows, seats_per_row):
    letters = "ABCDEFGHIJ"[:seats_per_row]
    codes = []
    for r in range(1, rows + 1):
        for l in letters:
            codes.append(f"{r}{l}")
    return codes


# ---------------------------------------------------------------------------
# Geo helpers for tracking
# ---------------------------------------------------------------------------
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def interpolate_position(lat1, lon1, lat2, lon2, fraction):
    fraction = max(0.0, min(1.0, fraction))
    lat = lat1 + (lat2 - lat1) * fraction
    lon = lon1 + (lon2 - lon1) * fraction
    return lat, lon


# ---------------------------------------------------------------------------
# Query helpers used by the GUI
# ---------------------------------------------------------------------------
def fetch_all(query, params=()):
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def fetch_one(query, params=()):
    conn = get_connection()
    row = conn.execute(query, params).fetchone()
    conn.close()
    return row


def execute(query, params=(), many=False):
    conn = get_connection()
    cur = conn.cursor()
    if many:
        cur.executemany(query, params)
    else:
        cur.execute(query, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


def get_flight_full(flight_id):
    return fetch_one("""
        SELECT f.*, p.tail_number, p.model, p.capacity, p.rows, p.seats_per_row,
               r.origin_code, r.destination_code, r.distance_km,
               ao.name AS origin_name, ao.city AS origin_city, ao.lat AS origin_lat, ao.lon AS origin_lon,
               ad.name AS dest_name, ad.city AS dest_city, ad.lat AS dest_lat, ad.lon AS dest_lon,
               s.name AS captain_name
        FROM flights f
        JOIN planes p ON f.plane_id = p.plane_id
        JOIN routes r ON f.route_id = r.route_id
        JOIN airports ao ON r.origin_code = ao.code
        JOIN airports ad ON r.destination_code = ad.code
        LEFT JOIN staff s ON f.captain_id = s.staff_id
        WHERE f.flight_id = ?
    """, (flight_id,))


def get_all_flights_full():
    return fetch_all("""
        SELECT f.*, p.tail_number, p.model, p.capacity, p.rows, p.seats_per_row,
               r.origin_code, r.destination_code, r.distance_km,
               ao.name AS origin_name, ao.city AS origin_city, ao.lat AS origin_lat, ao.lon AS origin_lon,
               ad.name AS dest_name, ad.city AS dest_city, ad.lat AS dest_lat, ad.lon AS dest_lon,
               s.name AS captain_name
        FROM flights f
        JOIN planes p ON f.plane_id = p.plane_id
        JOIN routes r ON f.route_id = r.route_id
        JOIN airports ao ON r.origin_code = ao.code
        JOIN airports ad ON r.destination_code = ad.code
        LEFT JOIN staff s ON f.captain_id = s.staff_id
        ORDER BY f.departure_time
    """)


def compute_live_status(dep_str, arr_str, now=None):
    """Returns (status, fraction_of_flight_completed)"""
    now = now or datetime.now()
    dep = datetime.fromisoformat(dep_str)
    arr = datetime.fromisoformat(arr_str)
    boarding_start = dep - timedelta(minutes=45)

    if now < boarding_start:
        return "Scheduled", 0.0
    if boarding_start <= now < dep:
        return "Boarding", 0.0
    if dep <= now < arr:
        total = (arr - dep).total_seconds()
        elapsed = (now - dep).total_seconds()
        frac = elapsed / total if total > 0 else 0
        return "In Air", frac
    return "Landed", 1.0


def booked_seats_for_flight(flight_id):
    rows = fetch_all(
        "SELECT seat_no FROM tickets WHERE flight_id=? AND status='Confirmed'",
        (flight_id,),
    )
    return {r["seat_no"] for r in rows}


def available_seats_for_flight(flight_id, rows, spr):
    booked = booked_seats_for_flight(flight_id)
    all_seats = all_seat_codes(rows, spr)
    return [s for s in all_seats if s not in booked]


def seats_booked_count(flight_id):
    row = fetch_one(
        "SELECT COUNT(*) AS c FROM tickets WHERE flight_id=? AND status='Confirmed'",
        (flight_id,),
    )
    return row["c"] if row else 0
