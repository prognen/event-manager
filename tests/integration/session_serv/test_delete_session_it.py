from __future__ import annotations

import pytest

from sqlalchemy.ext.asyncio import AsyncSession

from services.session_service import SessionService


@pytest.mark.asyncio
async def test_delete_route_success(
    session_service: SessionService, db_session: AsyncSession
) -> None:
    await session_service.delete(1)

    route = await session_service.get_by_id(1)
    assert route is None



