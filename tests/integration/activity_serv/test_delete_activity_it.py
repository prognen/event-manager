from __future__ import annotations

import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from services.activity_service import ActivityService


@pytest.mark.asyncio
async def test_delete_existing_entertainment(
    activity_service: ActivityService, db_session: AsyncSession
) -> None:
    await activity_service.delete(1)
    deleted = await activity_service.get_by_id(1)
    assert deleted is None



