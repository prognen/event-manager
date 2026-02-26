from __future__ import annotations

import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from services.lodging_service import LodgingService


@pytest.mark.asyncio
async def test_delete_existing_accommodation(
    lodging_service: LodgingService, db_session: AsyncSession
) -> None:
    await lodging_service.delete(1)
    deleted = await lodging_service.get_by_id(1)
    assert deleted is None



