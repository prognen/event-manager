from __future__ import annotations

import pytest

from services.activity_service import ActivityService


@pytest.mark.asyncio
async def test_get_empty_list_entertainments(
    activity_service: ActivityService,
) -> None:
    await activity_service.delete(1)
    await activity_service.delete(2)
    entertainments = await activity_service.get_list()

    assert len(entertainments) == 0



