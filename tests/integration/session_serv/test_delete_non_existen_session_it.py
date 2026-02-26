from __future__ import annotations

import pytest

from services.session_service import SessionService


@pytest.mark.asyncio
async def test_delete_non_existing_session_raises(session_service: SessionService) -> None:
    with pytest.raises(ValueError):
        await session_service.delete(999)



