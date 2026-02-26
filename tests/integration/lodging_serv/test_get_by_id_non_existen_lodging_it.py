from __future__ import annotations

import pytest

from services.lodging_service import LodgingService


@pytest.mark.asyncio
async def test_get_accommodation_by_id_not_found(
    lodging_service: LodgingService,
) -> None:
    Lodging = await lodging_service.get_by_id(999)

    assert Lodging is None



