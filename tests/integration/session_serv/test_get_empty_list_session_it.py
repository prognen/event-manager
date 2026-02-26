from __future__ import annotations

import pytest

from services.session_service import SessionService


@pytest.mark.asyncio
async def test_get_empty_sessions(session_service: SessionService) -> None:
    for i in range(1, 4):
        await session_service.delete(i)
    sessions = await session_service.get_all_sessions()

    assert len(sessions) == 0


