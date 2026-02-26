from __future__ import annotations

from datetime import datetime

import pytest

from models.venue import Venue
from models.activity import Activity
from services.activity_service import ActivityService


@pytest.mark.asyncio
async def test_update_non_existing_entertainment_raises(
    activity_service: ActivityService,
) -> None:
    non_existing = Activity(
        activity_id=999,
        duration="2 часа",
        address="test",
        activity_type="Музей",
        activity_time=datetime(2025, 1, 1, 12, 0, 0),
        Venue=(Venue(venue_id=1, name="Москва")),
    )

    await activity_service.update(non_existing)

    result = await activity_service.get_by_id(999)
    assert result is None



