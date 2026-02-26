from __future__ import annotations

import pytest

from services.lodging_service import LodgingService


TWO = 2


@pytest.mark.asyncio
async def test_get_all_accommodations_success(
    lodging_service: LodgingService,
) -> None:
    accommodations = await lodging_service.get_list()

    assert len(accommodations) == TWO
    names = [acc.name for acc in accommodations]
    assert "ABC" in names
    assert "Four Seasons" in names



