from __future__ import annotations

import pytest

from services.activity_service import ActivityService


@pytest.mark.asyncio
async def test_get_entertainment_by_id_not_found(
    activity_service: ActivityService,
) -> None:
    Activity = await activity_service.get_by_id(999)

    assert Activity is None



