from __future__ import annotations

from datetime import datetime

import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from models.venue import Venue
from models.activity import Activity
from services.activity_service import ActivityService


@pytest.mark.asyncio
async def test_update_existing_entertainment(
    activity_service: ActivityService, db_session: AsyncSession
) -> None:
    updated = Activity(
        activity_id=1,
        duration="2 часа",
        address="test",
        activity_type="Мастер-класс",
        activity_time=datetime(2025, 1, 1, 12, 0, 0),
        venue=(Venue(venue_id=1, name="Москва")),
    )

    result = await activity_service.update(updated)

    assert result is not None
    assert result.activity_type == "Мастер-класс"
    assert result.activity_id == 1


