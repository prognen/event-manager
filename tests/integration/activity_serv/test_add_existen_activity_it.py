from __future__ import annotations

import re

from datetime import datetime

import pytest

from models.venue import Venue
from models.activity import Activity
from services.activity_service import ActivityService


@pytest.mark.asyncio
async def test_add_duplicate_name_entertainment_raises(
    activity_service: ActivityService,
) -> None:
    existing_entertainment = Activity(
        activity_id=1,
        duration="4 часа",
        address="Главная площадь",
        activity_type="Нетворкинг",
        activity_time=datetime(2025, 4, 10, 16, 0, 0),
        venue=Venue(venue_id=1, name="Москва"),
    )
    with pytest.raises(
        ValueError, match=re.escape("Активность c таким ID уже существует.")
    ):
        await activity_service.add(existing_entertainment)



