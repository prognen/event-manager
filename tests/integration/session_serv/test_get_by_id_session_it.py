from __future__ import annotations

import pytest

from services.session_service import SessionService


@pytest.mark.asyncio
async def test_get_session_by_id_success(session_service: SessionService) -> None:
    session = await session_service.get_by_id(1)

    assert session is not None
    assert session.session_id == 1
    assert session.type == "Личные"


