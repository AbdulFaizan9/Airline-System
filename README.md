# SkyLine Airlines – Management & Real-Time Tracking System

Python + Tkinter + SQLite desktop application simulating a full airline's
booking, staff, and flight-tracking operations.

## Features
- **100+ wide-body aircraft** (Boeing 777/787/747, Airbus A350/A380/A330/767)
  each seating ~650–850 passengers, with an auto-generated seat map (row+letter).
- **41 real-world airports**, **160 routes**, **112 scheduled flights** (mix of
  past/boarding/in-air/landed so tracking has live data to show).
- **Ticket booking**: pick a flight, pick a free seat from the visual seat map,
  book **Online** or via a **Staff Counter agent** — every ticket records who
  booked it and through which channel.
- **Staff management**: pilots, co-pilots, cabin crew, booking agents, ground
  staff; add new staff and see how many tickets each agent has sold.
- **Live tracking tab**: a Tkinter-canvas world map plots every active flight's
  current position, interpolated in real time between its origin and
  destination airport based on elapsed flight time, refreshing every 3 seconds.
  Click a plane / list entry to see full flight detail (captain, aircraft,
  route, progress %, seats booked).
- **Reports tab**: search ticket sales by route, view who booked what and when.
- **Dashboard**: live counts (planes, today's flights, staff, tickets sold,
  revenue) plus a full flight table.

## Files
| File | Purpose |
|---|---|
| `database.py` | SQLite schema + all query/helper functions (seat maps, geo/interpolation, live status calc) |
| `seed_data.py` | Generates airports, 112 planes, 90 staff, 160 routes, 112 flights, ~500 passengers and thousands of sample tickets |
| `map_widget.py` | Tkinter Canvas "live map" widget (graticule + rough continents + moving plane markers) |
| `main_gui.py` | Main application window (Dashboard / Live Tracking / Book Ticket / Staff / Reports tabs) |
| `airline.db` | SQLite database file (auto-created on first run) |

## Setup

Requires Python 3.8+ with the standard library only (`tkinter`, `sqlite3` —
no `pip install` needed).

> On some Linux distros Tkinter isn't installed by default. If you get
> `ModuleNotFoundError: No module named 'tkinter'`, install it with:
> ```
> sudo apt-get install python3-tk
> ```
> On Windows/macOS, the official python.org installer already includes it.

## Run

# Airline Management System

A Python + Tkinter based Airline Booking System

## How to Run
1. Install Python 3.x
2. `python seed_data.py`  - to add sample flights and airports
3. `python main_gui.py`    - to start the GUI

## Files
- `main_gui.py` - Main application window
- `database.py` - Database logic
- `map_widget.py` - Map display
- `seed_data.py` - Sample data

## Notes
- The map is drawn purely with Tkinter Canvas (no internet / image files
  needed) — it shows a simplified lat/lon grid + rough continent shapes, not
  satellite imagery, so it works fully offline.
- Flight "live" status (Scheduled → Boarding → In Air → Landed) and the
  plane's map position are computed from real departure/arrival timestamps
  compared against your system clock, so what you see is always accurate to
  "now."
- Seat availability is enforced at the database level (`UNIQUE(flight_id, seat_no)`),
  so double-booking a seat is impossible even under concurrent use.
