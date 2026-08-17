"""
main_gui.py
-----------
Airline Management & Real-Time Tracking System
Tkinter + SQLite desktop application.

Run:  python3 main_gui.py
(If airline.db does not exist yet, run seed_data.py first.)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import random
from datetime import datetime

import database as db
from map_widget import LiveMap

if not os.path.exists(db.DB_PATH):
    import seed_data
    seed_data.seed()


APP_BG = "#f4f6f8"
HEADER_BG = "#0d1b2a"
ACCENT = "#1a73e8"


class AirlineApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SkyLine Airlines - Management & Tracking System")
        self.geometry("1300x800")
        self.configure(bg=APP_BG)

        self._build_header()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_dashboard = DashboardTab(self.notebook)
        self.tab_tracking = TrackingTab(self.notebook)
        self.tab_booking = BookingTab(self.notebook)
        self.tab_staff = StaffTab(self.notebook)
        self.tab_reports = ReportsTab(self.notebook)

        self.notebook.add(self.tab_dashboard, text="  Dashboard  ")
        self.notebook.add(self.tab_tracking, text="  Live Tracking  ")
        self.notebook.add(self.tab_booking, text="  Book Ticket  ")
        self.notebook.add(self.tab_staff, text="  Staff  ")
        self.notebook.add(self.tab_reports, text="  Reports  ")

    def _build_header(self):
        header = tk.Frame(self, bg=HEADER_BG, height=60)
        header.pack(fill="x")
        tk.Label(header, text="✈  SkyLine Airlines Control Center", bg=HEADER_BG,
                  fg="white", font=("Segoe UI", 18, "bold")).pack(side="left", padx=20, pady=10)
        self.clock_label = tk.Label(header, text="", bg=HEADER_BG, fg="#9aa0a6",
                                     font=("Segoe UI", 11))
        self.clock_label.pack(side="right", padx=20)
        self._tick_clock()

    def _tick_clock(self):
        self.clock_label.config(text=datetime.now().strftime("%A, %d %B %Y  |  %H:%M:%S"))
        self.after(1000, self._tick_clock)


# ---------------------------------------------------------------------------
# Dashboard Tab
# ---------------------------------------------------------------------------
class DashboardTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=APP_BG)
        self.stat_labels = {}
        self._build_stats_row()
        self._build_flight_table()
        self.refresh()

    def _build_stats_row(self):
        row = tk.Frame(self, bg=APP_BG)
        row.pack(fill="x", padx=10, pady=10)
        stats = ["Total Planes", "Total Flights Today", "Active Staff",
                 "Tickets Sold", "Revenue (PKR)"]
        for s in stats:
            card = tk.Frame(row, bg="white", relief="ridge", bd=1)
            card.pack(side="left", expand=True, fill="both", padx=6)
            tk.Label(card, text=s, bg="white", fg="#5f6368",
                      font=("Segoe UI", 10)).pack(pady=(10, 2))
            val = tk.Label(card, text="0", bg="white", fg=ACCENT,
                            font=("Segoe UI", 20, "bold"))
            val.pack(pady=(0, 10))
            self.stat_labels[s] = val

    def _build_flight_table(self):
        frame = tk.Frame(self, bg=APP_BG)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        tk.Label(frame, text="Upcoming / Live Flights", bg=APP_BG,
                  font=("Segoe UI", 13, "bold")).pack(anchor="w")

        cols = ("flight", "route", "plane", "dep", "arr", "status", "seats")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=18)
        headings = {"flight": "Flight #", "route": "Route", "plane": "Aircraft",
                    "dep": "Departure", "arr": "Arrival", "status": "Status",
                    "seats": "Seats Booked/Total"}
        widths = {"flight": 80, "route": 220, "plane": 200, "dep": 140,
                  "arr": 140, "status": 100, "seats": 140}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="center")
        self.tree.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        btn = tk.Button(self, text="Refresh", command=self.refresh, bg=ACCENT, fg="white")
        btn.pack(pady=4)

    def refresh(self):
        planes = db.fetch_one("SELECT COUNT(*) c FROM planes")["c"]
        flights_today = db.fetch_one(
            "SELECT COUNT(*) c FROM flights WHERE date(departure_time)=date('now')")["c"]
        staff = db.fetch_one("SELECT COUNT(*) c FROM staff")["c"]
        tickets = db.fetch_one("SELECT COUNT(*) c FROM tickets WHERE status='Confirmed'")["c"]
        revenue = db.fetch_one(
            "SELECT COALESCE(SUM(price),0) s FROM tickets WHERE status='Confirmed'")["s"]

        self.stat_labels["Total Planes"].config(text=str(planes))
        self.stat_labels["Total Flights Today"].config(text=str(flights_today))
        self.stat_labels["Active Staff"].config(text=str(staff))
        self.stat_labels["Tickets Sold"].config(text=str(tickets))
        self.stat_labels["Revenue (PKR)"].config(text=f"{revenue:,.0f}")

        for i in self.tree.get_children():
            self.tree.delete(i)

        flights = db.get_all_flights_full()
        for f in flights:
            status, _ = db.compute_live_status(f["departure_time"], f["arrival_time"])
            booked = db.seats_booked_count(f["flight_id"])
            route = f"{f['origin_code']} -> {f['destination_code']}"
            self.tree.insert("", "end", values=(
                f["flight_number"], route, f"{f['model']} ({f['tail_number']})",
                f["departure_time"].replace("T", " "),
                f["arrival_time"].replace("T", " "),
                status, f"{booked}/{f['capacity']}"
            ))


# ---------------------------------------------------------------------------
# Live Tracking Tab
# ---------------------------------------------------------------------------
class TrackingTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=APP_BG)
        left = tk.Frame(self, bg=APP_BG)
        left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        right = tk.Frame(self, bg=APP_BG, width=380)
        right.pack(side="right", fill="y", padx=8, pady=8)

        tk.Label(left, text="Real-Time Flight Tracking Map", bg=APP_BG,
                  font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.map_widget = LiveMap(left, self._get_active_flights, on_select=self._show_detail)
        self.map_widget.pack(fill="both", expand=True, pady=6)

        tk.Label(right, text="Flight Details", bg=APP_BG,
                  font=("Segoe UI", 13, "bold")).pack(anchor="w")
        self.detail_text = tk.Text(right, height=20, width=44, state="disabled",
                                    bg="white", relief="groove", bd=1, font=("Consolas", 10))
        self.detail_text.pack(fill="both", pady=6)

        tk.Label(right, text="Live Flights List", bg=APP_BG,
                  font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 0))
        self.listbox = tk.Listbox(right, height=14)
        self.listbox.pack(fill="both", expand=True, pady=4)
        self.listbox.bind("<<ListboxSelect>>", self._on_list_select)
        self._flight_id_by_index = []

        self._auto_refresh()

    def _get_active_flights(self):
        return db.get_all_flights_full()

    def _auto_refresh(self):
        self.map_widget.refresh()
        self._refresh_list()
        self.after(3000, self._auto_refresh)

    def _refresh_list(self):
        self.listbox.delete(0, "end")
        self._flight_id_by_index = []
        flights = db.get_all_flights_full()
        for f in flights:
            status, frac = db.compute_live_status(f["departure_time"], f["arrival_time"])
            if status in ("Boarding", "In Air", "Landed"):
                self.listbox.insert(
                    "end",
                    f"{f['flight_number']}  {f['origin_code']}->{f['destination_code']}  "
                    f"[{status}] {int(frac*100)}%"
                )
                self._flight_id_by_index.append(f["flight_id"])

    def _on_list_select(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        flight_id = self._flight_id_by_index[sel[0]]
        self._show_detail(flight_id)

    def _show_detail(self, flight_id):
        f = db.get_flight_full(flight_id)
        if not f:
            return
        status, frac = db.compute_live_status(f["departure_time"], f["arrival_time"])
        booked = db.seats_booked_count(flight_id)
        text = f"""Flight Number : {f['flight_number']}
Aircraft      : {f['model']}
Tail Number   : {f['tail_number']}
Capacity      : {f['capacity']} seats
Captain       : {f['captain_name'] or 'Unassigned'}

Route         : {f['origin_city']} ({f['origin_code']})
                -> {f['dest_city']} ({f['destination_code']})
Distance      : {f['distance_km']:.0f} km

Departure     : {f['departure_time'].replace('T',' ')}
Arrival       : {f['arrival_time'].replace('T',' ')}
Status        : {status}
Progress      : {frac*100:.1f}%

Seats Booked  : {booked} / {f['capacity']}
Base Price    : PKR {f['base_price']:.0f}
"""
        self.detail_text.config(state="normal")
        self.detail_text.delete("1.0", "end")
        self.detail_text.insert("1.0", text)
        self.detail_text.config(state="disabled")


# ---------------------------------------------------------------------------
# Booking Tab
# ---------------------------------------------------------------------------
class BookingTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=APP_BG)
        self.selected_flight_id = None
        self.rows = self.spr = 0

        form = tk.Frame(self, bg=APP_BG)
        form.pack(fill="x", padx=10, pady=10)

        tk.Label(form, text="Select Flight:", bg=APP_BG).grid(row=0, column=0, sticky="w")
        self.flight_combo = ttk.Combobox(form, width=60, state="readonly")
        self.flight_combo.grid(row=0, column=1, columnspan=3, sticky="w", padx=4, pady=4)
        self.flight_combo.bind("<<ComboboxSelected>>", self._on_flight_selected)

        tk.Label(form, text="Passenger Name:", bg=APP_BG).grid(row=1, column=0, sticky="w")
        self.name_entry = tk.Entry(form, width=30)
        self.name_entry.grid(row=1, column=1, sticky="w", padx=4, pady=4)

        tk.Label(form, text="CNIC / Passport:", bg=APP_BG).grid(row=1, column=2, sticky="w")
        self.cnic_entry = tk.Entry(form, width=25)
        self.cnic_entry.grid(row=1, column=3, sticky="w", padx=4, pady=4)

        tk.Label(form, text="Phone:", bg=APP_BG).grid(row=2, column=0, sticky="w")
        self.phone_entry = tk.Entry(form, width=30)
        self.phone_entry.grid(row=2, column=1, sticky="w", padx=4, pady=4)

        tk.Label(form, text="Email:", bg=APP_BG).grid(row=2, column=2, sticky="w")
        self.email_entry = tk.Entry(form, width=25)
        self.email_entry.grid(row=2, column=3, sticky="w", padx=4, pady=4)

        tk.Label(form, text="Booking Channel:", bg=APP_BG).grid(row=3, column=0, sticky="w")
        self.channel_var = tk.StringVar(value="Online")
        tk.Radiobutton(form, text="Online", variable=self.channel_var, value="Online",
                        bg=APP_BG, command=self._toggle_staff).grid(row=3, column=1, sticky="w")
        tk.Radiobutton(form, text="Staff Counter", variable=self.channel_var, value="Staff Counter",
                        bg=APP_BG, command=self._toggle_staff).grid(row=3, column=2, sticky="w")

        self.staff_combo = ttk.Combobox(form, width=30, state="disabled")
        self.staff_combo.grid(row=3, column=3, sticky="w", padx=4)

        mid = tk.Frame(self, bg=APP_BG)
        mid.pack(fill="both", expand=True, padx=10, pady=6)

        left = tk.Frame(mid, bg=APP_BG)
        left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text="Available Seats (click to pick):", bg=APP_BG,
                  font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.seat_canvas_frame = tk.Frame(left, bg="white", relief="groove", bd=1)
        self.seat_canvas_frame.pack(fill="both", expand=True)
        self.seat_scroll = tk.Canvas(self.seat_canvas_frame, bg="white")
        vscroll = ttk.Scrollbar(self.seat_canvas_frame, orient="vertical", command=self.seat_scroll.yview)
        self.seat_inner = tk.Frame(self.seat_scroll, bg="white")
        self.seat_inner.bind("<Configure>", lambda e: self.seat_scroll.configure(
            scrollregion=self.seat_scroll.bbox("all")))
        self.seat_scroll.create_window((0, 0), window=self.seat_inner, anchor="nw")
        self.seat_scroll.configure(yscrollcommand=vscroll.set)
        self.seat_scroll.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        right = tk.Frame(mid, bg=APP_BG, width=300)
        right.pack(side="right", fill="y")
        tk.Label(right, text="Selected Seat:", bg=APP_BG, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.selected_seat_label = tk.Label(right, text="(none)", bg=APP_BG, fg=ACCENT,
                                             font=("Segoe UI", 16, "bold"))
        self.selected_seat_label.pack(anchor="w", pady=6)

        self.price_label = tk.Label(right, text="Price: -", bg=APP_BG, font=("Segoe UI", 11))
        self.price_label.pack(anchor="w", pady=4)

        tk.Button(right, text="Confirm Booking", bg="#188038", fg="white",
                  font=("Segoe UI", 11, "bold"), command=self._confirm_booking).pack(pady=20, fill="x")

        self.selected_seat = None
        self.seat_buttons = {}

        self._load_staff_agents()
        self.refresh_flights()

    def _toggle_staff(self):
        if self.channel_var.get() == "Staff Counter":
            self.staff_combo.config(state="readonly")
        else:
            self.staff_combo.set("")
            self.staff_combo.config(state="disabled")

    def _load_staff_agents(self):
        agents = db.fetch_all("SELECT staff_id, name FROM staff WHERE role='Booking Agent'")
        self.agent_map = {f"{a['name']} (ID {a['staff_id']})": a["staff_id"] for a in agents}
        self.staff_combo["values"] = list(self.agent_map.keys())

    def refresh_flights(self):
        flights = db.get_all_flights_full()
        self.flight_map = {}
        display = []
        for f in flights:
            status, _ = db.compute_live_status(f["departure_time"], f["arrival_time"])
            if status in ("Scheduled", "Boarding"):
                label = (f"{f['flight_number']}  {f['origin_code']}->{f['destination_code']}  "
                         f"dep {f['departure_time'].replace('T',' ')}  ({f['model']})")
                self.flight_map[label] = f["flight_id"]
                display.append(label)
        self.flight_combo["values"] = display

    def _on_flight_selected(self, event=None):
        label = self.flight_combo.get()
        flight_id = self.flight_map.get(label)
        if not flight_id:
            return
        self.selected_flight_id = flight_id
        f = db.get_flight_full(flight_id)
        self.rows, self.spr = f["rows"], f["seats_per_row"]
        self.price_label.config(text=f"Price: PKR {f['base_price']:.0f}")
        self._render_seats()

    def _render_seats(self):
        for w in self.seat_inner.winfo_children():
            w.destroy()
        self.seat_buttons = {}
        self.selected_seat = None
        self.selected_seat_label.config(text="(none)")

        available = set(db.available_seats_for_flight(self.selected_flight_id, self.rows, self.spr))
        letters = "ABCDEFGHIJ"[:self.spr]

        # header row with column letters
        tk.Label(self.seat_inner, text="", width=5, bg="white").grid(row=0, column=0)
        for c, l in enumerate(letters):
            tk.Label(self.seat_inner, text=l, bg="white", width=4,
                      font=("Segoe UI", 8, "bold")).grid(row=0, column=c + 1)

        # Only render a manageable number of rows visually (cap at 60 for perf, show note)
        max_display_rows = min(self.rows, 80)
        for r in range(1, max_display_rows + 1):
            tk.Label(self.seat_inner, text=str(r), bg="white", width=4,
                      font=("Segoe UI", 8)).grid(row=r, column=0)
            for c, l in enumerate(letters):
                code = f"{r}{l}"
                is_avail = code in available
                btn = tk.Button(self.seat_inner, text="", width=2, height=1,
                                 bg="#34a853" if is_avail else "#ea4335",
                                 state="normal" if is_avail else "disabled",
                                 command=lambda code=code: self._pick_seat(code))
                btn.grid(row=r, column=c + 1, padx=1, pady=1)
                self.seat_buttons[code] = btn
        if self.rows > max_display_rows:
            tk.Label(self.seat_inner, bg="white", fg="#5f6368",
                      text=f"... {self.rows - max_display_rows} more rows (aircraft has {self.rows} total)"
                      ).grid(row=max_display_rows + 1, column=0, columnspan=self.spr + 1, sticky="w")

    def _pick_seat(self, code):
        if self.selected_seat and self.selected_seat in self.seat_buttons:
            self.seat_buttons[self.selected_seat].config(bg="#34a853")
        self.selected_seat = code
        self.seat_buttons[code].config(bg=ACCENT)
        self.selected_seat_label.config(text=code)

    def _confirm_booking(self):
        if not self.selected_flight_id:
            messagebox.showwarning("Missing Flight", "Please select a flight first.")
            return
        if not self.selected_seat:
            messagebox.showwarning("Missing Seat", "Please choose a seat.")
            return
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Missing Name", "Passenger name is required.")
            return

        channel = self.channel_var.get()
        staff_id = None
        if channel == "Staff Counter":
            staff_label = self.staff_combo.get()
            if not staff_label:
                messagebox.showwarning("Missing Staff", "Select the booking agent.")
                return
            staff_id = self.agent_map.get(staff_label)

        f = db.get_flight_full(self.selected_flight_id)

        passenger_id = db.execute(
            "INSERT INTO passengers (name, cnic_passport, phone, email) VALUES (?,?,?,?)",
            (name, self.cnic_entry.get().strip(), self.phone_entry.get().strip(),
             self.email_entry.get().strip())
        )

        try:
            db.execute("""
                INSERT INTO tickets (flight_id, passenger_id, seat_no, booking_channel,
                                      booked_by_staff_id, booking_time, price, status)
                VALUES (?,?,?,?,?,?,?,?)
            """, (self.selected_flight_id, passenger_id, self.selected_seat, channel,
                  staff_id, datetime.now().isoformat(timespec="minutes"),
                  f["base_price"], "Confirmed"))
        except Exception as e:
            messagebox.showerror("Booking Failed", f"Seat may already be taken.\n{e}")
            return

        messagebox.showinfo("Ticket Confirmed",
                             f"Ticket booked!\nFlight: {f['flight_number']}\n"
                             f"Passenger: {name}\nSeat: {self.selected_seat}\n"
                             f"Channel: {channel}\nPrice: PKR {f['base_price']:.0f}")

        self.name_entry.delete(0, "end")
        self.cnic_entry.delete(0, "end")
        self.phone_entry.delete(0, "end")
        self.email_entry.delete(0, "end")
        self._render_seats()


# ---------------------------------------------------------------------------
# Staff Tab
# ---------------------------------------------------------------------------
class StaffTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=APP_BG)

        top = tk.Frame(self, bg=APP_BG)
        top.pack(fill="x", padx=10, pady=10)

        tk.Label(top, text="Name:", bg=APP_BG).grid(row=0, column=0)
        self.name_entry = tk.Entry(top, width=25)
        self.name_entry.grid(row=0, column=1, padx=4)

        tk.Label(top, text="Role:", bg=APP_BG).grid(row=0, column=2)
        self.role_combo = ttk.Combobox(top, values=["Pilot", "Co-Pilot", "Cabin Crew",
                                                      "Booking Agent", "Ground Staff"],
                                        state="readonly", width=18)
        self.role_combo.grid(row=0, column=3, padx=4)

        tk.Label(top, text="Email:", bg=APP_BG).grid(row=0, column=4)
        self.email_entry = tk.Entry(top, width=25)
        self.email_entry.grid(row=0, column=5, padx=4)

        tk.Label(top, text="Phone:", bg=APP_BG).grid(row=0, column=6)
        self.phone_entry = tk.Entry(top, width=18)
        self.phone_entry.grid(row=0, column=7, padx=4)

        tk.Button(top, text="Add Staff", bg=ACCENT, fg="white",
                  command=self._add_staff).grid(row=0, column=8, padx=8)

        cols = ("id", "name", "role", "email", "phone", "bookings_made")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=22)
        heads = {"id": "ID", "name": "Name", "role": "Role", "email": "Email",
                 "phone": "Phone", "bookings_made": "Tickets Sold (Staff Counter)"}
        widths = {"id": 50, "name": 160, "role": 120, "email": 220, "phone": 130, "bookings_made": 190}
        for c in cols:
            self.tree.heading(c, text=heads[c])
            self.tree.column(c, width=widths[c], anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.refresh()

    def _add_staff(self):
        name = self.name_entry.get().strip()
        role = self.role_combo.get()
        if not name or not role:
            messagebox.showwarning("Missing Data", "Name and Role are required.")
            return
        db.execute("INSERT INTO staff (name, role, email, phone) VALUES (?,?,?,?)",
                   (name, role, self.email_entry.get().strip(), self.phone_entry.get().strip()))
        self.name_entry.delete(0, "end")
        self.email_entry.delete(0, "end")
        self.phone_entry.delete(0, "end")
        self.role_combo.set("")
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = db.fetch_all("""
            SELECT s.staff_id, s.name, s.role, s.email, s.phone,
                   (SELECT COUNT(*) FROM tickets t WHERE t.booked_by_staff_id = s.staff_id) AS sold
            FROM staff s ORDER BY s.role, s.name
        """)
        for r in rows:
            self.tree.insert("", "end", values=(r["staff_id"], r["name"], r["role"],
                                                  r["email"], r["phone"], r["sold"]))


# ---------------------------------------------------------------------------
# Reports Tab
# ---------------------------------------------------------------------------
class ReportsTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg=APP_BG)

        top = tk.Frame(self, bg=APP_BG)
        top.pack(fill="x", padx=10, pady=10)
        tk.Label(top, text="Search flights by route (origin code):", bg=APP_BG).pack(side="left")
        self.origin_entry = tk.Entry(top, width=8)
        self.origin_entry.pack(side="left", padx=4)
        tk.Label(top, text="Destination code:", bg=APP_BG).pack(side="left")
        self.dest_entry = tk.Entry(top, width=8)
        self.dest_entry.pack(side="left", padx=4)
        tk.Button(top, text="Search", bg=ACCENT, fg="white", command=self._search).pack(side="left", padx=8)
        tk.Button(top, text="Show All Ticket Sales", bg=ACCENT, fg="white",
                  command=self._show_all_tickets).pack(side="left", padx=8)

        cols = ("ticket", "flight", "passenger", "seat", "channel", "staff", "price", "time")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=24)
        heads = {"ticket": "Ticket ID", "flight": "Flight", "passenger": "Passenger",
                 "seat": "Seat", "channel": "Channel", "staff": "Booked By Staff",
                 "price": "Price", "time": "Booking Time"}
        widths = {"ticket": 70, "flight": 90, "passenger": 160, "seat": 60,
                  "channel": 110, "staff": 160, "price": 90, "time": 140}
        for c in cols:
            self.tree.heading(c, text=heads[c])
            self.tree.column(c, width=widths[c], anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self._show_all_tickets()

    def _base_query(self):
        return """
            SELECT t.ticket_id, f.flight_number, p.name AS passenger_name, t.seat_no,
                   t.booking_channel, s.name AS staff_name, t.price, t.booking_time,
                   r.origin_code, r.destination_code
            FROM tickets t
            JOIN flights f ON t.flight_id = f.flight_id
            JOIN routes r ON f.route_id = r.route_id
            JOIN passengers p ON t.passenger_id = p.passenger_id
            LEFT JOIN staff s ON t.booked_by_staff_id = s.staff_id
            WHERE t.status='Confirmed'
        """

    def _populate(self, rows):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for r in rows:
            self.tree.insert("", "end", values=(
                r["ticket_id"], r["flight_number"], r["passenger_name"], r["seat_no"],
                r["booking_channel"], r["staff_name"] or "Online (self-service)",
                f"{r['price']:.0f}", r["booking_time"].replace("T", " ")
            ))

    def _show_all_tickets(self):
        rows = db.fetch_all(self._base_query() + " ORDER BY t.booking_time DESC LIMIT 300")
        self._populate(rows)

    def _search(self):
        origin = self.origin_entry.get().strip().upper()
        dest = self.dest_entry.get().strip().upper()
        query = self._base_query()
        params = []
        if origin:
            query += " AND r.origin_code = ?"
            params.append(origin)
        if dest:
            query += " AND r.destination_code = ?"
            params.append(dest)
        query += " ORDER BY t.booking_time DESC LIMIT 300"
        rows = db.fetch_all(query, tuple(params))
        self._populate(rows)


if __name__ == "__main__":
    app = AirlineApp()
    app.mainloop()
