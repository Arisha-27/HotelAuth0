"""
Step 60-61: Hotel Database Simulation with Multi-Hotel Support
SQLite-backed database for hotels, rooms, guests, bookings, and incident logs.
Supports multi-hotel chains with proper data isolation.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from contextlib import contextmanager

from pydantic import BaseModel, Field

logger = logging.getLogger("lunaris.database")

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "lunaris.db")


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class Hotel(BaseModel):
    hotel_id: str
    name: str
    address: str
    city: str
    country: str
    total_rooms: int
    stars: int = 4
    status: str = "active"  # active, maintenance, closed
    metadata: dict = Field(default_factory=dict)


class Room(BaseModel):
    room_id: str
    hotel_id: str
    room_number: str
    floor: int
    room_type: str = "standard"  # standard, deluxe, suite, penthouse
    status: str = "available"  # available, occupied, maintenance, reserved
    price_per_night: float = 150.0
    amenities: list[str] = Field(default_factory=list)
    current_guest_id: Optional[str] = None


class Guest(BaseModel):
    guest_id: str
    name: str
    email: str
    phone: str
    vip_level: int = 0  # 0=regular, 1=silver, 2=gold, 3=platinum
    loyalty_points: int = 0
    preferences: dict = Field(default_factory=dict)
    visit_count: int = 0


class Booking(BaseModel):
    booking_id: str
    hotel_id: str
    room_id: str
    guest_id: str
    check_in: str
    check_out: str
    status: str = "confirmed"  # confirmed, checked_in, checked_out, cancelled
    total_price: float = 0.0
    special_requests: str = ""
    created_at: str = ""


class IncidentLog(BaseModel):
    incident_id: str
    hotel_id: str
    incident_type: str  # fire, security_breach, medical, maintenance, guest_complaint
    severity: str = "medium"  # low, medium, high, critical
    location: str = ""
    description: str
    reported_by: str = "system"
    status: str = "open"  # open, investigating, resolved, closed
    resolution: str = ""
    created_at: str = ""
    resolved_at: Optional[str] = None


class FinanceRecord(BaseModel):
    record_id: str
    hotel_id: str
    category: str  # revenue, expense, refund, penalty
    amount: float
    currency: str = "USD"
    description: str
    reference_id: str = ""  # booking_id or incident_id
    created_at: str = ""


# ─────────────────────────────────────────────
# Database Manager
# ─────────────────────────────────────────────
class HotelDatabase:
    """
    SQLite-backed hotel chain database with full CRUD operations.
    Pre-seeded with realistic demo data for 3 hotels.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        self._seed_data()

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
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

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS hotels (
                    hotel_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    address TEXT,
                    city TEXT,
                    country TEXT,
                    total_rooms INTEGER DEFAULT 30,
                    stars INTEGER DEFAULT 4,
                    status TEXT DEFAULT 'active',
                    metadata TEXT DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS rooms (
                    room_id TEXT PRIMARY KEY,
                    hotel_id TEXT NOT NULL,
                    room_number TEXT NOT NULL,
                    floor INTEGER,
                    room_type TEXT DEFAULT 'standard',
                    status TEXT DEFAULT 'available',
                    price_per_night REAL DEFAULT 150.0,
                    amenities TEXT DEFAULT '[]',
                    current_guest_id TEXT,
                    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
                );

                CREATE TABLE IF NOT EXISTS guests (
                    guest_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    vip_level INTEGER DEFAULT 0,
                    loyalty_points INTEGER DEFAULT 0,
                    preferences TEXT DEFAULT '{}',
                    visit_count INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id TEXT PRIMARY KEY,
                    hotel_id TEXT NOT NULL,
                    room_id TEXT NOT NULL,
                    guest_id TEXT NOT NULL,
                    check_in TEXT,
                    check_out TEXT,
                    status TEXT DEFAULT 'confirmed',
                    total_price REAL DEFAULT 0.0,
                    special_requests TEXT DEFAULT '',
                    created_at TEXT,
                    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id),
                    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
                    FOREIGN KEY (guest_id) REFERENCES guests(guest_id)
                );

                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    hotel_id TEXT NOT NULL,
                    incident_type TEXT,
                    severity TEXT DEFAULT 'medium',
                    location TEXT DEFAULT '',
                    description TEXT,
                    reported_by TEXT DEFAULT 'system',
                    status TEXT DEFAULT 'open',
                    resolution TEXT DEFAULT '',
                    created_at TEXT,
                    resolved_at TEXT,
                    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
                );

                CREATE TABLE IF NOT EXISTS finance (
                    record_id TEXT PRIMARY KEY,
                    hotel_id TEXT NOT NULL,
                    category TEXT,
                    amount REAL,
                    currency TEXT DEFAULT 'USD',
                    description TEXT,
                    reference_id TEXT DEFAULT '',
                    created_at TEXT,
                    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
                );

                CREATE INDEX IF NOT EXISTS idx_rooms_hotel ON rooms(hotel_id);
                CREATE INDEX IF NOT EXISTS idx_bookings_hotel ON bookings(hotel_id);
                CREATE INDEX IF NOT EXISTS idx_bookings_guest ON bookings(guest_id);
                CREATE INDEX IF NOT EXISTS idx_incidents_hotel ON incidents(hotel_id);
                CREATE INDEX IF NOT EXISTS idx_finance_hotel ON finance(hotel_id);
            """)

    def _seed_data(self):
        """Seed database with realistic demo data if empty."""
        with self._get_conn() as conn:
            count = conn.execute("SELECT COUNT(*) FROM hotels").fetchone()[0]
            if count > 0:
                return

            now = datetime.now(timezone.utc)

            # ── Hotels ──
            hotels = [
                ("hotel-downtown", "Lunaris Downtown", "123 Business Ave", "New York", "USA", 30, 5),
                ("hotel-airport", "Lunaris Airport Gateway", "1 Terminal Dr", "Chicago", "USA", 45, 4),
                ("hotel-resort", "Lunaris Beach Resort", "500 Ocean Blvd", "Miami", "USA", 60, 5),
            ]
            conn.executemany(
                "INSERT INTO hotels (hotel_id, name, address, city, country, total_rooms, stars) VALUES (?,?,?,?,?,?,?)",
                hotels,
            )

            # ── Rooms ──
            room_types = {
                1: ("standard", 149.0, ["WiFi", "TV", "Mini-bar"]),
                2: ("deluxe", 249.0, ["WiFi", "TV", "Mini-bar", "City View", "Room Service"]),
                3: ("suite", 449.0, ["WiFi", "TV", "Mini-bar", "Ocean View", "Room Service", "Jacuzzi", "Lounge"]),
            }
            rooms_data = []
            for hotel_id, _, _, _, _, total, _ in hotels:
                for floor in range(1, 4):
                    for room_num in range(1, 11):
                        rnum = f"{floor}{room_num:02d}"
                        rtype, price, amenities = room_types.get(floor, room_types[1])
                        status = "occupied" if room_num <= 4 else "available"
                        rooms_data.append((
                            f"{hotel_id}-room-{rnum}", hotel_id, rnum, floor,
                            rtype, status, price, json.dumps(amenities), None,
                        ))
            conn.executemany(
                "INSERT INTO rooms (room_id, hotel_id, room_number, floor, room_type, status, price_per_night, amenities, current_guest_id) VALUES (?,?,?,?,?,?,?,?,?)",
                rooms_data,
            )

            # ── Guests ──
            guests = [
                ("guest-001", "Alice Chen", "alice@example.com", "+1234567001", 3, 15400, '{"room_temp": 21, "pillow": "soft", "newspaper": "digital"}', 12),
                ("guest-002", "Bob Martinez", "bob@example.com", "+1234567002", 2, 8200, '{"room_temp": 23, "late_checkout": true}', 7),
                ("guest-003", "Dr. Sarah Johnson", "sarah@example.com", "+1234567003", 3, 22000, '{"allergies": ["nuts"], "room_temp": 20}', 18),
                ("guest-004", "James Williams", "james@example.com", "+1234567004", 1, 3100, '{}', 3),
                ("guest-005", "Maria Gonzalez", "maria@example.com", "+1234567005", 0, 500, '{}', 1),
                ("guest-006", "David Kim", "david@example.com", "+1234567006", 2, 9800, '{"room_temp": 22, "floor_preference": "high"}', 9),
                ("guest-007", "Emma Brown", "emma@example.com", "+1234567007", 0, 200, '{}', 1),
                ("guest-008", "Ahmed Hassan", "ahmed@example.com", "+1234567008", 1, 4500, '{"dietary": "halal"}', 4),
            ]
            conn.executemany(
                "INSERT INTO guests (guest_id, name, email, phone, vip_level, loyalty_points, preferences, visit_count) VALUES (?,?,?,?,?,?,?,?)",
                guests,
            )

            # ── Bookings ──
            bookings = [
                ("BK-20260401-001", "hotel-downtown", "hotel-downtown-room-101", "guest-001",
                 (now - timedelta(days=2)).isoformat(), (now + timedelta(days=3)).isoformat(),
                 "checked_in", 745.0, "Late checkout requested", now.isoformat()),
                ("BK-20260401-002", "hotel-downtown", "hotel-downtown-room-201", "guest-003",
                 (now - timedelta(days=1)).isoformat(), (now + timedelta(days=5)).isoformat(),
                 "checked_in", 1245.0, "Nut-free room", now.isoformat()),
                ("BK-20260401-003", "hotel-airport", "hotel-airport-room-102", "guest-002",
                 now.isoformat(), (now + timedelta(days=2)).isoformat(),
                 "confirmed", 298.0, "", now.isoformat()),
                ("BK-20260401-004", "hotel-resort", "hotel-resort-room-301", "guest-006",
                 (now + timedelta(days=1)).isoformat(), (now + timedelta(days=7)).isoformat(),
                 "confirmed", 3143.0, "Anniversary celebration", now.isoformat()),
            ]
            conn.executemany(
                "INSERT INTO bookings (booking_id, hotel_id, room_id, guest_id, check_in, check_out, status, total_price, special_requests, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                bookings,
            )

            # ── Incidents ──
            incidents = [
                ("INC-001", "hotel-downtown", "maintenance", "low", "Floor 2 - Room 203",
                 "AC unit making unusual noise", "housekeeping", "open", "", now.isoformat(), None),
                ("INC-002", "hotel-airport", "guest_complaint", "medium", "Floor 1 - Room 104",
                 "Guest reports noisy neighbors", "front_desk", "investigating", "", now.isoformat(), None),
            ]
            conn.executemany(
                "INSERT INTO incidents (incident_id, hotel_id, incident_type, severity, location, description, reported_by, status, resolution, created_at, resolved_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                incidents,
            )

            # ── Finance ──
            finance = [
                ("FIN-001", "hotel-downtown", "revenue", 745.0, "USD", "Booking BK-20260401-001 payment", "BK-20260401-001", now.isoformat()),
                ("FIN-002", "hotel-downtown", "revenue", 1245.0, "USD", "Booking BK-20260401-002 payment", "BK-20260401-002", now.isoformat()),
                ("FIN-003", "hotel-airport", "revenue", 298.0, "USD", "Booking BK-20260401-003 payment", "BK-20260401-003", now.isoformat()),
                ("FIN-004", "hotel-resort", "revenue", 3143.0, "USD", "Booking BK-20260401-004 payment", "BK-20260401-004", now.isoformat()),
                ("FIN-005", "hotel-downtown", "expense", -320.0, "USD", "Emergency HVAC repair", "INC-001", now.isoformat()),
            ]
            conn.executemany(
                "INSERT INTO finance (record_id, hotel_id, category, amount, currency, description, reference_id, created_at) VALUES (?,?,?,?,?,?,?,?)",
                finance,
            )

            logger.info("Database seeded with demo data for 3 hotels")

    # ─────────────────────────────────────────
    # Hotel CRUD
    # ─────────────────────────────────────────
    def get_hotels(self) -> list[dict]:
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM hotels").fetchall()
            return [dict(r) for r in rows]

    def get_hotel(self, hotel_id: str) -> Optional[dict]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM hotels WHERE hotel_id = ?", (hotel_id,)).fetchone()
            return dict(row) if row else None

    # ─────────────────────────────────────────
    # Room CRUD
    # ─────────────────────────────────────────
    def get_rooms(self, hotel_id: str, status: Optional[str] = None, floor: Optional[int] = None) -> list[dict]:
        with self._get_conn() as conn:
            query = "SELECT * FROM rooms WHERE hotel_id = ?"
            params = [hotel_id]
            if status:
                query += " AND status = ?"
                params.append(status)
            if floor:
                query += " AND floor = ?"
                params.append(floor)
            rows = conn.execute(query, params).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["amenities"] = json.loads(d["amenities"]) if d["amenities"] else []
                result.append(d)
            return result

    def update_room_status(self, room_id: str, status: str, guest_id: Optional[str] = None) -> bool:
        with self._get_conn() as conn:
            conn.execute("UPDATE rooms SET status = ?, current_guest_id = ? WHERE room_id = ?",
                        (status, guest_id, room_id))
            return conn.total_changes > 0

    # ─────────────────────────────────────────
    # Guest CRUD
    # ─────────────────────────────────────────
    def get_guest(self, guest_id: str) -> Optional[dict]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM guests WHERE guest_id = ?", (guest_id,)).fetchone()
            if row:
                d = dict(row)
                d["preferences"] = json.loads(d["preferences"]) if d["preferences"] else {}
                return d
            return None

    def get_guests(self, vip_only: bool = False) -> list[dict]:
        with self._get_conn() as conn:
            query = "SELECT * FROM guests"
            if vip_only:
                query += " WHERE vip_level >= 2"
            rows = conn.execute(query).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["preferences"] = json.loads(d["preferences"]) if d["preferences"] else {}
                result.append(d)
            return result

    def add_guest(self, guest: Guest) -> bool:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO guests (guest_id, name, email, phone, vip_level, loyalty_points, preferences, visit_count) VALUES (?,?,?,?,?,?,?,?)",
                (guest.guest_id, guest.name, guest.email, guest.phone, guest.vip_level,
                 guest.loyalty_points, json.dumps(guest.preferences), guest.visit_count),
            )
            return True

    # ─────────────────────────────────────────
    # Booking CRUD
    # ─────────────────────────────────────────
    def get_bookings(self, hotel_id: Optional[str] = None, guest_id: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
        with self._get_conn() as conn:
            query = "SELECT b.*, g.name as guest_name, g.vip_level FROM bookings b LEFT JOIN guests g ON b.guest_id = g.guest_id WHERE 1=1"
            params = []
            if hotel_id:
                query += " AND b.hotel_id = ?"
                params.append(hotel_id)
            if guest_id:
                query += " AND b.guest_id = ?"
                params.append(guest_id)
            if status:
                query += " AND b.status = ?"
                params.append(status)
            query += " ORDER BY b.created_at DESC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def create_booking(self, booking: Booking) -> bool:
        with self._get_conn() as conn:
            booking.created_at = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO bookings (booking_id, hotel_id, room_id, guest_id, check_in, check_out, status, total_price, special_requests, created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (booking.booking_id, booking.hotel_id, booking.room_id, booking.guest_id,
                 booking.check_in, booking.check_out, booking.status, booking.total_price,
                 booking.special_requests, booking.created_at),
            )
            return True

    def update_booking_status(self, booking_id: str, status: str) -> bool:
        with self._get_conn() as conn:
            conn.execute("UPDATE bookings SET status = ? WHERE booking_id = ?", (status, booking_id))
            return conn.total_changes > 0

    # ─────────────────────────────────────────
    # Incident CRUD
    # ─────────────────────────────────────────
    def log_incident(self, incident: IncidentLog) -> bool:
        with self._get_conn() as conn:
            incident.created_at = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO incidents (incident_id, hotel_id, incident_type, severity, location, description, reported_by, status, resolution, created_at, resolved_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (incident.incident_id, incident.hotel_id, incident.incident_type, incident.severity,
                 incident.location, incident.description, incident.reported_by, incident.status,
                 incident.resolution, incident.created_at, incident.resolved_at),
            )
            return True

    def get_incidents(self, hotel_id: Optional[str] = None, status: Optional[str] = None, severity: Optional[str] = None) -> list[dict]:
        with self._get_conn() as conn:
            query = "SELECT * FROM incidents WHERE 1=1"
            params = []
            if hotel_id:
                query += " AND hotel_id = ?"
                params.append(hotel_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            if severity:
                query += " AND severity = ?"
                params.append(severity)
            query += " ORDER BY created_at DESC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def resolve_incident(self, incident_id: str, resolution: str) -> bool:
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE incidents SET status = 'resolved', resolution = ?, resolved_at = ? WHERE incident_id = ?",
                (resolution, datetime.now(timezone.utc).isoformat(), incident_id),
            )
            return conn.total_changes > 0

    # ─────────────────────────────────────────
    # Finance CRUD
    # ─────────────────────────────────────────
    def log_finance(self, record: FinanceRecord) -> bool:
        with self._get_conn() as conn:
            record.created_at = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "INSERT INTO finance (record_id, hotel_id, category, amount, currency, description, reference_id, created_at) VALUES (?,?,?,?,?,?,?,?)",
                (record.record_id, record.hotel_id, record.category, record.amount,
                 record.currency, record.description, record.reference_id, record.created_at),
            )
            return True

    def get_finance_records(self, hotel_id: Optional[str] = None, category: Optional[str] = None) -> list[dict]:
        with self._get_conn() as conn:
            query = "SELECT * FROM finance WHERE 1=1"
            params = []
            if hotel_id:
                query += " AND hotel_id = ?"
                params.append(hotel_id)
            if category:
                query += " AND category = ?"
                params.append(category)
            query += " ORDER BY created_at DESC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_finance_summary(self, hotel_id: str) -> dict:
        """Get financial summary for a hotel."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT category, SUM(amount) as total, COUNT(*) as count FROM finance WHERE hotel_id = ? GROUP BY category",
                (hotel_id,),
            ).fetchall()
            summary = {"hotel_id": hotel_id, "categories": {}}
            grand_total = 0.0
            for r in rows:
                summary["categories"][r["category"]] = {"total": r["total"], "count": r["count"]}
                grand_total += r["total"]
            summary["grand_total"] = grand_total
            return summary

    # ─────────────────────────────────────────
    # Dashboard Queries
    # ─────────────────────────────────────────
    def get_dashboard_stats(self, hotel_id: str) -> dict:
        """Get comprehensive dashboard statistics for a hotel."""
        with self._get_conn() as conn:
            # Room stats
            rooms = conn.execute(
                "SELECT status, COUNT(*) as count FROM rooms WHERE hotel_id = ? GROUP BY status",
                (hotel_id,),
            ).fetchall()

            # Active bookings
            active_bookings = conn.execute(
                "SELECT COUNT(*) as count FROM bookings WHERE hotel_id = ? AND status IN ('confirmed', 'checked_in')",
                (hotel_id,),
            ).fetchone()

            # Open incidents
            open_incidents = conn.execute(
                "SELECT COUNT(*) as count FROM incidents WHERE hotel_id = ? AND status IN ('open', 'investigating')",
                (hotel_id,),
            ).fetchone()

            # Revenue today
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            revenue = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) as total FROM finance WHERE hotel_id = ? AND category = 'revenue' AND created_at LIKE ?",
                (hotel_id, f"{today}%"),
            ).fetchone()

            # VIP guests currently checked in
            vip_guests = conn.execute(
                """SELECT g.name, g.vip_level FROM bookings b
                   JOIN guests g ON b.guest_id = g.guest_id
                   WHERE b.hotel_id = ? AND b.status = 'checked_in' AND g.vip_level >= 2""",
                (hotel_id,),
            ).fetchall()

            return {
                "hotel_id": hotel_id,
                "rooms": {dict(r)["status"]: dict(r)["count"] for r in rooms},
                "active_bookings": active_bookings["count"],
                "open_incidents": open_incidents["count"],
                "revenue_today": revenue["total"],
                "vip_guests_present": [dict(g) for g in vip_guests],
            }


# ─────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────
hotel_db = HotelDatabase()
