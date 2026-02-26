from __future__ import annotations

import pytest

from services.session_service import SessionService


@pytest.mark.asyncio
async def test_get_sessions_by_type_success(session_service: SessionService) -> None:
    sessions = await session_service.get_sessions_by_type("Личные")

    assert len(sessions) > 0
    assert all(session.type == "Личные" for session in sessions)


