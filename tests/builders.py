"""
Object Mother / Data Builder pattern для генерации тестовых объектов.

Object Mother — предоставляет фабричные методы с разумными значениями по умолчанию
для каждого класса предметной области. Позволяет тестам создавать объекты
с минимальным количеством кода и явно указывать только те поля, которые важны
для конкретного теста.

Data Builder — позволяет создавать объекты через цепочку методов (fluent API),
переопределяя только нужные поля.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from models.activity import Activity
from models.event import Event
from models.lodging import Lodging
from models.program import Program
from models.session import Session
from models.user import User
from models.venue import Venue


# ---------------------------------------------------------------------------
# Venue (Площадка)
# ---------------------------------------------------------------------------

class VenueBuilder:
    """Data Builder для Venue."""

    def __init__(self) -> None:
        self._venue_id: int = 1
        self._name: str = "Конгресс-центр Москва"

    def with_id(self, venue_id: int) -> "VenueBuilder":
        self._venue_id = venue_id
        return self

    def with_name(self, name: str) -> "VenueBuilder":
        self._name = name
        return self

    def build(self) -> Venue:
        return Venue(venue_id=self._venue_id, name=self._name)


class VenueMother:
    """Object Mother для Venue."""

    @staticmethod
    def default() -> Venue:
        return VenueBuilder().build()

    @staticmethod
    def moscow() -> Venue:
        return VenueBuilder().with_id(1).with_name("Конгресс-центр Москва").build()

    @staticmethod
    def saint_petersburg() -> Venue:
        return VenueBuilder().with_id(2).with_name("Экспофорум СПб").build()

    @staticmethod
    def with_id(venue_id: int) -> Venue:
        return VenueBuilder().with_id(venue_id).build()


# ---------------------------------------------------------------------------
# Activity (Активность)
# ---------------------------------------------------------------------------

class ActivityBuilder:
    """Data Builder для Activity."""

    def __init__(self) -> None:
        self._activity_id: int = 1
        self._duration: str = "2 часа"
        self._address: str = "Большой зал, 3 этаж"
        self._activity_type: str = "Выставка"
        self._activity_time: datetime = datetime(2025, 6, 10, 10, 0, 0)
        self._venue: Optional[Venue] = None

    def with_id(self, activity_id: int) -> "ActivityBuilder":
        self._activity_id = activity_id
        return self

    def with_type(self, activity_type: str) -> "ActivityBuilder":
        self._activity_type = activity_type
        return self

    def with_time(self, activity_time: datetime) -> "ActivityBuilder":
        self._activity_time = activity_time
        return self

    def with_duration(self, duration: str) -> "ActivityBuilder":
        self._duration = duration
        return self

    def with_address(self, address: str) -> "ActivityBuilder":
        self._address = address
        return self

    def with_venue(self, venue: Venue) -> "ActivityBuilder":
        self._venue = venue
        return self

    def build(self) -> Activity:
        return Activity(
            activity_id=self._activity_id,
            duration=self._duration,
            address=self._address,
            activity_type=self._activity_type,
            activity_time=self._activity_time,
            venue=self._venue,
        )


class ActivityMother:
    """Object Mother для Activity."""

    @staticmethod
    def default() -> Activity:
        return ActivityBuilder().build()

    @staticmethod
    def exhibition() -> Activity:
        return (
            ActivityBuilder()
            .with_id(1)
            .with_type("Выставка")
            .with_duration("4 часа")
            .with_address("Зал А, 1 этаж")
            .with_time(datetime(2025, 6, 10, 9, 0, 0))
            .build()
        )

    @staticmethod
    def networking() -> Activity:
        return (
            ActivityBuilder()
            .with_id(2)
            .with_type("Нетворкинг")
            .with_duration("2 часа")
            .with_address("Комната 201")
            .with_time(datetime(2025, 6, 10, 14, 0, 0))
            .build()
        )

    @staticmethod
    def with_id(activity_id: int) -> Activity:
        return ActivityBuilder().with_id(activity_id).build()


# ---------------------------------------------------------------------------
# Lodging (Размещение)
# ---------------------------------------------------------------------------

class LodgingBuilder:
    """Data Builder для Lodging."""

    def __init__(self) -> None:
        self._lodging_id: int = 1
        self._price: int = 5000
        self._address: str = "ул. Тверская, 5"
        self._name: str = "Отель Метрополь"
        self._type: str = "Отель"
        self._rating: int = 4
        self._check_in: datetime = datetime(2025, 6, 9, 14, 0, 0)
        self._check_out: datetime = datetime(2025, 6, 12, 12, 0, 0)
        self._venue: Optional[Venue] = None

    def with_id(self, lodging_id: int) -> "LodgingBuilder":
        self._lodging_id = lodging_id
        return self

    def with_name(self, name: str) -> "LodgingBuilder":
        self._name = name
        return self

    def with_price(self, price: int) -> "LodgingBuilder":
        self._price = price
        return self

    def with_type(self, lodging_type: str) -> "LodgingBuilder":
        self._type = lodging_type
        return self

    def with_rating(self, rating: int) -> "LodgingBuilder":
        self._rating = rating
        return self

    def with_dates(self, check_in: datetime, check_out: datetime) -> "LodgingBuilder":
        self._check_in = check_in
        self._check_out = check_out
        return self

    def with_venue(self, venue: Venue) -> "LodgingBuilder":
        self._venue = venue
        return self

    def build(self) -> Lodging:
        return Lodging(
            lodging_id=self._lodging_id,
            price=self._price,
            address=self._address,
            name=self._name,
            type=self._type,
            rating=self._rating,
            check_in=self._check_in,
            check_out=self._check_out,
            venue=self._venue,
        )


class LodgingMother:
    """Object Mother для Lodging."""

    @staticmethod
    def default() -> Lodging:
        return LodgingBuilder().build()

    @staticmethod
    def hotel() -> Lodging:
        return (
            LodgingBuilder()
            .with_id(1)
            .with_name("Отель Метрополь")
            .with_type("Отель")
            .with_rating(5)
            .with_price(8000)
            .build()
        )

    @staticmethod
    def hostel() -> Lodging:
        return (
            LodgingBuilder()
            .with_id(2)
            .with_name("Хостел Центральный")
            .with_type("Хостел")
            .with_rating(3)
            .with_price(1200)
            .build()
        )

    @staticmethod
    def with_id(lodging_id: int) -> Lodging:
        return LodgingBuilder().with_id(lodging_id).build()


# ---------------------------------------------------------------------------
# User (Пользователь)
# ---------------------------------------------------------------------------

class UserBuilder:
    """Data Builder для User."""

    def __init__(self) -> None:
        self._user_id: int = 1
        self._fio: str = "Иванов Иван Иванович"
        self._number_passport: str = "1234567890"
        self._phone_number: str = "89261234567"
        self._email: str = "ivan@example.com"
        self._login: str = "ivan_user"
        self._password: str = "SecurePass123!"

    def with_id(self, user_id: int) -> "UserBuilder":
        self._user_id = user_id
        return self

    def with_fio(self, fio: str) -> "UserBuilder":
        self._fio = fio
        return self

    def with_email(self, email: str) -> "UserBuilder":
        self._email = email
        return self

    def with_login(self, login: str) -> "UserBuilder":
        self._login = login
        return self

    def build(self) -> User:
        return User(
            user_id=self._user_id,
            fio=self._fio,
            number_passport=self._number_passport,
            phone_number=self._phone_number,
            email=self._email,
            login=self._login,
            password=self._password,
        )


class UserMother:
    """Object Mother для User."""

    @staticmethod
    def default() -> User:
        return UserBuilder().build()

    @staticmethod
    def admin() -> User:
        return (
            UserBuilder()
            .with_id(1)
            .with_fio("Администратор Системы")
            .with_email("admin@eventmanager.ru")
            .with_login("admin")
            .build()
        )

    @staticmethod
    def participant() -> User:
        return (
            UserBuilder()
            .with_id(2)
            .with_fio("Петров Пётр Петрович")
            .with_email("petrov@example.com")
            .with_login("petrov")
            .build()
        )

    @staticmethod
    def with_id(user_id: int) -> User:
        return UserBuilder().with_id(user_id).build()


# ---------------------------------------------------------------------------
# Event (Мероприятие)
# ---------------------------------------------------------------------------

class EventBuilder:
    """Data Builder для Event."""

    def __init__(self) -> None:
        self._event_id: int = 1
        self._status: str = "Активное"
        self._users: list[User] = [UserBuilder().build()]
        self._activities: list[Activity] = [ActivityBuilder().build()]
        self._lodgings: list[Lodging] = [LodgingBuilder().build()]

    def with_id(self, event_id: int) -> "EventBuilder":
        self._event_id = event_id
        return self

    def with_status(self, status: str) -> "EventBuilder":
        self._status = status
        return self

    def with_users(self, users: list[User]) -> "EventBuilder":
        self._users = users
        return self

    def with_activities(self, activities: list[Activity]) -> "EventBuilder":
        self._activities = activities
        return self

    def with_lodgings(self, lodgings: list[Lodging]) -> "EventBuilder":
        self._lodgings = lodgings
        return self

    def build(self) -> Event:
        return Event(
            event_id=self._event_id,
            status=self._status,
            users=self._users,
            activities=self._activities,
            lodgings=self._lodgings,
        )


class EventMother:
    """Object Mother для Event."""

    @staticmethod
    def default() -> Event:
        return EventBuilder().build()

    @staticmethod
    def active() -> Event:
        return (
            EventBuilder()
            .with_id(1)
            .with_status("Активное")
            .with_users([UserMother.default()])
            .with_activities([ActivityMother.exhibition()])
            .with_lodgings([LodgingMother.hotel()])
            .build()
        )

    @staticmethod
    def completed() -> Event:
        return (
            EventBuilder()
            .with_id(2)
            .with_status("Завершено")
            .with_users([UserMother.default()])
            .with_activities([ActivityMother.networking()])
            .with_lodgings([LodgingMother.hostel()])
            .build()
        )

    @staticmethod
    def cancelled() -> Event:
        return (
            EventBuilder()
            .with_id(3)
            .with_status("Отменено")
            .with_users([UserMother.default()])
            .with_activities([ActivityMother.exhibition()])
            .with_lodgings([LodgingMother.default()])
            .build()
        )

    @staticmethod
    def with_id(event_id: int) -> Event:
        return EventBuilder().with_id(event_id).build()


# ---------------------------------------------------------------------------
# Program (Программа перемещения между площадками)
# ---------------------------------------------------------------------------

class ProgramBuilder:
    """Data Builder для Program."""

    def __init__(self) -> None:
        self._program_id: int = 1
        self._type_transport: str = "Автобус"
        self._cost: int = 2000
        self._distance: int = 500
        self._from_venue: Optional[Venue] = None
        self._to_venue: Optional[Venue] = None

    def with_id(self, program_id: int) -> "ProgramBuilder":
        self._program_id = program_id
        return self

    def with_transport(self, type_transport: str) -> "ProgramBuilder":
        self._type_transport = type_transport
        return self

    def with_cost(self, cost: int) -> "ProgramBuilder":
        self._cost = cost
        return self

    def with_distance(self, distance: int) -> "ProgramBuilder":
        self._distance = distance
        return self

    def with_from_venue(self, venue: Venue) -> "ProgramBuilder":
        self._from_venue = venue
        return self

    def with_to_venue(self, venue: Venue) -> "ProgramBuilder":
        self._to_venue = venue
        return self

    def build(self) -> Program:
        return Program(
            program_id=self._program_id,
            type_transport=self._type_transport,
            cost=self._cost,
            distance=self._distance,
            from_venue=self._from_venue,
            to_venue=self._to_venue,
        )


class ProgramMother:
    """Object Mother для Program."""

    @staticmethod
    def default() -> Program:
        return (
            ProgramBuilder()
            .with_from_venue(VenueMother.moscow())
            .with_to_venue(VenueMother.saint_petersburg())
            .build()
        )

    @staticmethod
    def by_train() -> Program:
        return (
            ProgramBuilder()
            .with_id(1)
            .with_transport("Поезд")
            .with_cost(1911)
            .with_distance(515)
            .with_from_venue(VenueMother.moscow())
            .with_to_venue(VenueMother.saint_petersburg())
            .build()
        )

    @staticmethod
    def by_plane() -> Program:
        return (
            ProgramBuilder()
            .with_id(2)
            .with_transport("Самолет")
            .with_cost(2223)
            .with_distance(467)
            .with_from_venue(VenueMother.moscow())
            .with_to_venue(VenueMother.saint_petersburg())
            .build()
        )

    @staticmethod
    def with_id(program_id: int) -> Program:
        return ProgramBuilder().with_id(program_id).build()


# ---------------------------------------------------------------------------
# Session (Сессия мероприятия)
# ---------------------------------------------------------------------------

class SessionBuilder:
    """Data Builder для Session."""

    def __init__(self) -> None:
        self._session_id: int = 1
        self._program: Optional[Program] = None
        self._event: Optional[Event] = None
        self._start_time: datetime = datetime(2025, 6, 10, 9, 0, 0)
        self._end_time: datetime = datetime(2025, 6, 10, 18, 0, 0)
        self._type: str = "Официальные"

    def with_id(self, session_id: int) -> "SessionBuilder":
        self._session_id = session_id
        return self

    def with_program(self, program: Program) -> "SessionBuilder":
        self._program = program
        return self

    def with_event(self, event: Event) -> "SessionBuilder":
        self._event = event
        return self

    def with_start_time(self, start_time: datetime) -> "SessionBuilder":
        self._start_time = start_time
        return self

    def with_end_time(self, end_time: datetime) -> "SessionBuilder":
        self._end_time = end_time
        return self

    def with_type(self, session_type: str) -> "SessionBuilder":
        self._type = session_type
        return self

    def build(self) -> Session:
        return Session(
            session_id=self._session_id,
            program=self._program,
            event=self._event,
            start_time=self._start_time,
            end_time=self._end_time,
            type=self._type,
        )


class SessionMother:
    """Object Mother для Session."""

    @staticmethod
    def default() -> Session:
        return (
            SessionBuilder()
            .with_program(ProgramMother.default())
            .with_event(EventMother.default())
            .build()
        )

    @staticmethod
    def official() -> Session:
        return (
            SessionBuilder()
            .with_id(1)
            .with_type("Официальные")
            .with_program(ProgramMother.by_train())
            .with_event(EventMother.active())
            .with_start_time(datetime(2025, 6, 10, 9, 0, 0))
            .with_end_time(datetime(2025, 6, 10, 18, 0, 0))
            .build()
        )

    @staticmethod
    def personal() -> Session:
        return (
            SessionBuilder()
            .with_id(2)
            .with_type("Личные")
            .with_program(ProgramMother.by_plane())
            .with_event(EventMother.active())
            .with_start_time(datetime(2025, 6, 11, 10, 0, 0))
            .with_end_time(datetime(2025, 6, 11, 17, 0, 0))
            .build()
        )

    @staticmethod
    def with_id(session_id: int) -> Session:
        return SessionBuilder().with_id(session_id).build()
