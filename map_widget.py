"""
map_widget.py
-------------
A lightweight "real time" world map rendered on a Tkinter Canvas
(no internet / external image required). Draws a lat/lon graticule,
rough continent outlines, airport dots, flight routes, and moving
plane icons whose position is interpolated live from each flight's
departure/arrival time and current progress.
"""

import tkinter as tk
import math
import database as db

MAP_W = 1000
MAP_H = 500

# Very rough simplified continent outlines (lon, lat) polygons - just enough
# to give visual context, NOT geographically precise.
CONTINENTS = [
    # Africa
    [(-17, 15), (10, 37), (33, 31), (43, 12), (40, -25), (18, -35), (12, -5), (-17, 15)],
    # Europe
    [(-10, 36), (-10, 60), (30, 70), (40, 45), (20, 36), (-10, 36)],
    # Asia
    [(30, 45), (30, 70), (140, 70), (140, 20), (95, 5), (60, 10), (30, 45)],
    # North America
    [(-170, 65), (-170, 15), (-95, 10), (-80, 25), (-60, 45), (-70, 60), (-170, 65)],
    # South America
    [(-82, 10), (-35, -5), (-40, -35), (-70, -55), (-82, -5), (-82, 10)],
    # Australia
    [(112, -10), (154, -10), (154, -38), (112, -38), (112, -10)],
]

STATUS_COLORS = {
    "Scheduled": "#9aa0a6",
    "Boarding": "#f4b400",
    "In Air": "#1a73e8",
    "Landed": "#188038",
}


def lonlat_to_xy(lon, lat):
    x = (lon + 180) / 360 * MAP_W
    y = (90 - lat) / 180 * MAP_H
    return x, y


class LiveMap(tk.Frame):
    def __init__(self, master, get_flights_callback, on_select=None, **kwargs):
        super().__init__(master, **kwargs)
        self.get_flights_callback = get_flights_callback
        self.on_select = on_select
        self.plane_items = {}  # flight_id -> canvas item ids

        self.canvas = tk.Canvas(self, width=MAP_W, height=MAP_H,
                                 bg="#0d1b2a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self._draw_base_map()
        self.canvas.bind("<Button-1>", self._on_click)
        self._plane_positions = {}  # flight_id -> (x, y)

        self.refresh()

    def _draw_base_map(self):
        # graticule
        for lon in range(-180, 181, 30):
            x, _ = lonlat_to_xy(lon, 0)
            self.canvas.create_line(x, 0, x, MAP_H, fill="#132a3e")
        for lat in range(-90, 91, 30):
            _, y = lonlat_to_xy(0, lat)
            self.canvas.create_line(0, y, MAP_W, y, fill="#132a3e")

        for poly in CONTINENTS:
            pts = []
            for lon, lat in poly:
                x, y = lonlat_to_xy(lon, lat)
                pts.extend([x, y])
            self.canvas.create_polygon(pts, fill="#16324a", outline="#1f4a6b", width=1)

        # airports
        airports = db.fetch_all("SELECT code, city, lat, lon FROM airports")
        for a in airports:
            x, y = lonlat_to_xy(a["lon"], a["lat"])
            self.canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill="#ffffff", outline="")

        legend_y = 15
        for status, color in STATUS_COLORS.items():
            self.canvas.create_oval(15, legend_y - 4, 23, legend_y + 4, fill=color, outline="")
            self.canvas.create_text(30, legend_y, text=status, fill="white",
                                     anchor="w", font=("Segoe UI", 8))
            legend_y += 16

    def _on_click(self, event):
        if not self.on_select:
            return
        closest = None
        closest_dist = 12
        for flight_id, (x, y) in self._plane_positions.items():
            d = math.hypot(event.x - x, event.y - y)
            if d < closest_dist:
                closest = flight_id
                closest_dist = d
        if closest is not None:
            self.on_select(closest)

    def refresh(self):
        # remove old plane markers
        for items in self.plane_items.values():
            for item in items:
                self.canvas.delete(item)
        self.plane_items.clear()
        self._plane_positions.clear()

        flights = self.get_flights_callback()
        for f in flights:
            status, frac = db.compute_live_status(f["departure_time"], f["arrival_time"])
            if status not in ("In Air", "Boarding", "Landed"):
                continue
            olat, olon = f["origin_lat"], f["origin_lon"]
            dlat, dlon = f["dest_lat"], f["dest_lon"]
            if status == "Boarding":
                lat, lon = olat, olon
            elif status == "Landed":
                lat, lon = dlat, dlon
            else:
                lat, lon = db.interpolate_position(olat, olon, dlat, dlon, frac)

            x, y = lonlat_to_xy(lon, lat)
            color = STATUS_COLORS.get(status, "#ffffff")

            # draw route line faintly
            ox, oy = lonlat_to_xy(olon, olat)
            dx, dy = lonlat_to_xy(dlon, dlat)
            line = self.canvas.create_line(ox, oy, dx, dy, fill="#274b63", dash=(2, 3))

            plane = self.canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=color, outline="white")
            label = self.canvas.create_text(x, y - 10, text=f["flight_number"], fill="white",
                                             font=("Segoe UI", 7, "bold"))

            self.plane_items[f["flight_id"]] = [line, plane, label]
            self._plane_positions[f["flight_id"]] = (x, y)

        self.canvas.tag_raise("all")
