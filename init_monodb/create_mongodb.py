from __future__ import annotations

from typing import Any

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine


# Для типизации MongoDB
MongoDB = Database[Any]


class PostgreSQLToMongoMigrator:
    def __init__(self, pg_async_url: str, mongo_uri: str):
        self.pg_async_url = pg_async_url
        self.mongo_uri = mongo_uri

    async def migrate(self) -> None:
        """Основной метод для выполнения миграции данных"""
        engine = create_async_engine(
            self.pg_async_url,
            connect_args={"server_settings": {"search_path": "travel_db"}},
            echo=True,
            pool_pre_ping=True,
        )
        try:
            mongo_client: MongoClient[Any] = MongoClient(
                self.mongo_uri, serverSelectionTimeoutMS=5000
            )
            mongo_client.admin.command("ping")  # Проверка подключения
            print("MongoDB подключена успешно!")
        except ConnectionFailure as e:
            print(f"Ошибка подключения к MongoDB: {e}")
        db: MongoDB = mongo_client["travel_db"]

        # Очистка MongoDB
        for collection in db.list_collection_names():
            db.drop_collection(collection)

        # Миграция данных
        async with AsyncSession(engine) as session:
            await self._migrate_cities(session, db)
            await self._migrate_users(session, db)
            await self._migrate_directory_routes(session, db)
            await self._migrate_entertainments(session, db)
            await self._migrate_accommodations(session, db)
            await self._migrate_travels(session, db)
            await self._migrate_routes(session, db)

        # Создание индексов
        self._create_indexes(db)

        await engine.dispose()
        mongo_client.close()
        print("Миграция успешно завершена")

    async def _migrate_cities(self, session: AsyncSession, db: MongoDB) -> None:
        """Миграция данных о городах"""
        result = await session.execute(
            text("SELECT city_id, name FROM city")
        )  # Note: added id here
        rows = result.fetchall()
        cities = [{"_id": row[0], "name": row[1]} for row in rows]

        if cities:
            db.cities.insert_many(cities)
            print(f"Inserted {len(cities)} cities")
        else:
            print("No cities found in the database")

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

    async def _migrate_directory_routes(
        self, session: AsyncSession, db: MongoDB
    ) -> None:
        """Миграция справочника маршрутов"""
        result = await session.execute(
            text(
                """
            SELECT id, type_transport, departure_city, arrival_city, distance, price
            FROM directory_route
        """
            )
        )
        routes: list[dict[str, Any]] = [
            {
                "_id": row[0],
                "type_transport": row[1],
                "departure_city_id": row[2],
                "arrival_city_id": row[3],
                "distance": row[4],
                "price": row[5],
            }
            for row in result.fetchall()
        ]
        if routes:
            db.directory_routes.insert_many(routes)

    async def _migrate_entertainments(self, session: AsyncSession, db: MongoDB) -> None:
        """Миграция данных о развлечениях"""
        result = await session.execute(
            text(
                """
            SELECT id, duration, address, event_name, event_time, city
            FROM entertainment
        """
            )
        )
        entertainments: list[dict[str, Any]] = [
            {
                "_id": row[0],
                "duration": row[1],
                "address": row[2],
                "event_name": row[3],
                "event_time": row[4],
                "city_id": row[5],
            }
            for row in result.fetchall()
        ]
        if entertainments:
            db.entertainments.insert_many(entertainments)

    async def _migrate_accommodations(self, session: AsyncSession, db: MongoDB) -> None:
        """Миграция данных о размещении"""
        result = await session.execute(
            text(
                """
            SELECT id, price, address, name, type, rating, check_in, check_out, city
            FROM accommodations
        """
            )
        )
        accommodations: list[dict[str, Any]] = [
            {
                "_id": row[0],
                "price": row[1],
                "address": row[2],
                "name": row[3],
                "type": row[4],
                "rating": row[5],
                "check_in": row[6],
                "check_out": row[7],
                "city_id": row[8],
            }
            for row in result.fetchall()
        ]
        if accommodations:
            db.accommodations.insert_many(accommodations)

    async def _migrate_travels(self, session: AsyncSession, db: MongoDB) -> None:
        """Миграция данных о путешествиях"""
        result = await session.execute(text("SELECT id, status FROM travel"))
        travels_raw = result.fetchall()
        result = await session.execute(
            text("SELECT travel_id, users_id FROM users_travel")
        )
        users_map: dict[int, list[int]] = {}
        for travel_id, user_id in result.fetchall():
            users_map.setdefault(travel_id, []).append(user_id)

        # Получаем связанные accommodations
        result = await session.execute(
            text("SELECT travel_id, accommodation_id FROM travel_accommodations")
        )
        accommodations_map: dict[int, list[int]] = {}
        for travel_id, accommodation_id in result.fetchall():
            accommodations_map.setdefault(travel_id, []).append(accommodation_id)

        # Получаем связанные entertainments
        result = await session.execute(
            text("SELECT travel_id, entertainment_id FROM travel_entertainment")
        )
        entertainments_map: dict[int, list[int]] = {}
        for travel_id, entertainment_id in result.fetchall():
            entertainments_map.setdefault(travel_id, []).append(entertainment_id)

        # Финальная сборка документов для MongoDB
        travels: list[dict[str, Any]] = []
        for row in travels_raw:
            travel_id = row[0]
            travel_doc = {
                "_id": travel_id,
                "status": row[1],
                "users": users_map.get(travel_id, []),
                "accommodations": accommodations_map.get(travel_id, []),
                "entertainments": entertainments_map.get(travel_id, []),
            }
            travels.append(travel_doc)
        if travels:
            db.travels.insert_many(travels)

    async def _migrate_routes(self, session: AsyncSession, db: MongoDB) -> None:
        routes = []
        travel_result = await session.execute(text("SELECT id, status FROM travel"))
        travels_raw = travel_result.fetchall()

        # users_travel
        result = await session.execute(
            text("SELECT travel_id, users_id FROM users_travel")
        )
        users_map: dict[int, list[int]] = {}
        for travel_id, user_id in result.fetchall():
            users_map.setdefault(travel_id, []).append(user_id)

        # travel_accommodations
        result = await session.execute(
            text("SELECT travel_id, accommodation_id FROM travel_accommodations")
        )
        accommodations_map: dict[int, list[int]] = {}
        for travel_id, accommodation_id in result.fetchall():
            accommodations_map.setdefault(travel_id, []).append(accommodation_id)

        # travel_entertainment
        result = await session.execute(
            text("SELECT travel_id, entertainment_id FROM travel_entertainment")
        )
        entertainments_map: dict[int, list[int]] = {}
        for travel_id, entertainment_id in result.fetchall():
            entertainments_map.setdefault(travel_id, []).append(entertainment_id)

        # Словарь travel_id -> full travel doc
        travel_docs: dict[int, dict[str, Any]] = {
            row[0]: {
                "_id": row[0],
                "status": row[1],
                "users": users_map.get(row[0], []),
                "accommodations": accommodations_map.get(row[0], []),
                "entertainments": entertainments_map.get(row[0], []),
            }
            for row in travels_raw
        }

        route_result = await session.execute(text("SELECT * FROM travel_db.route"))
        for row in route_result.fetchall():
            d_route_result = await session.execute(
                text("SELECT * FROM travel_db.directory_route WHERE id = :id"),
                {"id": row[1]},  # row[1] = d_route_id
            )
            d_route_data = d_route_result.fetchone()
            travel_id = row[2]
            travel_data = travel_docs.get(travel_id)

            routes.append(
                {
                    "_id": row[0],
                    "d_route": {
                        "_id": d_route_data[0],
                        "type_transport": d_route_data[1],
                        "departure_city_id": d_route_data[2],
                        "arrival_city_id": d_route_data[3],
                        "distance": d_route_data[4],
                        "price": d_route_data[5],
                    },
                    "travel": travel_data,
                    "start_time": row[3],
                    "end_time": row[4],
                    "type": row[5],
                }
            )

        if routes:
            db.routes.insert_many(routes)

    def _create_indexes(self, db: MongoDB) -> None:
        """Создание индексов в MongoDB"""
        db.cities.create_index("name", unique=True)
        db.users.create_index("email", unique=True)
        db.users.create_index("login", unique=True)
        db.users.create_index("passport", unique=True)
        db.users.create_index("phone", unique=True)
        db.directory_routes.create_index(
            [("departure_city_id", 1), ("arrival_city_id", 1)]
        )


async def async_init_mongodb() -> None:
    """Асинхронная инициализация MongoDB"""
    pg_async_url = "postgresql+asyncpg://egor:egor@postgres_container_ppo:5432/mydb"
    mongo_uri = "mongodb://admin:password@mongodb:27017"

    migrator = PostgreSQLToMongoMigrator(pg_async_url, mongo_uri)
    await migrator.migrate()
