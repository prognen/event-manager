from __future__ import annotations

from datetime import datetime

import pytest

from models.lodging import Lodging
from models.venue import Venue
from models.activity import Activity
from models.event import Event
from models.user import User
from services.event_service import EventService


@pytest.mark.asyncio
async def test_add_event_duplicate_id(event_service: EventService) -> None:
    us = [
        User(
            user_id=1,
            fio="Власов Егор Витальевич",
            number_passport="1111111111",
            phone_number="89261111111",
            email="egor@vlasov.info",
            login="user1",
            password="123!e5T78",
            is_admin=False,
        )
    ]
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
    new_event = Event(
        event_id=1,
        status="Активное",
        users=us,
        accommodations=accs,
        entertainments=ents,
    )

    res = await event_service.add(new_event)
    assert res is not None



