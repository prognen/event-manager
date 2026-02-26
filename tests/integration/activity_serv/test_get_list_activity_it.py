from __future__ import annotations

import pytest

from services.activity_service import ActivityService


TWO = 2


@pytest.mark.asyncio
async def test_get_all_entertainments_success(
    activity_service: ActivityService,
) -> None:
    entertainments = await activity_service.get_list()

    assert len(entertainments) == TWO
    names = [ent.activity_type for ent in entertainments]
    assert "Нетворкинг" in names
    assert "Выставка" in names


