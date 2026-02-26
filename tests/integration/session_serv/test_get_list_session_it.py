from __future__ import annotations

import pytest

from services.session_service import SessionService


EXPECTED_COUNT = 3
SESSION_ID_ONE = 1
SESSION_ID_TWO = 2


@pytest.mark.asyncio
async def test_get_all_sessions_success(session_service: SessionService) -> None:
    sessions = await session_service.get_all_sessions()

    assert len(sessions) == EXPECTED_COUNT
    assert any(session.session_id == SESSION_ID_ONE for session in sessions)
    assert any(session.session_id == SESSION_ID_TWO for session in sessions)
    assert any(session.session_id == EXPECTED_COUNT for session in sessions)
