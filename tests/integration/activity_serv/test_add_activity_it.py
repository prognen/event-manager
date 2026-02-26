from __future__ import annotations

from datetime import datetime

import pytest

from models.venue import Venue
from models.activity import Activity
from services.activity_service import ActivityService


THIRD = 3


@pytest.mark.asyncio
async def test_add_duplicate_name_entertainment_raises(
    activity_service: ActivityService,
) -> None:
    new_entertainment = Activity(
        activity_id=3,
        duration="2 часа",
        address="test",
        activity_type="Мастер-класс",
        activity_time=datetime(2025, 1, 1, 12, 0, 0),
        venue=Venue(venue_id=1, name="Москва"),
    )
    await activity_service.add(new_entertainment)
    result = await activity_service.get_by_id(3)
    assert result is not None
    assert result.activity_type == "Мастер-класс"
    assert result.activity_id == THIRD


