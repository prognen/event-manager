from __future__ import annotations

from typing import Any

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine


MongoDB = Database[Any]


class PostgreSQLToMongoMigrator:
    def __init__(self, pg_async_url: str, mongo_uri: str):
        self.pg_async_url = pg_async_url
        self.mongo_uri = mongo_uri

    async def migrate(self) -> None:
        """Основной метод для выполнения миграции данных"""
        engine = create_async_engine(
            self.pg_async_url,
            connect_args={"server_settings": {"search_path": "event_db"}},
            echo=True,
            pool_pre_ping=True,
        )
        try:
            mongo_client: MongoClient[Any] = MongoClient(
                self.mongo_uri, serverSelectionTimeoutMS=5000
            )
            mongo_client.admin.command("ping")
            print("MongoDB подключена успешно!")
        except ConnectionFailure as e:
            print(f"Ошибка подключения к MongoDB: {e}")
        db: MongoDB = mongo_client["event_db"]

        for collection in db.list_collection_names():
            db.drop_collection(collection)

        async with AsyncSession(engine) as session:
            await self._migrate_venues(session, db)
            await self._migrate_users(session, db)
            await self._migrate_programs(session, db)
            await self._migrate_activities(session, db)
            await self._migrate_lodgings(session, db)
            await self._migrate_events(session, db)
            await self._migrate_sessions(session, db)

        self._create_indexes(db)

        await engine.dispose()
        mongo_client.close()
        print("Миграция успешно завершена")

    async def _migrate_venues(self, session: AsyncSession, db: MongoDB) -> None:
        """Миграция данных о площадках"""
        result = await session.execute(text("SELECT venue_id, name FROM venue"))
        rows = result.fetchall()
        venues = [{"_id": row[0], "name": row[1]} for row in rows]
        if venues:
            db.venues.insert_many(venues)
            print(f"Inserted {len(venues)} venues")
        else:
            print("No venues found in the database")

    async def _migrate_users(self, session: AsyncSession, db: MongoDB) -> None:
        """Миграция данных пользователей"""
        result = await session.execute(
            text(
                """
            SELECT id, full_name, passport, phone, email, login, password, is_admin
            FROM users
        """
            )
        )
        users: list[dict[str, Any]] = [
            {
                "_id": row[0],
                "full_name": row[1],
                "passport": row[2],
                "phone": row[3],
                "email": row[4],
                "login": row[5],
                "password": row[6],
                "is_admin": row[7],
            }
            for row in result.fetchall()
        ]
        if users:
            db.users.insert_many(users)

    async def _migrate_programs(self, session: AsyncSession, db: MongoDB) -> None:
        """Миграция программ маршрутов"""
        result = await session.execute(
            text(
                """
            SELECT id, type_transport, from_venue, to_venue, distance, cost
            FROM program
        """
            )
        )
        programs: list[dict[str, Any]] = [
            {
                "_id": row[0],
                "type_transport": row[1],
                "from_venue_id": row[2],
                "to_venue_id": row[3],
                "distance": row[4],
                "cost": row[5],
            }
            for row in result.fetchall()
        ]
        if programs:
            db.programs.insert_many(programs)

    async def _migrate_activities(self, session: AsyncSession, db: MongoDB) -> None:
        """Миграция данных об активностях"""
        result = await session.execute(
            text(
                """
            SELECT id, duration, address, activity_type, activity_time, venue
            FROM activity
        """
            )
        )
        activities: list[dict[str, Any]] = [
            {
                "_id": row[0],
                "duration": row[1],
                "address": row[2],
                "activity_type": row[3],
                "activity_time": row[4],
                "venue_id": row[5],
            }
            for row in result.fetchall()
        ]
        if activities:
            db.activities.insert_many(activities)

    async def _migrate_lodgings(self, session: AsyncSession, db: MongoDB) -> None:
        """Миграция данных о размещении"""
        result = await session.execute(
            text(
                """
            SELECT id, price, address, name, type, rating, check_in, check_out, venue
            FROM lodgings
        """
            )
        )
        lodgings: list[dict[str, Any]] = [
            {
                "_id": row[0],
                "price": row[1],
                "address": row[2],
                "name": row[3],
                "type": row[4],
                "rating": row[5],
                "check_in": row[6],
                "check_out": row[7],
                "venue_id": row[8],
            }
            for row in result.fetchall()
        ]
        if lodgings:
            db.lodgings.insert_many(lodgings)

    async def _migrate_events(self, session: AsyncSession, db: MongoDB) -> None:
        """Миграция данных о мероприятиях"""
        result = await session.execute(text("SELECT id, status FROM event"))
        events_raw = result.fetchall()

        result = await session.execute(
            text("SELECT event_id, users_id FROM users_event")
        )
        users_map: dict[int, list[int]] = {}
        for event_id, user_id in result.fetchall():
            users_map.setdefault(event_id, []).append(user_id)

        result = await session.execute(
            text("SELECT event_id, lodging_id FROM event_lodgings")
        )
        lodgings_map: dict[int, list[int]] = {}
        for event_id, lodging_id in result.fetchall():
            lodgings_map.setdefault(event_id, []).append(lodging_id)

        result = await session.execute(
            text("SELECT event_id, activity_id FROM event_activity")
        )
        activities_map: dict[int, list[int]] = {}
        for event_id, activity_id in result.fetchall():
            activities_map.setdefault(event_id, []).append(activity_id)

        events: list[dict[str, Any]] = []
        for row in events_raw:
            event_id = row[0]
            event_doc = {
                "_id": event_id,
                "status": row[1],
                "users": users_map.get(event_id, []),
                "lodgings": lodgings_map.get(event_id, []),
                "activities": activities_map.get(event_id, []),
            }
            events.append(event_doc)
        if events:
            db.events.insert_many(events)

    async def _migrate_sessions(self, session: AsyncSession, db: MongoDB) -> None:
        """Миграция данных о сессиях"""
        result = await session.execute(text("SELECT id, status FROM event"))
        events_raw = result.fetchall()

        result = await session.execute(
            text("SELECT event_id, users_id FROM users_event")
        )
        users_map: dict[int, list[int]] = {}
        for event_id, user_id in result.fetchall():
            users_map.setdefault(event_id, []).append(user_id)

        result = await session.execute(
            text("SELECT event_id, lodging_id FROM event_lodgings")
        )
        lodgings_map: dict[int, list[int]] = {}
        for event_id, lodging_id in result.fetchall():
            lodgings_map.setdefault(event_id, []).append(lodging_id)

        result = await session.execute(
            text("SELECT event_id, activity_id FROM event_activity")
        )
        activities_map: dict[int, list[int]] = {}
        for event_id, activity_id in result.fetchall():
            activities_map.setdefault(event_id, []).append(activity_id)

        # Словарь event_id -> full event doc
        event_docs: dict[int, dict[str, Any]] = {
            row[0]: {
                "_id": row[0],
                "status": row[1],
                "users": users_map.get(row[0], []),
                "lodgings": lodgings_map.get(row[0], []),
                "activities": activities_map.get(row[0], []),
            }
            for row in events_raw
        }

        session_result = await session.execute(
            text("SELECT * FROM event_db.session")
        )
        sessions = []
        for row in session_result.fetchall():
            program_result = await session.execute(
                text("SELECT * FROM event_db.program WHERE id = :id"),
                {"id": row[1]},
            )
            program_data = program_result.fetchone()
            event_id = row[2]
            event_data = event_docs.get(event_id)

            sessions.append(
                {
                    "_id": row[0],
                    "program": {
                        "_id": program_data[0],
                        "type_transport": program_data[1],
                        "from_venue_id": program_data[2],
                        "to_venue_id": program_data[3],
                        "distance": program_data[4],
                        "cost": program_data[5],
                    },
                    "event": event_data,
                    "start_time": row[3],
                    "end_time": row[4],
                    "type": row[5],
                }
            )

        if sessions:
            db.sessions.insert_many(sessions)

    def _create_indexes(self, db: MongoDB) -> None:
        """Создание индексов в MongoDB"""
        db.venues.create_index("name", unique=True)
        db.users.create_index("email", unique=True)
        db.users.create_index("login", unique=True)
        db.users.create_index("passport", unique=True)
        db.users.create_index("phone", unique=True)
        db.programs.create_index([("from_venue_id", 1), ("to_venue_id", 1)])


async def async_init_mongodb() -> None:
    """Асинхронная инициализация MongoDB"""
    pg_async_url = "postgresql+asyncpg://egor:egor@postgres_container_ppo:5432/mydb"
    mongo_uri = "mongodb://admin:password@mongodb:27017"

    migrator = PostgreSQLToMongoMigrator(pg_async_url, mongo_uri)
    await migrator.migrate()
