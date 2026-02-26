from __future__ import annotations

import pytest

from services.activity_service import ActivityService


@pytest.mark.asyncio
async def test_delete_non_existing_entertainment_raises(
    activity_service: ActivityService,
) -> None:
    await activity_service.delete(999)

    acc = await activity_service.get_by_id(999)
    assert acc is None



