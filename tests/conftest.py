from __future__ import annotations

import asyncio
import uuid

from datetime import datetime
from typing import AsyncGenerator
from typing import cast
from unittest.mock import AsyncMock
from unittest.mock import Mock
from unittest.mock import create_autospec

import os
import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

from repository.lodging_repository import LodgingRepository
from repository.venue_repository import VenueRepository
from repository.program_repository import ProgramRepository
from repository.activity_repository import ActivityRepository
from repository.session_repository import SessionRepository
from repository.event_repository import EventRepository
from repository.user_repository import UserRepository
from services.lodging_service import LodgingService
from services.venue_service import VenueService
from services.program_service import ProgramService
from services.activity_service import ActivityService
from services.session_service import SessionService
from services.event_service import EventService
from services.user_service import AuthService
from services.user_service import UserService
import warnings
from sqlalchemy.exc import SAWarning
import logging



# Игнорируем все SAWarning
warnings.filterwarnings("ignore", category=SAWarning)
warnings.filterwarnings("ignore", message="Event loop is closed")
warnings.filterwarnings(
    "ignore",
    message="The garbage collector is trying to clean up non-checked-in connection",
)

logging.getLogger("sqlalchemy.pool").setLevel(logging.CRITICAL)


@pytest.fixture
def mock_venue_repo() -> Mock:
    mock = cast(Mock, create_autospec(VenueRepository, instance=True))
    mock.delete = AsyncMock()
    mock.get_list = AsyncMock()
    mock.get_by_id = AsyncMock()
    mock.update = AsyncMock()
    mock.add = AsyncMock()
    return mock


@pytest.fixture
def mock_repo() -> Mock:
    repo = Mock(spec=ProgramRepository, autospec=True)
    repo.get_by_id = AsyncMock()
    repo.get_list = AsyncMock()
    repo.add = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.change_transport = AsyncMock()
    repo.get_by_venues = AsyncMock()
    return repo


@pytest.fixture
def mock_lodging_repo() -> Mock:
    mock = Mock(spec=LodgingRepository, autospec=True)
    mock.get_by_id = AsyncMock()
    mock.get_list = AsyncMock()
    mock.add = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def mock_activity_repo() -> Mock:
    mock = Mock(spec=ActivityRepository, autospec=True)
    mock.get_by_id = AsyncMock()
    mock.get_list = AsyncMock()
    mock.add = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest_asyncio.fixture(scope="session")
async def event_loop() -> AsyncGenerator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


_DEFAULT_DB_URL = "postgresql+asyncpg://test_user:test_password@localhost:5432/test_db"
engine = create_async_engine(
    os.environ.get("DATABASE_URL", _DEFAULT_DB_URL), echo=True
)

AsyncSessionMaker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession]:
    schema_name = f"test_{uuid.uuid4().hex[:8]}"

    async with engine.begin() as conn:
        await conn.execute(text(f"CREATE SCHEMA {schema_name}"))

    try:
        async with AsyncSessionMaker() as session:
            await session.execute(text(f"SET search_path TO {schema_name}"))

            await create_tables(session)

            await fill_test_data(session)
            await session.commit()

            try:
                yield session
            finally:
                await session.rollback()
                await session.close()

    finally:
        async with engine.begin() as conn:
            await conn.execute(text(f"DROP SCHEMA {schema_name} CASCADE"))


async def create_tables(session: AsyncSession) -> None:
    tables = [
        """
        CREATE TABLE Venue (
            venue_id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL UNIQUE
        )
        """,
        """
        CREATE TABLE Activity (
            id SERIAL PRIMARY KEY,
            duration VARCHAR NOT NULL,
            address VARCHAR NOT NULL,
            activity_type VARCHAR NOT NULL UNIQUE,
            activity_time TIMESTAMP NOT NULL,
            Venue INTEGER REFERENCES Venue(venue_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE lodgings (
            id SERIAL PRIMARY KEY,
            price INTEGER NOT NULL,
            address VARCHAR NOT NULL,
            name VARCHAR NOT NULL UNIQUE,
            type VARCHAR NOT NULL,
            rating INTEGER NOT NULL,
            check_in TIMESTAMP NOT NULL,
            check_out TIMESTAMP NOT NULL, 
            Venue INTEGER NOT NULL REFERENCES Venue(venue_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE program (
            id SERIAL PRIMARY KEY,
            type_transport VARCHAR NOT NULL,
            from_venue INT REFERENCES Venue(venue_id) ON DELETE CASCADE,
            to_venue INT REFERENCES Venue(venue_id) ON DELETE CASCADE,
            distance INT NOT NULL,
            cost INT NOT NULL
        )
        """,
        """
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            full_name VARCHAR NOT NULL,
            passport VARCHAR NOT NULL UNIQUE,
            phone VARCHAR NOT NULL UNIQUE,
            email VARCHAR NOT NULL UNIQUE,
            login VARCHAR NOT NULL UNIQUE,
            password VARCHAR NOT NULL,
            is_admin BOOLEAN NOT NULL DEFAULT FALSE
        )
        """,
        """
        CREATE TABLE Event (
            id SERIAL PRIMARY KEY,
            status VARCHAR NOT NULL
        )
        """,
        """
        CREATE TABLE event_activity (
            id SERIAL PRIMARY KEY,
            event_id INT NOT NULL,
            activity_id INT NOT NULL,
            CONSTRAINT fk_event_id FOREIGN KEY (event_id) REFERENCES Event(id) ON DELETE CASCADE,
            CONSTRAINT fk_activity_id FOREIGN KEY (activity_id) REFERENCES Activity(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE event_lodgings (
            id SERIAL PRIMARY KEY,
            event_id INT NOT NULL,
            lodging_id INT NOT NULL,
            CONSTRAINT fk_event_id FOREIGN KEY (event_id) REFERENCES Event(id) ON DELETE CASCADE,
            CONSTRAINT fk_lodging_id FOREIGN KEY (lodging_id) REFERENCES lodgings(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE users_event (
            id SERIAL PRIMARY KEY,
            event_id INT NOT NULL,
            users_id INT NOT NULL,
            CONSTRAINT fk_event_id FOREIGN KEY (event_id) REFERENCES Event(id) ON DELETE CASCADE,
            CONSTRAINT fk_users_id FOREIGN KEY (users_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE session (
            id SERIAL PRIMARY KEY,
            program_id INT NOT NULL,
            event_id INT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            type VARCHAR(20) NOT NULL,
            CONSTRAINT fk_program_id FOREIGN KEY (program_id) REFERENCES program(id) ON DELETE CASCADE,
            CONSTRAINT fk_event_id FOREIGN KEY (event_id) REFERENCES Event(id) ON DELETE CASCADE
        )
        """,
    ]

    for table_sql in tables:
        await session.execute(text(table_sql))


async def fill_test_data(session: AsyncSession) -> None:
    await session.execute(
        text(
            """
        INSERT INTO Venue (name) VALUES 
        ('Москва'), ('Воронеж'), ('Санкт-Петербург'), 
        ('Екатеринбург'), ('Калининград')
        """
        )
    )
    entertainment_data = [
        {
            "duration": "4 часа",
            "address": "Главная площадь",
            "activity_type": "Нетворкинг",
            "activity_time": datetime(2025, 4, 10, 16, 0, 0),
            "Venue": 1,
        },
        {
            "duration": "3 часа",
            "address": "ул. Кузнецова, 4",
            "activity_type": "Выставка",
            "activity_time": datetime(2025, 4, 5, 10, 0, 0),
            "Venue": 1,
        },
    ]
    for data in entertainment_data:
        await session.execute(
            text(
                """
            INSERT INTO Activity 
            (duration, address, activity_type, activity_time, Venue) 
            VALUES (:duration, :address, :activity_type, :activity_time, :Venue)"""
            ),
            data,
        )
    await session.commit()
    accommodations_data = [
        {
            "price": 33450,
            "address": "ул. Дмитриевского, 7",
            "name": "ABC",
            "type": "Квартира",
            "rating": 3,
            "check_in": datetime(2025, 4, 2, 14, 0, 0),
            "check_out": datetime(2025, 4, 6, 18, 0, 0),
            "Venue": 1,
        },
        {
            "price": 46840,
            "address": "Улица Гоголя, 12",
            "name": "Four Seasons",
            "type": "Отель",
            "rating": 5,
            "check_in": datetime(2025, 3, 29, 12, 30, 0),
            "check_out": datetime(2025, 4, 5, 18, 0, 0),
            "Venue": 1,
        },
    ]

    for data in accommodations_data:
        await session.execute(
            text(
                """
            INSERT INTO lodgings 
            (price, address, name, type, rating, check_in, check_out, Venue) 
            VALUES (:price, :address, :name, :type, :rating, :check_in, :check_out, :Venue)
        """
            ),
            data,
        )

    programs = [
        {
            "type_transport": "Паром",
            "from_venue": 3,
            "to_venue": 5,
            "distance": 966,
            "cost": 3987,
        },
        {
            "type_transport": "Самолет",
            "from_venue": 3,
            "to_venue": 5,
            "distance": 966,
            "cost": 5123,
        },
        {
            "type_transport": "Автобус",
            "from_venue": 3,
            "to_venue": 4,
            "distance": 1840,
            "cost": 3796,
        },
        {
            "type_transport": "Поезд",
            "from_venue": 3,
            "to_venue": 5,
            "distance": 966,
            "cost": 2541,
        },
        {
            "type_transport": "Автобус",
            "from_venue": 3,
            "to_venue": 5,
            "distance": 966,
            "cost": 4756,
        },
        {
            "type_transport": "Самолет",
            "from_venue": 3,
            "to_venue": 4,
            "distance": 1840,
            "cost": 8322,
        },
        {
            "type_transport": "Поезд",
            "from_venue": 3,
            "to_venue": 4,
            "distance": 1840,
            "cost": 4305,
        },
        {
            "type_transport": "Самолет",
            "from_venue": 5,
            "to_venue": 4,
            "distance": 3025,
            "cost": 10650,
        },
        {
            "type_transport": "Поезд",
            "from_venue": 5,
            "to_venue": 4,
            "distance": 3025,
            "cost": 5988,
        },
        {
            "type_transport": "Самолет",
            "from_venue": 1,
            "to_venue": 2,
            "distance": 467,
            "cost": 2223,
        },
        {
            "type_transport": "Поезд",
            "from_venue": 1,
            "to_venue": 2,
            "distance": 515,
            "cost": 1911,
        },
        {
            "type_transport": "Поезд",
            "from_venue": 4,
            "to_venue": 1,
            "distance": 1780,
            "cost": 3500,
        },
    ]
    for data in programs:
        await session.execute(
            text(
                "INSERT INTO program (type_transport, from_venue, "
                "to_venue, distance, cost) "
                "VALUES (:type_transport, :from_venue, :to_venue, :distance, :cost)"
            ),
            data,
        )
    users = [
        {
            "fio": "Власов Егор Витальевич",
            "number_passport": "1111111111",
            "phone_number": "89261111111",
            "email": "egor@vlasov.info",
            "login": "user1",
            "password": "123!e5T78",
        },
        {
            "fio": "Иванов Иван Иванович",
            "number_passport": "2222222222",
            "phone_number": "89262222222",
            "email": "ivanov@ivanov.com",
            "login": "user2",
            "password": "456!f6R89",
        },
        {
            "fio": "Петров Петр Петрович",
            "number_passport": "3333333333",
            "phone_number": "89263333333",
            "email": "petrov@petrov.com",
            "login": "user3",
            "password": "789!g7T90",
        },
    ]
    for user_data in users:
        await session.execute(
            text(
                """
            INSERT INTO users (full_name, passport, phone, email, login, password, is_admin)
            VALUES (:fio, :number_passport, :phone_number, :email, :login, :password, false)
        """
            ),
            user_data,
        )

    events_data = [
        {"status": "Активное"},
        {"status": "Завершено"},
    ]
    tr_ent = [(1, 2), (2, 1)]
    tr_a = [(1, 1), (2, 2)]

    for i, event_data in enumerate(events_data, 1):
        await session.execute(
            text(
                """
            INSERT INTO Event (id, status) VALUES (:id, :status)
        """
            ),
            {
                "id": i,
                "status": event_data["status"],
            },
        )
    for t in tr_ent:
        await session.execute(
            text(
                "INSERT INTO event_activity (event_id, activity_id) \
                VALUES (:event_id, :activity_id)"
            ),
            {"event_id": t[0], "activity_id": t[1]},
        )
    for t in tr_a:
        await session.execute(
            text(
                "INSERT INTO event_lodgings (event_id, lodging_id) \
                VALUES (:event_id, :lodging_id)"
            ),
            {"event_id": t[0], "lodging_id": t[1]},
        )
    route = [
        {
            "program_id": 1,
            "event_id": 1,
            "start_time": datetime(2025, 4, 2, 7, 30, 0),
            "end_time": datetime(2025, 4, 6, 7, 0, 0),
            "type": "Личные",
        },
        {
            "program_id": 9,
            "event_id": 1,
            "start_time": datetime(2025, 4, 3, 7, 30, 0),
            "end_time": datetime(2025, 4, 6, 7, 0, 0),
            "type": "Личные",
        },
        {
            "program_id": 11,
            "event_id": 2,
            "start_time": datetime(2025, 3, 29, 6, 50, 0),
            "end_time": datetime(2025, 4, 5, 22, 45, 0),
            "type": "Личные",
        },
    ]
    for data in route:
        await session.execute(
            text(
                "INSERT INTO session (program_id, event_id, start_time, end_time, type) \
                VALUES (:program_id, :event_id, :start_time, :end_time, :type)"
            ),
            {
                "program_id": data["program_id"],
                "event_id": data["event_id"],
                "start_time": data["start_time"],
                "end_time": data["end_time"],
                "type": data["type"],
            },
        )
    await session.execute(
        text(
            "INSERT INTO users_event (event_id, users_id) VALUES (:event_id, :users_id)"
        ),
        {"event_id": 1, "users_id": 1},
    )
    await session.execute(
        text(
            "INSERT INTO users_event (event_id, users_id) VALUES (:event_id, :users_id)"
        ),
        {"event_id": 2, "users_id": 1},
    )
    await session.execute(
        text("SELECT setval('event_id_seq', (SELECT MAX(id) FROM event))")
    )
    await session.commit()


@pytest_asyncio.fixture
async def venue_repo(db_session: AsyncSession) -> VenueRepository:
    return VenueRepository(db_session)


@pytest_asyncio.fixture
async def venue_service(venue_repo: VenueRepository) -> VenueService:
    return VenueService(venue_repo)


@pytest_asyncio.fixture
async def lodging_repo(
    db_session: AsyncSession, venue_repo: VenueRepository
) -> LodgingRepository:
    return LodgingRepository(db_session, venue_repo)


@pytest_asyncio.fixture
async def lodging_service(
    lodging_repo: LodgingRepository,
) -> LodgingService:
    return LodgingService(lodging_repo)


@pytest_asyncio.fixture
async def activity_repo(
    db_session: AsyncSession, venue_repo: VenueRepository
) -> ActivityRepository:
    return ActivityRepository(db_session, venue_repo)


@pytest_asyncio.fixture
async def activity_service(
    activity_repo: ActivityRepository,
) -> ActivityService:
    return ActivityService(activity_repo)


@pytest_asyncio.fixture
async def program_repo(
    db_session: AsyncSession, venue_repo: VenueRepository
) -> ProgramRepository:
    return ProgramRepository(db_session, venue_repo)


@pytest_asyncio.fixture
async def program_service(
    program_repo: ProgramRepository,
) -> ProgramService:
    return ProgramService(program_repo)


@pytest_asyncio.fixture
async def user_repo(db_session: AsyncSession) -> UserRepository:
    return UserRepository(db_session)


@pytest_asyncio.fixture
async def user_service(user_repo: UserRepository) -> UserService:
    return UserService(user_repo)


@pytest_asyncio.fixture
async def auth_service(user_repo: UserRepository) -> AuthService:
    return AuthService(user_repo)


@pytest_asyncio.fixture
async def session_repo(
    db_session: AsyncSession,
    program_repo: ProgramRepository,
    event_repo: EventRepository,
) -> SessionRepository:
    return SessionRepository(db_session, program_repo, event_repo)


@pytest_asyncio.fixture
async def session_service(session_repo: SessionRepository) -> SessionService:
    return SessionService(session_repo)


@pytest_asyncio.fixture
async def event_repo(
    db_session: AsyncSession,
    user_repo: UserRepository,
    lodging_repo: LodgingRepository,
    activity_repo: ActivityRepository,
) -> EventRepository:
    return EventRepository(
        db_session, user_repo, activity_repo, lodging_repo
    )


@pytest_asyncio.fixture
async def event_service(db_session: AsyncSession) -> EventService:
    user_repo = UserRepository(db_session)
    venue_repo = VenueRepository(db_session)
    activity_repo = ActivityRepository(db_session, venue_repo)
    lodging_repo = LodgingRepository(db_session, venue_repo)
    event_repo = EventRepository(
        db_session, user_repo, activity_repo, lodging_repo
    )
    return EventService(event_repo)


def pytest_configure() -> None:
    if os.getenv("ENABLE_TRACING", "0") != "1":
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        service_name = "ppo-tests"
        provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
        exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        try:
            RequestsInstrumentor().instrument()
        except Exception:
            pass

        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
            HTTPXClientInstrumentor().instrument()
        except Exception:
            pass
    except ImportError:
        pass



