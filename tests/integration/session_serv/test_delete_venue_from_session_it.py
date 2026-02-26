from __future__ import annotations

import pytest

from services.session_service import SessionService


@pytest.mark.asyncio
async def test_delete_venue_from_session_success(session_service: SessionService) -> None:
    await session_service.delete_venue_from_session(1, 3)


