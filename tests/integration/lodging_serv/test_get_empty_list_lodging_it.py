from __future__ import annotations

import pytest

from services.lodging_service import LodgingService


@pytest.mark.asyncio
async def test_get_empty_list_accommodations(
    lodging_service: LodgingService,
) -> None:
    await lodging_service.delete(1)
    await lodging_service.delete(2)
    accommodations = await lodging_service.get_list()

    assert len(accommodations) == 0



