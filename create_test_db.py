from __future__ import annotations

from sqlalchemy import TIMESTAMP
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import Table
from sqlalchemy import create_engine
from sqlalchemy.sql import text


engine = create_engine("postgresql://egor@localhost:5432/postgres")
with engine.begin() as connection:
    connection.execute(text("CREATE SCHEMA IF NOT EXISTS event_db"))

metadata = MetaData(schema="event_db")

venue = Table(
    "venue",
    metadata,
    Column("venue_id", Integer, primary_key=True),
    Column("name", String(100), unique=True, nullable=False),
    schema="event_db",
)

program = Table(
    "program",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("type_transport", String(100), nullable=False),
    Column("from_venue", Integer, ForeignKey("event_db.venue.venue_id"), nullable=False),
    Column("to_venue", Integer, ForeignKey("event_db.venue.venue_id"), nullable=False),
    Column("distance", Integer, nullable=False),
    Column("cost", Integer, nullable=False),
    schema="event_db",
)

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("full_name", String(255), nullable=False),
    Column("passport", String(20), unique=True, nullable=False),
    Column("phone", String(20), unique=True, nullable=False),
    Column("email", String(100), unique=True, nullable=False),
    Column("login", String(50), unique=True, nullable=False),
    Column("password", String(255), nullable=False),
    Column("is_admin", Boolean, nullable=False, default=False),
    schema="event_db",
)

activity = Table(
    "activity",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("duration", String(50), nullable=False),
    Column("address", String(255), nullable=False),
    Column("activity_type", String(255), nullable=False),
    Column("activity_time", TIMESTAMP, nullable=False),
    Column("venue", Integer, ForeignKey("event_db.venue.venue_id"), nullable=False),
    schema="event_db",
)

lodgings = Table(
    "lodgings",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("price", Integer, nullable=False),
    Column("address", String(255), nullable=False),
    Column("name", String(255), nullable=False),
    Column("type", String(50), nullable=False),
    Column("rating", Integer, nullable=False),
    Column("check_in", TIMESTAMP, nullable=False),
    Column("check_out", TIMESTAMP, nullable=False),
    Column("venue", Integer, ForeignKey("event_db.venue.venue_id"), nullable=False),
    schema="event_db",
)

event = Table(
    "event",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("status", String(50), nullable=False),
    schema="event_db",
)

session = Table(
    "session",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("program_id", Integer, ForeignKey("event_db.program.id"), nullable=False),
    Column("event_id", Integer, ForeignKey("event_db.event.id"), nullable=False),
    Column("start_time", TIMESTAMP, nullable=False),
    Column("end_time", TIMESTAMP, nullable=False),
    Column("type", String(20), nullable=False),
    schema="event_db",
)

event_activity = Table(
    "event_activity",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("event_id", Integer, ForeignKey("event_db.event.id"), nullable=False),
    Column("activity_id", Integer, ForeignKey("event_db.activity.id"), nullable=False),
    schema="event_db",
)

event_lodgings = Table(
    "event_lodgings",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("event_id", Integer, ForeignKey("event_db.event.id"), nullable=False),
    Column("lodging_id", Integer, ForeignKey("event_db.lodgings.id"), nullable=False),
    schema="event_db",
)

users_event = Table(
    "users_event",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("event_id", Integer, ForeignKey("event_db.event.id"), nullable=False),
    Column("users_id", Integer, ForeignKey("event_db.users.id"), nullable=False),
    schema="event_db",
)
