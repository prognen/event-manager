from __future__ import annotations

import pytest

from services.activity_service import ActivityService


@pytest.mark.asyncio
async def test_get_entertainment_by_id_success(
    activity_service: ActivityService,
) -> None:
    activity = await activity_service.get_by_id(1)

    assert activity is not None
    assert activity.activity_type == "Нетворкинг"
    assert activity.activity_id == 1


