from __future__ import annotations

from datetime import datetime

import pytest

from models.lodging import Lodging
from models.venue import Venue
from models.program import DirectoryRoute
from models.activity import Activity
from models.session import Route
from models.event import Event
from models.user import User
from services.session_service import SessionService


@pytest.mark.asyncio
async def test_update_non_existing_route_raises(session_service: SessionService) -> None:
    d_route = DirectoryRoute(
        program_id=1,
        type_transport="Паром",
        cost=3987,
        distance=966,
        from_venue=Venue(venue_id=3, name="Санкт-Петербург"),
        destination_city=Venue(venue_id=5, name="Калининград"),
    )
    user = User(
        user_id=1,
        fio="Власов Егор Витальевич",
        number_passport="1111111111",
        phone_number="89261111111",
        email="egor@vlasov.info",
        login="user1",
        password="123!e5T78",
        is_admin=False,
    )
    accs = [
        Lodging(
            lodging_id=1,
            price=46840,
            address="Улица Гоголя, 12",
            name="Four Seasons",
            type="Отель",
            rating=5,
            check_in=datetime(2025, 3, 29, 12, 30, 0),
            check_out=datetime(2025, 4, 5, 18, 0, 0),
            Venue=Venue(venue_id=1, name="Москва"),
        ),
        Lodging(
            lodging_id=2,
            price=7340,
            address="Улица Толстого, 134",
            name="Мир",
            type="Хостел",
            rating=4,
            check_in=datetime(2025, 4, 2, 12, 30, 0),
            check_out=datetime(2025, 4, 5, 18, 0, 0),
            Venue=Venue(venue_id=1, name="Москва"),
        ),
    ]
    ents = [
        Activity(
            activity_id=1,
            duration="4 часа",
            address="Главная площадь",
            activity_type="Концерт",
            activity_time=datetime(2025, 4, 10, 16, 0, 0),
            Venue=Venue(venue_id=1, name="Москва"),
        ),
        Activity(
            activity_id=2,
            duration="3 часа",
            address="ул. Кузнецова, 4",
            activity_type="Выставка",
            activity_time=datetime(2025, 4, 5, 10, 0, 0),
            Venue=Venue(venue_id=1, name="Москва"),
        ),
    ]
    travels = Event(
        event_id=1,
        status="Активное",
        users=[user],
        accommodations=accs,
        entertainments=ents,
    )
    non_existing_route = Route(
        route_id=999,
        d_route=d_route,
        travels=travels,
        start_time=datetime(2025, 5, 1, 10, 0, 0),
        end_time=datetime(2025, 5, 5, 18, 0, 0),
        type="Личные",
    )
    await session_service.update(non_existing_route)
    result = await session_service.get_by_id(999)
    assert result is None



