"""
seed_data.py
------------
Populates airline.db with:
  - 40 major world airports
  - 100+ wide-body planes (each ~650-850 seats), several models
  - Staff (pilots, cabin crew, booking agents, ground staff)
  - Routes between airports
  - Flights (linking planes to routes with schedules)
  - Some sample passengers + tickets (Online & Staff Counter bookings)
"""

import random
from datetime import datetime, timedelta
import database as db

random.seed(42)

AIRPORTS = [
    ("KHI", "Jinnah Intl", "Karachi", "Pakistan", 24.9065, 67.1608),
    ("LHE", "Allama Iqbal Intl", "Lahore", "Pakistan", 31.5216, 74.4036),
    ("ISB", "Islamabad Intl", "Islamabad", "Pakistan", 33.5490, 72.8250),
    ("DXB", "Dubai Intl", "Dubai", "UAE", 25.2532, 55.3657),
    ("AUH", "Abu Dhabi Intl", "Abu Dhabi", "UAE", 24.4330, 54.6511),
    ("DOH", "Hamad Intl", "Doha", "Qatar", 25.2609, 51.6138),
    ("JED", "King Abdulaziz Intl", "Jeddah", "Saudi Arabia", 21.6796, 39.1565),
    ("RUH", "King Khalid Intl", "Riyadh", "Saudi Arabia", 24.9576, 46.6988),
    ("IST", "Istanbul Airport", "Istanbul", "Turkey", 41.2753, 28.7519),
    ("LHR", "Heathrow", "London", "UK", 51.4700, -0.4543),
    ("CDG", "Charles de Gaulle", "Paris", "France", 49.0097, 2.5479),
    ("FRA", "Frankfurt Airport", "Frankfurt", "Germany", 50.0379, 8.5622),
    ("AMS", "Schiphol", "Amsterdam", "Netherlands", 52.3105, 4.7683),
    ("MAD", "Barajas", "Madrid", "Spain", 40.4983, -3.5676),
    ("FCO", "Fiumicino", "Rome", "Italy", 41.8003, 12.2389),
    ("JFK", "John F Kennedy Intl", "New York", "USA", 40.6413, -73.7781),
    ("LAX", "Los Angeles Intl", "Los Angeles", "USA", 33.9416, -118.4085),
    ("ORD", "O'Hare Intl", "Chicago", "USA", 41.9742, -87.9073),
    ("YYZ", "Toronto Pearson", "Toronto", "Canada", 43.6777, -79.6248),
    ("GRU", "Guarulhos Intl", "Sao Paulo", "Brazil", -23.4356, -46.4731),
    ("JNB", "OR Tambo Intl", "Johannesburg", "South Africa", -26.1392, 28.2460),
    ("CAI", "Cairo Intl", "Cairo", "Egypt", 30.1219, 31.4056),
    ("NBO", "Jomo Kenyatta Intl", "Nairobi", "Kenya", -1.3192, 36.9278),
    ("DEL", "Indira Gandhi Intl", "Delhi", "India", 28.5562, 77.1000),
    ("BOM", "Chhatrapati Shivaji", "Mumbai", "India", 19.0896, 72.8656),
    ("DAC", "Hazrat Shahjalal Intl", "Dhaka", "Bangladesh", 23.8433, 90.3978),
    ("CMB", "Bandaranaike Intl", "Colombo", "Sri Lanka", 7.1808, 79.8841),
    ("BKK", "Suvarnabhumi", "Bangkok", "Thailand", 13.6900, 100.7501),
    ("SIN", "Changi Airport", "Singapore", "Singapore", 1.3644, 103.9915),
    ("KUL", "Kuala Lumpur Intl", "Kuala Lumpur", "Malaysia", 2.7456, 101.7099),
    ("HKG", "Hong Kong Intl", "Hong Kong", "China", 22.3080, 113.9185),
    ("PVG", "Pudong Intl", "Shanghai", "China", 31.1443, 121.8083),
    ("PEK", "Beijing Capital Intl", "Beijing", "China", 40.0799, 116.6031),
    ("NRT", "Narita Intl", "Tokyo", "Japan", 35.7720, 140.3929),
    ("ICN", "Incheon Intl", "Seoul", "South Korea", 37.4602, 126.4407),
    ("SYD", "Kingsford Smith", "Sydney", "Australia", -33.9399, 151.1753),
    ("MEL", "Melbourne Airport", "Melbourne", "Australia", -37.6690, 144.8410),
    ("AKL", "Auckland Airport", "Auckland", "New Zealand", -37.0082, 174.7850),
    ("IKA", "Imam Khomeini Intl", "Tehran", "Iran", 35.4161, 51.1522),
    ("KBL", "Hamid Karzai Intl", "Kabul", "Afghanistan", 34.5658, 69.2123),
    ("MCT", "Muscat Intl", "Muscat", "Oman", 23.5933, 58.2844),
]

PLANE_MODELS = [
    ("Boeing 777-300ER", 700),
    ("Airbus A350-900", 690),
    ("Boeing 787-9 Dreamliner", 670),
    ("Airbus A380-800", 853),
    ("Boeing 747-8", 660),
    ("Airbus A330-300", 680),
    ("Boeing 767-400", 650),
]

STAFF_ROLES = ["Pilot", "Co-Pilot", "Cabin Crew", "Booking Agent", "Ground Staff"]

FIRST_NAMES = ["Ahmed", "Ali", "Bilal", "Sara", "Ayesha", "Usman", "Fatima", "Hassan",
               "Zainab", "Omar", "Hina", "Imran", "Sana", "Kamran", "Nida", "Farhan",
               "Mariam", "Tariq", "Rabia", "Asad", "John", "Emily", "Michael", "Sophia",
               "David", "Laura", "Ahmed", "Noor", "Hamza", "Sadia"]
LAST_NAMES = ["Khan", "Malik", "Siddiqui", "Raza", "Sheikh", "Butt", "Chaudhry", "Farooq",
              "Iqbal", "Qureshi", "Baig", "Shah", "Ansari", "Smith", "Johnson", "Brown",
              "Williams", "Lee", "Garcia", "Hussain"]


def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def seed():
    db.create_schema(reset=True)
    conn = db.get_connection()
    cur = conn.cursor()

    # ---------------- Airports ----------------
    cur.executemany(
        "INSERT INTO airports (code, name, city, country, lat, lon) VALUES (?,?,?,?,?,?)",
        AIRPORTS,
    )

    # ---------------- Planes (100+) ----------------
    plane_rows = []
    tail_counter = 1
    total_planes = 112
    for i in range(total_planes):
        model, base_cap = PLANE_MODELS[i % len(PLANE_MODELS)]
        capacity_target = base_cap + random.randint(-10, 10)
        rows, spr = db.generate_seat_layout(capacity_target)
        actual_capacity = rows * spr
        tail = f"AP-{1000 + tail_counter}"
        tail_counter += 1
        plane_rows.append((tail, model, actual_capacity, rows, spr, "Active"))

    cur.executemany(
        "INSERT INTO planes (tail_number, model, capacity, rows, seats_per_row, status) VALUES (?,?,?,?,?,?)",
        plane_rows,
    )

    # ---------------- Staff ----------------
    staff_rows = []
    for _ in range(90):
        role = random.choice(STAFF_ROLES)
        name = random_name()
        email = name.lower().replace(" ", ".") + "@skyline-air.com"
        phone = "+92-3" + str(random.randint(100000000, 999999999))[:9]
        staff_rows.append((name, role, email, phone))
    cur.executemany(
        "INSERT INTO staff (name, role, email, phone) VALUES (?,?,?,?)", staff_rows
    )

    conn.commit()

    # fetch ids back
    airport_codes = [a[0] for a in AIRPORTS]
    plane_ids = [r["plane_id"] for r in cur.execute("SELECT plane_id FROM planes").fetchall()]
    pilot_ids = [r["staff_id"] for r in cur.execute(
        "SELECT staff_id FROM staff WHERE role='Pilot'").fetchall()]
    agent_ids = [r["staff_id"] for r in cur.execute(
        "SELECT staff_id FROM staff WHERE role='Booking Agent'").fetchall()]
    airport_coords = {a[0]: (a[4], a[5]) for a in AIRPORTS}

    # ---------------- Routes ----------------
    route_rows = []
    route_pairs = set()
    num_routes = 160
    while len(route_pairs) < num_routes:
        o, d = random.sample(airport_codes, 2)
        if (o, d) in route_pairs:
            continue
        route_pairs.add((o, d))
        lat1, lon1 = airport_coords[o]
        lat2, lon2 = airport_coords[d]
        dist = db.haversine_km(lat1, lon1, lat2, lon2)
        route_rows.append((o, d, round(dist, 1)))

    cur.executemany(
        "INSERT INTO routes (origin_code, destination_code, distance_km) VALUES (?,?,?)",
        route_rows,
    )
    conn.commit()
    route_ids = [r["route_id"] for r in cur.execute("SELECT route_id FROM routes").fetchall()]
    route_info = {r["route_id"]: r["distance_km"] for r in
                  cur.execute("SELECT route_id, distance_km FROM routes").fetchall()}

    # ---------------- Flights ----------------
    flight_rows = []
    now = datetime.now()
    airline_codes = ["SL", "SK", "AV"]
    flight_num_counter = 100

    # create a flight for every plane at least once, spread across -1 day to +3 days
    for idx, plane_id in enumerate(plane_ids):
        route_id = random.choice(route_ids)
        distance = route_info[route_id]
        # avg speed ~850 km/h + 30 min buffer for taxi/climb
        flight_hours = distance / 850.0 + 0.5
        dep_offset_hours = random.uniform(-20, 72)  # some in past, most upcoming
        dep_time = now + timedelta(hours=dep_offset_hours)
        arr_time = dep_time + timedelta(hours=flight_hours)
        flight_num_counter += 1
        fn = f"{random.choice(airline_codes)}{flight_num_counter}"
        captain = random.choice(pilot_ids) if pilot_ids else None
        base_price = round(random.uniform(25000, 120000), -2)
        flight_rows.append((fn, plane_id, route_id, captain,
                             dep_time.isoformat(timespec="minutes"),
                             arr_time.isoformat(timespec="minutes"),
                             base_price, "Scheduled"))

    cur.executemany("""
        INSERT INTO flights (flight_number, plane_id, route_id, captain_id,
                              departure_time, arrival_time, base_price, status)
        VALUES (?,?,?,?,?,?,?,?)
    """, flight_rows)
    conn.commit()

    flight_records = cur.execute(
        "SELECT flight_id, plane_id FROM flights").fetchall()
    plane_capacity = {r["plane_id"]: r["capacity"] for r in
                       cur.execute("SELECT plane_id, capacity, rows, seats_per_row FROM planes").fetchall()}
    plane_layout = {r["plane_id"]: (r["rows"], r["seats_per_row"]) for r in
                     cur.execute("SELECT plane_id, rows, seats_per_row FROM planes").fetchall()}

    # ---------------- Sample Passengers + Tickets ----------------
    passenger_rows = []
    for _ in range(500):
        name = random_name()
        cnic = f"{random.randint(10000,99999)}-{random.randint(1000000,9999999)}-{random.randint(1,9)}"
        phone = "+92-3" + str(random.randint(100000000, 999999999))[:9]
        email = name.lower().replace(" ", ".") + f"{random.randint(1,999)}@mail.com"
        passenger_rows.append((name, cnic, phone, email))
    cur.executemany(
        "INSERT INTO passengers (name, cnic_passport, phone, email) VALUES (?,?,?,?)",
        passenger_rows,
    )
    conn.commit()
    passenger_ids = [r["passenger_id"] for r in cur.execute("SELECT passenger_id FROM passengers").fetchall()]

    ticket_rows = []
    for flight in random.sample(flight_records, min(60, len(flight_records))):
        rows_, spr_ = plane_layout[flight["plane_id"]]
        seat_codes = db.all_seat_codes(rows_, spr_)
        n_book = random.randint(20, min(120, len(seat_codes)))
        chosen_seats = random.sample(seat_codes, n_book)
        for seat in chosen_seats:
            passenger_id = random.choice(passenger_ids)
            channel = random.choice(["Online", "Online", "Staff Counter"])
            staff_id = random.choice(agent_ids) if channel == "Staff Counter" and agent_ids else None
            booking_time = (now - timedelta(days=random.randint(0, 20),
                                             hours=random.randint(0, 23))).isoformat(timespec="minutes")
            price = round(random.uniform(25000, 120000), -2)
            ticket_rows.append((flight["flight_id"], passenger_id, seat, channel,
                                 staff_id, booking_time, price, "Confirmed"))

    cur.executemany("""
        INSERT OR IGNORE INTO tickets (flight_id, passenger_id, seat_no, booking_channel,
                                        booked_by_staff_id, booking_time, price, status)
        VALUES (?,?,?,?,?,?,?,?)
    """, ticket_rows)

    conn.commit()
    conn.close()
    print(f"Seeded: {len(AIRPORTS)} airports, {len(plane_rows)} planes, "
          f"{len(staff_rows)} staff, {len(route_rows)} routes, "
          f"{len(flight_rows)} flights, {len(ticket_rows)} tickets.")


if __name__ == "__main__":
    seed()
